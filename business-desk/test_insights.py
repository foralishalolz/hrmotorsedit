"""Owner scope, posted ledger arithmetic and dashboard settings boundaries."""
from datetime import timedelta, date
import json
import tempfile
import unittest

from domain import Desk, Problem
from regional import business_today


class OwnerInsights(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desk = Desk(self.temp.name)
        token, _ = self.desk.setup({'username': 'owner', 'name': 'Owner', 'password': 'fictional-test-password'})
        self.user, _ = self.desk.session(token)
        self.b = self.desk.save_business(self.user, {'data': {'name': 'Test Repairs', 'profile': 'garage'}})
        self.bid = self.b['id']
        self.day = business_today(self.b)
        self.c = self.save('customers', name='Test client')

    def tearDown(self): self.temp.cleanup()
    def save(self, record_kind, **data): return self.desk.save(self.user, self.bid, record_kind, {'data': data})
    def settings(self, **data):
        self.b = self.desk.save_business(self.user, {'id': self.bid, 'version': self.b['version'], 'data': data})
    def invoice(self, amount=100):
        invoice = self.save('invoices', customer_id=self.c['id'], date=self.day, vat_mode='none',
                            due_date=(date.fromisoformat(self.day)-timedelta(days=1)).isoformat(),
                            items=[{'description':'Test service','qty':1,'rate':amount,'tax_rate':0}])
        return self.desk.action(self.user, self.bid, 'invoices', invoice['id'], {'action':'issue','version':invoice['version']})
    def summary(self): return next(x for x in self.desk.portfolio(self.user)['businesses'] if x['id']==self.bid)

    def test_credits_refunds_and_advances_reconcile_with_source_balances(self):
        invoice = self.invoice()
        self.save('payments', invoice_id=invoice['id'], amount=70, date=self.day, method='Cash')
        self.save('credits', invoice_id=invoice['id'], amount=50, date=self.day, reason='Reviewed credit')
        self.save('payments', invoice_id=invoice['id'], amount=10, direction='refund', date=self.day, method='Cash')
        other = self.invoice(50)
        advance = self.save('payments', customer_id=self.c['id'], amount=30, date=self.day, method='Cash')
        self.desk.action(self.user,self.bid,'payments',advance['id'],{'action':'allocate','version':advance['version'],'invoice_id':other['id'],'amount':20})
        opening = self.save('opening_balances', customer_id=self.c['id'], amount=80, date=self.day,
                            source_reference='Approved opening', reconciled=True)
        self.save('payments', opening_balance_id=opening['id'], amount=25, date=self.day, method='Cash')
        summary = self.summary()
        state = self.desk.state(self.user,self.bid)['records']
        expected = sum(x['_balance'] for x in state['invoices'] if x['status']=='issued' and x['_balance']>0)
        expected += sum(x['_balance'] for x in state['opening_balances'] if x['_balance']>0)
        self.assertEqual(summary['outstanding'], expected)
        self.assertEqual(summary['outstanding'], 85)
        self.assertEqual(summary['collected_month'], 115)  # Allocation is not another receipt.
        self.assertEqual(summary['overdue'], 30)

    def test_future_receipts_and_older_months_are_not_current_collections(self):
        self.save('payments', customer_id=self.c['id'], amount=99, date=(date.fromisoformat(self.day)+timedelta(days=1)).isoformat())
        self.save('payments', customer_id=self.c['id'], amount=50, date=self.day[:8]+'01')
        previous = (date.fromisoformat(self.day[:8]+'01')-timedelta(days=1)).isoformat()
        self.save('payments', customer_id=self.c['id'], amount=7, date=previous)
        self.assertEqual(self.summary()['collected_month'], 50)

    def test_draft_invoices_and_negative_customer_credits_are_not_receivables(self):
        self.save('invoices', customer_id=self.c['id'],date=self.day,vat_mode='none',items=[{'description':'Draft','qty':1,'rate':100}])
        self.save('opening_balances', customer_id=self.c['id'], amount=-20, date=self.day,source_reference='Customer credit',reconciled=True)
        self.assertEqual(self.summary()['outstanding'],0)

    def test_currencies_are_separate_and_other_organisation_never_appears(self):
        self.invoice()
        indian = self.desk.save_business(self.user,{'data':{'name':'India Service','country':'IN','profile':'service','state_code':'27'}})
        foreign = {**self.user,'organization_id':'other-organisation'}
        self.desk.save_business(foreign,{'data':{'name':'PRIVATE-SENTINEL'}})
        result=self.desk.portfolio(self.user)
        self.assertEqual(result['total'],2)
        self.assertEqual(set(result['totals']),{'INR','NPR'})
        self.assertEqual(result['totals']['NPR']['outstanding'],100)
        self.assertEqual(result['totals']['INR']['outstanding'],0)
        self.assertNotIn('PRIVATE-SENTINEL',str(result))
        self.assertIn(indian['id'],[b['id'] for b in result['businesses']])

    def test_staff_cannot_request_owner_portfolio(self):
        for role in ('manager','frontdesk','technician','cashier','stock_clerk'):
            with self.subTest(role=role), self.assertRaises(Problem) as error:
                self.desk.portfolio({**self.user,'role':role})
            self.assertEqual(error.exception.status,403)

    def test_pagination_is_bounded_and_page_totals_are_explicit(self):
        for i in range(24): self.desk.save_business(self.user,{'data':{'name':'Branch '+str(i)}})
        first=self.desk.portfolio(self.user)
        second=self.desk.portfolio(self.user,24)
        self.assertEqual((first['total'],first['limit'],len(first['businesses']),len(second['businesses'])),(25,24,24,1))
        self.assertFalse(set(x['id'] for x in first['businesses']) & set(x['id'] for x in second['businesses']))
        self.assertEqual(first['totals_scope'],'visible_businesses')
        self.assertEqual(second['totals']['NPR']['businesses'],1)
        for invalid in (-1,'1.5','x',True,100001):
            with self.subTest(offset=invalid),self.assertRaises(Problem):self.desk.portfolio(self.user,invalid)

    def test_targets_panels_and_stale_settings_versions(self):
        old_version=self.b['version']
        self.settings(monthly_collection_target='25000.25',dashboard_panels=['focus','focus','team'])
        self.assertEqual(self.b['dashboard_panels'],['focus','team'])
        self.assertEqual(self.summary()['monthly_collection_target'],25000.25)
        with self.assertRaises(Problem) as error:
            self.desk.save_business(self.user,{'id':self.bid,'version':old_version,'data':{'monthly_collection_target':1}})
        self.assertEqual(error.exception.status,409)
        self.assertEqual(self.desk.state(self.user,self.bid)['business']['monthly_collection_target'],25000.25)
        for data in ({'monthly_collection_target':-1},{'monthly_collection_target':'nan'},
                     {'dashboard_panels':'focus'},{'dashboard_panels':['private_payroll']}):
            with self.subTest(data=data),self.assertRaises(Problem):self.settings(**data)

    def test_work_and_stock_actions_follow_actual_stage_and_movement(self):
        job=self.save('jobs',name='Repair',customer_id=self.c['id'],stage=self.b['stages'][0],blocker='Waiting for part')
        stock=self.save('stock',name='Filter',cost=1,opening_qty=2,reorder_at=1)
        self.save('movements',item_id=stock['id'],kind='issue',qty=1,unit_cost=1,date=self.day)
        summary=self.summary()
        self.assertEqual(summary['open_work'],1)
        self.assertGreaterEqual(summary['actions_due'],2)
        self.assertTrue(any(x['record_id']==job['id'] for x in summary['next_actions']))
        self.desk.save(self.user,self.bid,'jobs',{'id':job['id'],'version':job['version'],'data':{'stage':self.b['stages'][-1]}})
        self.assertEqual(self.summary()['open_work'],0)

    def test_task_priority_category_and_planned_dates(self):
        high=self.save('followups',name='Promised owner call',priority='high',task_category='work',due_date=self.day,status='open')
        future=(date.fromisoformat(self.day)+timedelta(days=3)).isoformat()
        self.save('followups',name='Later call',priority='normal',task_category='clients',due_date=future,status='open')
        alerts=self.desk.state(self.user,self.bid)['alerts']
        self.assertEqual([(x['record_id'],x['priority']) for x in alerts],[(high['id'],1)])
        for values in ({'priority':'secret'},{'task_category':'unknown'}):
            with self.assertRaises(Problem):self.save('followups',name='Invalid',**values)

    def test_old_business_settings_can_open_owner_overview(self):
        self.save('jobs',name='Previously recorded work',customer_id=self.c['id'],stage='Intake')
        legacy={k:v for k,v in self.b.items() if k not in ('stages','dashboard_panels','monthly_collection_target')}
        with self.desk.connect() as conn:
            conn.execute('UPDATE businesses SET data=? WHERE id=?',(json.dumps(legacy),self.bid))
        summary=self.summary()
        self.assertEqual(summary['open_work'],1)
        self.assertEqual(summary['monthly_collection_target'],0)


if __name__=='__main__': unittest.main()
