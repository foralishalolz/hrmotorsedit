"""Owner-only operating analytics. Decimal arithmetic, explicit cost basis.

This is a recorded operating result before income tax/depreciation, not a
statutory ledger. Labour line estimates are excluded when payroll is accrued.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo
import csv
import io

from regional import business_today

EXPENSE_TREATMENTS = ('Operating expense', 'Inventory purchase', 'Payroll payout',
                      'Staff advance', 'Capital asset', 'Tax payment', 'Owner withdrawal')


def expense_treatment(row):
    if row.get('category') == 'Staff advance': return 'Staff advance'
    return row.get('expense_treatment') or 'Operating expense'


def record_day(row, field='date', zone='Asia/Kathmandu'):
    value = row.get(field) or (row.get('created_at', '') if field == 'date' else '')
    if not value: return ''
    if len(value) == 10: return value
    try: return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(ZoneInfo(zone)).date().isoformat()
    except (ValueError, TypeError): return ''


def dates(start, end):
    day = start
    while day <= end:
        yield day.isoformat()
        day += timedelta(days=1)


def period_dates(start, end, today):
    from domain import Problem
    try:
        first = date.fromisoformat(start or today[:8] + '01')
        last = date.fromisoformat(end or today)
        if first > last or last > date.fromisoformat(today) or (last-first).days > 365:
            raise ValueError()
    except (ValueError, TypeError):
        raise Problem('Choose AD dates in order, no future end date, and at most 366 days.')
    return first, last


def split_credit(credit, total):
    """Use original lines; preserve the exact credit net with a final residual."""
    from domain import decimal, money
    lines = total['lines']
    returned = credit.get('return_lines') or []
    weights = [Decimal(0) for _ in lines]
    for item in returned:
        index = item.get('line_index', -1)
        if isinstance(index, int) and 0 <= index < len(lines):
            line = lines[index]
            weights[index] += decimal(line['net']) * decimal(item['qty']) / decimal(line['qty'])
    if not returned: weights = [decimal(line['net']) for line in lines]
    denominator = sum(weights, Decimal(0))
    output = [Decimal(0) for _ in lines]
    if denominator:
        total_credit = money(credit.get('net', 0)); cumulative = Decimal(0); distributed = Decimal(0)
        indices = [i for i, weight in enumerate(weights) if weight]
        for index in indices:
            cumulative += weights[index]
            target = money(total_credit * cumulative / denominator)
            output[index] = target-distributed; distributed = target
    return output


def analyse(business, records, first, last):
    from domain import calculate, decimal, money, number, STAGES
    start, end = first.isoformat(), last.isoformat()
    zone = 'Asia/Kolkata' if business.get('country') == 'IN' else 'Asia/Kathmandu'
    days = (last-first).days+1
    previous_end = first-timedelta(days=1)
    previous_start = previous_end-timedelta(days=days-1)
    all_start = previous_start.isoformat()
    def selected(value, a=start, b=end): return bool(value and a <= value <= b)
    def m(value=0): return money(decimal(value or 0))
    def metric(): return {'sales':Decimal(0), 'direct_cost':Decimal(0), 'expenses':Decimal(0),
                          'payroll':Decimal(0), 'commissions':Decimal(0), 'receipts':Decimal(0),
                          'outflow':Decimal(0), 'tax':Decimal(0), 'bills':0}
    current, previous = metric(), metric()
    daily = {day:metric() for day in dates(first, last)}
    def post(day, key, value):
        target = current if selected(day) else previous if selected(day, all_start, previous_end.isoformat()) else None
        if target is not None: target[key] += value
        if day in daily: daily[day][key] += value
    customers = {x['id']:x for x in records['customers']}
    client = defaultdict(lambda:{'sales':Decimal(0),'cost':Decimal(0),'bills':0,'lifetime_bills':0,
                                'first_bill':'','last_bill':'','outstanding':Decimal(0),'overdue':Decimal(0)})
    services = {}
    def service_key(line): return line.get('item_id') or line.get('service_id') or 'text:'+line.get('description','').strip().lower()[:120]
    def service(line):
        key = service_key(line)
        return services.setdefault(key, {'name':line.get('description') or 'Unnamed line', 'sales':Decimal(0),
            'direct_cost':Decimal(0),'units':Decimal(0),'bills':set(),'missing_cost':False,'category':line.get('category','Service')})
    issued = [x for x in records['invoices'] if x.get('status') == 'issued' and record_day(x, zone=zone) <= end]
    invoices = {x['id']:x for x in issued}
    totals = {x['id']:x.get('totals_snapshot') or calculate(x) for x in issued}
    paid, credited = defaultdict(Decimal), defaultdict(Decimal)
    missing_lines, manual_credits, labour_lines = [], 0, 0
    job_revenue, job_cost, job_hours = defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal)
    billed_jobs = {x.get('job_id') for x in issued if x.get('job_id')}
    weekdays = {str(i):{'sales':Decimal(0),'bills':0} for i in range(7)}
    for invoice in issued:
        day = record_day(invoice, zone=zone); total = totals[invoice['id']]; cid=invoice.get('customer_id','')
        c = client[cid];c['lifetime_bills']+=1
        c['first_bill']=min(c['first_bill'] or day,day);c['last_bill']=max(c['last_bill'],day)
        job_revenue[invoice.get('job_id','')] += m(total['net'])
        post(day,'sales',m(total['net']));post(day,'tax',m(total['tax']));post(day,'bills',1)
        if selected(day):
            c['sales']+=m(total['net']);c['bills']+=1
            weekday=weekdays[str(date.fromisoformat(day).weekday())];weekday['sales']+=m(total['net']);weekday['bills']+=1
        for index, line in enumerate(total['lines']):
            # Payroll is the business's wage cost; Labour line estimates are for job contribution only.
            cost = Decimal(0) if line.get('category') == 'Labour' else m(line.get('cost',0))
            post(day,'direct_cost',cost)
            if selected(day):
                if line.get('category')=='Labour' and m(line['net'])>0:labour_lines+=1
                c['cost']+=cost;s=service(line);s['sales']+=m(line['net']);s['direct_cost']+=cost
                s['units']+=decimal(line['qty']);s['bills'].add(invoice['id'])
                if line.get('category') != 'Labour' and m(line['net']) > 0 and not cost:
                    s['missing_cost']=True
                    missing_lines.append({'invoice_id':invoice['id'],'number':invoice.get('number',''),'description':line.get('description','')})
    for credit in records['credits']:
        day=record_day(credit, zone=zone);invoice=invoices.get(credit.get('invoice_id'))
        if day > end or not invoice: continue
        credited[invoice['id']]+=m(credit['amount']);job_revenue[invoice.get('job_id','')]-=m(credit.get('net',0))
        post(day,'sales',-m(credit.get('net',0)));post(day,'tax',-m(credit.get('tax',0)))
        if not selected(day,all_start,end): continue
        total=totals[invoice['id']];shares=split_credit(credit,total);restock=defaultdict(Decimal)
        for line in credit.get('return_lines') or []:
            if line.get('restock'):restock[line['line_index']]+=decimal(line['qty'])
        if selected(day) and not credit.get('return_lines'):manual_credits+=1
        for index, line in enumerate(total['lines']):
            reversed_cost=m(restock[index]*decimal(line.get('unit_cost',0))) if line.get('category')!='Labour' else Decimal(0)
            post(day,'direct_cost',-reversed_cost)
            if selected(day):
                c=client[invoice.get('customer_id','')];c['sales']-=shares[index];c['cost']-=reversed_cost
                s=service(line);s['sales']-=shares[index];s['direct_cost']-=reversed_cost
    for payment in records['payments']:
        day=record_day(payment,zone=zone);amount=m(payment['amount'])*(-1 if payment.get('direction')=='refund' else 1)
        post(day,'receipts',amount)
        if day <= end:paid[payment.get('invoice_id') or payment.get('opening_balance_id') or '']+=amount
    for allocation in records['allocations']:
        if record_day(allocation,zone=zone)<=end:paid[allocation['invoice_id']]+=m(allocation['amount'])
    ageing=[{'name':name,'amount':Decimal(0),'count':0} for name in ['Not due / no date','1–30 days','31–60 days','61–90 days','Over 90 days']]
    for row in issued+[x for x in records['opening_balances'] if record_day(x,zone=zone)<=end]:
        balance=(m(totals[row['id']]['total'])-credited[row['id']] if row['id'] in totals else m(row['amount']))-paid[row['id']]
        if balance <= 0: continue
        c=client[row.get('customer_id','')];c['outstanding']+=balance
        late=(last-date.fromisoformat(row['due_date'])).days if row.get('due_date') else 0
        bucket=ageing[0 if late<=0 else 1 if late<=30 else 2 if late<=60 else 3 if late<=90 else 4]
        bucket['amount']+=balance;bucket['count']+=1
        if late>0:c['overdue']+=balance
    expenses=defaultdict(Decimal);excluded=defaultdict(Decimal);ambiguous=[]
    for expense in records['expenses']:
        day=record_day(expense,zone=zone);amount=m(expense['amount']);post(day,'outflow',amount)
        treatment=expense_treatment(expense)
        if treatment=='Operating expense':
            post(day,'expenses',amount)
            if selected(day):expenses[expense.get('category','Other')]+=amount
            if day<=end:job_cost[expense.get('job_id','')]+=amount
            if selected(day) and expense.get('category') in ('Parts','Tools') and not expense.get('expense_treatment'):
                ambiguous.append({'id':expense['id'],'name':expense['name']})
        elif selected(day):excluded[treatment]+=amount
    payroll_commissions=set()
    for payroll in records['payroll']:
        if payroll.get('status') not in ('approved','paid'):continue
        payroll_commissions.update(payroll.get('commission_ids',[]))
        a,b=date.fromisoformat(payroll['start_date']),date.fromisoformat(payroll['end_date'])
        full=(b-a).days+1;amount=m(payroll.get('total_cost',0))
        # Cumulative cent boundaries preserve total wages without a negative last-day residual.
        for day in dates(max(a,previous_start),min(b,last)):
            index=(date.fromisoformat(day)-a).days
            share=m(amount*Decimal(index+1)/full)-m(amount*Decimal(index)/full)
            post(day,'payroll',share)
        if payroll.get('status')=='paid':post(record_day(payroll,'paid_at',zone),'outflow',m(payroll.get('total_net',0)))
    for commission in records['commissions']:
        day=record_day(commission,zone=zone)
        if commission.get('status') in ('approved','paid'):
            if commission['id'] not in payroll_commissions:post(day,'commissions',m(commission['amount']))
            if day<=end:job_cost[commission.get('job_id','')]+=m(commission['amount'])
        if commission.get('status')=='paid' and not commission.get('payroll_id'):
            post(record_day(commission,'paid_at',zone),'outflow',m(commission['amount']))
    for payment in records['supplier_payments']:post(record_day(payment,zone=zone),'outflow',m(payment['amount']))
    def finish_metric(value):
        result={key:number(m(val)) if isinstance(val,Decimal) else val for key,val in value.items()}
        result['gross_contribution']=number(m(value['sales']-value['direct_cost']))
        result['operating_result']=number(m(value['sales']-value['direct_cost']-value['expenses']-value['payroll']-value['commissions']))
        result['cash_movement']=number(m(value['receipts']-value['outflow']))
        result['margin_percent']=number(m(100*Decimal(str(result['operating_result']))/value['sales'])) if value['sales']>0 else None
        return result
    # Whole-job costs are a separate view. They are never added again to the period result.
    for movement in records['movements']:
        if record_day(movement,zone=zone)<=end and movement.get('kind') in ('issue','return'):
            job_cost[movement.get('job_id','')]+=m(decimal(movement['qty'])*decimal(movement.get('unit_cost',0))*(1 if movement['kind']=='issue' else -1))
    time_cost=defaultdict(Decimal);team_hours=defaultdict(Decimal)
    for entry in records['time_entries']:
        day=record_day(entry,'end_at',zone)
        if entry.get('end_at') and day<=end:
            hours=decimal(entry.get('hours',0));time_cost[entry.get('job_id','')]+=hours*decimal(entry.get('hourly_cost_snapshot',0));job_hours[entry.get('job_id','')]+=hours
            if selected(day):team_hours[entry.get('employee_id','')]+=hours
    final=(business.get('stages') or STAGES)[-1];job_rows=[];team=defaultdict(lambda:{'assigned':0,'completed':0,'overdue':0,'reviewed':0,'on_time':0,'reworks':0,'rating_total':0,'rated':0})
    stages=defaultdict(int)
    for job in records['jobs']:
        if record_day(job,zone=zone)>end:continue
        jid=job['id'];cost=job_cost[jid]+(decimal(job.get('labor_cost',0)) or time_cost[jid])+decimal(job.get('additional_material_cost',0))+decimal(job.get('subcontract_cost',0))
        complete=job.get('stage')==final;completion=job.get('completion_date','')
        if not complete:stages[job.get('stage','Intake')]+=1
        if jid in billed_jobs or cost:
            job_rows.append({'id':jid,'name':job['name'],'revenue':number(m(job_revenue[jid])),'cost':number(m(cost)),
                'contribution':number(m(job_revenue[jid]-cost)),'billed':jid in billed_jobs,'provisional':not job.get('costs_final',False),
                'hours':number(m(job_hours[jid])),'complete':complete})
        for eid in job.get('employee_ids',[]):
            t=team[eid]
            if selected(record_day(job,zone=zone)) or selected(completion) or not complete:
                t['assigned']+=1;t['completed']+=int(complete and (not completion or completion<=end))
                t['overdue']+=int(not complete and bool(job.get('due_date')) and job['due_date']<end)
                if complete and selected(completion) and job.get('due_date'):
                    t['reviewed']+=1;t['on_time']+=int(completion<=job['due_date'])
                t['reworks']+=int(job.get('rework_count',0))
                if job.get('quality_rating'):t['rated']+=1;t['rating_total']+=int(job['quality_rating'])
    attendance=defaultdict(lambda:defaultdict(int))
    for row in records['attendance']:
        if selected(record_day(row,zone=zone)):attendance[row['employee_id']][row.get('status','pending')]+=1
    team_rows=[]
    for employee in records['employees']:
        eid=employee['id'];t=team[eid];a=attendance[eid]
        team_rows.append({'id':eid,'name':employee['name'],'role':employee.get('role',''),'active':employee.get('active',True),**t,
            'hours':number(m(team_hours[eid])),'attendance':dict(a),'on_time_percent':round(t['on_time']*100/t['reviewed'],1) if t['reviewed'] else None,
            'quality_rating':round(t['rating_total']/t['rated'],1) if t['rated'] else None,
            'signal':'Needs follow-up' if t['overdue'] else 'On track' if t['reviewed']>=3 else 'More records needed'})
    client_rows=[]
    for cid,c in client.items():
        customer=customers.get(cid,{});last_bill=c['last_bill'];inactive=bool(last_bill and (last-date.fromisoformat(last_bill)).days>=90)
        if not (c['bills'] or c['sales'] or c['outstanding'] or inactive):continue
        client_rows.append({'id':cid,'name':customer.get('name','Unlinked customer'),**{k:number(m(v)) if isinstance(v,Decimal) else v for k,v in c.items()},
            'contribution':number(m(c['sales']-c['cost'])),'segment':'No billed history' if not c['first_bill'] else 'Inactive 90 days' if inactive else 'Returning' if c['first_bill']<start else 'New',
            'risk':'Overdue' if c['overdue'] else 'Open balance' if c['outstanding'] else 'Clear'})
    active_clients=[c for c in client_rows if c['bills']]
    returning=sum(c['first_bill']<start for c in active_clients)
    service_rows=[{**s,'sales':number(m(s['sales'])),'direct_cost':number(m(s['direct_cost'])),
                   'contribution':number(m(s['sales']-s['direct_cost'])),'units':number(s['units']),'bills':len(s['bills'])} for s in services.values()]
    decided=[q for q in records['quotes'] if selected(record_day(q,zone=zone)) and q.get('status') in ('accepted','declined')]
    sources=defaultdict(lambda:{'opened':0,'won':0,'lost':0})
    for lead in records['leads']:
        if selected(record_day(lead,zone=zone)):
            s=sources[lead.get('source') or 'Unrecorded'];s['opened']+=1;s['won']+=int(lead.get('stage') in ('won','delivered'));s['lost']+=int(lead.get('stage')=='lost')
    net=finish_metric(current);before=finish_metric(previous)
    overdue=sum((c['overdue'] for c in client.values()),Decimal(0));outstanding=sum((c['outstanding'] for c in client.values()),Decimal(0))
    quality={'missing_cost_lines':len(missing_lines),'missing_cost_sources':missing_lines[:20],
        'unclassified_expenses':len(ambiguous),'expense_sources':ambiguous[:20],'manual_credits':manual_credits,
        'provisional_jobs':sum(j['provisional'] for j in job_rows if j['billed']),
        'draft_payroll':sum(p.get('status')=='draft' and p['start_date']<=end and p['end_date']>=start for p in records['payroll']),
        'labour_without_payroll':labour_lines if current['payroll']==0 else 0}
    quality['result_status']='Costs need review' if any(quality[k] for k in ('missing_cost_lines','unclassified_expenses','draft_payroll','labour_without_payroll')) else 'Recorded estimate'
    recommendations=[]
    def advice(code,title,evidence,action,category,kind='',rid='',severity='review'):
        recommendations.append({'id':code,'title':title,'evidence':evidence,'action':action,'category':category,'kind':kind,'record_id':rid,'severity':severity})
    if missing_lines:advice('costs','Complete costing before comparing profits',f"{len(missing_lines)} non-Labour billed lines have no recorded cost.",'Check catalogue costs, capture them on future bills and record reviewed adjustments for missing costs.','work','invoices',missing_lines[0]['invoice_id'],'high')
    if ambiguous:advice('classify','Review expense classification',f"{len(ambiguous)} Parts/Tools expenses have no explicit profit treatment.",'Separate stock purchases and capital assets from operating expenses to avoid counting costs twice.','collections','expenses',ambiguous[0]['id'],'high')
    if quality['labour_without_payroll']:advice('wages','Record the wage cost behind billed labour',f"{labour_lines} Labour lines were billed but no approved payroll cost overlaps this period.",'Prepare and review payroll or record the actual operating wage expense. Check for duplicate payouts before relying on this result.','team',severity='high')
    if overdue>0:
        worst=max(client_rows,key=lambda c:c['overdue']);advice('collect','Prioritise overdue collections',f"{business.get('currency','NPR')} {number(m(overdue)):,.2f} is overdue at the selected end date.",'Agree a payment date with the client and record the collection against its source balance.','collections','customers',worst['id'],'high')
    losing=sorted([j for j in job_rows if j['billed'] and j['contribution']<0],key=lambda j:j['contribution'])
    if losing:advice('job-loss','Review the lowest job contribution',f"{losing[0]['name']}: {business.get('currency','NPR')} {losing[0]['contribution']:,.2f}; {'provisional' if losing[0]['provisional'] else 'costs checked'}.",'Check scope changes, material issues, labour time and the agreed price before quoting similar work.','work','jobs',losing[0]['id'],'high')
    if net['operating_result']<0 and net['bills']>=3:advice('result','Review the recorded operating loss',f"Selected-period result: {business.get('currency','NPR')} {net['operating_result']:,.2f}.",'Review cost completeness and the largest operating expense categories before changing prices or staffing.','collections',severity='high')
    biggest=max(active_clients,key=lambda c:c['sales'],default=None)
    concentration=round(max(0,biggest['sales'])/net['sales']*100,1) if biggest and net['sales']>0 else None
    if concentration and concentration>=40 and len(active_clients)>=5:advice('concentration','Reduce reliance on one client',f"{biggest['name']} contributes {concentration}% of net sales across {len(active_clients)} billed clients.",'Develop other client relationships while maintaining this account and monitoring its payment terms.','clients','customers',biggest['id'])
    inactive=[c for c in client_rows if c['segment']=='Inactive 90 days']
    if inactive:advice('inactive','Review clients who have not returned',f"{len(inactive)} previously billed clients have no bill in 90 days.",'Check whether another service is due and use each client’s agreed contact preferences.','clients','customers',inactive[0]['id'])
    reviewed=sum(t['reviewed'] for t in team_rows)
    if any(t['overdue'] for t in team_rows):advice('delivery','Resolve overdue assigned work',f"{sum(t['overdue'] for t in team_rows)} assignment instances are overdue; shared jobs can appear for more than one person.",'Review blockers, parts availability and delivery promises with the assigned team.','work')
    if net['bills']>=7 and days>=14:
        peak=max(weekdays,key=lambda key:weekdays[key]['sales']);advice('capacity','Plan around the busiest recorded day',f"{['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'][int(peak)]} has the highest net billed sales across {net['bills']} bills.",'Compare this with appointments and staffing before shifting capacity; a short sample can change.','team')
    if not recommendations:advice('baseline','Build a reliable baseline',f"This period contains {net['bills']} issued bills and {len(active_clients)} billed clients.",'Keep costs, delivery reviews, attendance and client follow-up dates current, then compare another period.','other')
    trend=[];buckets={}
    for day,value in daily.items():
        key=day if days<=45 else day[:7];bucket=buckets.setdefault(key,metric())
        for name,val in value.items():bucket[name]+=val
    trend=[{'date':key,**finish_metric(value)} for key,value in buckets.items()]
    def extrema(rows,key):
        return {'highest':max(rows,key=lambda x:x[key],default=None),'lowest':min(rows,key=lambda x:x[key],default=None),'sample':len(rows)}
    highlights={'services':extrema(service_rows,'contribution'),'clients':extrema(active_clients,'contribution'),
        'jobs':extrema([j for j in job_rows if j['billed']],'contribution'),
        'team_delivery':extrema([t for t in team_rows if t['reviewed']>=3],'on_time_percent')}
    return {'business_id':business['id'],'business_name':business.get('trading_name') or business['name'],'currency':business.get('currency','NPR'),
        'period':{'start':start,'end':end,'days':days,'previous_start':all_start,'previous_end':previous_end.isoformat()},
        'summary':net,'previous':before,'trend':trend,'quality':quality,'recommendations':recommendations,'highlights':highlights,
        'receivables':{'outstanding':number(m(outstanding)),'overdue':number(m(overdue)),'ageing':[{**b,'amount':number(m(b['amount']))} for b in ageing]},
        'clients':sorted(client_rows,key=lambda c:(-c['sales'],c['name']))[:100], 'client_total':len(client_rows),
        'services':sorted(service_rows,key=lambda s:(-s['contribution'],s['name']))[:100], 'service_total':len(service_rows),
        'jobs':sorted(job_rows,key=lambda j:j['contribution'])[:100], 'job_total':len(job_rows),
        'team':sorted(team_rows,key=lambda t:(-t['overdue'],t['name']))[:100], 'team_total':len(team_rows),
        'expenses':[{'category':key,'amount':number(m(value))} for key,value in sorted(expenses.items(),key=lambda x:-x[1])],
        'excluded_expenses':[{'treatment':key,'amount':number(m(value))} for key,value in excluded.items()],
        'patterns':{'weekdays':[{'day':key,'sales':number(m(v['sales'])),'bills':v['bills']} for key,v in weekdays.items()],
            'billed_clients':len(active_clients),'returning_clients':returning,'returning_percent':round(returning*100/len(active_clients),1) if active_clients else None,
            'largest_client_percent':concentration,'decided_quotes':len(decided),'accepted_quotes':sum(q['status']=='accepted' for q in decided),
            'sources':[{'source':key,**value} for key,value in sources.items()], 'open_stages':dict(stages),'reviewed_assignments':reviewed},
        'basis':['Sales and credits use document dates and exclude VAT/GST. Draft bills are excluded.',
            'Direct costs use retained bill line costs; Labour lines are excluded because approved payroll is counted separately. Only restocked line returns reverse direct costs.',
            'Approved/paid payroll employer cost is allocated evenly over its pay period. Commissions included in payroll are counted once; other approved commissions use their record date.',
            'Operating expenses count once. Inventory purchases, payroll payouts, advances, assets, tax payments and owner withdrawals are separate cash movements.',
            'The result excludes depreciation, income tax, unrecorded costs and unpaid operating supplier bills. Cash includes advances, supplier payments, paid net payroll and refunds.',
            'Client/service contribution excludes shared overhead and payroll. Whole-job contribution is lifetime through the end date and is not added to period profit.',
            'Team metrics measure saved records. Shared jobs appear for each assignee; missing reviews are not poor performance. Historical assignments/stages are not reconstructed.',
            'Manual credit net is apportioned across the original bill lines. Tables show up to 100 entries; highest/lowest highlights use all qualifying records. Team highlights require at least three delivery reviews per person.']}


class AnalyticsFeatures:
    def analytics(self, user, bid, start='', end=''):
        from domain import Problem, now
        if user['role']!='owner':raise Problem('Only the owner can view profit and performance analytics.',403)
        self.business_allowed(user,bid)
        with self.connect() as conn:
            if getattr(self,'cloud',False):conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ')
            else:conn.execute('BEGIN')
            business=self.business(conn,bid)
            first,last=period_dates(start,end,business_today(business))
            records=self.records(conn,bid)
        result=analyse(business,records,first,last);result['generated_at']=now()
        return result

    def analytics_csv(self, user, bid, start='', end=''):
        report=self.analytics(user,bid,start,end);stream=io.StringIO(newline='');writer=csv.writer(stream)
        writer.writerow(['Section','Name','Metric','Value','Currency','From AD','To AD'])
        def write(section,name,key,value):
            def safe(text):return "'"+text if isinstance(text,str) and text.startswith(('=','+','-','@','\t','\r')) else text
            writer.writerow([safe(section),safe(name),safe(key),safe(value),report['currency'],report['period']['start'],report['period']['end']])
        for key,value in report['summary'].items():write('Summary',report['business_name'],key,value)
        for section,keys in [('clients',['sales','contribution','outstanding','overdue','bills']),('services',['sales','direct_cost','contribution','units']),('team',['assigned','completed','overdue','hours','on_time_percent','quality_rating'])]:
            for row in report[section]:
                for key in keys:write(section,row['name'],key,row[key])
        for text in report['basis']:write('Basis','',text,'')
        return ('\ufeff'+stream.getvalue()).encode()
