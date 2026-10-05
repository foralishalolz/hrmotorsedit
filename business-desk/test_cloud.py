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
    def test_owner_portfolio_is_scoped_on_postgres_and_gateway(self):
        invoice=self.issue(self.draft())
        self.worker.save(self.user,self.bid,'payments',{'data':{'invoice_id':invoice['id'],'amount':25,'date':today()}})
        data=self.worker.portfolio(self.user)
        self.assertEqual([b['id'] for b in data['businesses']],[self.bid])
        self.assertEqual(data['businesses'][0]['outstanding'],75)
        self.assertEqual(data['businesses'][0]['collected_month'],25)
        with self.assertRaises(Problem):self.worker.portfolio({**self.user,'role':'manager'})
        (status,_),body=self.wsgi('/api/portfolio',headers={'HTTP_COOKIE':'desk_session='+self.token})
        self.assertTrue(status.startswith('200'),status)
        self.assertEqual(body['businesses'][0]['id'],self.bid)
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

    def test_owner_analytics_postgres_snapshot_and_gateway_are_scoped(self):
        self.issue(self.draft());r=self.worker.analytics(self.user,self.bid)
        self.assertEqual(r['summary']['sales'],100);self.assertEqual(r['business_id'],self.bid)
        with self.assertRaises(Problem):self.worker.analytics(self.user,self.other_b['id'])
        (status,_),body=self.wsgi('/api/analytics',headers={'HTTP_COOKIE':'desk_session='+self.token,'QUERY_STRING':'business='+self.bid})
        self.assertTrue(status.startswith('200'),status);self.assertEqual(body['summary']['sales'],100)

    def test_verified_identity_signup_creates_only_its_own_organisation(self):
        identity={'id':str(uuid.uuid4()),'email':'owner@example.test','ttl':3600,'role':'manager','organization_id':self.user['organization_id']}
        token,result=self.desk.email_identity(identity,'Verified Owner',True)
        user,_=self.worker.session(token)
        self.assertEqual(user['role'],'owner');self.assertNotEqual(user['organization_id'],self.user['organization_id'])
        self.assertEqual(self.worker.businesses(user),[]);self.assertEqual(result['user']['auth_email'],'owner@example.test')
        again,_=self.worker.email_identity(identity,'Changed display input',False)
        self.assertEqual(self.desk.session(again)[0]['id'],user['id'])
        with self.desk.connect() as conn:
            ttl=conn.execute('SELECT extract(epoch FROM expires-now()) AS ttl FROM desk_sessions WHERE token_hash=?',(self.desk.token_hash(token),)).fetchone()['ttl']
        self.assertTrue(0<ttl<=3600)

    def test_email_invitation_keeps_saved_staff_role_and_business_scope(self):
        self.desk.add_user(self.user,{'name':'Invited front desk','auth_email':'staff@example.test','role':'frontdesk','business_ids':[self.bid]})
        identity={'id':str(uuid.uuid4()),'email':'staff@example.test','ttl':3600,'role':'owner','organization_id':self.other['organization_id']}
        token,_=self.worker.email_identity(identity,'Untrusted new name',True)
        staff,_=self.desk.session(token)
        self.assertEqual(staff['role'],'frontdesk');self.assertEqual(staff['organization_id'],self.user['organization_id'])
        self.assertEqual([b['id'] for b in self.worker.businesses(staff)],[self.bid])
        with self.assertRaises(Problem):self.worker.analytics(staff,self.bid)
        with self.assertRaises(Problem):self.worker.state(staff,self.other_b['id'])
        with self.desk.connect() as conn:conn.execute('UPDATE users SET active=0 WHERE id=?',(staff['id'],))
        with self.assertRaises(Problem):self.worker.session(token)
        with self.assertRaises(Problem):self.worker.email_identity(identity,'',True)

    def test_email_signups_cannot_claim_legacy_usernames_or_closed_registration(self):
        self.desk.add_user(self.user,{'name':'Existing employee','username':'legacy@example.test','password':'fictional-password','role':'frontdesk','business_ids':[self.bid]})
        identity={'id':str(uuid.uuid4()),'email':'legacy@example.test','ttl':3600}
        with self.assertRaises(Problem):self.worker.email_identity(identity,'Person',False)
        token,_=self.worker.email_identity(identity,'Independent owner',True)
        self.assertNotEqual(self.desk.session(token)[0]['organization_id'],self.user['organization_id'])

    def test_expired_duplicate_or_foreign_invitation_rejected(self):
        data={'name':'Staff','auth_email':'staff@example.test','role':'frontdesk','business_ids':[self.bid]}
        self.desk.add_user(self.user,data)
        with self.assertRaises(Problem):self.worker.add_user(self.other,{**data,'business_ids':[self.other_b['id']]})
        with self.assertRaises(Problem):self.desk.add_user(self.user,{**data,'auth_email':'other@example.test','business_ids':[self.other_b['id']]})
        with self.desk.connect() as conn:conn.execute("UPDATE desk_email_invites SET expires=now()-interval '1 day'")
        with self.assertRaises(Problem):self.worker.email_identity({'id':str(uuid.uuid4()),'email':'staff@example.test','ttl':3600},'',True)
        accounts=self.desk.users(self.user);self.assertTrue(any(x.get('invite_pending') and x.get('auth_email')=='staff@example.test' for x in accounts))

    def test_gateway_email_verification_to_saved_session_uses_only_provider_identity(self):
        from cloud_auth import SupabaseEmailAuth
        identity={'id':str(uuid.uuid4()),'email':'gateway@example.test','ttl':3600}
        env={'DESK_EMAIL_AUTH':'true','SUPABASE_URL':'https://fictional-ci-project.supabase.co','SUPABASE_PUBLISHABLE_KEY':'sb_publishable_fictional_ci_key_only'}
        with unittest.mock.patch.dict(os.environ,env),unittest.mock.patch.object(SupabaseEmailAuth,'send_code') as send,unittest.mock.patch.object(SupabaseEmailAuth,'verify',return_value=identity):
            status,_=self.wsgi('/api/email-code','POST',{'email':identity['email'],'signup':True,'role':'owner'})
            self.assertTrue(status[0].startswith('200'));send.assert_called_once_with(identity['email'],create_user=True)
            (status,headers),body=self.wsgi('/api/email-login','POST',{'email':identity['email'],'code':'123456','signup':True,'name':'Gateway owner','provider_id':self.user['id'],'organization_id':self.user['organization_id']})
            self.assertTrue(status.startswith('200'),body);cookie=dict(headers)['Set-Cookie']
            self.assertIn('HttpOnly',cookie);self.assertIn('Secure',cookie);self.assertIn('SameSite=Strict',cookie);self.assertIn('Max-Age=3600',cookie)
            saved=self.worker.session(cookie.split(';')[0].split('=',1)[1])[0]
            self.assertEqual(saved['id'],body['user']['id']);self.assertNotEqual(saved['organization_id'],self.user['organization_id'])
            self.assertNotIn('access_token',body)


