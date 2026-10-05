"""Financial regression cases plus real SQLite permissions and saved source records."""
from datetime import date, timedelta
from decimal import Decimal
import csv
import io
import tempfile
import unittest
from analytics import analyse, period_dates, record_day, split_credit
from domain import Desk, Problem, KINDS, calculate
from regional import business_today


class OperatingAnalytics(unittest.TestCase):
    def setUp(self):
        self.records={kind:[] for kind in KINDS}
        self.business={'id':'business','name':'Test Repairs','trading_name':'Repair Studio','currency':'NPR','country':'NP','stages':['Intake','Delivered']}
        self.first,self.last=date(2026,9,1),date(2026,9,30)
        self.records['customers']=[{'id':'client','name':'Test Client'}]
    def bill(self,identity='bill',day='2026-09-10',items=None,**values):
        row={'id':identity,'date':day,'due_date':'2026-09-20','status':'issued','number':identity,'customer_id':'client','vat_mode':'none',
             'items':items or [{'description':'Repair','qty':1,'rate':100,'unit_cost':30}],**values}
        row['totals_snapshot']=calculate(row);self.records['invoices'].append(row);return row
    def report(self):return analyse(self.business,self.records,self.first,self.last)

    def test_sales_profit_tax_and_cash_are_distinct_and_payroll_commissions_count_once(self):
        self.bill(items=[{'description':'Parts','qty':2,'rate':100,'unit_cost':30,'category':'Parts'},
                         {'description':'Fitting','qty':1,'rate':300,'unit_cost':90,'category':'Labour'}],vat_mode='added',vat_rate=13)
        self.records['expenses']=[{'id':'e','name':'Rent','date':'2026-09-10','amount':50,'category':'Rent'},
                                  {'id':'w','name':'Withdrawal','date':'2026-09-10','amount':20,'expense_treatment':'Owner withdrawal'}]
        self.records['payroll']=[{'id':'p','status':'paid','start_date':'2026-09-01','end_date':'2026-09-30','total_cost':120,'total_net':105,
                                 'commission_ids':['inside'],'paid_at':'2026-09-30T10:00:00+00:00'}]
        self.records['commissions']=[{'id':'inside','status':'paid','amount':10,'date':'2026-09-10','payroll_id':'p'},
                                     {'id':'outside','status':'approved','amount':15,'date':'2026-09-10'}]
        self.records['payments']=[{'id':'payment','date':'2026-09-10','invoice_id':'bill','amount':100},
                                  {'id':'advance','date':'2026-09-10','customer_id':'client','amount':40}]
        self.records['supplier_payments']=[{'id':'s','date':'2026-09-12','amount':30}]
        r=self.report();s=r['summary']
        self.assertEqual((s['sales'],s['tax'],s['direct_cost'],s['payroll'],s['commissions']),(500,65,60,120,15))
        self.assertEqual((s['operating_result'],s['cash_movement'],s['receipts'],s['outflow']),(255,-65,140,205))
        self.assertEqual(r['receivables']['outstanding'],465)

    def test_restocked_returns_reverse_cost_but_manual_credits_do_not(self):
        self.bill(items=[{'description':'Filter','qty':2,'rate':100,'unit_cost':40,'category':'Parts'}])
        self.records['credits']=[{'id':'return','invoice_id':'bill','date':'2026-09-15','amount':100,'net':100,'tax':0,
                                  'return_lines':[{'line_index':0,'qty':1,'restock':True}]},
                                 {'id':'manual','invoice_id':'bill','date':'2026-09-16','amount':25,'net':25,'tax':0}]
        r=self.report();self.assertEqual((r['summary']['sales'],r['summary']['direct_cost'],r['summary']['operating_result']),(75,40,35))
        self.assertEqual(r['services'][0]['contribution'],35);self.assertEqual(r['quality']['manual_credits'],1)

    def test_credit_in_current_period_reduces_older_sale_without_counting_old_revenue(self):
        self.bill(day='2026-08-15')
        self.records['credits']=[{'id':'credit','invoice_id':'bill','date':'2026-09-10','amount':20,'net':20,'tax':0}]
        r=self.report();self.assertEqual((r['summary']['sales'],r['summary']['direct_cost']),(-20,0))
        self.assertEqual(r['clients'][0]['sales'],-20);self.assertEqual(r['previous']['sales'],100)

    def test_advance_allocation_not_double_cash_and_future_receipt_not_historical_balance(self):
        self.bill()
        self.records['payments']=[{'id':'a','date':'2026-09-10','amount':40,'customer_id':'client'},
                                  {'id':'f','date':'2026-10-01','amount':60,'invoice_id':'bill'}]
        self.records['allocations']=[{'id':'x','date':'2026-09-11','invoice_id':'bill','amount':40}]
        r=self.report();self.assertEqual(r['summary']['receipts'],40);self.assertEqual(r['receivables']['overdue'],60)

    def test_drafts_and_future_bills_excluded_and_opening_only_has_no_billed_history(self):
        self.bill(status='draft');self.bill(identity='future',day='2026-10-01')
        self.records['opening_balances']=[{'id':'o','date':'2026-08-01','due_date':'2026-06-01','amount':75,'customer_id':'client'}]
        r=self.report();self.assertEqual(r['summary']['sales'],0);self.assertEqual(r['receivables']['ageing'][-1]['amount'],75)
        self.assertEqual(r['clients'][0]['segment'],'No billed history')

    def test_expense_classes_exclude_inventory_capital_and_payout_from_result(self):
        classes=['Inventory purchase','Payroll payout','Staff advance','Capital asset','Tax payment','Owner withdrawal']
        self.records['expenses']=[{'id':str(i),'name':t,'date':'2026-09-10','amount':10,'expense_treatment':t} for i,t in enumerate(classes)]
        r=self.report();self.assertEqual(r['summary']['operating_result'],0);self.assertEqual(r['summary']['outflow'],60)
        self.assertEqual(len(r['excluded_expenses']),6)

    def test_cent_payroll_allocation_is_nonnegative_and_sums_exactly_across_ranges(self):
        self.records['payroll']=[{'id':'p','status':'approved','start_date':'2026-09-01','end_date':'2026-09-30','total_cost':0.16}]
        r=self.report();wages=[Decimal(str(x['payroll'])) for x in r['trend']]
        self.assertTrue(all(x>=0 for x in wages));self.assertEqual(sum(wages),Decimal('0.16'))
        self.first=date(2026,9,16);right=self.report()['summary']['payroll'];self.first=date(2026,9,1);self.last=date(2026,9,15)
        self.assertEqual(Decimal(str(right))+Decimal(str(self.report()['summary']['payroll'])),Decimal('0.16'))

    def test_many_small_credit_shares_never_negative_and_total_is_exact(self):
        total=calculate({'vat_mode':'none','items':[{'description':str(i),'qty':1,'rate':1} for i in range(31)]})
        shares=split_credit({'net':0.16},total)
        self.assertTrue(all(x>=0 for x in shares));self.assertEqual(sum(shares),Decimal('0.16'))

    def test_fully_credited_job_remains_billed_and_loss_recommendation_points_to_it(self):
        self.bill(job_id='j')
        self.records['jobs']=[{'id':'j','name':'Costly repair','date':'2026-09-01','stage':'Delivered','labor_cost':50,'costs_final':True}]
        self.records['credits']=[{'id':'c','invoice_id':'bill','date':'2026-09-15','amount':100,'net':100,'tax':0}]
        r=self.report();self.assertTrue(r['jobs'][0]['billed']);self.assertEqual(r['jobs'][0]['contribution'],-50)
        self.assertTrue(any(x['id']=='job-loss' and x['record_id']=='j' for x in r['recommendations']))

    def test_quality_gaps_and_billed_labour_without_payroll_are_visible(self):
        self.bill(items=[{'description':'Uncosted','qty':1,'rate':100}, {'description':'Labour','qty':1,'rate':100,'category':'Labour'}])
        self.records['expenses']=[{'id':'e','name':'Legacy tools','date':'2026-09-10','amount':20,'category':'Tools'}]
        r=self.report();self.assertEqual(r['quality']['result_status'],'Costs need review')
        self.assertEqual((r['quality']['missing_cost_lines'],r['quality']['unclassified_expenses'],r['quality']['labour_without_payroll']),(1,1,1))
        self.assertTrue({'costs','classify','wages'}.issubset({a['id'] for a in r['recommendations']}))

    def test_highlights_include_worst_service_beyond_the_100_row_table(self):
        self.bill(items=[{'description':str(i),'qty':1,'rate':100+i,'unit_cost':1} for i in range(101)]+[{'description':'Loss service','qty':1,'rate':1,'unit_cost':200}])
        r=self.report();self.assertEqual(len(r['services']),100);self.assertEqual(r['service_total'],102)
        self.assertEqual(r['highlights']['services']['lowest']['name'],'Loss service')

    def test_team_samples_shared_assignments_and_missing_attendance_are_explicit(self):
        self.records['employees']=[{'id':'one','name':'One'},{'id':'two','name':'Two'}]
        self.records['jobs']=[{'id':str(i),'name':'Done '+str(i),'date':'2026-09-02','stage':'Delivered','completion_date':'2026-09-10',
                              'due_date':'2026-09-12','employee_ids':['one','two'],'quality_rating':4,'rework_count':1} for i in range(3)]
        self.records['jobs'].append({'id':'overdue','name':'Blocked','date':'2026-09-15','stage':'Intake','due_date':'2026-09-29','employee_ids':['one']})
        self.records['attendance']=[{'id':'a','employee_id':'one','date':'2026-09-10','status':'approved'}]
        r=self.report();one=next(x for x in r['team'] if x['id']=='one');two=next(x for x in r['team'] if x['id']=='two')
        self.assertEqual((one['assigned'],one['completed'],one['overdue'],one['reviewed']),(4,3,1,3))
        self.assertEqual(two['attendance'],{});self.assertEqual(r['highlights']['team_delivery']['sample'],2)
        self.assertEqual(one['on_time_percent'],100);self.assertEqual(one['quality_rating'],4)

    def test_business_timezone_and_date_range_validation(self):
        self.assertEqual(record_day({'created_at':'2026-09-30T20:00:00+00:00'}),'2026-10-01')
        self.assertEqual(period_dates('','', '2026-10-05'),(date(2026,10,1),date(2026,10,5)))
        for first,last in [('2026-10-06','2026-10-05'),('bad','2026-10-05'),('2025-01-01','2026-10-05'),('2026-10-01','2026-10-06')]:
            with self.assertRaises(Problem):period_dates(first,last,'2026-10-05')


