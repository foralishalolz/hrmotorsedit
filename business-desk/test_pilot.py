"""Failure-oriented checks for multi-device commands and sector workflows."""
import copy
import hashlib
import io
import json
import tempfile
import threading
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from domain import Desk, Problem, today, password_hash, password_ok
from hosted import create_app


class PilotWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.desk = Desk(self.temp.name)
        self.token, _ = self.desk.setup({'name':'Pilot owner','username':'owner','password':'test-only-password'})
        self.user, _ = self.desk.session(self.token)
        self.b = self.desk.save_business(self.user, {'data':{'name':'Pilot showroom','profile':'showroom','vat_registered':True}})
        self.bid = self.b['id']
        self.customer = self.save('customers', name='Fictional customer')

    def tearDown(self): self.temp.cleanup()
    def save(self, record_type, **data): return self.desk.save(self.user, self.bid, record_type, {'data':data})
    def update(self, row, **data): return self.desk.save(self.user,self.bid,row['type'],{'id':row['id'],'version':row['version'],'data':{**row,**data}})
    def action(self, row, action, **data): return self.desk.action(self.user,self.bid,row['type'],row['id'],{'version':row['version'],'action':action,**data})
    def state(self): return self.desk.state(self.user,self.bid)
    def get(self, kind, rid): return next(x for x in self.state()['records'][kind] if x['id']==rid)
    def envelope(self, endpoint, payload):
        return {'operation_id':uuid.uuid4().hex,'endpoint':endpoint,'payload':{'business_id':self.bid,**payload},'data_epoch':self.state()['data_epoch']}
    def vehicle(self, vin='TEST-CHASSIS-1'): return self.save('vehicles',name='Fictional Hatchback',vin=vin,sale_price=1000000,purchase_cost=800000,date=today())
    def lead(self, vehicle=None): return self.save('leads',name='Test enquiry',customer_id=self.customer['id'],vehicle_id=vehicle['id'] if vehicle else '',stage='new',due_date=today(),next_action='Arrange visit',expected_value=1000000)
    def invoice(self, **extra):
        row=self.save('invoices',customer_id=self.customer['id'],items=[{'description':'Test service','qty':1,'rate':100}],vat_mode='none',date=today(),**extra)
        return self.action(row,'issue')

    def test_retry_returns_same_payment_and_one_number(self):
        invoice=self.invoice()
        op=self.envelope('record',{'kind':'payments','data':{'invoice_id':invoice['id'],'amount':25,'date':today()}})
        first=self.desk.command(self.user,op)
        second=self.desk.command(self.user,op)
        self.assertEqual(first,second)
        self.assertEqual(len(self.state()['records']['payments']),1)
        self.assertTrue(first['number'].endswith('0001'))
        next_payment=self.save('payments',invoice_id=invoice['id'],amount=25,date=today())
        self.assertTrue(next_payment['number'].endswith('0002'))

    def test_concurrent_same_operation_commits_once(self):
        op=self.envelope('record',{'kind':'payments','data':{'customer_id':self.customer['id'],'amount':25,'date':today()}})
        with ThreadPoolExecutor(max_workers=4) as executor:
            results=list(executor.map(lambda _:self.desk.command(self.user,op),range(4)))
        self.assertEqual(len({x['id'] for x in results}),1)
        self.assertEqual(len(self.state()['records']['payments']),1)

    def test_operation_id_cannot_be_reused_for_different_data(self):
        op=self.envelope('record',{'kind':'customers','data':{'name':'Original'}})
        self.desk.command(self.user,op)
        op['payload']['data']['name']='Changed'
        with self.assertRaises(Problem) as error: self.desk.command(self.user,op)
        self.assertEqual(error.exception.status,409)

    def test_failed_command_rolls_back_number_and_receipt(self):
        invoice=self.invoice()
        op=self.envelope('record',{'kind':'payments','data':{'invoice_id':invoice['id'],'amount':101,'date':today()}})
        with self.assertRaises(Problem): self.desk.command(self.user,op)
        with self.desk.connect() as conn:
            self.assertEqual(conn.execute('SELECT COUNT(*) FROM commands').fetchone()[0],0)
        receipt=self.save('payments',invoice_id=invoice['id'],amount=100,date=today())
        self.assertTrue(receipt['number'].endswith('0001'))

    def test_old_database_epoch_rejected_after_restore(self):
        op=self.envelope('record',{'kind':'customers','data':{'name':'Queued before restore'}})
        backup=self.desk.backup().read_bytes();self.desk.restore(self.user,backup)
        with self.assertRaises(Problem) as error:self.desk.command(self.user,op)
        self.assertEqual(error.exception.status,409)

    def test_offline_dependency_ids_and_stale_edit(self):
        cid=uuid.uuid4().hex
        op=self.envelope('record',{'kind':'customers','id':cid,'data':{'name':'Offline customer'}})
        customer=self.desk.command(self.user,op)
        quote=self.desk.command(self.user,self.envelope('record',{'kind':'quotes','data':{'customer_id':cid,'items':[{'description':'Repair','rate':500}],'vat_mode':'none'}}))
        self.assertEqual(quote['customer_id'],cid)
        self.update(customer,name='Changed by another device')
        stale=self.envelope('record',{'kind':'customers','id':cid,'version':customer['version'],'data':{'name':'Stale draft'}})
        with self.assertRaises(Problem) as error:self.desk.command(self.user,stale)
        self.assertEqual(error.exception.status,409)

    def test_chassis_unique_and_concurrent_reservation(self):
        vehicle=self.vehicle()
        with self.assertRaises(Problem):self.vehicle('test-chassis-1')
        leads=[self.lead(vehicle),self.lead(vehicle)]
        barrier=threading.Barrier(2)
        def reserve(row):
            barrier.wait()
            try:return self.action(row,'reserve')['id']
            except Problem:return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as executor: results=list(executor.map(reserve,leads))
        self.assertEqual(results.count('rejected'),1)
        self.assertEqual(self.get('vehicles',vehicle['id'])['status'],'reserved')

    def test_showroom_booking_collection_and_delivery(self):
        vehicle=self.vehicle();lead=self.action(self.lead(vehicle),'reserve')
        invoice=self.action(lead,'invoice');issued=self.action(invoice,'issue')
        self.assertEqual(self.get('vehicles',vehicle['id'])['status'],'sold')
        lead=self.get('leads',lead['id'])
        with self.assertRaises(Problem):self.action(lead,'deliver')
        total=issued['totals_snapshot']['total']
        self.save('payments',invoice_id=issued['id'],amount=total,date=today())
        with self.assertRaises(Problem):self.action(lead,'deliver')
        lead=self.update(lead,pdi_complete=True,documents_complete=True,handover_signed=True)
        self.assertEqual(self.action(lead,'deliver')['stage'],'delivered')
        self.assertEqual(self.get('invoices',issued['id'])['_balance'],0)

    def test_release_requires_reason_and_cannot_release_invoiced_vehicle(self):
        vehicle=self.vehicle();lead=self.action(self.lead(vehicle),'reserve')
        with self.assertRaises(Problem):self.action(lead,'release')
        self.action(lead,'release',reason='Customer changed plans')
        self.assertEqual(self.get('vehicles',vehicle['id'])['status'],'available')
        lead=self.action(self.lead(vehicle),'reserve')
        self.action(self.action(lead,'invoice'),'issue')
        with self.assertRaises(Problem):self.action(self.get('leads',lead['id']),'release',reason='Cancel')

    def test_reserved_and_sold_state_cannot_be_forged_by_edit(self):
        vehicle=self.vehicle()
        with self.assertRaises(Problem):self.update(vehicle,status='sold')
        lead=self.lead(vehicle)
        with self.assertRaises(Problem):self.update(lead,stage='booked')
        self.action(lead,'reserve');reserved=self.get('vehicles',vehicle['id'])
        with self.assertRaises(Problem):self.update(reserved,status='available')

    def test_invoice_stock_consumption_atomic_and_not_duplicated_on_retry(self):
        stock=self.save('stock',name='Part',opening_qty=3,cost=25)
        invoice=self.save('invoices',customer_id=self.customer['id'],vat_mode='none',items=[{'item_id':stock['id'],'description':'Part','qty':2,'rate':50}])
        op=self.envelope('action',{'kind':'invoices','id':invoice['id'],'version':invoice['version'],'action':'issue'})
        self.desk.command(self.user,op);self.desk.command(self.user,op)
        self.assertEqual(self.get('stock',stock['id'])['_quantity'],1)
        next_invoice=self.save('invoices',customer_id=self.customer['id'],items=[{'item_id':stock['id'],'description':'Part','qty':2,'rate':50}])
        with self.assertRaises(Problem):self.action(next_invoice,'issue')
        self.assertEqual(self.get('invoices',next_invoice['id'])['status'],'draft')
        self.assertEqual(self.get('stock',stock['id'])['_quantity'],1)

    def test_invoice_does_not_consume_job_parts_twice(self):
        stock=self.save('stock',name='Repair part',opening_qty=5,cost=25)
        job=self.save('jobs',name='Repair',customer_id=self.customer['id'])
        self.save('movements',item_id=stock['id'],job_id=job['id'],kind='issue',qty=2,unit_cost=25,date=today())
        invoice=self.save('invoices',customer_id=self.customer['id'],job_id=job['id'],items=[{'item_id':stock['id'],'description':'Repair part','qty':3,'rate':50}])
        self.action(invoice,'issue')
        self.assertEqual(self.get('stock',stock['id'])['_quantity'],2)
        self.assertEqual(self.get('jobs',job['id'])['_cost'],75)

    def test_supplier_bill_payment_duplicate_and_overpayment(self):
        supplier=self.save('suppliers',name='Fictional supplier')
        bill=self.save('supplier_bills',supplier_id=supplier['id'],reference='B-1',net=100,tax=13,date=today(),due_date=today())
        with self.assertRaises(Problem):self.save('supplier_bills',supplier_id=supplier['id'],reference='b-1',net=100,due_date=today())
        self.save('supplier_payments',supplier_bill_id=bill['id'],amount=50,date=today())
        self.assertEqual(self.get('supplier_bills',bill['id'])['_balance'],63)
        with self.assertRaises(Problem):self.save('supplier_payments',supplier_bill_id=bill['id'],amount=64,date=today())
        self.assertTrue(any(x['type']=='supplier_bills' for x in self.state()['alerts']))

    def test_commission_on_collected_showroom_sale(self):
        lead=self.lead();invoice=self.invoice(lead_id=lead['id'])
        employee=self.save('employees',name='Salesperson',active=True)
        earning=self.save('commissions',employee_id=employee['id'],lead_id=lead['id'],basis_amount=100,percent=10,collection_required=True)
        self.assertEqual(self.get('commissions',earning['id'])['_eligible'],0)
        self.save('payments',invoice_id=invoice['id'],amount=100,date=today())
        self.assertEqual(self.get('commissions',earning['id'])['_eligible'],10)

    def test_access_rechecked_for_idempotent_replay(self):
        op=self.envelope('record',{'kind':'payments','data':{'customer_id':self.customer['id'],'amount':25,'date':today()}})
        self.desk.command(self.user,op)
        changed={**self.user,'role':'technician','business_ids':json.dumps([self.bid])}
        with self.assertRaises(Problem) as error:self.desk.command(changed,op)
        self.assertEqual(error.exception.status,403)

    def test_password_upgrade_and_session_revocation(self):
        old_salt='00'*16
        old=old_salt+':'+hashlib.pbkdf2_hmac('sha256',b'test-password',bytes.fromhex(old_salt),260000).hex()
        self.assertTrue(password_ok('test-password',old))
        self.assertTrue(password_ok('test-password',password_hash('test-password')))
        with self.desk.transaction() as conn:conn.execute('UPDATE users SET password=? WHERE id=?',(password_hash('changed-password'),self.user['id']))
        with self.assertRaises(Problem):self.desk.session(self.token)


