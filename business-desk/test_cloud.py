"""Real Postgres two-worker, isolation and WSGI tests. Only a disposable CI DB.
Set DESK_TEST_POSTGRES_URL ending /desk_ci. Never use a production database.
"""
import io
import json
import os
import unittest
import unittest.mock
import uuid
from concurrent.futures import ThreadPoolExecutor
from domain import Problem, today

URL=os.environ.get('DESK_TEST_POSTGRES_URL','')
@unittest.skipUnless(URL,'Disposable PostgreSQL test URL not configured')
class HostedBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not URL.endswith('/desk_ci'): raise RuntimeError('Refusing destructive test reset outside the disposable desk_ci database.')
        from cloud import CloudDesk
        cls.CloudDesk=CloudDesk;cls.desk=CloudDesk(URL,bootstrap=True);cls.worker=CloudDesk(URL)
    @classmethod
    def tearDownClass(cls): cls.worker.close();cls.desk.close()
    def setUp(self):
        with self.desk.connect() as conn:
            conn.execute('TRUNCATE users,businesses,records,counters,attachments,audit,commands,desk_sessions,desk_rate_limits RESTART IDENTITY CASCADE')
        self.token,_=self.desk.setup({'username':'one','name':'Owner one','password':'fictional-password'})
        self.user,_=self.desk.session(self.token)
        other_token,_=self.worker.setup({'username':'two','name':'Owner two','password':'fictional-password'})
        self.other,_=self.worker.session(other_token)
        self.b=self.desk.save_business(self.user,{'data':{'name':'One Garage'}});self.bid=self.b['id']
        self.other_b=self.worker.save_business(self.other,{'data':{'name':'Two Service'}})
        self.c=self.desk.save(self.user,self.bid,'customers',{'data':{'name':'One Customer'}})
    def draft(self,desk=None,stock=None):
        return (desk or self.desk).save(self.user,self.bid,'invoices',{'data':{'customer_id':self.c['id'],'date':today(),'vat_mode':'none','items':[{'description':'Service','qty':1,'rate':100,'tax_rate':0,**({'item_id':stock['id']} if stock else {})}]}})
    def issue(self,invoice,desk=None):
        return (desk or self.desk).action(self.user,self.bid,'invoices',invoice['id'],{'version':invoice['version'],'action':'issue'})
    def envelope(self,endpoint,payload):
        return {'operation_id':uuid.uuid4().hex,'endpoint':endpoint,'payload':{'business_id':self.bid,**payload},'data_epoch':self.desk.state(self.user,self.bid)['data_epoch']}
    def wsgi(self,path,method='GET',data=None,headers=None):
        from api import index
        index._desk=self.desk
        raw=json.dumps(data or {}).encode()
        env={'PATH_INFO':path,'QUERY_STRING':'','REQUEST_METHOD':method,'HTTP_HOST':'desk.example.test','REMOTE_ADDR':'127.0.0.1','wsgi.input':io.BytesIO(raw),'CONTENT_TYPE':'application/json','CONTENT_LENGTH':str(len(raw))}
        env.update(headers or {})
        captured=[]
        with unittest.mock.patch.dict(os.environ,{'DESK_PUBLIC_ORIGIN':'https://desk.example.test','DESK_SETUP_KEY':'fictional-pilot-invite-32-characters-only','DESK_REGISTRATION_ENABLED':'true'}):
            body=b''.join(index.application(env,lambda status,values:captured.append((status,values))))
        return captured[0],json.loads(body)
    def test_sessions_survive_workers_and_are_hashed(self):
        user,csrf=self.worker.session(self.token);self.assertEqual(user['id'],self.user['id'])
        with self.desk.connect() as conn:
            stored=conn.execute('SELECT token_hash FROM desk_sessions WHERE user_id=?',(self.user['id'],)).fetchone()[0]
        self.assertNotEqual(stored,self.token);self.assertEqual(len(stored),64)
        self.worker.sessions.pop(self.token)
        with self.assertRaises(Problem):self.desk.session(self.token)
    def test_private_orgs_cannot_list_or_modify_each_other(self):
        self.assertNotEqual(self.user['organization_id'],self.other['organization_id'])
        self.assertEqual([x['id'] for x in self.desk.businesses(self.user)],[self.bid])
        other_bid=self.other_b['id']
        attempts=[lambda:self.desk.state(self.user,other_bid),lambda:self.desk.save(self.user,other_bid,'customers',{'data':{'name':'Intruder'}}),lambda:self.desk.save_business(self.user,{'id':other_bid,'version':1,'data':{'name':'Changed'}}),lambda:self.desk.add_user(self.user,{'name':'Leak','username':'leak','password':'fictional-password','role':'manager','business_ids':[other_bid]})]
        for action in attempts:
            with self.assertRaises(Problem):action()
        self.assertEqual(len(self.desk.users(self.user)),1)
    def test_foreign_record_reference_is_rejected(self):
        with self.assertRaises(Problem):self.desk.save(self.other,self.other_b['id'],'assets',{'data':{'name':'Foreign car','customer_id':self.c['id']}})
    def test_two_workers_replaying_one_receipt_post_once(self):
        inv=self.issue(self.draft())
        command=self.envelope('record',{'kind':'payments','id':uuid.uuid4().hex,'data':{'invoice_id':inv['id'],'date':today(),'amount':30,'method':'Cash'}})
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda n:(self.desk if n%2 else self.worker).command(self.user,command),range(8)))
        self.assertEqual(len({x['id'] for x in results}),1)
        records=self.desk.state(self.user,self.bid)['records'];self.assertEqual(len(records['payments']),1);self.assertEqual(records['invoices'][0]['_balance'],70)
    def test_two_workers_cannot_sell_last_stock_twice(self):
        stock=self.desk.save(self.user,self.bid,'stock',{'data':{'name':'Last filter','opening_qty':1,'cost':30,'rate':100}})
        one,two=self.draft(stock=stock),self.draft(desk=self.worker,stock=stock)
        def sell(pair):
            try:return self.issue(pair[1],pair[0])['status']
            except Problem:return 'rejected'
        with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(sell,[(self.desk,one),(self.worker,two)]))
        self.assertEqual(sorted(result),['issued','rejected']);records=self.desk.state(self.user,self.bid)['records'];self.assertEqual(records['stock'][0]['_quantity'],0)
    def test_cloud_export_only_contains_callers_organisation(self):
        self.worker.save(self.other,self.other_b['id'],'customers',{'data':{'name':'Private other customer'}})
        file=self.desk.backup(user=self.user)
        try:
            data=json.loads(file.read_text());self.assertEqual(len(data['businesses']),1)
            self.assertNotIn('Private other customer',file.read_text());self.assertNotIn('fictional-password',file.read_text());self.assertNotIn('users',data['data'])
        finally:file.unlink()
        with self.assertRaises(Problem):self.desk.restore(self.user,b'sqlite')
    def test_shared_login_rate_limit_and_account_invalidation(self):
        for i in range(10):
            with self.assertRaises(Problem):(self.worker if i%2 else self.desk).login({'username':'one','password':'wrong'})
        with self.assertRaises(Problem) as error:self.worker.login({'username':'one','password':'fictional-password'})
        self.assertEqual(error.exception.status,429)
        self.worker.invalidate_sessions(self.user['id'])
        with self.assertRaises(Problem):self.desk.session(self.token)
    def test_import_preview_rolls_back_on_postgres(self):
        payload={'kind':'stock','rows':[{'name':'Valid','opening_qty':3},{'name':'Invalid','opening_qty':-1}]}
        result=self.desk.import_batch(self.user,self.bid,payload,True)
        self.assertEqual((result['created'],len(result['errors'])),(1,1));self.assertEqual(self.desk.state(self.user,self.bid)['records']['stock'],[])
    def test_wsgi_origin_csrf_private_account_and_payload_limit(self):
        import unittest.mock
        status,health=self.wsgi('/api/health');self.assertTrue(status[0].startswith('200'));self.assertTrue(health['cloud'])
        self.assertTrue(self.wsgi('/api/state')[0][0].startswith('401'))
        self.assertTrue(self.wsgi('/api/health',headers={'HTTP_HOST':'attacker.example'})[0][0].startswith('403'))
        self.assertTrue(self.wsgi('/api/logout','POST',headers={'HTTP_COOKIE':'desk_session='+self.token})[0][0].startswith('403'))
        user,csrf=self.desk.session(self.token)
        self.assertTrue(self.wsgi('/api/account','POST',{'id':self.other['id'],'password':'new-fictional-password'},headers={'HTTP_COOKIE':'desk_session='+self.token,'HTTP_X_CSRF_TOKEN':csrf})[0][0].startswith('404'))
        self.assertTrue(self.wsgi('/api/login','POST',headers={'CONTENT_LENGTH':'4000000'})[0][0].startswith('413'))
        self.assertTrue(self.wsgi('/api/setup','POST',{'username':'three','name':'Third','password':'fictional-password'})[0][0].startswith('403'))
    def test_cloud_configuration_never_falls_back_to_sqlite(self):
        import unittest.mock
        from api import index
        previous=index._desk;index._desk=None
        try:
            captured=[]
            with unittest.mock.patch.dict(os.environ,{'DESK_PUBLIC_ORIGIN':'https://desk.example.test','DESK_SETUP_KEY':'fictional-pilot-invite-32-characters-only','DATABASE_URL':''}):
                body=b''.join(index.application({'HTTP_HOST':'desk.example.test'},lambda status,headers:captured.append(status)))
            self.assertTrue(captured[0].startswith('503'));self.assertIn(b'No local database',body)
        finally:index._desk=previous
