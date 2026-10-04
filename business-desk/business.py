"""Sector presets and linked sales / purchasing workflows.

Transactions, authorisation and audit events are owned by Desk. No network calls.
"""
from datetime import date, timedelta

PROFILES = {
    'garage': {'name': 'Garage & collision repair', 'modules': ['sales', 'pipeline', 'workshop', 'customers', 'insurance', 'money', 'stock', 'team', 'followups', 'reports'],
               'stages': ['Intake', 'Awaiting approval', 'Awaiting parts', 'Body repair', 'Painting', 'Quality check', 'Ready', 'Delivered'],
               'work_label': 'Workshop', 'focus': 'Deliver on time and collect every completed job.'},
    'showroom': {'name': 'Vehicle showroom', 'modules': ['pipeline', 'vehicles', 'sales', 'customers', 'money', 'stock', 'team', 'followups', 'reports'],
                 'stages': ['Preparation', 'Quality check', 'Ready', 'Delivered'], 'work_label': 'Preparation',
                 'focus': 'Follow every enquiry through booking, payment and delivery.'},
    'retail': {'name': 'Retail & trading', 'modules': ['money', 'stock', 'customers', 'sales', 'pipeline', 'team', 'followups', 'reports'],
               'stages': ['Received', 'Picking', 'Ready', 'Delivered'], 'work_label': 'Orders',
               'focus': 'Bill quickly, control stock and recover customer credit.'},
    'service': {'name': 'Service & repair business', 'modules': ['workshop', 'sales', 'pipeline', 'customers', 'money', 'stock', 'team', 'followups', 'reports'],
                'stages': ['Requested', 'Scheduled', 'In progress', 'Quality check', 'Ready', 'Delivered'], 'work_label': 'Service work',
                'focus': 'Keep appointments, approve work and collect payment.'},
}
LEAD_STAGES = ('new', 'contacted', 'test_drive', 'quoted', 'booked', 'delivered', 'won', 'lost')
DELIVERY_CHECKS = ('pdi_complete', 'documents_complete', 'handover_signed')


