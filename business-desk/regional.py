"""Country configuration, customer preferences and retained line returns.

This is a domestic operational ledger, not a tax-filing or IRP integration.
"""
import re
from datetime import datetime, timedelta, timezone, date

INDIA_STATES = dict(x.split(':', 1) for x in (
    '01:Jammu and Kashmir|02:Himachal Pradesh|03:Punjab|04:Chandigarh|05:Uttarakhand|06:Haryana|07:Delhi|08:Rajasthan|09:Uttar Pradesh|10:Bihar|11:Sikkim|12:Arunachal Pradesh|13:Nagaland|14:Manipur|15:Mizoram|16:Tripura|17:Meghalaya|18:Assam|19:West Bengal|20:Jharkhand|21:Odisha|22:Chhattisgarh|23:Madhya Pradesh|24:Gujarat|26:Dadra and Nagar Haveli and Daman and Diu|27:Maharashtra|29:Karnataka|30:Goa|31:Lakshadweep|32:Kerala|33:Tamil Nadu|34:Puducherry|35:Andaman and Nicobar Islands|36:Telangana|37:Andhra Pradesh|38:Ladakh'
).split('|'))
UTGST_STATES = {'04', '26', '31', '35', '38'}
CHECKLISTS = {
    'garage': ['Record complaint and existing damage', 'Confirm estimate approval', 'Check parts and completed work', 'Complete final quality check', 'Explain work and handover'],
    'showroom': ['Complete pre-delivery inspection', 'Check registration and ownership documents', 'Confirm collection', 'Record signed handover'],
    'retail': ['Confirm items and quantities', 'Check packing or collection', 'Record delivery'],
    'service': ['Confirm request and appointment', 'Record diagnosis and approval', 'Complete service and test', 'Confirm customer handover'],
}


def business_today(business=None):
    offset = 330 if (business or {}).get('country') == 'IN' else 345
    return datetime.now(timezone(timedelta(minutes=offset))).date().isoformat()


def financial_year(day):
    value = date.fromisoformat(day)
    start = value.year if value.month >= 4 else value.year - 1
    return f'{start % 100:02}{(start + 1) % 100:02}'


def checked_gstin(value, state=''):
    from domain import Problem
    value = str(value or '').strip().upper()
    if value and (not re.fullmatch(r'[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]', value) or value[:2] not in INDIA_STATES):
        raise Problem('Enter a GSTIN in the 15-character format with a supported state code.')
    if value and state and value[:2] != state:
        raise Problem('GSTIN and registration state must match.')
    return value


