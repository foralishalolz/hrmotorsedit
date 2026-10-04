"""Country, client configuration and financial return failure cases."""
import copy
import tempfile
import unittest
from domain import Desk, Problem, calculate, today
from regional import financial_year
from server import print_document


class RegionalWorkflows(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.desk=Desk(self.temp.name)
        token,_=self.desk.setup({'name':'Test owner','username':'owner','password':'test-only-password'})
        self.user,_=self.desk.session(token)
        self.business=self.desk.save_business(self.user,{'data':{'name':'Fictional India Repairs','country':'IN','profile':'garage','address':'Test road, Pune','state_code':'27','gst_registration':'regular','gstin':'27ABCDE1234F1Z5','vat_rate':18}})
        self.bid=self.business['id']
        self.customer=self.save('customers',name='Test client',address='Test lane, Pune',state_code='27',discount_percent=5,payment_terms_days=15,tags='Fleet, VIP, Fleet')

    def tearDown(self): self.temp.cleanup()
    def save(self,kind,**data): return self.desk.save(self.user,self.bid,kind,{'data':data})
    def change_business(self,**data):
        self.business=self.desk.save_business(self.user,{'id':self.bid,'version':self.business['version'],'data':{**self.business,**data}})
        return self.business
    def action(self,row,action,**data): return self.desk.action(self.user,self.bid,row['type'],row['id'],{'version':row['version'],'action':action,**data})
    def draft(self,**data):
        return self.save('invoices',**{'customer_id':self.customer['id'],'items':[{'description':'Reviewed service','qty':1,'rate':1000,'tax_rate':18,'hsn_sac':'998729'}],'vat_mode':'added','date':today(),**data})
    def issued(self,**data): return self.action(self.draft(**data),'issue')
    def state(self): return self.desk.state(self.user,self.bid)
    def get(self,kind,rid): return next(x for x in self.state()['records'][kind] if x['id']==rid)

    def test_country_currency_and_customer_preferences(self):
        self.assertEqual(self.business['currency'],'INR')
        self.assertEqual(self.business['timezone'],'Asia/Kolkata')
        self.assertEqual(self.customer['tags'],['Fleet','VIP'])
        self.assertEqual(self.customer['discount_percent'],5)
        self.assertEqual(self.customer['payment_terms_days'],15)

    def test_intra_state_split_and_seller_snapshot(self):
        invoice=self.issued()
        self.assertEqual(invoice['totals_snapshot']['tax_components'],{'CGST':90,'SGST':90})
        self.change_business(name='Changed name',state_code='29',gstin='29ABCDE1234F1Z5')
        printed=print_document(self.desk,self.user,self.bid,'invoices',invoice['id']).decode()
        self.assertIn('Fictional India Repairs',printed)
        self.assertIn('27ABCDE1234F1Z5',printed)
        self.assertIn('TAX INVOICE',printed)
        self.assertIn('HSN / SAC: 998729',printed)
        self.assertIn('INR 1,180.00',printed)
        self.assertIn('CGST',printed)
        self.assertNotIn('NPR',printed)

    def test_inter_state_igst(self):
        invoice=self.issued(place_of_supply='29')
        self.assertEqual(invoice['totals_snapshot']['tax_components'],{'IGST':180})

    def test_union_territory_split(self):
        self.change_business(state_code='04',gstin='04ABCDE1234F1Z5')
        invoice=self.issued(place_of_supply='04')
        self.assertEqual(invoice['totals_snapshot']['tax_components'],{'CGST':90,'UTGST':90})

    def test_included_tax_and_percentage_cess(self):
        invoice=self.issued(vat_mode='included',items=[{'description':'Test goods','qty':1,'rate':1200,'tax_rate':18,'cess_rate':2,'hsn_sac':'8708'}])
        totals=invoice['totals_snapshot']
        self.assertEqual(totals['net'],1000)
        self.assertEqual(totals['total'],1200)
        self.assertEqual(totals['tax_components'],{'CGST':90,'SGST':90,'Cess':20})

    def test_component_cents_reconcile(self):
        invoice=self.issued(items=[{'description':'Small amount','qty':1,'rate':0.03,'tax_rate':18,'hsn_sac':'8708'}])
        totals=invoice['totals_snapshot']
        self.assertAlmostEqual(sum(totals['tax_components'].values()),totals['tax'])
        self.assertAlmostEqual(totals['net']+totals['tax'],totals['total'])

    def test_composition_cannot_collect_tax(self):
        self.change_business(gst_registration='composition')
        with self.assertRaises(Problem): self.draft()
        invoice=self.issued(vat_mode='none')
        self.assertEqual(invoice['totals_snapshot']['tax'],0)
        self.assertEqual(invoice['document_title'],'BILL OF SUPPLY')

    def test_unregistered_invoice_has_no_gst(self):
        self.change_business(gst_registration='unregistered',gstin='')
        with self.assertRaises(Problem): self.draft()
        invoice=self.issued(vat_mode='none')
        self.assertEqual(invoice['document_title'],'INVOICE')

    def test_missing_hsn_and_address_block_issue(self):
        draft=self.draft(items=[{'description':'No HSN','rate':100,'qty':1}])
        with self.assertRaises(Problem): self.action(draft,'issue')
        self.assertEqual(self.get('invoices',draft['id'])['status'],'draft')
        self.change_business(address='')
        with self.assertRaises(Problem): self.issued()

    def test_einvoice_required_is_not_bypassed_by_client_data(self):
        self.change_business(einvoice_required=True)
        draft=self.draft(einvoice_required=False,country='NP')
        with self.assertRaisesRegex(Problem,'IRP'): self.action(draft,'issue')

    def test_country_cannot_relabel_existing_money(self):
        self.draft()
        with self.assertRaisesRegex(Problem,'Country and currency'): self.change_business(country='NP')

    def test_gstin_state_validation(self):
        with self.assertRaises(Problem): self.change_business(gstin='WRONG')
        with self.assertRaises(Problem): self.change_business(gstin='29ABCDE1234F1Z5')

    def test_indian_financial_year_numbering(self):
        self.assertEqual(financial_year('2026-03-31'),'2526')
        self.assertEqual(financial_year('2026-04-01'),'2627')
        first=self.issued(date='2026-03-31');second=self.issued(date='2026-04-01')
        self.assertEqual(first['number'],'INV-2526-0001')
        self.assertEqual(second['number'],'INV-2627-0001')
        self.assertLessEqual(len(second['number']),16)

    def test_custom_fields_and_job_checklist(self):
        self.change_business(job_checklist=['Photograph damage','Check paint match'],custom_fields=[{'kind':'jobs','key':'paint_code','label':'Paint code','type':'text'}])
        job=self.save('jobs',name='Paint panel',customer_id=self.customer['id'],custom_fields={'paint_code':'AB-12'})
        self.assertEqual([x['name'] for x in job['tasks']],['Photograph damage','Check paint match'])
        self.assertEqual(job['custom_fields']['paint_code'],'AB-12')
        with self.assertRaises(Problem): self.change_business(custom_fields=[{'kind':'jobs','key':'../evil','label':'No','type':'text'}])

    def test_barcode_uniqueness_within_business(self):
        self.save('stock',name='One',barcode='TEST-0001')
        with self.assertRaisesRegex(Problem,'barcode'): self.save('stock',name='Two',barcode='TEST-0001')

    def test_line_return_retains_tax_and_restock(self):
        item=self.save('stock',name='Test filter',opening_qty=4,cost=30,rate=100)
        invoice=self.issued(items=[{'description':'Test filter','item_id':item['id'],'qty':2,'rate':100,'tax_rate':18,'hsn_sac':'8421'}])
        self.assertEqual(self.get('stock',item['id'])['_quantity'],2)
        credit=self.action(invoice,'return',reason='One unopened item returned',items=[{'line_index':0,'qty':1,'restock':True}])
        self.assertEqual(credit['amount'],118)
        self.assertEqual(credit['tax_components'],{'CGST':9,'SGST':9})
        self.assertEqual(self.get('stock',item['id'])['_quantity'],3)
        self.assertEqual(self.get('invoices',invoice['id'])['_balance'],118)
        with self.assertRaises(Problem): self.action(invoice,'return',reason='Stale reviewer',items=[{'line_index':0,'qty':1}])
        fresh=self.get('invoices',invoice['id'])
        with self.assertRaises(Problem): self.action(fresh,'return',reason='Too many',items=[{'line_index':0,'qty':2}])
        self.assertEqual(len(self.state()['records']['credits']),1)

    def test_return_rolls_back_stock_on_invalid_second_line(self):
        item=self.save('stock',name='Part',opening_qty=5,cost=10)
        invoice=self.issued(items=[{'description':'Part','item_id':item['id'],'qty':1,'rate':100,'tax_rate':18,'hsn_sac':'8708'}])
        with self.assertRaises(Problem): self.action(invoice,'return',reason='Invalid line',items=[{'line_index':0,'qty':1,'restock':True},{'line_index':99,'qty':1}])
        self.assertEqual(self.get('stock',item['id'])['_quantity'],4)
        self.assertFalse(self.state()['records']['credits'])

    def test_full_partial_returns_do_not_lose_rounding_cents(self):
        invoice=self.issued(items=[{'description':'Fractional service','qty':3,'rate':0.19,'tax_rate':18,'hsn_sac':'998729'}])
        for _ in range(3):
            self.action(self.get('invoices',invoice['id']),'return',reason='One unit credit',items=[{'line_index':0,'qty':1}])
        self.assertEqual(self.get('invoices',invoice['id'])['_balance'],0)
        self.assertAlmostEqual(sum(x['tax'] for x in self.state()['records']['credits']),invoice['totals_snapshot']['tax'])

    def test_cashier_cannot_post_return_credit(self):
        invoice=self.issued()
        cashier={**self.user,'role':'cashier','business_ids':'["'+self.bid+'"]'}
        with self.assertRaises(Problem): self.desk.action(cashier,self.bid,'invoices',invoice['id'],{'version':invoice['version'],'action':'return','reason':'No permission','items':[{'line_index':0,'qty':1}]})

    def test_nepal_calculation_preserved(self):
        totals=calculate({'vat_mode':'added','vat_rate':13,'items':[{'description':'Part','qty':2,'rate':100}]})
        self.assertEqual(totals['total'],226)
        self.assertFalse(totals['tax_components'])


if __name__=='__main__': unittest.main()