@unittest.skipUnless(URL,'Disposable PostgreSQL test URL not configured')
class PrivateSupabaseSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not URL.endswith('/desk_ci'):raise RuntimeError('Only the disposable desk_ci database can be used.')
        from cloud import CloudDesk
        cls.CloudDesk=CloudDesk;cls.desk=CloudDesk(URL,bootstrap=True,schema='desk_private_ci')
        with cls.desk.connect() as conn:
            for name in ('anon','authenticated'):
                if not conn.execute('SELECT 1 FROM pg_roles WHERE rolname=?',(name,)).fetchone():conn.execute('CREATE ROLE '+name+' NOLOGIN')
            if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='desk_runtime_ci'").fetchone():
                conn.execute("CREATE ROLE desk_runtime_ci LOGIN PASSWORD 'fictional-runtime-password' NOSUPERUSER NOBYPASSRLS")
        from deploy.setup_supabase import secure_schema
        secure_schema(cls.desk,'desk_runtime_ci')
        from urllib.parse import urlsplit,urlunsplit
        parsed=urlsplit(URL);runtime_url=urlunsplit(parsed._replace(netloc='desk_runtime_ci:fictional-runtime-password@'+parsed.hostname+':'+str(parsed.port or 5432)))
        cls.runtime=CloudDesk(runtime_url,schema='desk_private_ci')
    @classmethod
    def tearDownClass(cls):cls.runtime.close();cls.desk.close()
    def test_runtime_role_can_signup_and_reconnect_without_ddl(self):
        identity={'id':str(uuid.uuid4()),'email':'private'+uuid.uuid4().hex+'@example.test','ttl':3600}
        token,_=self.runtime.email_identity(identity,'Private schema owner',True)
        user,_=self.runtime.session(token)
        business=self.runtime.save_business(user,{'data':{'name':'Private runtime garage'}})
        self.assertEqual(self.runtime.analytics(user,business['id'])['business_id'],business['id'])
        with self.runtime.connect() as conn:
            self.assertTrue(self.runtime.column_exists(conn,'users','organization_id'))
        with self.assertRaises(Exception):
            with self.runtime.connect() as conn:conn.execute('CREATE TABLE desk_private_ci.forbidden(id TEXT)')
    def test_data_api_roles_cannot_read_records_and_rls_enabled(self):
        with self.desk.connect() as conn:
            for role in ('anon','authenticated'):
                self.assertFalse(conn.execute("SELECT has_schema_privilege(?,?,'USAGE') AS allowed",(role,self.desk.schema)).fetchone()['allowed'])
                self.assertFalse(conn.execute("SELECT has_table_privilege(?,?,'SELECT') AS allowed",(role,self.desk.schema+'.records')).fetchone()['allowed'])
            rows=conn.execute('SELECT c.relname,c.relrowsecurity FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname=? AND c.relkind=?',(self.desk.schema,'r')).fetchall()
            self.assertTrue(all(x['relrowsecurity'] for x in rows));self.assertEqual(len(rows),12)