class RegionalFeatures:
    def configure_region(self, data):
        from domain import Problem
        country = data.setdefault('country', 'NP')
        if country not in ('NP', 'IN'):
            raise Problem('Choose Nepal or India.')
        data['currency'] = 'INR' if country == 'IN' else 'NPR'
        data['timezone'] = 'Asia/Kolkata' if country == 'IN' else 'Asia/Kathmandu'
        data.setdefault('brand_color', 'indigo')
        if data['brand_color'] not in ('indigo', 'blue', 'emerald', 'orange'):
            raise Problem('Choose a supported brand colour.')
        data['workspace_name'] = str(data.get('workspace_name') or data['name']).strip()[:70]
        data['speciality'] = str(data.get('speciality', '')).strip()[:100]
        data.setdefault('job_checklist', CHECKLISTS[data['profile']])
        if not isinstance(data['job_checklist'], list) or len(data['job_checklist']) > 30:
            raise Problem('Use at most 30 default checklist items.')
        data['job_checklist'] = list(dict.fromkeys(str(x).strip()[:200] for x in data['job_checklist'] if str(x).strip()))
        definitions = data.setdefault('custom_fields', [])
        if not isinstance(definitions, list) or len(definitions) > 20:
            raise Problem('Use at most 20 custom fields.')
        seen = set()
        for field in definitions:
            if not isinstance(field, dict) or not re.fullmatch(r'[a-z][a-z0-9_]{0,30}', str(field.get('key', ''))):
                raise Problem('Custom field keys must start with a letter and use lowercase letters, digits or underscores.')
            if field.get('kind') not in ('customers', 'jobs', 'leads', 'assets') or field.get('type') not in ('text', 'number', 'date'):
                raise Problem('Choose a supported custom field area and type.')
            if not str(field.get('label', '')).strip() or len(str(field['label'])) > 80:
                raise Problem('Custom fields need a short label.')
            pair = (field['kind'], field['key'])
            if pair in seen: raise Problem('Custom field keys must be unique within their area.')
            seen.add(pair)
        if country == 'IN':
            if data.get('state_code') not in INDIA_STATES: raise Problem('Choose the Indian registration state.')
            data.setdefault('gst_registration', 'unregistered')
            if data['gst_registration'] not in ('regular', 'composition', 'unregistered'):
                raise Problem('Choose a supported GST registration type.')
            data['gstin'] = checked_gstin(data.get('gstin'), data['state_code'])
            if data['gst_registration'] != 'unregistered' and not data['gstin']:
                raise Problem('GST registered businesses need a GSTIN.')
            data['vat_registered'] = data['gst_registration'] == 'regular'
            data.setdefault('vat_rate', 0)
            data['einvoice_required'] = bool(data.get('einvoice_required'))

    def validate_personalisation(self, conn, bid, kind, data, old):
        from domain import Problem, decimal, number, checked_date, identifier
        business = self.business(conn, bid)
        if kind == 'customers':
            tags = data.get('tags', [])
            if isinstance(tags, str): tags = tags.split(',')
            if not isinstance(tags, list) or len(tags) > 12: raise Problem('Use at most 12 customer tags.')
            data['tags'] = list(dict.fromkeys(str(x).strip()[:35] for x in tags if str(x).strip()))
            for key, maximum in [('discount_percent', 100), ('payment_terms_days', 365), ('reminder_days', 365)]:
                data[key] = number(decimal(data.get(key, business.get('payment_terms_days', 7) if key == 'payment_terms_days' else 0), key.replace('_', ' '), 0, maximum))
            data['marketing_opt_in'] = bool(data.get('marketing_opt_in', False))
            if business.get('country') == 'IN':
                if data.get('state_code') and data['state_code'] not in INDIA_STATES: raise Problem('Choose a valid customer state.')
                data['gstin'] = checked_gstin(data.get('gstin'), data.get('state_code', ''))
        if kind in ('stock', 'services'):
            if data.get('hsn_sac') and not re.fullmatch(r'\d{4}|\d{6}|\d{8}', str(data['hsn_sac'])):
                raise Problem('HSN / SAC must contain 4, 6 or 8 digits.')
            for key in ('tax_rate', 'cess_rate'):
                if key in data: data[key] = number(decimal(data[key], key.replace('_', ' '), 0, 100))
            if kind == 'stock':
                data['barcode'] = str(data.get('barcode', '')).strip()[:80]
                if data['barcode'] and any(x['id'] != (old or {}).get('id') and x.get('barcode') == data['barcode'] for x in self.records(conn, bid)['stock']):
                    raise Problem('That barcode already belongs to another stock item.', 409)
        if kind == 'jobs' and not old:
            data.setdefault('stage', business.get('stages', ['Intake'])[0])
            if not data.get('tasks'):
                data['tasks'] = [{'id': identifier(), 'name': x, 'done': False} for x in business.get('job_checklist', CHECKLISTS[business.get('profile', 'garage')])]
        if kind in ('customers', 'jobs', 'leads', 'assets'):
            values = data.get('custom_fields', {})
            if not isinstance(values, dict) or len(values) > 20: raise Problem('Custom values must be a field map.')
            for field in business.get('custom_fields', []):
                if field['kind'] != kind: continue
                value = values.get(field['key'], '')
                if value == '': continue
                if field['type'] == 'number': value = number(decimal(value, field['label']))
                elif field['type'] == 'date': value = checked_date(value, field['label'])
                else: value = str(value)[:2000]
                values[field['key']] = value
            data['custom_fields'] = values
        if kind in ('quotes', 'invoices'):
            self.prepare_regional_document(conn, bid, data)

    def prepare_regional_document(self, conn, bid, data, issuing=False):
        from domain import Problem, calculate
        b = self.business(conn, bid)
        data['country'] = b.get('country', 'NP')
        data['currency'] = b.get('currency', 'NPR')
        if data['country'] != 'IN': return
        customer = self.record(conn, bid, data.get('customer_id'), 'customers')
        data['seller_state'] = b['state_code']
        data['place_of_supply'] = data.get('place_of_supply') or customer.get('state_code') or b['state_code']
        if data['place_of_supply'] not in INDIA_STATES: raise Problem('Choose a supported domestic place of supply.')
        data['gst_registration'] = b['gst_registration']
        if b['gst_registration'] != 'regular' and data.get('vat_mode', 'added') != 'none':
            raise Problem('Unregistered and composition businesses cannot collect GST. Select no tax.')
        if issuing:
            if b.get('einvoice_required'):
                raise Problem('This business requires e-invoicing. IRP integration is not configured; use your approved invoicing system.')
            if b['gst_registration'] != 'unregistered':
                if not b.get('address') or not customer.get('address'):
                    raise Problem('Enter business and customer addresses before issuing this GST document.')
                for line in data.get('items', []):
                    if not re.fullmatch(r'\d{4}|\d{6}|\d{8}', str(line.get('hsn_sac', ''))):
                        raise Problem('Enter the reviewed HSN / SAC on every GST invoice line.')
                if b['gst_registration'] == 'regular' and data.get('vat_mode') == 'none' and any(float(x.get('tax_rate', data.get('vat_rate', 0)) or 0) > 0 or float(x.get('cess_rate', 0) or 0) > 0 for x in data.get('items', [])):
                    raise Problem('A no-tax bill cannot contain taxable GST rates. Review the line tax settings.')
            if len(str(data.get('customer_gstin', ''))) > 0: checked_gstin(data['customer_gstin'])
        data['document_title'] = ('TAX INVOICE' if data.get('vat_mode') != 'none' else 'BILL OF SUPPLY') if b['gst_registration'] != 'unregistered' else 'INVOICE'
        data['financial_year'] = financial_year(data.get('date') or business_today(b))

    def line_return(self, conn, user, bid, invoice, payload):
        from domain import Problem, decimal, money, number, identifier, now
        self.permitted(user, 'credits', True)
        if invoice.get('status') != 'issued': raise Problem('Returns require an issued invoice.')
        if invoice.get('vehicle_id'): raise Problem('Vehicle ownership returns require a separate reviewed showroom workflow.')
        if not str(payload.get('reason', '')).strip(): raise Problem('Record the reason for the return or service credit.')
        requests = payload.get('items', [])
        if not isinstance(requests, list) or not requests or len(requests) > 250: raise Problem('Choose at least one invoice line to return.')
        records = self.records(conn, bid)
        credits = [x for x in records['credits'] if x.get('invoice_id') == invoice['id']]
        if any(not x.get('return_lines') for x in credits): raise Problem('This invoice already has an amount-only credit. Reconcile it before making a line return.')
        source = invoice['totals_snapshot']['lines']
        returned, net, tax, components, seen = [], money(0), money(0), {}, set()
        cid = identifier()
        for request in requests:
            index = request.get('line_index')
            if not isinstance(index, int) or index < 0 or index >= len(source) or index in seen: raise Problem('Choose each original invoice line once.')
            seen.add(index)
            line = source[index]
            prior = sum((decimal(x['qty']) for credit in credits for x in credit.get('return_lines', []) if x['line_index'] == index), decimal(0))
            qty = decimal(request.get('qty'), 'Return quantity', '.0001')
            original = decimal(line['qty'])
            if qty + prior > original: raise Problem('The return exceeds the remaining quantity on ' + line['description'] + '.')
            allocation = lambda amount: money(decimal(amount) * (prior + qty) / original) - money(decimal(amount) * prior / original)
            line_net, line_tax = allocation(line['net']), allocation(line['tax'])
            split = {key: number(allocation(amount)) for key, amount in line.get('tax_components', {}).items()}
            # Allocate any cent residual to the last original component.
            if split:
                last = list(split)[-1]
                split[last] = number(money(split[last]) + line_tax - sum((money(x) for x in split.values()), money(0)))
            restock = bool(request.get('restock'))
            if restock:
                self.permitted(user, 'movements', True)
                if not line.get('item_id') or invoice.get('job_id'): raise Problem('Only directly sold stock can be restocked here. Use the job parts return workflow for workshop parts.')
                item = self.record(conn, bid, line['item_id'], 'stock')
                self.put(conn, bid, 'movements', {'item_id': item['id'], 'kind': 'return', 'qty': number(qty), 'unit_cost': line.get('unit_cost', item['cost']), 'date': business_today(self.business(conn, bid)), 'invoice_id': invoice['id'], 'credit_id': cid, 'notes': str(payload['reason'])[:1000]})
            returned.append({'line_index': index, 'description': line['description'], 'hsn_sac': line.get('hsn_sac', ''), 'tax_rate': line.get('tax_rate', 0), 'qty': number(qty), 'unit': line.get('unit', ''), 'net': number(line_net), 'tax': number(line_tax), 'tax_components': split, 'restocked': restock})
            net += line_net; tax += line_tax
            for key, amount in split.items(): components[key] = number(money(components.get(key, 0)) + money(amount))
        if net + tax <= 0: raise Problem('The credited amount must be greater than zero.')
        record = self.put(conn, bid, 'credits', {'invoice_id': invoice['id'], 'customer_id': invoice['customer_id'], 'amount': number(net + tax), 'net': number(net), 'tax': number(tax), 'return_lines': returned, 'tax_components': components, 'country': invoice.get('country', 'NP'), 'currency': invoice.get('currency', 'NPR'), 'seller_snapshot': invoice.get('seller_snapshot'), 'customer_snapshot': invoice.get('customer_snapshot'), 'reason': str(payload['reason'])[:2000], 'date': business_today(self.business(conn, bid)), 'number': self.next_number(conn, bid, 'CRN'), 'created_by': user['name']}, cid)
        # Change the invoice version as well, so two reviewers cannot return stale quantities.
        invoice['last_return_at'] = now()
        self.put(conn, bid, 'invoices', invoice, invoice['id'])
        return record
