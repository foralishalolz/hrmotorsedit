"""Business identity, controlled migration, collections and operating checks."""
import base64
import hashlib
import json
import re
from regional import business_today


IMPORT_FIELDS = {
    'customers': ['name','phone','email','address','pan','state_code','gstin','tags','preferred_language','discount_percent','payment_terms_days','credit_limit'],
    'stock': ['name','sku','barcode','unit','opening_qty','cost','rate','reorder_at','location','category_label','hsn_sac','tax_rate','cess_rate'],
    'services': ['name','category','unit','rate','cost','notes','hsn_sac','tax_rate','cess_rate'],
    'suppliers': ['name','contact_person','phone','email','address','pan','terms'],
    'vehicles': ['name','vin','condition','model_year','color','sale_price','purchase_cost','location','arrival_date','hsn_sac','tax_rate','cess_rate'],
    'opening_balances': ['customer_phone','source_reference','amount','date','notes'],
}
NUMERIC_FIELDS = {'opening_qty','cost','rate','reorder_at','tax_rate','cess_rate','sale_price','purchase_cost','discount_percent','payment_terms_days','credit_limit','amount'}


def phone_key(value):
    return re.sub(r'\D', '', str(value or ''))


def validate_identity(data):
    from domain import Problem
    for key, limit in [('trading_name',100),('short_name',24),('invoice_footer',1500),('payment_instructions',1500),('business_description',1200)]:
        data[key] = str(data.get(key, '')).strip()[:limit]
    colour = str(data.get('brand_hex', '')).strip()
    if colour and not re.fullmatch(r'#[0-9a-fA-F]{6}', colour): raise Problem('Brand colour must be a six-digit hex colour.')
    data['brand_hex'] = colour
    logo = str(data.get('logo_data', ''))
    if logo:
        match = re.fullmatch(r'data:image/(png|jpeg);base64,([A-Za-z0-9+/=]+)', logo)
        if not match: raise Problem('Use a PNG or JPEG business logo.')
        try: raw = base64.b64decode(match[2], validate=True)
        except ValueError: raise Problem('The logo could not be read.')
        if len(raw) > 100_000: raise Problem('Use a business logo smaller than 100 KB.')
        if not (raw.startswith(b'\x89PNG\r\n\x1a\n') if match[1] == 'png' else raw.startswith(b'\xff\xd8\xff')):
            raise Problem('The logo does not match its image format.')
    data['logo_data'] = logo
    rules = data.setdefault('operating_rules', {})
    if not isinstance(rules, dict): raise Problem('Operating rules must be a settings map.')
    data['operating_rules'] = {key: bool(rules.get(key, False)) for key in ('credit_limit_enforced','handover_requires_payment','handover_requires_checks','work_requires_quote_approval')}
    discovery = data.setdefault('discovery', {})
    if not isinstance(discovery, dict) or len(discovery) > 20: raise Problem('Use a short business configuration worksheet.')
    data['discovery'] = {str(k)[:60]:str(v)[:1500] for k,v in discovery.items()}


class ImportPreview(Exception):
    def __init__(self, result): self.result = result


