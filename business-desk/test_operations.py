"""Migration rollback, source reconciliation and policy gates—not mirrored UI tests."""
import base64
import tempfile
import unittest
from domain import Desk, Problem, today
from branding import manifest
from server import print_document

class BusinessOperations(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.desk=Desk(self.temp.name)
        token,_=self.desk.setup({'username':'owner','name':'Owner','password':'fictional-test-password'})
        self.user,_=self.desk.session(token)
        self.b=self.desk.save_business(self.user,{'data':{'name':'Legal Repairs Pvt','profile':'garage'}});self.bid=self.b['id']
        self.c=self.save('customers',name='Fleet',phone='9000000001')
    def tearDown(self): self.temp.cleanup()
    def save(self,kind,**data): return self.desk.save(self.user,self.bid,kind,{'data':data})
    def update(self,row,**data): return self.desk.save(self.user,self.bid,row['type'],{'id':row['id'],'version':row['version'],'data':data})
    def settings(self,**data):
        self.b=self.desk.save_business(self.user,{'id':self.bid,'version':self.b['version'],'data':data})
    def records(self): return self.desk.state(self.user,self.bid)['records']
    def invoice(self,rate=100,job_id=''):
        return self.save('invoices',customer_id=self.c['id'],date=today(),vat_mode='none',job_id=job_id,items=[{'description':'Service','qty':1,'rate':rate,'tax_rate':0}])
    def issue(self,invoice,**payload): return self.desk.action(self.user,self.bid,'invoices',invoice['id'],{'action':'issue','version':invoice['version'],**payload})
    def opening(self,amount=500,source='ledger-1'):
        return self.save('opening_balances',customer_id=self.c['id'],amount=amount,date=today(),source_reference=source,reconciled=True)

    def test_brand_identity_document_and_manifest_snapshot(self):
        self.settings(trading_name='Fleet Works',short_name='Fleet',brand_hex='#ffffff',invoice_footer='Thank you',payment_instructions='Bank reference required')
        inv=self.issue(self.invoice())
        self.settings(trading_name='A different name')
        body=print_document(self.desk,self.user,self.bid,'invoices',inv['id']).decode()
        self.assertIn('Fleet Works',body);self.assertIn('Legal Repairs Pvt',body);self.assertIn('Thank you',body)
        data=manifest({**self.b,'trading_name':'Fleet Works'})
        self.assertEqual(data['name'],'Fleet Works');self.assertIn(self.bid,data['start_url'])
        svg=base64.b64decode(data['icons'][0]['src'].split(',',1)[1]).decode();self.assertIn('fill="#172033"',svg)
    def test_brand_rejects_active_logo_content_and_invalid_colours(self):
        for change in [{'logo_data':'data:image/svg+xml;base64,PHN2Zz4='},{'brand_hex':'red; background:url(x)'},{'logo_data':'data:image/png;base64,'+base64.b64encode(b'<script>').decode()}]:
            with self.assertRaises(Problem):self.settings(**change)
    def test_preview_does_not_post_records_counters_or_audit(self):
        before=self.records();state=self.desk.state(self.user,self.bid)
        data={'kind':'opening_balances','rows':[{'customer_phone':'9000000001','source_reference':'src','amount':200,'date':today()}],'reconciled':True}
        preview=self.desk.import_batch(self.user,self.bid,data,True)
        self.assertEqual(preview['created'],1);self.assertEqual(self.records()['opening_balances'],[])
        self.assertEqual(self.desk.state(self.user,self.bid)['audit'],state['audit'])
        opening=self.opening();self.assertTrue(opening['number'].endswith('0001'))
    def test_invalid_import_rolls_back_whole_batch(self):
        payload={'kind':'stock','rows':[{'name':'Filter','sku':'f1','opening_qty':2,'cost':10},{'name':'Bad','opening_qty':-1}]}
        with self.assertRaises(Problem):self.desk.import_batch(self.user,self.bid,payload)
        self.assertEqual(self.records()['stock'],[])
        result=self.desk.import_batch(self.user,self.bid,payload,True)
        self.assertEqual(result['created'],1);self.assertEqual(result['errors'][0]['row'],2);self.assertEqual(self.records()['stock'],[])
    def test_import_duplicates_skip_without_overwrite(self):
        payload={'kind':'customers','rows':[{'name':'Fleet','phone':'9000000001','address':'Overwritten?'},{'name':'Second','phone':'9000000002'},{'name':'Second','phone':'9000000002'}]}
        result=self.desk.import_batch(self.user,self.bid,payload)
        self.assertEqual((result['created'],result['skipped']),(1,2))
        self.assertEqual(self.records()['customers'][-1].get('address',''),'')
    def test_openings_require_source_reconciliation_and_retain_corrections(self):
        with self.assertRaises(Problem):self.save('opening_balances',customer_id=self.c['id'],amount=500,date=today(),source_reference='x')
        opening=self.opening()
        for action in [lambda:self.update(opening,amount=1),lambda:self.desk.archive(self.user,self.bid,'opening_balances',opening['id'],opening['version']),lambda:self.opening()]:
            with self.assertRaises(Problem):action()
    def test_opening_collection_caps_and_statement(self):
        opening=self.opening()
        self.save('payments',opening_balance_id=opening['id'],date=today(),amount=200,method='Cash')
        self.assertEqual(self.records()['opening_balances'][0]['_balance'],300)
        with self.assertRaises(Problem):self.save('payments',opening_balance_id=opening['id'],date=today(),amount=301,method='Cash')
        statement=self.desk.customer_statement(self.user,self.bid,self.c['id']);self.assertEqual(statement['balance'],300)
        self.assertEqual(len(statement['entries']),2);self.assertEqual(self.records()['payments'][0]['_unallocated'],0)
    def test_opening_customer_credit_refund(self):
        opening=self.opening(-300)
        with self.assertRaises(Problem):self.save('payments',opening_balance_id=opening['id'],date=today(),amount=20,direction='receipt')
        self.save('payments',opening_balance_id=opening['id'],date=today(),amount=100,direction='refund',method='Cash')
        self.assertEqual(self.records()['opening_balances'][0]['_balance'],-200)
        self.assertEqual(self.desk.customer_statement(self.user,self.bid,self.c['id'])['balance'],-200)
    def test_credit_limit_includes_openings_and_audits_owner_override(self):
        self.update(self.c,credit_limit=550);self.settings(operating_rules={'credit_limit_enforced':True});self.opening(500)
        invoice=self.invoice(100)
        with self.assertRaises(Problem):self.issue(invoice)
        self.assertEqual(self.records()['invoices'][0]['status'],'draft')
        issued=self.issue(invoice,credit_override_reason='Agreed one-off limit for fleet manager')
        self.assertEqual(issued['status'],'issued');self.assertTrue(any(x['action']=='Credit limit override' for x in self.desk.state(self.user,self.bid)['audit']))
    def test_price_agreements_are_owner_only_and_business_scoped(self):
        item=self.save('stock',name='Filter',cost=10)
        prices=[{'kind':'stock','item_id':item['id'],'min_qty':5,'rate':15}]
        customer=self.update(self.c,price_agreements=prices,credit_limit=100)
        staff={**self.user,'role':'frontdesk','business_ids':'["'+self.bid+'"]'}
        updated=self.desk.save(staff,self.bid,'customers',{'id':customer['id'],'version':customer['version'],'data':{'price_agreements':[],'credit_limit':0}})
        self.assertEqual(updated['price_agreements'],prices);self.assertEqual(updated['credit_limit'],100)
        other=self.desk.save_business(self.user,{'data':{'name':'Other'}})
        bad=self.desk.save(self.user,other['id'],'stock',{'data':{'name':'Different item'}})
        with self.assertRaises(Problem):self.update(updated,price_agreements=[{'kind':'stock','item_id':bad['id'],'rate':1}])
    def test_cash_count_variance_and_later_source_changes(self):
        self.save('payments',customer_id=self.c['id'],amount=300,date=today(),method='Cash')
        self.save('payments',customer_id=self.c['id'],amount=900,date=today(),method='Bank transfer')
        self.save('expenses',name='Fuel',amount=50,date=today(),method='Cash')
        count=self.save('cash_closures',date=today(),opening_float=100,counted_cash=340)
        self.assertEqual((count['expected_cash'],count['variance']),(350,-10))
        with self.assertRaises(Problem):self.desk.archive(self.user,self.bid,'cash_closures',count['id'],count['version'])
        self.save('expenses',name='Tea',amount=10,date=today(),method='Cash')
        self.assertTrue(self.records()['cash_closures'][0]['_source_changed'])
        with self.assertRaises(Problem):self.save('cash_closures',date=today(),opening_float=100,counted_cash=340)
        replacement=self.save('cash_closures',date=today(),opening_float=100,counted_cash=340,notes='Late tea expense reviewed against cash drawer')
        self.assertEqual(replacement['variance'],0)
    def test_stock_count_conflict_and_partial_failure_are_atomic(self):
        a=self.save('stock',name='A',opening_qty=5,cost=1);b=self.save('stock',name='B',opening_qty=2,cost=2)
        payload={'reason':'Quarterly physical count','items':[{'item_id':a['id'],'version':1,'expected_qty':5,'counted_qty':3},{'item_id':b['id'],'version':1,'expected_qty':999,'counted_qty':0}]}
        with self.assertRaises(Problem):self.desk.stock_count(self.user,self.bid,payload)
        self.assertEqual(self.records()['movements'],[])
        payload['items'][1]['expected_qty']=2
        self.assertEqual(self.desk.stock_count(self.user,self.bid,payload)['adjustments'],2)
        with self.assertRaises(Problem):self.desk.stock_count(self.user,self.bid,payload)
    def test_handover_requires_bill_payment_and_required_checklist(self):
        self.settings(job_checklist=['Safety check'],operating_rules={'handover_requires_payment':True,'handover_requires_checks':True})
        job=self.save('jobs',name='Repair',customer_id=self.c['id'],stage=self.b['stages'][0],tasks=[{'name':'Safety check','done':False}])
        with self.assertRaises(Problem):self.update(job,stage=self.b['stages'][-1])
        with self.assertRaises(Problem):self.save('jobs',name='Already handed over',customer_id=self.c['id'],stage=self.b['stages'][-1],tasks=[{'name':'Safety check','done':True}])
        inv=self.issue(self.invoice(job_id=job['id']));self.save('payments',invoice_id=inv['id'],date=today(),amount=100,method='Cash')
        with self.assertRaises(Problem):self.update(job,stage=self.b['stages'][-1],tasks=[{'name':'Different check','done':True}])
        updated=self.update(job,stage=self.b['stages'][-1],tasks=[{'name':'Safety check','done':True}]);self.assertEqual(updated['stage'],self.b['stages'][-1])
    def test_inspection_technician_assignment_and_condition(self):
        employee=self.save('employees',name='Mechanic',active=True)
        job=self.save('jobs',name='Repair',customer_id=self.c['id'],stage=self.b['stages'][0],employee_ids=[employee['id']],tasks=[])
        staff={**self.user,'role':'technician','business_ids':'["'+self.bid+'"]','employee_id':employee['id']}
        result=self.desk.save(staff,self.bid,'jobs',{'id':job['id'],'version':job['version'],'data':{'inspection':[{'area':'Brakes','condition':'urgent','notes':'Review','recommendation':'Confirm scope'}]}})
        self.assertEqual(result['inspection'][0]['condition'],'urgent')
        with self.assertRaises(Problem):self.desk.save({**staff,'employee_id':'unassigned'},self.bid,'jobs',{'id':job['id'],'version':result['version'],'data':{'inspection':[]}})
