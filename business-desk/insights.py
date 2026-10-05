"""Read-only owner portfolio and bounded, validated dashboard configuration.

Each page belongs to one organisation. Currency totals cover that page only;
collections are recorded receipts less refunds, including customer advances.
"""
from collections import defaultdict
from datetime import date
import json

from regional import business_today

PANELS = ('focus', 'collections', 'sector', 'schedule', 'team', 'assistant')
PAGE_SIZE = 24


def validate_dashboard(data):
    from domain import Problem, decimal, money, number
    data['monthly_collection_target'] = number(money(decimal(
        data.get('monthly_collection_target', 0), 'Monthly collection target', 0)))
    panels = data.get('dashboard_panels', list(PANELS))
    if not isinstance(panels, list) or len(panels) > len(PANELS) or any(
            not isinstance(x, str) or x not in PANELS for x in panels):
        raise Problem('Choose supported dashboard panels.')
    data['dashboard_panels'] = list(dict.fromkeys(panels))


def enrich_portfolio(records, day):
    """Linear financial/stock rollups using the same posted-record arithmetic.

    No payroll, job-cost, attachment, audit or user data is returned by this API.
    """
    from domain import calculate, decimal, money, number
    zero = money(0)
    paid, credited, openings, stock, suppliers = [defaultdict(lambda: zero) for _ in range(5)]
    month = zero
    for row in records['payments']:
        amount = money(row['amount']) * (-1 if row.get('direction') == 'refund' else 1)
        if row.get('invoice_id'): paid[row['invoice_id']] += amount
        if row.get('opening_balance_id'): openings[row['opening_balance_id']] += amount
        if day[:7] == row.get('date', '')[:7] and row['date'] <= day: month += amount
    for row in records['allocations']: paid[row['invoice_id']] += money(row['amount'])
    for row in records['credits']: credited[row['invoice_id']] += money(row['amount'])
    for row in records['invoices']:
        total = row.get('totals_snapshot') or calculate(row)
        row['_balance'] = number(money(decimal(total['total']) - credited[row['id']] - paid[row['id']]))
    for row in records['opening_balances']:
        row['_balance'] = number(money(row['amount']) - openings[row['id']])
    for row in records['movements']:
        stock[row['item_id']] += decimal(row['qty']) * (-1 if row.get('kind') == 'issue' else 1)
    for row in records['stock']:
        row['_quantity'] = number(decimal(row.get('opening_qty', 0)) + stock[row['id']])
    for row in records['supplier_payments']: suppliers[row['supplier_bill_id']] += money(row['amount'])
    for row in records['supplier_bills']: row['_balance'] = number(money(row['amount']) - suppliers[row['id']])
    for row in records['vehicles']:
        row['_age_days'] = max(0, (date.fromisoformat(day) - date.fromisoformat(row['date'])).days) if row.get('date') else 0
    return month


class InsightsFeatures:
    def portfolio(self, user, offset=0):
        from domain import KINDS, Problem, money, number, now
        if user['role'] != 'owner':
            raise Problem('Only the owner can view all-business totals.', 403)
        try:
            if isinstance(offset, bool): raise ValueError()
            offset = int(str(offset))
            if not 0 <= offset <= 100000: raise ValueError()
        except (ValueError, TypeError):
            raise Problem('Choose a valid overview page.')
        org = user.get('organization_id', 'local')
        # Both business listing and record selection explicitly use the owner org.
        with self.connect() as conn:
            total = conn.execute('SELECT COUNT(*) FROM businesses WHERE organization_id=?', (org,)).fetchone()[0]
            selected = conn.execute('SELECT * FROM businesses WHERE organization_id=? ORDER BY id LIMIT ? OFFSET ?',
                                    (org, PAGE_SIZE, offset)).fetchall()
            businesses = [{**json.loads(r['data']), 'id': r['id']} for r in selected]
            grouped = {b['id']: {kind: [] for kind in KINDS} for b in businesses}
            if businesses:
                ids = [b['id'] for b in businesses]
                placeholders = ','.join('?' for _ in ids)
                rows = conn.execute('SELECT r.* FROM records r JOIN businesses b ON b.id=r.business_id '
                                    'WHERE b.organization_id=? AND r.archived=0 AND r.business_id IN (' + placeholders + ') '
                                    'ORDER BY r.created_at DESC', (org, *ids))
                for row in rows: grouped[row['business_id']][row['kind']].append(self.unpack(row))
        result, totals = [], {}
        for business in businesses:
            records = grouped[business['id']]
            day = business_today(business)
            collected = enrich_portfolio(records, day)
            owing = [r for r in records['invoices'] if r.get('status') == 'issued' and r['_balance'] > .009]
            owing += [r for r in records['opening_balances'] if r['_balance'] > .009]
            outstanding = sum((money(r['_balance']) for r in owing), money(0))
            overdue = sum((money(r['_balance']) for r in owing if r.get('due_date') and r['due_date'] < day), money(0))
            if business.get('profile') == 'showroom':
                work = sum(r.get('stage') not in ('lost', 'won', 'delivered') for r in records['leads'])
            else:
                final = business['stages'][-1]
                work = sum(r.get('stage') != final for r in records['jobs'])
            # Cash-count review depends on additional expense-source fingerprints.
            # Omit it from the portfolio; the business's full Focus inbox retains it.
            records['cash_closures'] = []
            alerts = self.alerts(business, records)
            currency = business.get('currency', 'NPR')
            bucket = totals.setdefault(currency, {'businesses': 0, 'outstanding': money(0), 'collected_month': money(0)})
            bucket['businesses'] += 1
            bucket['outstanding'] += outstanding
            bucket['collected_month'] += collected
            result.append({
                'id': business['id'], 'name': business.get('trading_name') or business['name'],
                'legal_name': business['name'], 'profile': business.get('profile', 'garage'),
                'currency': currency, 'country': business.get('country', 'NP'), 'today': day,
                'brand_hex': business.get('brand_hex', ''), 'goal': business.get('goal', ''),
                'monthly_collection_target': business.get('monthly_collection_target', 0),
                'customers': len(records['customers']), 'open_work': work,
                'outstanding': number(outstanding), 'overdue': number(overdue),
                'collected_month': number(collected), 'actions_due': len(alerts),
                'next_actions': [{'title': a['title'], 'type': a['type'], 'record_id': a['record_id']} for a in alerts[:3]],
            })
        return {'businesses': result, 'total': total, 'offset': offset, 'limit': PAGE_SIZE,
                'generated_at': now(), 'totals_scope': 'visible_businesses',
                'totals': {currency: {**values, 'outstanding': number(values['outstanding']),
                                      'collected_month': number(values['collected_month'])} for currency, values in totals.items()}}