class OperationsFeatures:
    def validate_operations(self, conn, user, bid, kind, data, old):
        from domain import Problem, decimal, money, number, checked_date
        if kind == 'customers':
            data['credit_limit'] = number(money(decimal(data.get('credit_limit',0), 'Credit limit', 0)))
            agreements = data.setdefault('price_agreements', [])
            if not isinstance(agreements,list) or len(agreements)>100: raise Problem('Use at most 100 agreed item prices per customer.')
            seen=set()
            for price in agreements:
                if not isinstance(price,dict) or price.get('kind') not in ('stock','services'): raise Problem('Choose a stock item or service for each agreed price.')
                self.record(conn,bid,price.get('item_id'),price['kind'])
                price['min_qty']=number(decimal(price.get('min_qty',1),'Minimum quantity','.0001'))
                price['rate']=number(money(decimal(price.get('rate'), 'Agreed price', 0)))
                key=(price['kind'],price['item_id'],price['min_qty'])
                if key in seen: raise Problem('Each item and minimum quantity needs one agreed price.')
                seen.add(key)
            if user['role']!='owner':
                data['credit_limit']=(old or {}).get('credit_limit',0)
                data['price_agreements']=(old or {}).get('price_agreements',[])
        if kind == 'jobs':
            inspection=data.get('inspection',[])
            if not isinstance(inspection,list) or len(inspection)>40: raise Problem('Use at most 40 inspection findings.')
            for finding in inspection:
                if not isinstance(finding,dict) or finding.get('condition') not in ('not_checked','good','advisory','urgent'): raise Problem('Choose a condition for each inspection finding.')
                if not str(finding.get('area','')).strip(): raise Problem('Name the inspected area.')
                for key in ('area','notes','recommendation'): finding[key]=str(finding.get(key,''))[:1500]
            business=self.business(conn,bid)
            if data.get('stage') and data['stage'] not in business['stages']: raise Problem('Choose a configured work stage.')
            if not old or data.get('stage')!=old.get('stage'):
                business=self.business(conn,bid); rules=business.get('operating_rules',{})
                if rules.get('work_requires_quote_approval') and data.get('quote_id') and data.get('stage') not in (business['stages'][0],'Awaiting approval'):
                    if self.record(conn,bid,data['quote_id'],'quotes').get('status')!='accepted': raise Problem('Record approval of the linked quotation before starting work.')
                if data.get('stage')==business['stages'][-1]:
                    reason=str(data.get('handover_override_reason','')).strip()
                    override=user['role']=='owner' and len(reason)>=10
                    checks=data.get('tasks',[])
                    configured={x.casefold() for x in business.get('job_checklist',[])}
                    present={str(x.get('name','')).strip().casefold() for x in checks}
                    if rules.get('handover_requires_checks') and (not checks or not configured.issubset(present) or any(x.get('done') is not True for x in checks)) and not override:
                        raise Problem('Complete the handover checklist, or ask the owner to record an override reason.')
                    if rules.get('handover_requires_payment'):
                        records=self.enrich(self.records(conn,bid)); invoices=[x for x in records['invoices'] if old and x.get('job_id')==old['id'] and x.get('status')=='issued']
                        if (not invoices or any(x['_balance']>.009 for x in invoices)) and not override: raise Problem('Complete billing and collection before handover, or ask the owner to record an override reason.')
                    if override: self.audit(conn,user,bid,'Handover override','jobs',(old or {}).get('id',''),reason)
        if kind == 'opening_balances':
            if user['role']!='owner': raise Problem('Only the owner can post reconciled opening balances.',403)
            if old: raise Problem('Opening balances are retained. Post a separate reviewed correction.',409)
            if not data.get('reconciled'): raise Problem('Confirm that the opening balance was reconciled to source records.')
            if not data.get('customer_id'): raise Problem('Choose the customer for this opening balance.')
            data['amount']=number(money(decimal(data.get('amount'),'Opening balance')))
            if not data['amount']: raise Problem('An opening balance cannot be zero.')
            data['date']=checked_date(data.get('date'),'Balance as-of date',False)
            data['source_reference']=str(data.get('source_reference','')).strip()[:120]
            if not data['source_reference']: raise Problem('Retain the original statement or ledger reference.')
            if any(x.get('source_reference','').casefold()==data['source_reference'].casefold() and x.get('customer_id')==data['customer_id'] for x in self.records(conn,bid)[kind]): raise Problem('That customer opening reference is already recorded.',409)
            data['number']=self.next_number(conn,bid,'OPEN',data['date']);data['status']='posted'
        if kind == 'cash_closures':
            if old: raise Problem('Cash counts are retained. The owner can post a reviewed replacement.',409)
            data['date']=checked_date(data.get('date') or business_today(self.business(conn,bid)))
            data['opening_float']=number(money(decimal(data.get('opening_float'), 'Opening cash float', 0)))
            data['counted_cash']=number(money(decimal(data.get('counted_cash'), 'Cash physically counted', 0)))
            records=self.records(conn,bid); previous=[x for x in records[kind] if x['date']==data['date']]
            if previous and (user['role']!='owner' or len(str(data.get('notes','')).strip())<10): raise Problem('This day already has a count. The owner must record a reason for a replacement.',409)
            expected,fingerprint=self.cash_position(records,data['date'],data['opening_float'])
            data.update(expected_cash=expected,variance=number(money(data['counted_cash'])-money(expected)),source_hash=fingerprint,status='posted',number=self.next_number(conn,bid,'CASH',data['date']),counted_by=user['name'])

    def validate_opening_payment(self, conn, bid, data):
        from domain import Problem, decimal, money, number, checked_date
        opening=self.record(conn,bid,data['opening_balance_id'],'opening_balances')
        if data.get('invoice_id'): raise Problem('Link a receipt to an invoice or an opening balance, not both.')
        data['customer_id']=opening['customer_id']
        direction=data.get('direction','receipt')
        if direction not in ('receipt','refund'): raise Problem('Choose receipt or refund.')
        amount=money(decimal(data.get('amount'),'Amount','.01'))
        records=self.records(conn,bid)
        balance=money(opening['amount'])-sum((money(x['amount'])*(1 if x.get('direction')=='receipt' else -1) for x in records['payments'] if x.get('opening_balance_id')==opening['id']),money(0))
        if (direction=='receipt' and (balance<=0 or amount>balance)) or (direction=='refund' and (balance>=0 or amount>-balance)): raise Problem('The amount exceeds the remaining opening balance or customer credit.')
        data.update(amount=number(amount),direction=direction,date=checked_date(data.get('date') or business_today(self.business(conn,bid))),number=self.next_number(conn,bid,'RCT' if direction=='receipt' else 'RFD'))

    def enforce_credit_limit(self, conn, user, bid, invoice, totals, payload):
        from domain import Problem, money
        business=self.business(conn,bid)
        if not business.get('operating_rules',{}).get('credit_limit_enforced'): return
        customer=self.record(conn,bid,invoice['customer_id'],'customers');limit=money(customer.get('credit_limit',0))
        if limit<=0: return
        records=self.enrich(self.records(conn,bid))
        outstanding=sum((money(x['_balance']) for kind in ('invoices','opening_balances') for x in records[kind] if x.get('customer_id')==customer['id'] and x.get('_balance',0)>0 and x.get('status') in ('issued','posted')),money(0))
        if outstanding+money(totals['total'])>limit:
            reason=str(payload.get('credit_override_reason','')).strip()
            if user['role']!='owner' or len(reason)<10: raise Problem('This bill exceeds the customer credit limit. Ask the owner to record an override reason.',409)
            invoice['credit_override_reason']=reason
            self.audit(conn,user,bid,'Credit limit override','invoices',invoice['id'],reason)

    def cash_position(self, records, day, opening=0):
        from domain import money,number
        entries=[];total=money(opening)
        for kind in ('payments','expenses','supplier_payments'):
            for row in records[kind]:
                if row.get('date')!=day or str(row.get('method','')).casefold()!='cash': continue
                sign=1 if kind=='payments' and row.get('direction')!='refund' else -1
                total+=money(row['amount'])*sign
                entries.append((kind,row['id'],row['amount'],row.get('direction','')))
        fingerprint=hashlib.sha256(json.dumps(sorted(entries),sort_keys=True).encode()).hexdigest()
        return number(total),fingerprint

    def enrich_operations(self, records):
        from domain import money,number
        grouped={}
        for p in records['payments']:
            if p.get('opening_balance_id'): grouped[p['opening_balance_id']]=grouped.get(p['opening_balance_id'],money(0))+money(p['amount'])*(1 if p.get('direction')!='refund' else -1)
        for row in records['opening_balances']:
            row['_paid']=number(grouped.get(row['id'],money(0)));row['_balance']=number(money(row['amount'])-money(row['_paid']))
        for row in records['cash_closures']:
            _,fingerprint=self.cash_position(records,row['date'],row['opening_float']);row['_source_changed']=fingerprint!=row['source_hash']

    def stock_count(self,user,bid,payload):
        from domain import Problem,decimal,number
        self.business_allowed(user,bid);self.permitted(user,'movements',True)
        entries=payload.get('items',[]);reason=str(payload.get('reason','')).strip()
        if not isinstance(entries,list) or not 1<=len(entries)<=100 or len(reason)<5: raise Problem('Choose up to 100 stock items and record a count reason.')
        seen=set();created=[]
        with self.transaction() as conn:
            records=self.records(conn,bid)
            for x in entries:
                if x.get('item_id') in seen: raise Problem('Count each item once.')
                seen.add(x.get('item_id'));item=self.record(conn,bid,x.get('item_id'),'stock')
                actual=decimal(self.stock_quantity(records,item['id']));expected=decimal(x.get('expected_qty'),'Expected quantity',0)
                if actual!=expected or x.get('version')!=item['version']: raise Problem('Stock changed while you were counting. Refresh and review the count.',409)
                counted=decimal(x.get('counted_qty'),'Counted quantity',0);delta=counted-actual
                if delta:
                    created.append(self.save(user,bid,'movements',{'data':{'item_id':item['id'],'kind':'adjustment','qty':number(delta),'unit_cost':item['cost'],'date':business_today(self.business(conn,bid)),'notes':'Physical count: '+reason}}))
            self.audit(conn,user,bid,'Stock count posted','stock','',reason)
        return {'ok':True,'adjustments':len(created)}

    def import_batch(self,user,bid,payload,preview=False):
        from domain import Problem,decimal,number
        self.business_allowed(user,bid)
        if user['role']!='owner': raise Problem('Only the owner can import business records.',403)
        kind=payload.get('kind');rows=payload.get('rows',[])
        if kind not in IMPORT_FIELDS or not isinstance(rows,list) or not 1<=len(rows)<=250: raise Problem('Choose a supported import area and 1–250 rows per batch.')
        result={'created':0,'skipped':0,'errors':[],'sample':[]}
        try:
            with self.transaction() as conn:
                existing=self.records(conn,bid)
                for i,source in enumerate(rows):
                    if not isinstance(source,dict): raise Problem('Each import row must be a field map.')
                    data={k:source[k] for k in IMPORT_FIELDS[kind] if k in source and source[k] not in ('',None)}
                    try:
                        if kind!='opening_balances' and not str(data.get('name','')).strip(): raise Problem('Name is required.')
                        if kind=='vehicles' and not str(data.get('vin','')).strip(): raise Problem('A chassis / VIN is required.')
                        for key in NUMERIC_FIELDS & data.keys(): data[key]=number(decimal(data[key],key.replace('_',' ')))
                        if kind=='opening_balances':
                            phone=phone_key(data.pop('customer_phone',''));matches=[x for x in existing['customers'] if phone and phone_key(x.get('phone'))==phone]
                            if len(matches)!=1: raise Problem('Customer phone must match exactly one imported customer.')
                            data['customer_id']=matches[0]['id'];data['reconciled']=bool(payload.get('reconciled'))
                        key=self.import_identity(kind,data)
                        if any(self.import_identity(kind,x)==key for x in existing[kind]): result['skipped']+=1;continue
                        data['import_source']=str(payload.get('filename','CSV import'))[:120]
                        saved=self.save(user,bid,kind,{'data':data});existing[kind].append(saved);result['created']+=1
                        if len(result['sample'])<5: result['sample'].append({k:v for k,v in data.items() if k not in ('customer_id',)})
                    except Problem as error:
                        result['errors'].append({'row':i+1,'message':str(error)})
                        # Roll back the whole batch if any row is invalid.
                        if not preview: raise Problem('Import row '+str(i+1)+': '+str(error),error.status)
                if preview: raise ImportPreview(result)
                self.audit(conn,user,bid,'CSV batch imported',kind,'',f"{result['created']} created; {result['skipped']} duplicates skipped")
        except ImportPreview as done: return done.result
        return result

    def import_identity(self,kind,data):
        if kind=='stock': return ('sku',str(data['sku']).strip().casefold()) if data.get('sku') else ('barcode',str(data['barcode']).strip()) if data.get('barcode') else ('name',str(data.get('name','')).strip().casefold())
        if kind=='vehicles': return str(data.get('vin','')).strip().casefold()
        if kind=='opening_balances': return (data.get('customer_id'),str(data.get('source_reference','')).strip().casefold())
        return (str(data.get('name','')).strip().casefold(),phone_key(data.get('phone',''))) if kind in ('customers','suppliers') else str(data.get('name','')).strip().casefold()

    def customer_statement(self,user,bid,cid):
        from domain import money,number
        state=self.state(user,bid);customer=next((x for x in state['records']['customers'] if x['id']==cid),None)
        if customer is None:
            from domain import Problem
            raise Problem('Customer not found in this business.',404)
        entries=[]
        for kind in ('invoices','opening_balances','payments','credits'):
            for x in state['records'][kind]:
                if x.get('customer_id')!=cid or (kind=='invoices' and x.get('status')!='issued'): continue
                amount=x['_totals']['total'] if kind=='invoices' else x['amount']
                sign=-1 if kind=='credits' or (kind=='payments' and x.get('direction')!='refund') else 1
                entries.append({'date':x['date'],'reference':x.get('number',''),'kind':kind,'description':x.get('subject') or x.get('source_reference') or x.get('reason') or x.get('notes') or kind.replace('_',' '),'amount':number(money(amount)*sign)})
        entries.sort(key=lambda x:(x['date'],x['reference']));balance=money(0)
        for x in entries: balance+=money(x['amount']);x['running_balance']=number(balance)
        return {'business':state['business'],'customer':customer,'entries':entries,'balance':number(balance),'as_of':state['today']}
