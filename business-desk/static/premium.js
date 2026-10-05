'use strict';

// Small, local assets: no UI framework, remote font, chart service or icon CDN.
const premiumIcons = {
  focus: '<path d="M12 3v3m0 12v3M3 12h3m12 0h3"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
  portfolio: '<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  sliders: '<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="15" cy="17" r="3"/>',
  pulse: '<path d="M3 13h4l3-7 4 13 3-6h4"/>',
  calendar: '<rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 11h18m-13 4h2m4 0h2"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  glass: '<rect x="4" y="4" width="16" height="16" rx="5"/><path d="m7 14 7-7m-3 10 6-6"/>',
  chevron: '<path d="m9 6 6 6-6 6"/>',
};
function deskIcon(name) {
  return premiumIcons[name] ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${premiumIcons[name]}</svg>` : icon(name);
}
const focusGroups = {all:'Everything',collections:'Collections',work:'Work & visits',clients:'Clients & sales',stock:'Stock & suppliers',team:'People',other:'Other'};
const panelNames = {focus:'Priority inbox',collections:'Collection pulse',sector:'Sector workflow',schedule:'Upcoming schedule',team:'Team presence',assistant:'Ask your records'};
const searchIndexes = new WeakMap();
function extendPremiumModels() {
  sections.reports.name='Business health';
  models.expenses.fields.push(['expense_treatment','Profit and loss treatment','select',['Operating expense','Inventory purchase','Payroll payout','Staff advance','Capital asset','Tax payment','Owner withdrawal']]);
  sections.focus={name:'Focus inbox',icon:deskIcon('focus'),hint:'A clear next step for every business issue.'};
  sections.portfolio={name:'All businesses',icon:deskIcon('portfolio'),hint:'An owner overview, with each currency kept separate.'};
  models.followups.fields.push(['task_category','Task category','select',Object.keys(focusGroups).filter(k=>k!=='all')],['priority','Priority','select',['normal','high','low']]);
  Object.assign(models.followups.defaults,{task_category:'clients',priority:'normal'});
}
function readable(kind) {return S.state.permissions.read.includes(kind);}
function fullFinancialView() {return ['invoices','payments','credits','allocations','opening_balances'].every(readable);}
function enabledPanel(name) {const panels=S.state.business.dashboard_panels;return (Array.isArray(panels)?panels:Object.keys(panelNames)).includes(name);}
function signedCollections(list) {return list.reduce((sum,x)=>sum+Math.round(Number(x.amount||0)*100)*(x.direction==='refund'?-1:1),0)/100;}
function amountIn(value,currencyCode=currency()) {return currencyCode+' '+Number(value||0).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2});}
function categoryFor(kind,record=null) {
  if(kind==='followups'&&['collections','work','stock','clients','team','other'].includes(record?.task_category))return record.task_category;
  if(['invoices','payments','credits','opening_balances','cash_closures','supplier_bills','supplier_payments'].includes(kind))return 'collections';
  if(['jobs','appointments','assets'].includes(kind))return 'work';
  if(['stock','movements','purchases','vehicles'].includes(kind))return 'stock';
  if(['employees','attendance','time_entries','payroll','commissions'].includes(kind))return 'team';
  return 'clients';
}
function focusItems(period='due') {
  if(period==='due')return S.state.alerts.map(alert=>({...alert,category:categoryFor(alert.type,find(alert.type,alert.record_id))}));
  const today=S.state.today, end=addDays(today,7), visible=new Set(S.state.alerts.map(a=>a.type+':'+a.record_id));
  return ['followups','appointments','jobs','leads','purchases','contracts'].flatMap(kind=>rows(kind).filter(row=>{
    const day=kind==='appointments'?row.date:kind==='purchases'?row.expected_date:kind==='contracts'?row.expiry_date:row.due_date;
    return day>today&&day<=end&&!visible.has(kind+':'+row.id)&&!['completed','cancelled','closed','received'].includes(row.status)&&
      !(kind==='jobs'&&row.stage===S.state.stages.at(-1))&&!(kind==='leads'&&['lost','won','delivered'].includes(row.stage));
  }).map(row=>({key:'upcoming:'+kind+':'+row.id,type:kind,record_id:row.id,title:label(row),
    detail:kind==='followups'?row.notes||'':refLabel('customers',row.customer_id),
    next_action:row.next_action||row.blocker||'Review the planned date and prepare the next step.',
    due_date:kind==='appointments'?row.date:kind==='purchases'?row.expected_date:kind==='contracts'?row.expiry_date:row.due_date,
    priority:{high:1,normal:2,low:3}[row.priority]||2,category:categoryFor(kind,row),upcoming:true})))
    .sort((a,b)=>a.due_date.localeCompare(b.due_date)||a.priority-b.priority);
}
function focusRow(alert,compact=false) {
  const record=find(alert.type,alert.record_id), customer=record?.customer_id?find('customers',record.customer_id):null;
  return `<li class="focus-row ${alert.priority===1?'urgent':''}"><span class="focus-symbol ${e(alert.category)}">${deskIcon({collections:'money',work:'workshop',clients:'customers',stock:'stock',team:'team'}[alert.category]||'focus')}</span><div class="focus-copy"><div class="focus-meta">${e(focusGroups[alert.category]||'Business action')}${alert.upcoming?`<span>${e(dateLabel(alert.due_date))}</span>`:alert.priority===1?'<span class="priority-dot">Priority</span>':''}</div><button class="record-link" data-action="open" data-kind="${e(alert.type)}" data-id="${e(alert.record_id)}">${e(alert.title)}</button><p>${e(alert.detail||customer?.name||alert.next_action)}</p>${!compact?`<small>${e(alert.next_action)}</small>`:''}${alert.last_note?`<small class="focus-note">Last note: ${e(alert.last_note)}</small>`:''}</div><div class="focus-row-actions">${alert.type==='followups'&&can('followups')?`<button class="btn small" data-action="edit" data-kind="followups" data-id="${e(alert.record_id)}">Update</button>`:!alert.upcoming&&can('followups')?`<button class="btn small" data-action="follow-alert" data-key="${e(alert.key)}">Plan next step</button>`:`<button class="icon-button" data-action="open" data-kind="${e(alert.type)}" data-id="${e(alert.record_id)}" aria-label="Open ${e(alert.title)}">${deskIcon('chevron')}</button>`}</div></li>`;
}
function focusCard() {
  const items=focusItems();
  return `<section class="card focus-card"><div class="card-head"><div><div class="card-eyebrow">NEXT BEST ACTION</div><h2>Your focus today <span class="soft-count">${items.length}</span></h2><p>Saved promises, balances and work that needs attention.</p></div><button class="btn text small" data-action="navigate" data-page="focus">Open inbox ${deskIcon('arrow')}</button></div>${items.length?`<ul class="focus-list">${items.slice(0,4).map(x=>focusRow(x,true)).join('')}</ul>`:empty('You’re up to date','Set a next date on your work and customer follow-ups to keep this view useful.')}<div class="card-bottom"><span>${items.filter(a=>a.priority===1).length} priority actions</span>${can('followups')?`<button class="btn text small" data-action="new" data-kind="followups">${deskIcon('plus')} Add a task</button>`:''}</div></section>`;
}
function renderFocus() {
  const period=S.focusPeriod||'due', group=S.focusGroup||'all', all=focusItems(period);
  const query=(S.focusQuery||'').toLowerCase().trim(), filtered=all.filter(x=>(group==='all'||x.category===group)&&(!query||[x.title,x.detail,x.next_action].join(' ').toLowerCase().includes(query)));
  $('#content').innerHTML=pageHead('A clear next step.',`One inbox for ${ownName(S.state.business)}. Assign responsibility and record what happens next.`,can('followups')?`<button class="btn primary" data-action="new" data-kind="followups">${deskIcon('plus')} Add a task</button>`:'','FOCUS INBOX')+
    `<div class="focus-toolbar"><div class="segmented" role="group" aria-label="Focus time period">${[['due','Due & unresolved'],['upcoming','Next 7 days']].map(([key,text])=>`<button data-action="focus-period" data-period="${key}" aria-pressed="${period===key}">${text}</button>`).join('')}</div><label class="focus-search">${deskIcon('search')}<input id="focus-search" value="${e(S.focusQuery||'')}" placeholder="Find an action…" aria-label="Search focus inbox"></label></div>`+
    `<div class="focus-categories" role="group" aria-label="Focus categories">${Object.entries(focusGroups).filter(([key])=>key==='all'||all.some(x=>x.category===key)).map(([key,text])=>`<button class="chip-button ${group===key?'selected':''}" data-action="focus-group" data-group="${key}" aria-pressed="${group===key}">${e(text)}<span>${key==='all'?all.length:all.filter(x=>x.category===key).length}</span></button>`).join('')}</div><section class="card"><div class="card-head"><div><h2>${period==='due'?'Due & unresolved':'Coming up this week'}</h2><p id="focus-result-count">${filtered.length} ${filtered.length===1?'action':'actions'}${S.offline?' · Saved offline view':''}</p></div>${S.offline?'<span class="badge amber">Offline</span>':'<span class="badge green">From your records</span>'}</div><div id="focus-results">${focusResults(filtered,period)}</div></section><p class="source-note">Completing a reminder records its outcome. The source bill, stock balance or work stage decides whether the underlying issue is resolved.</p>`;
  $('#focus-search').oninput=event=>{
    S.focusQuery=event.target.value;const term=S.focusQuery.toLowerCase().trim();const list=all.filter(x=>(group==='all'||x.category===group)&&(!term||[x.title,x.detail,x.next_action].join(' ').toLowerCase().includes(term)));
    $('#focus-results').innerHTML=focusResults(list,period);$('#focus-result-count').textContent=list.length+' actions';
  };
}
function focusResults(items,period) {return items.length?`<ul class="focus-list">${items.slice(0,100).map(x=>focusRow(x)).join('')}</ul>${items.length>100?'<p class="source-note">First 100 actions shown. Use a category or search to narrow the list.</p>':''}`:empty(period==='upcoming'?'Room for what’s next':'Nothing in this view',period==='upcoming'?'Add a future date to a task, visit, enquiry or promised delivery.':'Try another category, or add a planned follow-up.');}

function collectionPulse() {
  const day=S.state.today, month=day.slice(0,7), payments=rows('payments'), net=signedCollections(payments.filter(x=>x.date?.startsWith(month)&&x.date<=day));
  const days=Array.from({length:14},(_,i)=>addDays(day,i-13));const values=days.map(d=>signedCollections(payments.filter(x=>x.date===d)));
  const low=Math.min(0,...values),high=Math.max(1,...values),range=high-low;
  const y=v=>160-((v-low)/range)*126, points=values.map((v,i)=>[20+i*560/13,y(v)]),baseline=y(0);
  const path=points.map(([x,y],i)=>(i?'L':'M')+x.toFixed(1)+' '+y.toFixed(1)).join(' '), area=path+` L580 ${baseline.toFixed(1)} L20 ${baseline.toFixed(1)} Z`;
  const target=Number(S.state.business.monthly_collection_target||0),percent=target?Math.round(net/target*100):0;
  return `<section class="card collection-pulse"><div class="card-head"><div><div class="card-eyebrow">COLLECTION PULSE</div><h2>Money coming in</h2><p>Recorded receipts less refunds · Includes advances.</p></div><span class="pill-label">Last 14 days</span></div><div class="pulse-summary"><div><span class="muted">${e(new Date(day+'T12:00:00').toLocaleDateString('en-GB',{month:'long',year:'numeric'}))} to date</span><strong class="mono">${e(amountIn(net))}</strong></div>${can('payments')?`<button class="btn small" data-action="new" data-kind="payments">${deskIcon('plus')} Receipt</button>`:''}</div><div class="pulse-chart"><div class="chart-axis"><span>${e(amountIn(high))}</span><span>${e(amountIn(low))}</span></div><svg viewBox="0 0 600 185" role="img" aria-labelledby="pulse-title pulse-desc"><title id="pulse-title">Recorded daily net collections</title><desc id="pulse-desc">${e(days.map((d,i)=>d+': '+amountIn(values[i])).join('; '))}</desc><defs><linearGradient id="pulse-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="currentColor" stop-opacity=".18"/><stop offset="100%" stop-color="currentColor" stop-opacity=".01"/></linearGradient></defs><path d="M20 ${baseline.toFixed(1)} H580" class="chart-zero"/><path d="${area}" fill="url(#pulse-fill)"/><path d="${path}" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>${points.map(([x,y],i)=>`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3" fill="currentColor"><title>${e(dateLabel(days[i])+': '+amountIn(values[i]))}</title></circle>`).join('')}</svg><div class="chart-dates"><span>${e(dateLabel(days[0]))}</span><span>${e(dateLabel(day))}</span></div></div><div class="target-strip"><div><span>Monthly collection target</span>${target?`<b>${e(amountIn(target))} <span class="muted">· ${percent}%</span></b>`:'<b>Set a target that fits your business</b>'}</div>${owner()?`<button class="icon-button" data-action="dashboard-config" aria-label="Set collection target">${deskIcon('sliders')}</button>`:''}</div>${target?`<div class="target-track" role="progressbar" aria-label="Monthly collection target progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.max(0,Math.min(100,percent))}" aria-valuetext="${e(amountIn(net)+' collected against '+amountIn(target))}"><span style="width:${Math.max(0,Math.min(100,percent))}%"></span></div>`:''}</section>`;
}
function collectionQueue() {
  const owing=[...rows('invoices').filter(x=>x.status==='issued'&&x._balance>.009),...rows('opening_balances').filter(x=>x._balance>.009)].sort((a,b)=>(a.due_date||a.date||'9999').localeCompare(b.due_date||b.date||'9999'));
  return `<section class="card"><div class="card-head"><div><h2>Ready to collect</h2><p>Oldest outstanding dates first.</p></div><span class="soft-count">${owing.length}</span></div>${owing.length?`<div class="collection-list">${owing.slice(0,4).map(x=>`<div class="collection-row"><span class="initial-badge">${e(refLabel('customers',x.customer_id).slice(0,1))}</span><div class="grow"><button class="record-link" data-action="open" data-kind="${e(x.type||'invoices')}" data-id="${e(x.id)}">${e(refLabel('customers',x.customer_id))}</button><p>${e(x.source_reference||x.number)} · ${x.due_date?'Due '+e(dateLabel(x.due_date)):'Opening balance'}</p></div><b class="mono">${e(amountIn(x._balance))}</b>${can('payments')?`<button class="btn small" data-action="${x.type==='opening_balances'?'opening-payment':'invoice-payment'}" data-id="${e(x.id)}">Receipt</button>`:''}</div>`).join('')}</div>`:empty('Collections are clear','Issued bills and reconciled customer openings appear here.')}</section>`;
}
function scheduleCard() {
  const upcoming=focusItems('upcoming').filter(x=>['appointments','jobs','followups','leads'].includes(x.type)).slice(0,4);
  return `<section class="card schedule-card"><div class="card-head"><div><h2>Your next seven days</h2><p>Visits, promises and planned follow-ups.</p></div>${deskIcon('calendar')}</div>${upcoming.length?upcoming.map(x=>`<div class="schedule-row"><div class="date-square"><b>${Number(x.due_date.slice(-2))}</b><span>${e(new Date(x.due_date+'T12:00:00').toLocaleDateString('en-GB',{month:'short'}))}</span></div><div class="grow"><button class="record-link" data-action="open" data-kind="${x.type}" data-id="${e(x.record_id)}">${e(x.title)}</button><p>${e(focusGroups[x.category])}</p></div></div>`).join(''):empty('A little room ahead','Set a next date when planning work or following up with a client.')}</section>`;
}
function teamCard() {
  const employees=rows('employees').filter(x=>x.active!==false&&(S.user.role!=='technician'||x.id===S.user.employee_id));
  const attendance=rows('attendance').filter(x=>x.date===S.state.today),byEmployee=new Map(attendance.map(x=>[x.employee_id,x]));
  return `<section class="card team-pulse"><div class="card-head"><div><h2>${S.user.role==='technician'?'Your attendance':'Team presence'}</h2><p>Today’s recorded attendance.</p></div>${deskIcon('team')}</div>${employees.length?employees.slice(0,5).map(x=>{const a=byEmployee.get(x.id);return `<div class="team-row"><span class="avatar small">${e(x.name.slice(0,1))}</span><div class="grow"><b>${e(x.name)}</b><p>${e(x.role||'Team member')}</p></div>${a?`<button class="attendance-link" data-action="open" data-kind="attendance" data-id="${e(a.id)}">${status(a.status)}</button>`:'<span class="badge gray">Not recorded</span>'}</div>`;}).join(''):empty('Bring your team together','Add employees to connect attendance and work assignments.')}<div class="card-bottom"><span>${employees.length} ${S.user.role==='technician'?'assigned employee':'active team members'}</span>${can('attendance')?`<button class="btn text small" data-action="new" data-kind="attendance">Record attendance</button>`:''}</div></section>`;
}
function assistantCard() {return `<section class="card assistant"><div class="card-head"><div><div class="card-eyebrow">YOUR BUSINESS, CONNECTED</div><h2>Ask your records</h2></div>${deskIcon('spark')}</div><div class="card-body"><p class="help-text">Check what is due, who owes you or where work is stuck.</p><form id="assistant-form" class="assistant-question"><input name="question" placeholder="What needs attention today?" aria-label="Ask your business desk" required maxlength="500"><button class="btn primary small">${deskIcon('arrow')}<span class="sr-only">Ask</span></button></form><div class="chips">${['Today’s priorities','Who owes us?','Work blockers'].map(question=>`<button class="chip-button" data-action="ask" data-question="${e(question)}">${e(question)}</button>`).join('')}</div><div id="assistant-answer"></div></div></section>`;}
function renderPremiumToday() {
  const b=S.state.business,profile=b.profile||'garage',day=S.state.today,financial=fullFinancialView();
  const owing=financial?[...rows('invoices').filter(x=>x.status==='issued'&&x._balance>.009),...rows('opening_balances').filter(x=>x._balance>.009)]:[];
  const work=profile==='showroom'?rows('leads').filter(x=>!['lost','won','delivered'].includes(x.stage)):rows('jobs').filter(x=>x.stage!==S.state.stages.at(-1));
  const low=rows('stock').filter(x=>x._quantity<=x.reorder_at),due=focusItems();
  const zone=b.country==='IN'?'Asia/Kolkata':'Asia/Kathmandu',hour=Number(new Intl.DateTimeFormat('en-GB',{hour:'numeric',hourCycle:'h23',timeZone:zone}).format(new Date()));
  const actions=[['payments','Record receipt','money'],['customers','Add client','customers'],[profile==='showroom'?'leads':'quotes',profile==='showroom'?'New enquiry':'New quotation','sales'],[profile==='showroom'?'vehicles':profile==='retail'?'stock':profile==='service'?'appointments':'jobs',profile==='showroom'?'Add vehicle':profile==='retail'?'Add stock':profile==='service'?'Book a visit':'Open job card',profile==='retail'?'stock':profile==='showroom'?'vehicles':'workshop']].filter(([kind])=>can(kind));
  const primary=can('invoices')?`<button class="btn" data-action="quick-bill">${deskIcon('stock')} Quick bill</button><button class="btn primary" data-action="new" data-kind="invoices">${deskIcon('plus')} New bill</button>`:'';
  const roleMetric=readable('customers')?['Your clients',rows('customers').length]:readable('jobs')?['Assigned work',work.length]:['Catalogue items',rows('stock').length+rows('services').length];
  const outstanding=owing.reduce((n,x)=>n+x._balance,0),net=signedCollections(rows('payments').filter(x=>x.date===day));
  $('#content').innerHTML=`<div class="workspace-greeting"><div class="welcome-label"><span class="live-mark"></span>${e(profileChoices[profile]?.name||'Your workspace')} <span>·</span> ${e(b.country==='IN'?'India':'Nepal')}</div><div class="greeting-main"><div><h1>Good ${hour<12?'morning':hour<18?'afternoon':'evening'}, ${e(S.user.name.split(' ')[0])}<span class="greeting-period">.</span></h1><p>Your day at <strong>${e(ownName(b))}</strong>, at a glance.</p></div><div class="actions greeting-actions">${primary}${owner()?`<button class="icon-button dashboard-customise" data-action="dashboard-config" aria-label="Personalise dashboard" title="Personalise your dashboard">${deskIcon('sliders')}</button>`:''}</div></div>${b.goal?`<div class="business-goal">${deskIcon('focus')}<span>${e(b.goal)}</span></div>`:''}</div>`+
    (S.offline?'<div class="notice warning">Offline workspace · Saved information may be older. Drafts can sync later; bills, receipts and stock postings need the server.</div>':'')+setupChecklist()+
    `<div class="stats premium-stats">${financial?stat('Waiting to be collected',rupees(outstanding),owing.length+' open balances',true):stat(roleMetric[0],roleMetric[1],'Available to your role',true)}${financial?stat('Collected today',rupees(net),'Recorded receipts less refunds'):stat('Actions due',due.length,'From your saved records')}${stat(profile==='showroom'?'Open enquiries':profile==='retail'||!readable('jobs')&&readable('stock')?'Reorder alerts':'Work in progress',profile==='retail'||!readable('jobs')&&readable('stock')?low.length:work.length,profile==='showroom'?'Next steps in your pipeline':profile==='retail'||!readable('jobs')&&readable('stock')?'At or below reorder level':'Open work orders')}${stat(financial?'Priority actions':'Planned this week',financial?due.filter(x=>x.priority===1).length:focusItems('upcoming').length,financial?'Open the Focus inbox':'Next seven days')}</div>`+
    `<div class="premium-dashboard"><div class="dashboard-main">${enabledPanel('collections')&&financial?collectionPulse():''}${enabledPanel('focus')?focusCard():''}${enabledPanel('sector')?sectorFocus():''}${enabledPanel('collections')&&financial?collectionQueue():''}${profile==='showroom'&&enabledPanel('sector')&&readable('leads')?`<section class="card"><div class="card-head"><div><h2>Sales in motion</h2><p>Move each enquiry towards a clear decision.</p></div><button class="btn text small" data-action="navigate" data-page="pipeline">Pipeline ${deskIcon('arrow')}</button></div>${leadBoard(work.slice(0,8))}</section>`:''}</div><aside class="dashboard-rail">${actions.length?`<section class="card start-card"><div class="card-head"><div><div class="card-eyebrow">QUICK START</div><h2>Make progress.</h2></div>${deskIcon('plus')}</div><div class="card-body"><div class="quick-grid">${actions.map(([kind,title,symbol])=>`<button class="quick-action" data-action="new" data-kind="${kind}"><span>${deskIcon(symbol)}</span><b>${e(title)}</b>${deskIcon('chevron')}</button>`).join('')}</div></div></section>`:''}${enabledPanel('schedule')?scheduleCard():''}${enabledPanel('team')&&readable('attendance')?teamCard():''}${enabledPanel('assistant')?assistantCard():''}</aside></div><div class="workspace-foot"><span>${deskIcon('check')} ${S.offline?'Saved offline view':'Connected to '+(S.health?.hosted?'your business server':'your local server')}</span><button class="btn text small" data-action="appearance">${deskIcon('glass')} Display preferences</button></div>`;
  $('#assistant-form')?.addEventListener('submit',event=>{event.preventDefault();ask(new FormData(event.target).get('question'));});
}

function dashboardConfig() {
  if(!owner())throw new Error('Only the owner can configure this business dashboard.');
  const b=S.state.business;
  showDialog('Make the dashboard yours',`<form id="dashboard-form"><div id="form-error" class="form-error"></div><div class="configuration-business"><img src="${e(ownIcon(b))}" alt=""><div><b>${e(ownName(b))}</b><span>${e(profileChoices[b.profile]?.name||'Business workspace')}</span></div></div><div class="form-grid"><div class="field full"><label for="dashboard-goal">Your current business focus</label><input id="dashboard-goal" name="goal" value="${e(b.goal||'')}" maxlength="300" placeholder="For example, finish promised jobs and collect overdue bills"><small>Shown to your team as a shared focus.</small></div><div class="field full"><label for="dashboard-target">Monthly collection target, ${e(b.currency)}</label><input id="dashboard-target" name="target" type="number" step=".01" min="0" max="1000000000000" value="${Number(b.monthly_collection_target||0)}"><small>Compared with recorded receipts less refunds each calendar month. Set 0 to leave it off.</small></div></div><div class="form-section"><h3>Panels that help your business</h3><p class="help-text">Staff see panels supported by their role. Your choice applies to this business.</p><div class="dashboard-options">${Object.entries(panelNames).map(([key,title])=>`<label><input type="checkbox" name="panels" value="${key}" ${enabledPanel(key)?'checked':''}><span>${e(title)}</span></label>`).join('')}</div></div><div class="notice">For approval rules, stages, billing and client terms, use Guided configuration in Settings.</div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="dashboard-form">Save dashboard</button>`,false,'Your name, your goals, your daily workflow.');
  let savedBusiness=null;
  $('#dashboard-form').onsubmit=async event=>{
    event.preventDefault();const form=event.target,button=$('[form=dashboard-form][type=submit]');if(button.disabled)return;button.disabled=true;
    try{
      if(!savedBusiness){const values=new FormData(form);savedBusiness=await api('businesses',{id:b.id,version:b.version,data:{goal:values.get('goal'),monthly_collection_target:Number(values.get('target')),dashboard_panels:values.getAll('panels')}});}
      button.textContent='Applying dashboard…';await openSavedBusiness(savedBusiness);$('#editor').close();toast('Your dashboard is ready.');
    }catch(error){if(savedBusiness){$$('input,select,textarea',form).forEach(control=>control.disabled=true);button.textContent='Open saved dashboard';}formError(error.message);}finally{button.disabled=false;}
  };
}
function readDisplay() {
  try {const data=JSON.parse(localStorage.getItem('bd_display_'+S.user?.id)||'{}');return {density:data.density==='compact'?'compact':'comfortable',surface:data.surface==='solid'?'solid':'glass'};}
  catch{return {density:'comfortable',surface:'glass'};}
}
function applyDisplay() {const display=readDisplay();document.documentElement.dataset.density=display.density;document.documentElement.dataset.surface=display.surface;}
function appearanceDialog() {
  const display=readDisplay();
  showDialog('Comfort, your way',`<form id="display-form"><div id="form-error" class="form-error"></div><div class="display-preview">${deskIcon('glass')}<div><b>A workspace that feels like yours.</b><p>These choices stay on this device for your account.</p></div></div><fieldset class="choice-fieldset"><legend>Surface style</legend><label><input type="radio" name="surface" value="glass" ${display.surface==='glass'?'checked':''}><div><b>Liquid glass</b><small>Soft translucent navigation and floating panels.</small></div></label><label><input type="radio" name="surface" value="solid" ${display.surface==='solid'?'checked':''}><div><b>Solid surfaces</b><small>Clear opaque panels with less visual detail.</small></div></label></fieldset><fieldset class="choice-fieldset"><legend>Workspace density</legend><label><input type="radio" name="density" value="comfortable" ${display.density==='comfortable'?'checked':''}><div><b>Comfortable</b><small>More space for everyday phone and desktop use.</small></div></label><label><input type="radio" name="density" value="compact" ${display.density==='compact'?'checked':''}><div><b>Compact</b><small>More records on a desktop. Touch targets stay large.</small></div></label></fieldset></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="display-form">Save display preferences</button>`);
  $('#display-form').onsubmit=event=>{event.preventDefault();try{localStorage.setItem('bd_display_'+S.user.id,JSON.stringify(Object.fromEntries(new FormData(event.target))));applyDisplay();$('#editor').close();toast('Display preferences saved.');}catch{formError('This browser could not save display preferences.');}};
}
function displaySettingsCard() {return `<section class="card"><div class="card-head"><div><h2>Your daily workspace</h2><p>Make the business dashboard and this device comfortable to use.</p></div>${deskIcon('glass')}</div><div class="card-body"><div class="actions">${owner()?`<button class="btn" data-action="dashboard-config">${deskIcon('sliders')} Personalise dashboard</button>`:''}<button class="btn" data-action="appearance">Display preferences</button></div></div></section>`;}

function searchIndex() {
  if(searchIndexes.has(S.state))return searchIndexes.get(S.state);
  const entries=Object.entries(S.state.records).flatMap(([kind,list])=>list.map(record=>{
    const values=Object.entries(record).filter(([key,value])=>!key.startsWith('_')&&typeof value==='string'&&!/^(id|.*_id|.*_at)$/.test(key)).map(([,value])=>value);
    for(const [key,ref] of Object.entries(refs))if(record[key])values.push(refLabel(ref,record[key]));
    values.push(label(record));return {kind,record,text:values.join(' ').toLowerCase()};
  }));searchIndexes.set(S.state,entries);return entries;
}
function renderPremiumSearch() {
  const term=S.query.toLowerCase().trim(),found=searchIndex().filter(x=>x.text.includes(term));
  $('#content').innerHTML=pageHead('Find it. Keep moving.',`${found.length} matching records for “${S.query}”`,'','SEARCH YOUR BUSINESS')+`<section class="card search-card">${found.length?found.slice(0,100).map(({kind,record})=>`<div class="search-result"><span class="focus-symbol">${deskIcon({customers:'customers',jobs:'workshop',invoices:'money',stock:'stock',followups:'focus',appointments:'calendar'}[kind]||'sales')}</span><div class="grow"><button class="record-link" data-action="open" data-kind="${e(kind)}" data-id="${e(record.id)}">${e(label(record))}</button><div class="cell-sub">${e(models[kind]?.name||kind)} · ${e(record.number||record.date||'')}</div></div>${record.status?status(record.status):''}</div>`).join(''):empty('Nothing found yet','Try a client name, phone number, bill reference, vehicle or job title.')}</section>${found.length>100?'<p class="source-note">First 100 matches shown. Add another word to narrow your search.</p>':''}`;
}
function queueSearch(value) {
  S.query=value;clearTimeout(S.searchTimer);
  if(!value.trim()){renderContent();return;}
  const businessId=S.bid,query=value;
  S.searchTimer=setTimeout(()=>{if(S.bid===businessId&&S.query===query&&S.state&&!S.loadingBusiness)renderContent();},140);
}

function portfolioHead() {return pageHead('Every business. One clear view.','Your organisation’s businesses, with their own names, workflows and currencies.',`<button class="btn" data-action="portfolio-refresh">${deskIcon('refresh')} Refresh overview</button><button class="btn primary" data-action="new-business">${deskIcon('plus')} Add business</button>`,'OWNER OVERVIEW');}
async function renderPortfolio(force=false) {
  if(!owner()){S.page='today';renderShell();return;}
  const offset=S.portfolioOffset||0,userId=S.user.id;
  const cached=S.portfolioCache;
  if(!force&&cached&&cached.userId===userId&&cached.data.offset===offset&&Date.now()-cached.time<60000){paintPortfolio(cached.data);return;}
  const request=(S.portfolioRequest||0)+1;S.portfolioRequest=request;
  $('#content').innerHTML=portfolioHead()+`<div class="portfolio-loading" role="status" aria-live="polite"><span class="loading-dot"></span>Opening your owner overview…</div><div class="portfolio-grid" aria-hidden="true">${Array.from({length:3},()=>'<div class="portfolio-skeleton"><span></span><span></span><span></span></div>').join('')}</div>`;
  try{
    if(S.offline)throw new Error('Connect to the server to load current totals for your other businesses.');
    const data=await api('portfolio?offset='+offset);
    if(S.user?.id!==userId||request!==S.portfolioRequest||S.page!=='portfolio'||S.query.trim())return;
    S.portfolioCache={data,userId,time:Date.now()};paintPortfolio(data);
  }catch(error){
    if(S.user?.id!==userId||request!==S.portfolioRequest||S.page!=='portfolio'||S.query.trim()||S.needsLogin)return;
    $('#content').innerHTML=portfolioHead()+`<section class="card">${empty('The overview could not load',error.message,'<button class="btn primary" data-action="portfolio-refresh">Try again</button>')}</section>`;
  }
}
function paintPortfolio(data) {
  const currencies=Object.entries(data.totals);
  $('#content').innerHTML=portfolioHead()+`<div class="portfolio-summary">${currencies.map(([code,values])=>`<section class="card currency-summary"><div><span class="currency-label">${e(code)}</span><span class="muted">${values.businesses} ${values.businesses===1?'business':'businesses'} on this page</span></div><div class="currency-metrics"><div><small>Waiting to be collected</small><strong class="mono">${e(amountIn(values.outstanding,code))}</strong></div><div><small>Recorded collections this month</small><strong class="mono">${e(amountIn(values.collected_month,code))}</strong></div></div></section>`).join('')}</div><div class="portfolio-grid">${data.businesses.map(b=>{
    const target=Number(b.monthly_collection_target||0),progress=target?Math.round(b.collected_month/target*100):0;
    return `<section class="card business-tile" style="--business-colour:${/^#[a-f\d]{6}$/i.test(b.brand_hex)?b.brand_hex:'#5754d6'}"><div class="business-tile-head"><span class="business-monogram">${e(b.name.slice(0,2).toUpperCase())}</span><div class="grow"><h2>${e(b.name)}</h2><p>${e(profileChoices[b.profile]?.name||'Business')} · ${e(b.country==='IN'?'India':'Nepal')}</p></div>${b.id===S.bid?'<span class="badge green">Active</span>':''}</div>${b.goal?`<p class="portfolio-goal">${deskIcon('focus')} ${e(b.goal)}</p>`:''}<div class="business-tile-metrics"><div><small>Outstanding</small><strong class="mono">${e(amountIn(b.outstanding,b.currency))}</strong><span>${e(amountIn(b.overdue,b.currency))} overdue</span></div><div><small>Collected this month</small><strong class="mono">${e(amountIn(b.collected_month,b.currency))}</strong><span>${target?progress+'% of '+e(amountIn(target,b.currency)):'No monthly target set'}</span></div></div><div class="business-tile-counts"><span>${deskIcon('customers')} ${b.customers} clients</span><span>${deskIcon('workshop')} ${b.open_work} open ${b.profile==='showroom'?'enquiries':'jobs'}</span><span>${deskIcon('focus')} ${b.actions_due} actions</span></div>${b.next_actions.length?`<div class="portfolio-next">${b.next_actions.slice(0,2).map(a=>`<button data-action="portfolio-open" data-business="${e(b.id)}" data-kind="${e(a.type)}" data-id="${e(a.record_id)}"><span>${e(a.title)}</span>${deskIcon('chevron')}</button>`).join('')}</div>`:'<div class="portfolio-clear">No generated actions due</div>'}<button class="btn business-enter" data-action="switch-business" data-business="${e(b.id)}">Open workspace ${deskIcon('arrow')}</button></section>`;
  }).join('')}</div>${!data.businesses.length?`<section class="card">${empty('Your businesses belong here','Add a business to give it its own workspace.','<button class="btn primary" data-action="new-business">Add business</button>')}</section>`:''}<div class="portfolio-footer"><p>Totals cover these ${data.businesses.length} businesses. Each business uses its local calendar month. Receipts include advances and exclude future-dated entries. Cash-count review is available inside each business.</p><div class="pagination"><span>${data.total?data.offset+1:0}–${Math.min(data.total,data.offset+data.limit)} of ${data.total}</span><button class="btn small" data-action="portfolio-page" data-offset="${Math.max(0,data.offset-data.limit)}" ${data.offset===0?'disabled':''}>Previous</button><button class="btn small" data-action="portfolio-page" data-offset="${data.offset+data.limit}" ${data.offset+data.limit>=data.total?'disabled':''}>Next</button></div></div><p class="source-note">Last loaded ${e(new Date(data.generated_at).toLocaleTimeString('en-GB',{hour:'2-digit',minute:'2-digit'}))}. Refresh to see later changes.</p>`;
}
async function openSavedBusiness(business,page=S.page) {
  const previous={bid:S.bid,state:S.state,businesses:S.businesses,page:S.page,tab:S.tab};
  S.bid=business.id;S.page=page;S.tab='';
  try{await loadBusinesses();}
  catch(error){Object.assign(S,previous);if(!S.needsLogin){if(S.state)renderShell();else renderNoBusiness();}throw new Error('The business was saved, but its workspace could not load. '+error.message);}
}
async function switchBusiness(businessId,recordKind='',recordId='') {
  if(S.loadingBusiness)return;
  if(!S.businesses.some(b=>b.id===businessId))throw new Error('This business is no longer available. Refresh your business list.');
  const previous={id:S.bid,state:S.state,page:S.page,tab:S.tab};
  S.loadingBusiness=true;S.bid=businessId;S.query='';S.filter='';S.listQuery='';S.page='today';S.tab='';
  const layout=$('.layout');layout?.classList.add('workspace-loading');layout?.setAttribute('aria-busy','true');$('#business-picker').disabled=true;
  $('#content').innerHTML=`<div class="business-loading" role="status"><span class="loading-dot"></span><h2>Opening ${e(ownName(S.businesses.find(b=>b.id===businessId)))}…</h2><p>Loading this business’s records and permissions.</p></div>`;
  try{
    await reload();
    if(S.state?.business.id!==businessId)throw new Error('The business could not be loaded.');
    try{localStorage.setItem('bd_business_'+S.user.id,businessId);}catch{toast('Business opened. This browser could not remember your default business.',true);}
    window.scrollTo(0,0);
    if(recordKind&&recordId)openRecord(recordKind,recordId);
  }catch(error){S.bid=previous.id;S.state=previous.state;S.page=previous.page;S.tab=previous.tab;if(!S.needsLogin)renderShell();throw error;}
  finally{S.loadingBusiness=false;$('.layout')?.classList.remove('workspace-loading');$('.layout')?.removeAttribute('aria-busy');if($('#business-picker'))$('#business-picker').disabled=false;}
}
async function premiumAction(button) {
  if(S.loadingBusiness)return true;
  if(await analyticsAction(button))return true;
  const {action}=button.dataset;
  if(action==='close-navigation'){$('.layout')?.classList.remove('nav-open');$('.mobile-menu')?.setAttribute('aria-expanded','false');$('.mobile-menu')?.focus();return true;}
  if(action==='dashboard-config'){dashboardConfig();return true;}
  if(action==='appearance'){appearanceDialog();return true;}
  if(action==='focus-period'){S.focusPeriod=button.dataset.period;S.focusGroup='all';renderFocus();return true;}
  if(action==='focus-group'){S.focusGroup=button.dataset.group;renderFocus();return true;}
  if(action==='portfolio-refresh'){await renderPortfolio(true);return true;}
  if(action==='portfolio-page'){S.portfolioOffset=Number(button.dataset.offset);await renderPortfolio();return true;}
  if(action==='switch-business'||action==='portfolio-open'){await switchBusiness(button.dataset.business,action==='portfolio-open'?button.dataset.kind:'',action==='portfolio-open'?button.dataset.id:'');return true;}
  return false;
}

document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!$('#editor').open&&$('.layout')?.classList.contains('nav-open')){$('.layout').classList.remove('nav-open');$('.mobile-menu')?.setAttribute('aria-expanded','false');$('.mobile-menu')?.focus();}});