class BusinessFeatures:
    def configure_profile(self, data, existing=False):
        from domain import Problem
        key = data.get('profile', 'garage')
        if key not in PROFILES:
            raise Problem('Choose a supported business profile.')
        preset = PROFILES[key]
        data['profile'] = key
        data.setdefault('sector', preset['name'])
        data.setdefault('goal', preset['focus'])
        data.setdefault('stages', preset['stages'])
        data.setdefault('modules', preset['modules'])
        allowed = set().union(*(x['modules'] for x in PROFILES.values()))
        if not isinstance(data['modules'], list) or any(x not in allowed for x in data['modules']):
            raise Problem('Choose supported workspace modules.')
        data['modules'] = list(dict.fromkeys(['customers', 'money', 'followups'] + data['modules']))

    def validate_business_record(self, conn, user, bid, kind, data, old):
        from domain import Problem, decimal, money, number, today, checked_date
        records = self.records(conn, bid)
        if kind == 'vehicles':
            if not str(data.get('name', '')).strip() or not str(data.get('vin', '')).strip():
                raise Problem('Vehicle name and chassis / VIN are required.')
            data['vin'] = str(data['vin']).strip().upper()
            if any(x['id'] != (old or {}).get('id') and x.get('vin') == data['vin'] for x in records['vehicles']):
                raise Problem('This chassis / VIN already exists in vehicle inventory.', 409)
            data['sale_price'] = number(money(decimal(data.get('sale_price'), 'Selling price', 0)))
            data['purchase_cost'] = number(money(decimal(data.get('purchase_cost'), 'Purchase cost', 0)))
            data['status'] = data.get('status') or 'available'
            if old and old.get('status') in ('reserved', 'sold'):
                if any(data.get(k) != old.get(k) for k in ('vin', 'status', 'reserved_lead_id', 'invoice_id')):
                    raise Problem('A reserved or sold vehicle is controlled by its sales enquiry.', 409)
            elif data['status'] not in ('available', 'in_transit') or data.get('reserved_lead_id') or data.get('invoice_id'):
                raise Problem('Reserve and sell vehicles from the sales enquiry.')
        if kind == 'leads':
            if not str(data.get('name', '')).strip() or not data.get('customer_id'):
                raise Problem('Enquiry title and customer are required.')
            data.setdefault('stage', 'new')
            if data['stage'] not in LEAD_STAGES:
                raise Problem('Choose a valid enquiry stage.')
            if not old and data['stage'] in ('booked', 'delivered'):
                raise Problem('Use Reserve vehicle and Deliver to record these stages.')
            if old and (data['stage'] != old.get('stage')) and (data['stage'] in ('booked', 'delivered') or old.get('stage') in ('booked', 'delivered')):
                raise Problem('Use the reservation and delivery actions for this enquiry.')
            if old and old.get('stage') in ('booked', 'delivered') and any(data.get(k) != old.get(k) for k in ('customer_id', 'vehicle_id', 'invoice_id')):
                raise Problem('Customer, vehicle and invoice are retained for a reserved sale.')
            if data['stage'] not in ('delivered', 'won', 'lost'):
                data['due_date'] = checked_date(data.get('due_date'), 'Next follow-up date', optional=False)
                if not str(data.get('next_action', '')).strip():
                    raise Problem('Every open enquiry needs a next action.')
            if data['stage'] == 'lost' and not str(data.get('lost_reason', '')).strip():
                raise Problem('Record why the enquiry was lost.')
            data['expected_value'] = number(money(decimal(data.get('expected_value'), 'Expected value', 0)))
            for key in DELIVERY_CHECKS:
                data[key] = bool(data.get(key))
        if kind == 'supplier_bills':
            if old:
                raise Problem('Supplier bills are retained. Add a separate adjustment bill for corrections.')
            if not data.get('supplier_id') or not str(data.get('reference', '')).strip():
                raise Problem('Supplier and original bill reference are required.')
            if any(x.get('supplier_id') == data['supplier_id'] and x.get('reference', '').casefold() == data['reference'].strip().casefold() for x in records[kind]):
                raise Problem('That supplier bill has already been recorded.', 409)
            data['reference'] = data['reference'].strip()
            data['net'] = number(money(decimal(data.get('net'), 'Net purchase amount', 0)))
            data['tax'] = number(money(decimal(data.get('tax'), 'Supplier tax', 0)))
            data['amount'] = number(money(data['net']) + money(data['tax']))
            if data['amount'] <= 0:
                raise Problem('The supplier bill must be greater than zero.')
            data['date'] = checked_date(data.get('date') or today())
            data['due_date'] = checked_date(data.get('due_date'), 'Payment due date', optional=False)
            if data.get('purchase_id'):
                order = self.record(conn, bid, data['purchase_id'], 'purchases')
                if order.get('supplier_id') != data['supplier_id']:
                    raise Problem('The purchase order belongs to another supplier.')
            data['status'] = 'posted'
            data['number'] = self.next_number(conn, bid, 'BILL')
        if kind == 'supplier_payments':
            if old:
                raise Problem('Supplier payments are retained.')
            bill = self.record(conn, bid, data.get('supplier_bill_id'), 'supplier_bills')
            amount = money(decimal(data.get('amount'), 'Payment amount', '.01'))
            paid = sum((money(x['amount']) for x in records[kind] if x.get('supplier_bill_id') == bill['id']), money(0))
            if amount > money(bill['amount']) - paid:
                raise Problem('Payment exceeds the supplier bill balance.')
            reference = str(data.get('reference', '')).strip()
            if reference and any(x.get('reference') == reference and x.get('method') == data.get('method') for x in records[kind]):
                raise Problem('That supplier payment reference is already recorded.', 409)
            data.update(amount=number(amount), supplier_id=bill['supplier_id'], date=checked_date(data.get('date'), optional=False),
                        number=self.next_number(conn, bid, 'SPAY'))

    def sales_action(self, conn, user, bid, record, action, payload, business):
        from domain import Problem, today, now, money
        rid = record['id']
        if action == 'reserve':
            if record.get('stage') in ('lost', 'won', 'delivered', 'booked'):
                raise Problem('This enquiry cannot reserve another vehicle.', 409)
            vehicle = self.record(conn, bid, record.get('vehicle_id'), 'vehicles')
            if vehicle.get('status') != 'available':
                raise Problem('This vehicle is no longer available. Choose another vehicle.', 409)
            vehicle.update(status='reserved', reserved_lead_id=rid)
            self.put(conn, bid, 'vehicles', vehicle, vehicle['id'])
            record.update(stage='booked', reserved_at=now())
        elif action == 'release':
            if record.get('stage') != 'booked':
                raise Problem('Only a reserved enquiry can be released.')
            if not str(payload.get('reason', '')).strip():
                raise Problem('Enter a reason for releasing this reservation.')
            records = self.records(conn, bid)
            if any(x.get('lead_id') == rid and x.get('status') == 'issued' for x in records['invoices']):
                raise Problem('This vehicle has an issued invoice. Review its credit/refund before any return; automatic resale is disabled.', 409)
            vehicle = self.record(conn, bid, record['vehicle_id'], 'vehicles')
            if vehicle.get('reserved_lead_id') != rid:
                raise Problem('This reservation belongs to another enquiry.', 409)
            vehicle.update(status='available', reserved_lead_id='')
            self.put(conn, bid, 'vehicles', vehicle, vehicle['id'])
            record.update(stage='lost', lost_reason=payload['reason'])
        elif action in ('quote', 'invoice'):
            kind = 'quotes' if action == 'quote' else 'invoices'
            self.permitted(user, kind, True)
            records = self.records(conn, bid)
            existing = next((x for x in records[kind] if x.get('lead_id') == rid), None)
            if existing:
                return existing
            vehicle = self.record(conn, bid, record['vehicle_id'], 'vehicles') if record.get('vehicle_id') else None
            if vehicle and action == 'invoice' and (record.get('stage') != 'booked' or vehicle.get('reserved_lead_id') != rid):
                raise Problem('Reserve the available vehicle before creating its invoice.')
            quote = next((x for x in records['quotes'] if x.get('lead_id') == rid and x.get('status') == 'accepted'), None)
            item = {'description': vehicle['name'] + ' · VIN ' + vehicle['vin'] if vehicle else record['name'],
                    'qty': 1, 'unit': 'vehicle' if vehicle else 'service', 'rate': vehicle['sale_price'] if vehicle else record.get('expected_value', 0)}
            result = self.put(conn, bid, kind, {'customer_id': record['customer_id'], 'lead_id': rid,
                'vehicle_id': (vehicle or {}).get('id', ''), 'subject': record['name'], 'status': 'draft', 'date': today(),
                'due_date': (date.fromisoformat(today()) + timedelta(days=int(business.get('payment_terms_days', 7)))).isoformat(),
                'items': quote['items'] if quote else [item], 'vat_mode': (quote or {}).get('vat_mode', 'added' if business.get('vat_registered') else 'none'),
                'vat_rate': (quote or {}).get('vat_rate', business.get('vat_rate', 13)),
                'discount_percent': (quote or {}).get('discount_percent', 0), 'terms': (quote or {}).get('terms', business.get('terms', ''))})
            record[kind[:-1] + '_id'] = result['id']
            self.put(conn, bid, 'leads', record, rid)
            return result
        elif action == 'deliver':
            if record.get('stage') != 'booked' or not record.get('vehicle_id'):
                raise Problem('Reserve this vehicle before delivery.')
            records = self.records(conn, bid)
            invoices = [x for x in records['invoices'] if x.get('lead_id') == rid and x.get('status') == 'issued']
            if not invoices or any(self.invoice_values(records, x)[3] != money(0) for x in invoices):
                raise Problem('Delivery requires an issued invoice with no outstanding amount or unresolved customer credit.')
            if not all(record.get(x) for x in DELIVERY_CHECKS):
                raise Problem('Complete PDI, registration documents, and signed handover before delivery.')
            vehicle = self.record(conn, bid, record['vehicle_id'], 'vehicles')
            if vehicle.get('reserved_lead_id') != rid or vehicle.get('status') != 'sold':
                raise Problem('Vehicle allocation does not match this invoiced sale.', 409)
            record.update(stage='delivered', delivered_at=now(), delivered_by=user['name'])
        else:
            raise Problem('That sales action is not available.')
        return self.put(conn, bid, 'leads', record, rid)

    def issue_inventory(self, conn, bid, invoice):
        """Reserve/consume inventory and invoice in the caller's one transaction."""
        from domain import Problem, decimal, number, today
        records = self.records(conn, bid)
        if invoice.get('job_id') and any(x.get('job_id') == invoice['job_id'] and x['id'] != invoice['id'] and x.get('status') == 'issued' for x in records['invoices']):
            raise Problem('This job already has an issued invoice. Use a credit for corrections or a separate job for additional work.', 409)
        if invoice.get('vehicle_id'):
            vehicle = self.record(conn, bid, invoice['vehicle_id'], 'vehicles')
            lead = self.record(conn, bid, invoice.get('lead_id'), 'leads')
            if lead['customer_id'] != invoice['customer_id'] or lead.get('vehicle_id') != vehicle['id']:
                raise Problem('The vehicle, enquiry and invoice customer must match.')
            if lead.get('stage') != 'booked' or vehicle.get('status') != 'reserved' or vehicle.get('reserved_lead_id') != lead['id']:
                raise Problem('The vehicle is not reserved for this sale.', 409)
            vehicle.update(status='sold', invoice_id=invoice['id'])
            self.put(conn, bid, 'vehicles', vehicle, vehicle['id'])
        needed = {}
        for item in invoice.get('items', []):
            if item.get('item_id'):
                needed[item['item_id']] = needed.get(item['item_id'], decimal(0)) + decimal(item['qty'])
        for item_id, qty in needed.items():
            item = self.record(conn, bid, item_id, 'stock')
            # Parts already consumed on this job are not consumed a second time
            # merely because the invoice includes their selling price.
            if invoice.get('job_id'):
                issued = sum((decimal(x['qty']) * (1 if x.get('kind') == 'issue' else -1)
                              for x in records['movements'] if x.get('job_id') == invoice['job_id'] and x.get('item_id') == item_id and x.get('kind') in ('issue','return')), decimal(0))
                qty = max(decimal(0), qty - issued)
            if not qty: continue
            if qty > self.stock_quantity(records, item_id):
                raise Problem('Insufficient stock for ' + item['name'] + '. Receive stock or adjust the draft invoice.', 409)
            self.put(conn, bid, 'movements', {'item_id': item_id, 'kind': 'issue', 'qty': number(qty),
                'unit_cost': item.get('cost', 0), 'invoice_id': invoice['id'], 'job_id': invoice.get('job_id', ''), 'date': today(),
                'notes': 'Stock sold on invoice ' + invoice['number']})

    def enrich_business_records(self, records):
        from domain import money, number
        for bill in records['supplier_bills']:
            paid = sum((money(x['amount']) for x in records['supplier_payments'] if x.get('supplier_bill_id') == bill['id']), money(0))
            bill.update(_paid=number(paid), _balance=number(money(bill['amount']) - paid))
        for vehicle in records['vehicles']:
            vehicle['_age_days'] = max(0, (date.today() - date.fromisoformat(vehicle['date'])).days) if vehicle.get('date') else 0

    def business_alerts(self, records):
        from domain import today
        alerts = []
        def add(kind, record, title, detail, step, priority=2):
            alerts.append({'key': kind + ':' + record['id'], 'priority': priority, 'title': title,
                           'detail': detail, 'type': kind, 'record_id': record['id'], 'next_action': step})
        for lead in records['leads']:
            if lead.get('stage') not in ('lost', 'won', 'delivered') and lead.get('due_date', '9999') <= today():
                add('leads', lead, 'Sales follow-up due', lead['name'], lead.get('next_action', 'Contact the customer.'), 1)
        for bill in records['supplier_bills']:
            if bill.get('_balance', 0) > 0 and bill.get('due_date', '9999') <= today():
                add('supplier_bills', bill, 'Supplier payment due', bill['reference'], 'Review the bill and record the supplier payment.', 1)
        for vehicle in records['vehicles']:
            if vehicle.get('status') == 'available' and vehicle.get('_age_days', 0) >= 45:
                add('vehicles', vehicle, 'Review ageing vehicle stock', vehicle['name'], 'Review price, enquiries, and carrying cost.')
        return alerts
