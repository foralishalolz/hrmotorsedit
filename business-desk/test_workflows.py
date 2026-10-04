"""Meaningful operating and access-control checks. Run: python3 -m unittest -v"""
import base64
import http.client
import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from http.server import ThreadingHTTPServer

from domain import Desk, Problem, calculate, today
from server import Handler, print_document


class OperatingWorkflow(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.desk=Desk(self.temp.name)
        token,_=self.desk.setup({'name':'Test Owner','username':'testowner','password':'testing-only-123'})
        self.owner,_=self.desk.session(token)
        self.business=self.desk.save_business(self.owner,{'data':{'name':'Test Garage','vat_rate':13,'quote_followup_days':3,'payment_terms_days':7}})
        self.bid=self.business['id']
        self.customer=self.save('customers',name='Test Customer',phone='fictional')
        self.employee=self.save('employees',name='Test Mechanic',active=True,salary_type='monthly',base_salary=30000,hourly_cost=250,overtime_rate=300,shift_hours=8,employee_percent=10,employer_percent=20)

    def tearDown(self): self.temp.cleanup()
    def save(self,record_type,**data): return self.desk.save(self.owner,self.bid,record_type,{'data':data})
    def update(self,record,**changes): return self.desk.save(self.owner,self.bid,record['type'],{'id':record['id'],'version':record['version'],'data':{**record,**changes}})
    def action(self,record,action,**data): return self.desk.action(self.owner,self.bid,record['type'],record['id'],{'version':record['version'],'action':action,**data})
    def state_record(self,kind,rid): return next(x for x in self.desk.state(self.owner,self.bid)['records'][kind] if x['id']==rid)
    def invoice(self,job_id=''):
        draft=self.save('invoices',customer_id=self.customer['id'],job_id=job_id,date=today(),due_date=today(),vat_mode='added',vat_rate=13,items=[{'description':'Repair','qty':1,'rate':1000,'unit_cost':250}])
        return self.action(draft,'issue')
    def job(self): return self.save('jobs',name='Test repair',customer_id=self.customer['id'],employee_ids=[self.employee['id']],stage='Intake',tasks=[])
    def payroll(self,start='2026-01-01',end='2026-01-31',commissions=None):
        return self.desk.prepare_payroll(self.owner,self.bid,{'start_date':start,'end_date':end,'lines':[{'employee_id':self.employee['id'],'units':1,'overtime_hours':2,'bonus':1000,'withholding':500,'deductions':1000,'deduction_note':'Authorised advance recovery','contribution_base':30000,'commission_ids':commissions or []}]})
    def technician(self):
        self.desk.add_user(self.owner,{'name':'Test technician','username':'technician','password':'testing-only-123','role':'technician','business_ids':[self.bid],'employee_id':self.employee['id']})
        token,_=self.desk.login({'username':'technician','password':'testing-only-123'})
        return self.desk.session(token)[0]

    def test_decimal_rounding_added_included_and_no_vat(self):
        added=calculate({'vat_mode':'added','items':[{'description':'a','qty':1,'rate':.05},{'description':'b','qty':1,'rate':.05}]})
        self.assertEqual((added['net'],added['tax'],added['total']),(.1,.02,.12))
        included=calculate({'vat_mode':'included','items':[{'description':'Repair','qty':2,'rate':113}]})
        self.assertEqual((included['net'],included['tax'],included['total']),(200,26,226))
        no_tax=calculate({'vat_mode':'none','items':[{'description':'Repair','qty':1,'rate':113}]})
        self.assertEqual((no_tax['net'],no_tax['tax']),(113,0))
        draft=self.save('quotes',customer_id=self.customer['id'],vat_mode='none',vat_rate=13,items=[{'description':'Repair','qty':1,'rate':100}])
        restored=self.update(draft,vat_mode='added')
        self.assertEqual(calculate(restored)['total'],113)

    def test_line_and_document_discounts_and_mixed_tax(self):
        result=calculate({'vat_mode':'added','discount_percent':10,'items':[{'description':'a','qty':1,'rate':100,'discount':10,'tax_rate':13},{'description':'b','qty':1,'rate':100,'tax_rate':0}]})
        self.assertEqual((result['net'],result['tax'],result['total'],result['discount']),(171,10.53,181.53,29))

    def test_reject_invalid_prices_and_quantities(self):
        for line in ({'description':'a','rate':-1},{'description':'a','rate':'NaN'},{'description':'a','rate':10,'qty':0},{'description':'','rate':10}):
            with self.assertRaises(Problem): calculate({'items':[line]})

    def test_approved_quote_to_job_invoice_and_collection(self):
        draft=self.save('quotes',customer_id=self.customer['id'],subject='Panel work',date=today(),items=[{'description':'Repair panel','qty':2,'rate':500}])
        sent=self.action(draft,'send')
        with self.assertRaises(Problem): self.update(sent,subject='Changed after sending')
        with self.assertRaises(Problem): self.action(sent,'accept',approved_by='')
        accepted=self.action(sent,'accept',approved_by='Test Customer',channel='Phone')
        job=self.action(accepted,'job',due_date=today())
        self.assertEqual(job['tasks'][0]['name'],'Repair panel')
        again=self.action(accepted,'job')
        self.assertEqual(again['id'],job['id'])
        bill=self.action(job,'invoice');issued=self.action(bill,'issue')
        self.save('payments',invoice_id=issued['id'],date=today(),amount=300,method='Cash')
        state=self.state_record('invoices',issued['id'])
        self.assertEqual((state['_paid'],state['_balance']),(300,830))

    def test_snapshots_survive_party_and_business_changes(self):
        invoice=self.invoice()
        self.update(self.customer,name='New Customer Name')
        self.desk.save_business(self.owner,{'id':self.bid,'version':self.business['version'],'data':{**self.business,'name':'New Garage Name'}})
        html=print_document(self.desk,self.owner,self.bid,'invoices',invoice['id']).decode()
        self.assertIn('Test Garage',html);self.assertIn('Test Customer',html)
        self.assertNotIn('New Garage Name',html);self.assertNotIn('New Customer Name',html)
        with self.assertRaises(Problem): self.update(invoice,items=[])

    def test_revision_keeps_previous_quote(self):
        sent=self.action(self.save('quotes',customer_id=self.customer['id'],items=[{'description':'a','rate':100}]),'send')
        revision=self.action(sent,'revise')
        self.assertEqual((revision['revision'],revision['status'],revision['previous_id']),(2,'draft',sent['id']))
        self.assertNotIn('number',revision)
        self.assertEqual(self.state_record('quotes',sent['id'])['status'],'sent')

    def test_optimistic_version_prevents_lost_edits(self):
        self.update(self.customer,phone='new')
        with self.assertRaises(Problem) as problem:self.update(self.customer,phone='stale')
        self.assertEqual(problem.exception.status,409)

    def test_receipts_overpayment_duplicates_credits_refunds(self):
        invoice=self.invoice()
        with self.assertRaises(Problem):self.save('payments',invoice_id=invoice['id'],date=today(),amount=1200)
        receipt=self.save('payments',invoice_id=invoice['id'],date=today(),amount=1130,method='Bank transfer',reference='TEST-1')
        with self.assertRaises(Problem):self.save('payments',customer_id=self.customer['id'],date=today(),amount=10,method='Bank transfer',reference='TEST-1')
        credit=self.save('credits',invoice_id=invoice['id'],amount=113,date=today(),reason='Agreed reduction')
        self.assertEqual((credit['net'],credit['tax']),(100,13))
        self.assertEqual(self.state_record('invoices',invoice['id'])['_balance'],-113)
        self.save('payments',invoice_id=invoice['id'],date=today(),direction='refund',amount=113)
        self.assertEqual(self.state_record('invoices',invoice['id'])['_balance'],0)
        with self.assertRaises(Problem):self.update(receipt,amount=1)
        with self.assertRaises(Problem):self.save('credits',invoice_id=invoice['id'],amount=1200,reason='Too much')
        small=self.action(self.save('invoices',customer_id=self.customer['id'],date=today(),vat_rate=13,items=[{'description':'Small priced part','rate':.38}]),'issue')
        for _ in range(43):self.save('credits',invoice_id=small['id'],amount=.01,date=today(),reason='Test cumulative cent credit')
        credits=[x for x in self.desk.state(self.owner,self.bid)['records']['credits'] if x['invoice_id']==small['id']]
        self.assertEqual(sum(Decimal(str(x['net'])) for x in credits),Decimal('.38'))
        self.assertEqual(sum(Decimal(str(x['tax'])) for x in credits),Decimal('.05'))

    def test_advance_allocation_has_no_duplicate_cash(self):
        advance=self.save('payments',customer_id=self.customer['id'],amount=500,date=today(),method='Cash')
        self.assertTrue(advance['number'].startswith('RCT-'))
        invoice=self.invoice();allocation=self.action(advance,'allocate',invoice_id=invoice['id'],amount=200)
        self.assertEqual(allocation['amount'],200)
        self.assertEqual(self.state_record('invoices',invoice['id'])['_balance'],930)
        self.assertEqual(self.state_record('payments',advance['id'])['_unallocated'],300)
        self.assertEqual(sum(x['amount'] for x in self.desk.state(self.owner,self.bid)['records']['payments']),500)
        with self.assertRaises(Problem):self.action(advance,'allocate',invoice_id=invoice['id'],amount=400)

    def test_stock_ledger_partial_receipts_and_negative_stock(self):
        item=self.save('stock',name='Primer',opening_qty=2,cost=100,reorder_at=1)
        order=self.save('purchases',items=[{'item_id':item['id'],'qty':5,'cost':90}])
        partial=self.action(order,'receive',items=[{'item_id':item['id'],'qty':2}])
        self.assertEqual(partial['status'],'partial')
        with self.assertRaises(Problem):self.action(partial,'receive',items=[{'item_id':item['id'],'qty':4}])
        full=self.action(partial,'receive',items=[{'item_id':item['id'],'qty':3}])
        self.assertEqual(full['status'],'received')
        self.assertEqual(self.state_record('stock',item['id'])['_quantity'],7)
        self.save('movements',item_id=item['id'],kind='issue',qty=6,unit_cost=90)
        with self.assertRaises(Problem):self.save('movements',item_id=item['id'],kind='issue',qty=2)
        self.save('movements',item_id=item['id'],kind='return',qty=1,unit_cost=90)
        self.assertEqual(self.state_record('stock',item['id'])['_quantity'],2)
        with self.assertRaises(Problem):self.update(item,opening_qty=20)

    def test_collection_based_commission_and_double_payment_block(self):
        job=self.job();invoice=self.invoice(job['id'])
        earning=self.save('commissions',name='Service incentive',employee_id=self.employee['id'],job_id=job['id'],basis_amount=1000,percent=10,fixed_amount=0,collection_required=True)
        approved=self.action(earning,'approve')
        self.save('payments',invoice_id=invoice['id'],date=today(),amount=565)
        self.assertEqual(self.state_record('commissions',earning['id'])['_eligible'],50)
        with self.assertRaises(Problem):self.action(approved,'pay')
        self.save('payments',invoice_id=invoice['id'],date=today(),amount=565)
        paid=self.action(approved,'pay')
        with self.assertRaises(Problem):self.action(paid,'pay')

    def test_payroll_reviews_rates_deductions_and_overlaps(self):
        draft=self.payroll();line=draft['lines'][0]
        self.assertEqual((line['gross'],line['employee_contribution'],line['employer_contribution'],line['net'],line['employer_cost']),(31600,3000,6000,27100,37600))
        second_draft=self.payroll()
        approved=self.action(draft,'approve')
        with self.assertRaises(Problem):self.action(second_draft,'approve')
        paid=self.action(approved,'pay');self.assertEqual(paid['status'],'paid')
        with self.assertRaises(Problem):self.payroll()

    def test_payroll_reserves_commission_and_rechecks_collection(self):
        job=self.job();invoice=self.invoice(job['id'])
        self.save('payments',invoice_id=invoice['id'],date=today(),amount=1130)
        earning=self.action(self.save('commissions',name='Incentive',employee_id=self.employee['id'],job_id=job['id'],basis_amount=1000,percent=10,collection_required=True),'approve')
        payroll=self.action(self.payroll(commissions=[earning['id']]),'approve')
        reserved=self.state_record('commissions',earning['id'])
        with self.assertRaises(Problem):self.action(reserved,'pay')
        self.save('payments',invoice_id=invoice['id'],date=today(),amount=50,direction='refund')
        with self.assertRaises(Problem):self.action(payroll,'pay')

    def test_overnight_attendance_duration_and_duplicate_shift(self):
        attendance=self.save('attendance',employee_id=self.employee['id'],date=today(),in_time='22:00',out_time='06:00',overnight=True,break_minutes=30,status='approved')
        self.assertEqual(attendance['hours'],7.5)
        with self.assertRaises(Problem):self.save('attendance',employee_id=self.employee['id'],date=today())

    def test_appointment_resource_conflicts(self):
        self.save('appointments',name='Inspection',customer_id=self.customer['id'],date=today(),time='10:00',duration_minutes=60,bay='Bay A',status='booked')
        with self.assertRaises(Problem):self.save('appointments',name='Collision',customer_id=self.customer['id'],date=today(),time='10:30',duration_minutes=60,bay='Bay A',status='booked')
        self.save('appointments',name='Later service',customer_id=self.customer['id'],date=today(),time='11:00',duration_minutes=60,bay='Bay A',status='booked')

    def test_technician_limits_and_private_data(self):
        tech=self.technician();assigned=self.job();unassigned=self.save('jobs',name='Other work',customer_id=self.customer['id'],employee_ids=[])
        state=self.desk.state(tech,self.bid)
        self.assertEqual([x['id'] for x in state['records']['jobs']],[assigned['id']])
        self.assertNotIn('base_salary',state['records']['employees'][0])
        with self.assertRaises(Problem):self.desk.action(tech,self.bid,'jobs',assigned['id'],{'version':assigned['version'],'action':'invoice'})
        with self.assertRaises(Problem):print_document(self.desk,tech,self.bid,'jobs',unassigned['id'])
        with self.assertRaises(Problem):self.desk.save(tech,self.bid,'jobs',{'id':unassigned['id'],'version':unassigned['version'],'data':{**unassigned,'stage':'Painting'}})

    def test_business_scope_and_record_reference_isolation(self):
        second=self.desk.save_business(self.owner,{'data':{'name':'Other Business'}})
        foreign=self.desk.save(self.owner,second['id'],'customers',{'data':{'name':'Foreign Customer'}})
        with self.assertRaises(Problem):self.save('quotes',customer_id=foreign['id'],items=[])
        tech=self.technician()
        with self.assertRaises(Problem):self.desk.state(tech,second['id'])

    def test_task_timer_retains_hourly_cost_and_one_active_task(self):
        job=self.job()
        timer=self.desk.time_action(self.owner,self.bid,{'employee_id':self.employee['id'],'job_id':job['id'],'action':'start'})
        with self.assertRaises(Problem):self.desk.time_action(self.owner,self.bid,{'employee_id':self.employee['id'],'job_id':job['id'],'action':'start'})
        self.update(self.employee,hourly_cost=800)
        with self.desk.transaction() as conn:
            timer['start_at']=(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(timespec='seconds')
            self.desk.put(conn,self.bid,'time_entries',timer,timer['id'])
        stopped=self.desk.time_action(self.owner,self.bid,{'employee_id':self.employee['id'],'action':'stop'})
        self.assertEqual(stopped['hourly_cost_snapshot'],250)
        self.assertAlmostEqual(self.state_record('jobs',job['id'])['_cost'],250,delta=.1)

    def test_followup_snooze_and_original_file_backup_restore(self):
        quote=self.action(self.save('quotes',customer_id=self.customer['id'],items=[{'description':'a','rate':100}]),'send')
        with self.desk.transaction() as conn:
            quote['sent_at']=(datetime.now(timezone.utc)-timedelta(days=5)).isoformat();quote=self.desk.put(conn,self.bid,'quotes',quote,quote['id'])
        self.assertTrue(any(x['key']=='quote:'+quote['id'] for x in self.desk.state(self.owner,self.bid)['alerts']))
        self.save('followups',name='Quote follow-up',alert_key='quote:'+quote['id'],date=today(),due_date=(datetime.now(timezone.utc)+timedelta(days=2)).date().isoformat(),status='waiting')
        self.assertFalse(any(x['key']=='quote:'+quote['id'] for x in self.desk.state(self.owner,self.bid)['alerts']))
        uploaded=self.desk.attachment(self.owner,self.bid,{'record_id':quote['id'],'filename':'original-test.txt','content':base64.b64encode(b'Original fictional evidence').decode()})
        backup=self.desk.backup().read_bytes()
        self.save('customers',name='Created after backup')
        self.desk.restore(self.owner,backup)
        self.assertFalse(any(x['name']=='Created after backup' for x in self.desk.state(self.owner,self.bid)['records']['customers']))
        self.assertEqual(self.desk.get_attachment(self.owner,self.bid,uploaded['id'])['content'],b'Original fictional evidence')
        self.assertFalse(self.desk.sessions)

    def test_legacy_dedup_and_hypothetical_comparison(self):
        legacy={'clientName':'Legacy test customer','vehicleRegNo':'TEST-001','items':[{'description':'Repair','qty':1,'unit':'job','rate':100}],'rageeItems':[{'description':'Repair','qty':1,'rate':110}],'vatMode':'added','zainTerms':['Sample terms']}
        first=self.desk.import_legacy(self.owner,self.bid,[legacy]);again=self.desk.import_legacy(self.owner,self.bid,[legacy])
        self.assertEqual((first['imported'],again['skipped']),(1,1))
        scenario=self.desk.state(self.owner,self.bid)['records']['external_quotes'][0]
        self.assertTrue(scenario['simulation'])
        document=print_document(self.desk,self.owner,self.bid,'external_quotes',scenario['id']).decode()
        self.assertIn('HYPOTHETICAL COMPARISON',document)


class QuietHandler(Handler):
    def log_message(self,*args): pass


class HttpBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
        cls.server.desk=Desk(cls.temp.name);cls.port=cls.server.server_port
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
        response,raw=cls.request('POST','/api/setup',{'name':'HTTP Test Owner','username':'httpowner','password':'testing-only-123'})
        cls.cookie=response.getheader('Set-Cookie').split(';')[0];cls.csrf=json.loads(raw)['csrf']
        _,raw=cls.request('POST','/api/businesses',{'data':{'name':'HTTP Test Business'}})
        cls.bid=json.loads(raw)['id']
    @classmethod
    def tearDownClass(cls): cls.server.shutdown();cls.server.server_close();cls.temp.cleanup()
    @classmethod
    def request(cls,method,path,data=None,extra=None):
        headers={'Host':f'127.0.0.1:{cls.port}','Content-Type':'application/json'}
        if hasattr(cls,'cookie'):headers['Cookie']=cls.cookie;headers['X-CSRF-Token']=cls.csrf
        headers.update(extra or {})
        conn=http.client.HTTPConnection('127.0.0.1',cls.port,timeout=5)
        conn.request(method,path,json.dumps(data).encode() if data is not None else None,headers)
        response=conn.getresponse();raw=response.read();conn.close();return response,raw

    def test_static_app_and_security_headers(self):
        response,body=self.request('GET','/')
        self.assertEqual(response.status,200);self.assertIn(b'/app.js',body)
        self.assertEqual(response.getheader('X-Content-Type-Options'),'nosniff')
        self.assertIn("frame-ancestors 'none'",response.getheader('Content-Security-Policy'))

    def test_csrf_origin_and_host_rejected(self):
        for headers in ({'X-CSRF-Token':'wrong'},{'Origin':'https://foreign.example'},{'Host':'foreign.example'}):
            response,_=self.request('POST','/api/record',{'business_id':self.bid,'kind':'customers','data':{'name':'Blocked'}},headers)
            self.assertEqual(response.status,403)

    def test_api_to_database_and_json_csv_exports(self):
        response,body=self.request('POST','/api/record',{'business_id':self.bid,'kind':'customers','data':{'name':'=TEST formula','phone':'TEST'}})
        self.assertEqual(response.status,200);rid=json.loads(body)['id']
        response,body=self.request('GET','/api/state?business='+self.bid)
        self.assertTrue(any(x['id']==rid for x in json.loads(body)['records']['customers']))
        response,body=self.request('GET','/api/export?business='+self.bid+'&format=csv&kind=customers')
        self.assertEqual(response.status,200);self.assertIn(b"'=TEST formula",body)
        response,body=self.request('GET','/api/export?business='+self.bid+'&format=json')
        self.assertEqual(json.loads(body)['format'],'business-desk-record-export-v1')

    def test_full_backup_download(self):
        response,body=self.request('POST','/api/backup',{})
        self.assertEqual(response.status,200);self.assertTrue(body.startswith(b'SQLite format 3\x00'))


if __name__=='__main__': unittest.main(verbosity=2)