class SavedAnalyticsBoundary(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.desk=Desk(self.temp.name)
        self.token,_=self.desk.setup({'name':'Owner','username':'owner','password':'fictional-password'})
        self.user,_=self.desk.session(self.token)
        self.b=self.desk.save_business(self.user,{'data':{'name':'Real source repairs','profile':'garage'}});self.bid=self.b['id'];self.day=business_today(self.b)
        self.c=self.desk.save(self.user,self.bid,'customers',{'data':{'name':'=Dangerous spreadsheet formula'}})
    def tearDown(self):self.temp.cleanup()
    def save(self,kind,**data):return self.desk.save(self.user,self.bid,kind,{'data':data})
    def test_saved_bill_costs_and_csv_formula_escape_owner_permissions(self):
        invoice=self.save('invoices',customer_id=self.c['id'],date=self.day,vat_mode='none',items=[{'description':'Costed repair','qty':2,'rate':100,'unit_cost':30}])
        self.desk.action(self.user,self.bid,'invoices',invoice['id'],{'action':'issue','version':invoice['version']})
        r=self.desk.analytics(self.user,self.bid);self.assertEqual(r['summary']['operating_result'],140)
        rows=list(csv.reader(io.StringIO(self.desk.analytics_csv(self.user,self.bid).decode('utf-8-sig'))))
        self.assertTrue(any(row[1]=="'=Dangerous spreadsheet formula" for row in rows))
        for role in ['manager','cashier','frontdesk','technician','stock_clerk']:
            with self.assertRaises(Problem) as error:self.desk.analytics({**self.user,'role':role},self.bid)
            self.assertEqual(error.exception.status,403)
    def test_quality_review_requires_owner_final_stage_and_bounded_real_values(self):
        job=self.save('jobs',name='Reviewed work',customer_id=self.c['id'],stage='Intake')
        def update(user,**data):return self.desk.save(user,self.bid,'jobs',{'id':job['id'],'version':job['version'],'data':data})
        for data in [{'quality_rating':6},{'rework_count':1.5},{'completion_date':self.day}]:
            with self.assertRaises(Problem):update(self.user,**data)
        manager={**self.user,'role':'manager','business_ids':'["'+self.bid+'"]'}
        with self.assertRaises(Problem) as error:update(manager,quality_rating=5)
        self.assertEqual(error.exception.status,403)
        done=update(self.user,stage=self.b['stages'][-1],completion_date=self.day,quality_rating=5,rework_count=1,quality_notes='Client confirmed delivery')
        self.assertEqual((done['completion_date'],done['quality_rating'],done['rework_count']),(self.day,5,1))
    def test_invalid_expense_treatment_rejected_and_stock_purchase_not_job_operating_cost(self):
        with self.assertRaises(Problem):self.save('expenses',name='Wrong',amount=10,expense_treatment='Made up')
        job=self.save('jobs',name='Work',customer_id=self.c['id'])
        self.save('expenses',name='Stock purchase',amount=20,job_id=job['id'],expense_treatment='Inventory purchase',date=self.day)
        r=self.desk.analytics(self.user,self.bid);self.assertEqual(r['summary']['expenses'],0)
        self.assertEqual(r['summary']['outflow'],20)
