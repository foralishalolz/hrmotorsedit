'use strict';

const profileChoices = {
  garage: {name:'Garage & collision', icon:'◈', description:'Estimates, repair stages, insurance and collections.', focus:'Deliver repairs on time and collect completed jobs.'},
  showroom: {name:'Vehicle showroom', icon:'◇', description:'Enquiries, vehicle stock, bookings and delivery.', focus:'Follow every enquiry through booking, payment and delivery.'},
  retail: {name:'Retail & trading', icon:'▣', description:'Fast billing, stock, suppliers and customer credit.', focus:'Bill quickly, control stock and recover customer credit.'},
  service: {name:'Service & repair', icon:'↗', description:'Appointments, work orders, repeat service and teams.', focus:'Keep appointments, approve work and collect payment.'},
};
function extendModels() {
  sections.pipeline={name:'Sales pipeline',icon:'↗',tabs:['leads'],hint:'Every enquiry has an owner, a next action, and a follow-up date.'};
  sections.vehicles={name:'Vehicle inventory',icon:'◇',tabs:['vehicles'],hint:'One record per chassis. Reserve a vehicle from its sales enquiry.'};
  sections.money.name='Billing & money';
  sections.stock.tabs.push('supplier_bills','supplier_payments');
  models.leads=m('Sales enquiries','enquiry',[
    ['name','Enquiry / opportunity','text'],['customer_id','Customer','ref','customers'],['phone','Callback number','tel'],
    ['source','Where did this enquiry come from?','select',['Walk-in','Referral','Phone','Facebook','Website','Existing customer','Other']],
    ['employee_id','Responsible employee','ref','employees'],['vehicle_id','Interested vehicle','ref','vehicles'],
    ['stage','Stage','select',['new','contacted','test_drive','quoted','booked','won','lost','delivered']],
    ['expected_value','Expected sale, NPR','number'],['due_date','Next follow-up date','date'],['next_action','What should happen next?','text'],
    ['finance_status','Finance status','select',['Not required','Customer arranging','Documents pending','Submitted','Approved','Disbursed']],
    ['lost_reason','Reason if lost','text'],['pdi_complete','Pre-delivery inspection complete','checkbox'],
    ['documents_complete','Registration / ownership documents checked','checkbox'],['handover_signed','Customer handover signed','checkbox'],['notes','Conversation notes','textarea'],
  ],['name','customer_id','stage','employee_id','due_date','next_action'],{stage:'new',source:'Walk-in',expected_value:0,next_action:'Call the customer and confirm their requirements.',finance_status:'Not required'});
  models.vehicles=m('Vehicle inventory','vehicle',[
    ['name','Make, model and variant','text'],['vin','Chassis / VIN','text'],['color','Colour','text'],['model_year','Model year','text'],
    ['condition','Condition','select',['New','Used','Demo']],['status','Availability','select',['available','in_transit','reserved','sold']],
    ['date','Stock arrival date','date'],['location','Showroom / yard','text'],['supplier_id','Supplier','ref','suppliers'],
    ['purchase_cost','Purchase cost, NPR','owner-number'],['sale_price','Selling price, NPR','number'],['notes','Specification / stock notes','textarea'],
  ],['name','vin','condition','sale_price','status','_age_days'],{condition:'New',status:'available',sale_price:0,purchase_cost:0});
  models.supplier_bills=m('Supplier bills','supplier bill',[
    ['supplier_id','Supplier','ref','suppliers'],['reference','Original supplier bill number','text'],['purchase_id','Purchase order (optional)','ref','purchases'],
    ['date','Bill date','date'],['due_date','Payment due','date'],['net','Net purchase amount, NPR','number'],['tax','Tax on supplier bill, NPR','number'],['notes','Bill notes','textarea'],
  ],['number','supplier_id','reference','amount','_balance','due_date'],{net:0,tax:0});
  models.supplier_payments=m('Supplier payments','supplier payment',[
    ['supplier_bill_id','Supplier bill','ref','supplier_bills'],['amount','Amount paid, NPR','number'],['date','Payment date','date'],
    ['method','Payment method','select',['Cash','Bank transfer','Cheque','Digital wallet','Other']],['reference','Bank / payment reference','text'],['notes','Payment notes','textarea'],
  ],['number','supplier_bill_id','amount','method','date'],{method:'Cash'});
  Object.assign(refs,{vehicle_id:'vehicles',lead_id:'leads',supplier_bill_id:'supplier_bills',purchase_id:'purchases'});
  Object.assign(headers,{vin:'Chassis / VIN',condition:'Condition',sale_price:'Price, NPR',_age_days:'Days in stock',stage:'Stage',next_action:'Next action',supplier_bill_id:'Supplier bill'});
  Object.assign(required,{leads:['name','customer_id','due_date','next_action'],vehicles:['name','vin'],supplier_bills:['supplier_id','reference','due_date'],supplier_payments:['supplier_bill_id','amount','date']});
  models.commissions.fields.splice(3,0,['lead_id','Sales enquiry (instead of a job)','ref','leads']);
  immutable.add('supplier_bills'); immutable.add('supplier_payments');
}
function enabledSections() {
  const modules=S.state.business.modules || ['sales','pipeline','workshop','customers','insurance','money','stock','team','followups','reports'];
  const order=['today',...modules,'settings'];
  return [...new Set(order)].filter(key=>sections[key]).map(key=>[key,sections[key]])
    .filter(([key,section])=>(!section.tabs || section.tabs.some(kind=>S.state.permissions.read.includes(kind))) && (owner() || key!=='reports'));
}
function setupWizard(selected='garage'){return workspaceOnboarding(selected);}
function customiseWorkspace() {
  const b=S.state.business;
  const available=Object.entries(sections).filter(([key])=>!['today','settings'].includes(key));
  showDialog('Choose the work you manage', `<form id="workspace-form"><div id="form-error" class="form-error"></div><p class="help-text">Keep the daily navigation relevant. Hiding a module preserves its records and permissions.</p><div class="module-grid">${available.map(([key,section])=>`<label><input type="checkbox" name="modules" value="${key}" ${(b.modules||[]).includes(key)?'checked':''} ${['customers','money','followups'].includes(key)?'disabled':''}><span><b>${e(section.name)}</b><small>${e(section.hint)}</small></span></label>`).join('')}</div></form>`, '<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="workspace-form">Save workspace</button>', true);
  $('#workspace-form').onsubmit=async event=>{event.preventDefault();try{
    const modules=[...new Set(['customers','money','followups',...new FormData(event.target).getAll('modules')])];
    await api('businesses',{id:b.id,version:b.version,data:{...b,modules}});$('#editor').close();await reload();toast('Workspace updated.');
  }catch(error){formError(error.message);}};
}
function setupChecklist() {
  if(!owner())return '';
  const checks=[{title:'Add your first customer',done:rows('customers').length>0,kind:'customers'},
    {title:S.state.business.profile==='showroom'?'Add a vehicle to stock':'Add a service or stock item',done:rows(S.state.business.profile==='showroom'?'vehicles':'stock').length+rows('services').length>0,kind:S.state.business.profile==='showroom'?'vehicles':'services'},
    {title:'Create the first bill',done:rows('invoices').length>0,kind:'invoices'}];
  const completed=checks.filter(x=>x.done).length;
  if(completed===checks.length)return '';
  return `<section class="launch-strip"><div><span class="eyebrow">GET STARTED</span><h3>A few steps to your first working day</h3><small>${completed} of ${checks.length} complete</small></div><div class="launch-steps">${checks.map((x,i)=>`<button class="launch-step ${x.done?'done':''}" data-action="new" data-kind="${x.kind}"><span>${x.done?'✓':i+1}</span>${x.title}</button>`).join('')}</div></section>`;
}
function renderWorkspaceToday() {
  const b=S.state.business, profile=b.profile||'garage';
  const invoices=rows('invoices').filter(x=>x.status==='issued');
  const openings=rows('opening_balances').filter(x=>x._balance>0);
  const owing=[...invoices.filter(x=>x._balance>0),...openings].sort((a,b)=>(a.due_date||a.date||'9999').localeCompare(b.due_date||b.date||'9999'));
  const outstanding=owing.reduce((n,x)=>n+x._balance,0);
  const overdue=owing.filter(x=>x.due_date&&x.due_date<S.state.today);
  const receipts=rows('payments').filter(x=>x.date===S.state.today).reduce((n,x)=>n+(x.direction==='refund'?-1:1)*x.amount,0);
  const work=profile==='showroom'?rows('leads').filter(x=>!['lost','won','delivered'].includes(x.stage)):rows('jobs').filter(x=>x.stage!==S.state.stages.at(-1));
  const low=rows('stock').filter(x=>x._quantity<=x.reorder_at);
  const issues=S.state.alerts;
  const primary=can('invoices')?`<button class="btn" data-action="quick-bill">${icon('stock')} Quick bill</button><button class="btn primary" data-action="new" data-kind="invoices">${icon('plus')} New bill</button>`:'';
  const actions=[['payments','Record receipt'],['customers','Add customer'],[profile==='showroom'?'leads':'quotes',profile==='showroom'?'New enquiry':'New quotation'],[profile==='showroom'?'vehicles':profile==='retail'?'stock':profile==='service'?'appointments':'jobs',profile==='showroom'?'Add vehicle':profile==='retail'?'New stock item':profile==='service'?'Book service visit':'Open job card']].filter(([kind])=>can(kind));
  $('#content').innerHTML=pageHead(`Good ${new Date().getHours()<12?'morning':'afternoon'}, ${S.user.name.split(' ')[0]}.`, 'Here is what needs your attention at '+ownName(b)+'.',primary,profileChoices[profile]?.name||'YOUR BUSINESS')+
    (S.offline?'<div class="notice warning">Offline workspace · Information may be older. Only saved drafts sync later; issuing bills, posting receipts and allocating stock require the server.</div>':'')+setupChecklist()+
    `<div class="stats">${stat('Waiting to be collected',rupees(outstanding),`${owing.length-openings.length} unpaid invoices${openings.length?' + '+openings.length+' opening balances':''}`,true)}${stat('Collected today',rupees(receipts),'Receipts less refunds')}${stat(profile==='showroom'?'Open enquiries':profile==='retail'?'Stock at reorder level':'Work in progress',profile==='retail'?low.length:work.length,profile==='showroom'?'Follow-up owners and next steps':profile==='retail'?'Review before ordering':'Open work orders')}${stat('Actions due',issues.length,`${overdue.length} overdue invoices`)}</div>
    <div class="dashboard-grid"><div><section class="card priorities"><div class="card-head"><div><h2>Your next actions</h2><p>Based on saved dates, balances and work progress.</p></div><button class="btn text small" data-action="navigate" data-page="followups">View all</button></div>${issues.length?`<ul class="row-list">${issues.slice(0,5).map(alertHTML).join('')}</ul>`:empty('Nothing overdue','Add dates and next steps to enquiries, bills and jobs to see priorities here.')}</section>
    <section class="card"><div class="card-head"><div><h2>Collect what you have earned</h2><p>Oldest dates first. Open the source record for the next receipt.</p></div><span class="badge amber">${owing.length} open</span></div>${owing.length?`<div class="collection-list">${owing.slice(0,5).map(x=>`<div class="collection-row"><div class="initial-badge">${e(refLabel('customers',x.customer_id).slice(0,1))}</div><div class="grow"><button class="record-link" data-action="open" data-kind="${x.type||'invoices'}" data-id="${x.id}">${e(refLabel('customers',x.customer_id))}</button><p>${e(x.source_reference||x.number)} · ${x.due_date?'Due '+e(dateLabel(x.due_date)):'No due date'}</p></div><b class="mono">${rupees(x._balance)}</b>${can('payments')?`<button class="btn small" data-action="${x.type==='opening_balances'?'opening-payment':'invoice-payment'}" data-id="${x.id}">Receipt</button>`:''}</div>`).join('')}</div>`:empty('No outstanding balances','Issued invoices and reconciled opening balances appear here.')}</section>
    ${sectorFocus()}${profile==='showroom'?`<section class="card"><div class="card-head"><h2>Sales in motion</h2><button class="btn text small" data-action="navigate" data-page="pipeline">Pipeline</button></div>${leadBoard(work.slice(0,12))}</section>`:''}</div>
    <aside><section class="card"><div class="card-head"><h2>Start something</h2></div><div class="card-body"><div class="action-stack">${actions.map(([kind,title])=>`<button class="quick-action" data-action="new" data-kind="${kind}">${icon('plus')}<b>${title}</b></button>`).join('')}</div></div></section>
    <section class="card assistant"><div class="card-head"><div><div class="eyebrow">OWNER’S DESK</div><h2>Ask your records</h2></div>${icon('spark')}</div><div class="card-body"><p class="help-text">Your focus: ${e(b.goal||profileChoices[profile]?.focus||'Keep the business moving.')}</p><form id="assistant-form" class="assistant-question"><input name="question" placeholder="Who needs a follow-up?" aria-label="Ask your business desk" required><button class="btn dark small">Ask</button></form><div class="chips">${['Today’s priorities','Who owes us?','Stock to order'].map(q=>`<button class="chip" data-action="ask" data-question="${e(q)}">${e(q)}</button>`).join('')}</div><div id="assistant-answer"></div><p class="inline-note">Answers from saved records. Messages remain under your control.</p></div></section>
    <section class="card"><div class="card-head"><h2>${profile==='showroom'?'Vehicle stock':'Business pulse'}</h2></div><div class="card-body">${profile==='showroom'?['available','reserved','sold'].map(stage=>`<div class="summary-line"><span>${e(stage[0].toUpperCase()+stage.slice(1))}</span><b>${rows('vehicles').filter(x=>x.status===stage).length}</b></div>`).join(''):`<div class="summary-line"><span>Unanswered quotations</span><b>${rows('quotes').filter(x=>x.status==='sent').length}</b></div><div class="summary-line"><span>Low stock items</span><b>${low.length}</b></div><div class="summary-line"><span>Supplier bills due</span><b>${rows('supplier_bills').filter(x=>x._balance>0&&x.due_date<=S.state.today).length}</b></div>`}</div></section></aside></div>`;
  $('#assistant-form').onsubmit=event=>{event.preventDefault();ask(new FormData(event.target).get('question'));};
}
function leadBoard(leads) {
  const stages=['new','contacted','test_drive','quoted','booked','won','delivered','lost'].filter(stage=>leads.some(x=>x.stage===stage));
  if(!leads.length)return empty('No open enquiries','Capture the customer’s requirement and their next follow-up.');
  return `<div class="sales-board">${stages.map(stage=>`<section class="sales-column"><h3>${e(stage.replaceAll('_',' '))}<span>${leads.filter(x=>x.stage===stage).length}</span></h3>${leads.filter(x=>x.stage===stage).map(x=>`<article class="opportunity"><button class="record-link" data-action="open" data-kind="leads" data-id="${x.id}">${e(x.name)}</button><p>${e(refLabel('customers',x.customer_id))}</p><strong>${rupees(x.expected_value)}</strong><small>${e(x.next_action||'Sale complete')}</small><div>${status(x._pending?'pending sync':x.due_date<=S.state.today?'follow-up due':'scheduled')} <small>${e(dateLabel(x.due_date))}</small></div></article>`).join('')}</section>`).join('')}</div>`;
}
function vehicleCards(vehicles) {
  if(!vehicles.length)return empty('Your vehicle stock starts here','Add each chassis once. An enquiry reserves the vehicle and its invoice records the sale.',can('vehicles')?'<button class="btn primary" data-action="new" data-kind="vehicles">+ Add vehicle</button>':'');
  return `<div class="vehicle-grid">${vehicles.map(v=>`<article class="vehicle-card"><div class="vehicle-top"><span class="vehicle-symbol" aria-hidden="true">${icon('vehicles')}</span>${status(v.status)}</div><small>${e(v.condition)} · ${e(v.model_year||'Year not entered')}</small><button class="record-link" data-action="open" data-kind="vehicles" data-id="${v.id}">${e(v.name)}</button><p class="vin">${e(v.vin)}</p><div class="vehicle-price"><strong>${rupees(v.sale_price)}</strong><small>${v._age_days||0} days in stock</small></div><div class="vehicle-bottom"><span>${e(v.location||'Location to assign')}</span><button class="btn small" data-action="open" data-kind="vehicles" data-id="${v.id}">Open</button></div></article>`).join('')}</div>`;
}
function extraRecordButtons(kind,record) {
  if(record._pending)return '<span class="badge amber">Pending sync · Server actions unavailable</span>';
  const a=(title,operation)=>`<button class="btn" data-action="record-action" data-kind="${kind}" data-id="${record.id}" data-operation="${operation}">${title}</button>`;
  if(kind==='leads'&&can(kind))return (can('quotes')?a('Create / open quote','quote'):'')+
    (record.vehicle_id&&!['booked','lost','won','delivered'].includes(record.stage)?a('Reserve vehicle','reserve'):'')+
    (record.stage==='booked'?a('Release reservation','release')+(can('invoices')?a('Create / open invoice','invoice'):'')+a('Complete delivery','deliver'):'')+
    (!record.vehicle_id&&can('invoices')?a('Create / open invoice','invoice'):'');
  if(kind==='supplier_bills'&&can('supplier_payments')&&record._balance>0)return `<button class="btn primary" data-action="supplier-pay" data-id="${record.id}">Record supplier payment</button>`;
  return '';
}
function offlineSettings() {
  showDialog('Offline drafts on this device', `<form id="offline-form"><div id="form-error" class="form-error"></div><p class="help-text">Save an encrypted copy of this workspace on a device you control. Use it for customers, enquiries, quotation drafts, attendance and follow-up notes when the connection drops. Payroll and commissions are excluded. Access expires 24 hours after the last online refresh.</p><div class="notice">Your offline passphrase protects the saved copy. Keep it separate from your account password. Losing it requires clearing the device copy; sync your pending work first.</div><div class="field"><label for="offline-pass">Offline passphrase</label><input id="offline-pass" type="password" minlength="10" autocomplete="new-password" required></div></form>`, '<button class="btn" id="forget-offline">Remove saved workspace</button><button class="btn primary" type="submit" form="offline-form">Enable encrypted offline drafts</button>',false,'Works on HTTPS or this computer’s localhost address');
  $('#offline-form').onsubmit=async event=>{event.preventDefault();try{await DeskSync.enable($('#offline-pass').value);$('#editor').close();toast('Encrypted offline workspace enabled for this session and device.');}catch(error){formError(error.message);}};
  $('#forget-offline').onclick=async()=>{try{await DeskSync.forget();$('#editor').close();toast('Offline copy removed.');}catch(error){formError(error.message);}};
}
async function renderOfflineUnlock(error) {
  let accounts=[];try{accounts=await DeskSync.accounts();}catch{}
  $('#app').innerHTML=`<div class="offline-unlock"><img src="/icon.svg" alt=""><div class="eyebrow">CONNECTION UNAVAILABLE</div><h1>${accounts.length?'Open your saved workspace':'Reconnect to your business'}</h1><p>${accounts.length?'Unlock this device’s encrypted draft workspace.':'Keep the local server running or reconnect to the online service.'}</p>${accounts.length?`<form id="offline-unlock"><div class="field"><label for="offline-account">Saved account</label><select id="offline-account">${accounts.map(x=>`<option value="${e(x.id)}">${e(x.name)}</option>`).join('')}</select></div><div class="field"><label for="offline-secret">Offline passphrase</label><input id="offline-secret" type="password" required autocomplete="current-password"></div><div id="offline-error" class="form-error"></div><button class="btn primary">Unlock offline drafts</button></form>`:''}<button class="btn" data-action="reload-page">Retry connection</button></div>`;
  $('#offline-unlock')?.addEventListener('submit',async event=>{event.preventDefault();try{await DeskSync.unlock($('#offline-account').value,$('#offline-secret').value);}catch(err){$('#offline-error').textContent=err.message;}});
}
function quickCustomer(select) {
  const name=window.prompt('Customer name'); if(!name?.trim())return;
  api('record',{business_id:S.bid,kind:'customers',data:{name:name.trim(),customer_type:'Individual'}}).then(async record=>{
    S.state.records.customers.unshift(record);
    select.insertAdjacentHTML('beforeend',`<option value="${e(record.id)}">${e(record.name)}</option>`);select.value=record.id;
    select.dispatchEvent(new Event('change',{bubbles:true}));toast(record._pending?'Customer draft queued.':'Customer added. Add phone and address from Customers.');
  }).catch(error=>formError(error.message));
}
document.addEventListener('click', async event=>{
  const button=event.target.closest('[data-action]');if(!button)return;
  try{
    if(button.dataset.action==='sync')DeskSync.dialog();
    if(button.dataset.action==='customise-workspace')customiseWorkspace();
    if(button.dataset.action==='offline-settings')offlineSettings();
    if(button.dataset.action==='quick-customer')quickCustomer($('#field-customer_id'));
    if(button.dataset.action==='supplier-pay'){const bill=find('supplier_bills',button.dataset.id);editRecord('supplier_payments','',{supplier_bill_id:bill.id,amount:bill._balance});}
  }catch(error){toast(error.message,true);}
});