class HostedBoundary(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.app=create_app(self.temp.name,'https://desk.example.test','x'*40)
    def tearDown(self):self.temp.cleanup()
    def request(self,path='/',method='GET',data=None,headers=None):
        raw=json.dumps(data or {}).encode()
        env={'REQUEST_METHOD':method,'PATH_INFO':path,'QUERY_STRING':'','REMOTE_ADDR':'192.0.2.1','HTTP_HOST':'desk.example.test','wsgi.input':io.BytesIO(raw),'CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw))}
        env.update(headers or {}); response={}
        content=b''.join(self.app(env,lambda status,headers:response.update(status=int(status.split()[0]),headers=dict(headers))))
        response['body']=json.loads(content) if response['headers'].get('Content-Type','').startswith('application/json') else content
        return response
    def test_host_origin_setup_secret_and_secure_cookie(self):
        data={'name':'Owner','username':'owner','password':'test-only-password'}
        self.assertEqual(self.request('/api/setup','POST',data)['status'],403)
        data['setup_key']='x'*40
        self.assertEqual(self.request('/api/setup','POST',data,{'HTTP_HOST':'attacker.test'})['status'],403)
        self.assertEqual(self.request('/api/setup','POST',data,{'HTTP_ORIGIN':'https://attacker.test'})['status'],403)
        success=self.request('/api/setup','POST',data)
        self.assertEqual(success['status'],200)
        self.assertIn('Secure',success['headers']['Set-Cookie'])
        self.assertIn('HttpOnly',success['headers']['Set-Cookie'])
        self.assertIn('Strict-Transport-Security',success['headers'])
    def test_reject_invalid_host_configuration(self):
        for origin in ['http://desk.example.test','https://desk.example.test/path','https://user@desk.example.test']:
            with self.assertRaises(ValueError):create_app(self.temp.name,origin,'x'*40)
        with self.assertRaises(ValueError):create_app(self.temp.name,'https://desk.example.test','short')
    def test_methods_and_auth_rate_limit(self):
        self.assertEqual(self.request('/','DELETE')['status'],405)
        for _ in range(30):self.request('/api/login','POST',{'username':str(uuid.uuid4()),'password':'incorrect-password'})
        self.assertEqual(self.request('/api/login','POST',{})['status'],429)
