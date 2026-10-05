"""Provider-boundary verification with fictional responses; never sends real email."""
import base64
from io import BytesIO
import json
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from cloud_auth import SupabaseEmailAuth, normal_email
from domain import Problem

KEY='sb_publishable_fictional_test_key_not_a_real_key'
UID='c46a5c84-70a5-411e-8ed8-78a2c3958d58'

class VerifiedEmailBoundary(unittest.TestCase):
    def setUp(self):self.auth=SupabaseEmailAuth('https://fictional-test-project.supabase.co',KEY)
    def test_rejects_secret_keys_untrusted_urls_and_service_role_legacy_jwt(self):
        for url in ['http://fictional.supabase.co','https://evil.test','https://fictional.supabase.co/other','https://secret@fictional.supabase.co','https://fictional.supabase.co?query=yes']:
            with self.assertRaises(ValueError):SupabaseEmailAuth(url,KEY)
        for key in ['sb_secret_no','not_a_key','e30.'+base64.urlsafe_b64encode(b'{"role":"service_role"}').decode().rstrip('=')+'.signature']:
            with self.assertRaises(ValueError):SupabaseEmailAuth('https://fictional.supabase.co',key)
    def test_email_normalisation_rejects_header_injection_and_invalid_addresses(self):
        self.assertEqual(normal_email(' Person@Example.test '),'person@example.test')
        for value in ['missing','a@b','a\r\n@b.test','a b@b.test','a@'+('x'*255)+'.test']:
            with self.assertRaises(Problem):normal_email(value)
    def test_send_code_does_not_submit_roles_or_metadata(self):
        self.auth.request=Mock(return_value={});self.auth.send_code(' Person@Example.test ',True)
        self.auth.request.assert_called_once_with('/otp',{'email':'person@example.test','create_user':True})
    def test_verify_gets_authoritative_user_ignores_provider_metadata_and_caps_session(self):
        self.auth.request=Mock(side_effect=[{'access_token':'fictional-token','expires_in':86400,'user':{'id':'untrusted'}},
            {'id':UID,'email':'person@example.test','email_confirmed_at':'2026-01-01','user_metadata':{'role':'owner','organization_id':'foreign'}}])
        identity=self.auth.verify('person@example.test','123456')
        self.assertEqual(identity,{'id':UID,'email':'person@example.test','ttl':3600})
        self.assertEqual(self.auth.request.call_args_list[-1].args,('/user',));self.assertEqual(self.auth.request.call_args_list[-1].kwargs,{'token':'fictional-token'})
    def test_unconfirmed_mismatched_or_malformed_identity_is_rejected(self):
        for user in [{'id':UID,'email':'person@example.test'},{'id':UID,'email':'other@example.test','email_confirmed_at':'now'},
                     {'id':'forged','email':'person@example.test','email_confirmed_at':'now'}]:
            self.auth.request=Mock(side_effect=[{'access_token':'fictional-token'},user])
            with self.assertRaises(Problem) as error:self.auth.verify('person@example.test','123456')
            self.assertEqual(error.exception.status,401)
    def test_invalid_code_does_not_contact_provider(self):
        self.auth.request=Mock()
        for code in ['123','abcdef','12345678901']:
            with self.assertRaises(Problem):self.auth.verify('person@example.test',code)
        self.auth.request.assert_not_called()
    def test_network_errors_and_provider_error_bodies_do_not_leak(self):
        for status in [400,401,429,500]:
            self.auth.opener.open=Mock(side_effect=HTTPError('https://fictional.supabase.co',status,'SECRET-SENTINEL',{},BytesIO(b'SECRET-SENTINEL')))
            with self.assertRaises(Problem) as error:self.auth.request('/otp',{})
            self.assertNotIn('SECRET-SENTINEL',str(error.exception));self.assertEqual(error.exception.status,429 if status==429 else 503 if status==500 else 401)
        self.auth.opener.open=Mock(side_effect=URLError('SECRET-SENTINEL'))
        with self.assertRaises(Problem) as error:self.auth.request('/user',token='SECRET-SENTINEL')
        self.assertEqual(error.exception.status,503);self.assertNotIn('SECRET-SENTINEL',str(error.exception))
    def test_http_transport_uses_fixed_endpoint_timeout_and_bounded_response(self):
        response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=None);response.read.return_value=b'{}'
        self.auth.opener.open=Mock(return_value=response)
        self.assertEqual(self.auth.request('/otp',{'email':'person@example.test'}),{})
        request=self.auth.opener.open.call_args.args[0]
        self.assertEqual(request.full_url,'https://fictional-test-project.supabase.co/auth/v1/otp')
        self.assertEqual(self.auth.opener.open.call_args.kwargs,{'timeout':8});response.read.assert_called_once_with(1_048_577)

if __name__=='__main__':unittest.main()
