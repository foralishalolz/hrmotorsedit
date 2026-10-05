'use strict';

const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const e = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = value => Number(value || 0).toLocaleString(indian()?'en-IN':'en-NP', {minimumFractionDigits:2, maximumFractionDigits:2});
const rupees = value => `${currency()} ${fmt(value)}`;
const count = value => Number(value || 0).toLocaleString(indian()?'en-IN':'en-NP', {maximumFractionDigits:3});
const addDays = (iso, days) => { const d = new Date(iso+'T12:00:00Z'); d.setUTCDate(d.getUTCDate()+Number(days)); return d.toISOString().slice(0,10); };
const dateLabel = iso => iso ? new Date(iso+'T12:00:00Z').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'}) : '—';
const label = record => record?.name || record?.subject || record?.number || record?.reference || record?.issuer || record?.task || record?.date || 'Untitled';
const S = {user:null,csrf:'',businesses:[],bid:'',state:null,page:'today',tab:'',query:'',filter:'',listQuery:'',board:false,reportStart:'',reportEnd:'',accounts:[]};
let dialogCleanup = null;

const sections = {
  today:{name:'Today',icon:'◷',hint:'Your business at a glance'},
  sales:{name:'Quotations',icon:'▤',tabs:['quotes','services'],hint:'Estimate quickly, record approval, and turn it into work.'},
  workshop:{name:'Jobs & bookings',icon:'▦',tabs:['jobs','appointments','contracts','assets'],hint:'Keep every job, delivery promise, and service visit connected.'},
  customers:{name:'Customers',icon:'♧',tabs:['customers'],hint:'A complete local history for every customer.'},
  insurance:{name:'Insurance',icon:'◇',tabs:['claims','external_quotes'],hint:'Track approvals, original comparison documents, and settlement follow-ups.'},
  money:{name:'Money',icon:'◈',tabs:['invoices','payments','credits','expenses','allocations'],hint:'Know what was billed, collected, credited, and spent.'},
  stock:{name:'Stock & suppliers',icon:'▣',tabs:['stock','purchases','movements','suppliers'],hint:'Order what you need and issue materials against actual jobs.'},
  team:{name:'Team & payroll',icon:'♙',tabs:['employees','attendance','time_entries','commissions','payroll'],hint:'Attendance, task time, incentives, and reviewed payroll in one place.'},
  followups:{name:'Follow-ups',icon:'↗',tabs:['followups'],hint:'A dated next step, a responsible person, and a clear outcome.'},
  reports:{name:'Reports',icon:'▥',hint:'Read your numbers with the underlying records.'},
  settings:{name:'Settings',icon:'⚙',hint:'Business profile, local accounts, and backups.'},
};
const m = (name,singular,fields,columns,defaults={}) => ({name,singular,fields,columns,defaults});
const models = {
  customers:m('Customers','customer',[
    ['name','Customer name','text'],['customer_type','Customer type','select',['Individual','Business','Fleet','Insurer']],['phone','Phone','tel'],['email','Email','email'],['pan','PAN / VAT number','text'],['address','Address','text'],['contact_person','Contact person','text'],['preferred_channel','Preferred follow-up','select',['Phone','SMS','WhatsApp','Email','In person']],['notes','Notes','textarea'],
  ],['name','phone','customer_type','balance'],{customer_type:'Individual',preferred_channel:'Phone'}),
  assets:m('Vehicles & assets','asset',[
    ['name','Vehicle / equipment name','text'],['customer_id','Customer','ref','customers'],['asset_type','Type','select',['Vehicle','Motorcycle','Equipment','Appliance','Property','Other']],['registration','Registration / asset ID','text'],['chassis','Chassis / serial number','text'],['odometer','Odometer / usage','number'],['color','Colour / specification','text'],['notes','History / notes','textarea'],
  ],['name','customer_id','registration','asset_type'],{asset_type:'Vehicle'}),
  services:m('Service catalogue','service',[
    ['name','Service name','text'],['category','Category','select',['Labour','Part','Material','Service','Subcontract']],['unit','Unit','text'],['rate','Selling rate, NPR','number'],['cost','Estimated unit cost, NPR','owner-number'],['notes','Scope / notes','textarea'],
  ],['name','category','unit','rate'],{category:'Service',unit:'job',rate:0,cost:0}),
  quotes:m('Quotations','quotation',[],['number','customer_id','subject','total','status'],{status:'draft'}),
  invoices:m('Invoices','invoice',[],['number','customer_id','total','_paid','_balance','status'],{status:'draft'}),
  jobs:m('Job cards','job',[
    ['name','Job / work title','text'],['customer_id','Customer','ref','customers'],['asset_id','Vehicle / asset','ref','assets'],['quote_id','Approved quotation','ref','quotes'],['date','Opened, AD','date'],['due_date','Promised delivery, AD','date'],['stage','Work stage','stages'],['bay','Bay / work area','text'],['employee_ids','Assigned team','multi','employees'],['blocker','What is holding this job up?','text'],['labor_cost','Labour cost override, NPR','owner-number',null,'Leave 0 to use recorded task hours × the hourly cost saved when each timer started.'],['additional_material_cost','Other materials, NPR','owner-number',null,'Exclude stock already issued to this job.'],['subcontract_cost','Subcontract cost, NPR','owner-number'],['costs_final','All direct costs have been checked','owner-checkbox'],['notes','Work notes / customer instructions','textarea'],
  ],['number','name','customer_id','stage','due_date'],{stage:'Intake',labor_cost:0,additional_material_cost:0,subcontract_cost:0,employee_ids:[],tasks:[],costs_final:false}),
  claims:m('Insurance claims','claim',[
    ['name','Claim title','text'],['reference','Claim reference','text'],['customer_id','Customer','ref','customers'],['job_id','Linked job','ref','jobs'],['insurer','Insurer','text'],['policy_number','Policy number','text'],['surveyor','Surveyor / contact','text'],['contact_phone','Insurer / surveyor phone','tel'],['status','Claim stage','select',['documents_pending','submitted','survey_scheduled','approval_pending','approved','repairing','awaiting_settlement','settled','closed']],['requested','Requested total including VAT, NPR','number'],['approved','Approved by insurer, NPR','number'],['customer_share','Expected customer share, NPR','number'],['insurer_share','Expected insurer share, NPR','number'],['due_date','Next follow-up, AD','date'],['next_action','Next action','text'],['notes','Excess, depreciation, supplements / notes','textarea'],
  ],['reference','insurer','job_id','approved','due_date','status'],{status:'documents_pending',requested:0,approved:0,customer_share:0,insurer_share:0}),
  external_quotes:m('Comparison quotations','comparison',[],['issuer','quote_id','total','source','date']),
  payments:m('Receipts & refunds','payment',[
    ['invoice_id','Issued invoice (blank = customer advance)','ref','invoices'],['customer_id','Customer (required for an advance)','ref','customers'],['claim_id','Insurance claim, if relevant','ref','claims'],['direction','Entry type','select',['receipt','refund']],['amount','Amount, NPR','number'],['date','Received / refunded, AD','date'],['method','Payment method','select',['Cash','Bank transfer','Cheque','Digital wallet','Other']],['payer_type','Paid by / refunded to','select',['Customer','Insurer','Other']],['payer','Payer / recipient name','text'],['reference','Bank / cheque / wallet reference','text'],['notes','Notes','textarea'],
  ],['number','invoice_id','amount','method','date','direction'],{direction:'receipt',method:'Cash',payer_type:'Customer'}),
  credits:m('Credit notes','credit note',[
    ['invoice_id','Issued invoice','ref','invoices'],['amount','Credit amount including VAT, NPR','number'],['date','Credit date, AD','date'],['reason','Reason for this credit','textarea'],
  ],['number','invoice_id','amount','reason','date']),
  expenses:m('Expenses & advances','expense',[
    ['name','Expense title','text'],['category','Category','select',['Rent','Utilities','Fuel','Parts','Subcontract','Tools','Marketing','Staff advance','Other']],['amount','Amount paid, NPR','number'],['date','Paid on, AD','date'],['job_id','Direct job cost (optional)','ref','jobs'],['employee_id','Employee (for a staff advance)','ref','employees'],['supplier_id','Supplier (optional)','ref','suppliers'],['method','Paid through','select',['Cash','Bank transfer','Digital wallet','Other']],['reference','Receipt / reference','text'],['notes','Notes / purpose','textarea'],
  ],['name','category','amount','job_id','date'],{category:'Other',method:'Cash'}),
  suppliers:m('Suppliers','supplier',[
    ['name','Supplier name','text'],['contact_person','Contact person','text'],['phone','Phone','tel'],['email','Email','email'],['pan','PAN / VAT number','text'],['address','Address','text'],['terms','Payment / delivery terms','textarea'],['notes','Notes','textarea'],
  ],['name','contact_person','phone','pan']),
  stock:m('Stock items','stock item',[
    ['name','Item name','text'],['sku','SKU / part number','text'],['unit','Unit','text'],['opening_qty','Opening quantity','number',null,'Once saved, use a movement to correct quantity.'],['cost','Default purchase / issue cost, NPR','number'],['rate','Selling rate, NPR','number'],['reorder_at','Reorder at or below','number'],['location','Shelf / location','text'],['supplier_id','Preferred supplier','ref','suppliers'],['notes','Notes','textarea'],
  ],['name','sku','_quantity','unit','reorder_at','cost'],{unit:'pc',opening_qty:0,cost:0,rate:0,reorder_at:0}),
  movements:m('Stock ledger','movement',[
    ['item_id','Stock item','ref','stock'],['kind','Movement','select',['receipt','issue','return','adjustment']],['qty','Quantity (negative only for an adjustment)','signed-number'],['unit_cost','Unit cost, NPR','number'],['job_id','Job (for use / return)','ref','jobs'],['supplier_id','Supplier (for receipt)','ref','suppliers'],['date','Movement date, AD','date'],['notes','Reason / delivery reference','textarea'],
  ],['item_id','kind','qty','job_id','date'],{kind:'receipt',qty:1,unit_cost:0}),
  purchases:m('Purchase orders','purchase order',[],['number','supplier_id','total','expected_date','status'],{status:'ordered'}),
  employees:m('Employees & beneficiaries','employee',[
    ['name','Name','text'],['role','Job title / function','text'],['phone','Phone','tel'],['start_date','Joining date, AD','date'],['active','Active','checkbox'],['salary_type','Pay basis','owner-select',['monthly','daily','hourly']],['base_salary','Pay per month / day / hour, NPR','owner-number'],['hourly_cost','Hourly job costing rate, NPR','owner-number'],['overtime_rate','Overtime rate per hour, NPR','owner-number'],['shift_hours','Normal shift hours','number'],['employee_percent','Employee contribution rate, %','owner-number',null,'Owner configured. Confirm the applicable basis and rates before payroll.'],['employer_percent','Employer contribution rate, %','owner-number'],['notes','Employment / payment notes','textarea'],
  ],['name','role','phone','active'],{active:true,salary_type:'monthly',base_salary:0,hourly_cost:0,overtime_rate:0,shift_hours:8,employee_percent:0,employer_percent:0}),
  attendance:m('Attendance','attendance',[
    ['employee_id','Employee','ref','employees'],['date','Shift date, AD','date'],['in_time','Clock in','time'],['out_time','Clock out','time'],['break_minutes','Unpaid break, minutes','number'],['overnight','Shift ends the following day','checkbox'],['status','Review status','select',['pending','approved','leave','absent']],['notes','Leave / correction / missing punch notes','textarea'],
  ],['employee_id','date','in_time','out_time','hours','status'],{break_minutes:0,overnight:false,status:'pending'}),
  time_entries:m('Task timers','task timer',[],['employee_id','job_id','task','start_at','hours','timer_status']),
  commissions:m('Commissions & incentives','commission',[
    ['name','Earning / commission title','text'],['employee_id','Beneficiary','ref','employees'],['job_id','Linked job','ref','jobs'],['date','Earned on, AD','date'],['basis','Calculation basis','select',['Net labour revenue','Net service revenue','Job contribution','Fixed referral','Other agreed basis']],['basis_amount','Agreed basis amount excluding VAT, NPR','number'],['percent','Commission rate, %','number'],['fixed_amount','Additional fixed amount, NPR','number'],['collection_required','Pay only when linked job invoices are collected','checkbox'],['notes','Agreement / allocation notes','textarea'],
  ],['name','employee_id','amount','_eligible','status'],{basis:'Net labour revenue',basis_amount:0,percent:0,fixed_amount:0,collection_required:true,status:'earned'}),
  payroll:m('Payroll runs','payroll run',[],['number','start_date','end_date','total_net','total_cost','status']),
  followups:m('Follow-up tasks','follow-up',[
    ['name','Task / follow-up title','text'],['customer_id','Customer (optional)','ref','customers'],['job_id','Job (optional)','ref','jobs'],['employee_id','Responsible employee (optional)','ref','employees'],['date','Last action, AD','date'],['due_date','Next action due, AD','date'],['channel','Follow-up channel','select',['Phone','SMS','WhatsApp','Email','In person','Internal']],['status','Status','select',['open','waiting','completed']],['next_action','Next step / expected outcome','text'],['notes','Contact outcome / notes','textarea'],
  ],['name','customer_id','employee_id','due_date','status'],{status:'open',channel:'Internal'}),
  appointments:m('Appointments','appointment',[
    ['name','Appointment title','text'],['customer_id','Customer','ref','customers'],['asset_id','Vehicle / asset','ref','assets'],['date','Visit date, AD','date'],['time','Arrival time','time'],['duration_minutes','Reserved duration, minutes','number'],['bay','Bay / service area','text'],['employee_id','Assigned employee','ref','employees'],['status','Status','select',['booked','confirmed','arrived','completed','cancelled']],['notes','Service request / notes','textarea'],
  ],['name','customer_id','date','time','bay','status'],{status:'booked',duration_minutes:60}),
  contracts:m('Service agreements','service agreement',[
    ['name','Agreement title','text'],['customer_id','Customer','ref','customers'],['asset_id','Vehicle / asset','ref','assets'],['start_date','Start date, AD','date'],['expiry_date','Renewal / expiry, AD','date'],['visit_interval_days','Service interval, days','number'],['status','Status','select',['active','renewal_pending','closed']],['terms','Scope / limits / billing terms','textarea'],['notes','Notes','textarea'],
  ],['name','customer_id','expiry_date','status'],{status:'active',visit_interval_days:90}),
  allocations:m('Advance allocations','allocation',[],['number','payment_id','invoice_id','amount','date']),
};
const headers = {name:'Name',number:'Reference',subject:'Scope',customer_id:'Customer',employee_id:'Employee',job_id:'Job',quote_id:'Own quotation',invoice_id:'Invoice',supplier_id:'Supplier',item_id:'Stock item',payment_id:'Advance receipt',_quantity:'Available',_paid:'Net paid',_balance:'Outstanding',_eligible:'Collection eligible',reorder_at:'Reorder at',cost:'Unit cost',rate:'Rate',total:'Total, NPR',amount:'Amount, NPR',total_net:'Net pay, NPR',total_cost:'Employer cost',due_date:'Due / follow-up',expected_date:'Expected',start_date:'From',end_date:'To',date:'Date',registration:'Registration / ID',asset_type:'Type',customer_type:'Type',status:'Status',source:'Source',kind:'Movement',qty:'Quantity',in_time:'In',out_time:'Out',timer_status:'Timer',start_at:'Started',approved:'Approved, NPR',active:'Active',reference:'Reference',issuer:'Issuer / scenario',insurer:'Insurer',phone:'Phone',role:'Function',pan:'PAN / VAT',contact_person:'Contact',unit:'Unit',method:'Method',direction:'Entry',hours:'Hours',task:'Task',bay:'Work area',time:'Time',category:'Category',reason:'Reason'};
const refs = {customer_id:'customers',employee_id:'employees',job_id:'jobs',quote_id:'quotes',invoice_id:'invoices',supplier_id:'suppliers',item_id:'stock',payment_id:'payments'};
const immutable = new Set(['payments','credits','movements','time_entries','allocations','payroll']);
const required = {customers:['name'],assets:['name','customer_id'],services:['name'],jobs:['name','customer_id'],claims:['name','insurer'],payments:['amount','date'],credits:['invoice_id','amount','reason'],expenses:['name','amount','date'],suppliers:['name'],stock:['name'],movements:['item_id','qty'],employees:['name'],attendance:['employee_id','date'],commissions:['name','employee_id'],followups:['name','due_date'],appointments:['name','customer_id','date','time'],contracts:['name','customer_id','expiry_date']};

function rows(kind) { return S.state?.records?.[kind] || []; }
function find(kind,id) { return indexedRecord(kind,id); }
function refLabel(kind,id) { return id ? label(find(kind,id)) : '—'; }
function can(kind) { return !!S.state?.permissions?.write?.includes(kind); }
function owner() { return S.user?.role==='owner'; }
function activeKind() { return S.tab || sections[S.page]?.tabs?.find(k=>S.state?.permissions.read.includes(k)); }
function status(value) {
  const text=String(value || '').replaceAll('_',' ');
  const color=/^(accepted|issued|paid|approved|received|completed|active|Ready|Delivered|settled)$/i.test(value)?'green':/^(declined|absent|cancelled|closed|refund)$/i.test(value)?'red':/^(sent|pending|earned|partial|waiting|awaiting|documents|approval|renewal)/i.test(value)?'amber':'blue';
  return `<span class="badge ${color}">${e(text || 'draft')}</span>`;
}
function toast(message,error=false) {
  const node=document.createElement('div'); node.className='toast'+(error?' error':'');
  const text=document.createElement('span');text.textContent=message;
  const dismiss=document.createElement('button');dismiss.type='button';dismiss.className='icon-button';dismiss.setAttribute('aria-label','Dismiss notification');dismiss.textContent='×';dismiss.onclick=()=>node.remove();
  node.append(text,dismiss);$('#toasts').replaceChildren(node);setTimeout(()=>node.remove(),error?9000:5500);
}
async function api(path,data) { return DeskSync.request(path,data); }
async function rawApi(path,data) {
  const response=await fetch('/api/'+path,{credentials:'same-origin',headers:data===undefined?{}:{'Content-Type':'application/json','X-CSRF-Token':S.csrf},method:data===undefined?'GET':'POST',body:data===undefined?undefined:JSON.stringify(data)});
  let result;
  if (response.headers.get('Content-Type')?.includes('application/json')) result=await response.json();
  else result=await response.blob();
  if (!response.ok) {
    if (response.status===401 && !['login','setup'].includes(path)) { S.needsLogin=true; renderAuth(false); }
    const error=new Error(result.error || 'Could not complete the operation.'); error.status=response.status; throw error;
  }
  return result;
}
async function reload() {
  S.state=await DeskSync.state();
  S.businesses=S.businesses.map(x=>x.id===S.bid?S.state.business:x);
  if (S.tab && !S.state.permissions.read.includes(S.tab)) S.tab='';
  renderShell();
}
async function loadBusinesses() {
  DeskSync.setUser(S.user);
  S.businesses=await api('businesses');
  const saved=localStorage.getItem('bd_business_'+S.user.id);
  const requested=new URLSearchParams(location.search).get('business');
  S.bid=S.businesses.find(x=>x.id===(S.bid||requested||saved))?.id || S.businesses[0]?.id || '';
  if (!S.bid) { S.state=null; renderNoBusiness(); return; }
  localStorage.setItem('bd_business_'+S.user.id,S.bid);
  await reload();
}
async function init() {
  try {
    const health=await api('health'); S.health=health;
    if (health.user) { S.user=health.user; S.csrf=health.csrf; await loadBusinesses(); }
    else renderAuth(health.setup_required);
  } catch(error) {
    await renderOfflineUnlock(error);
  }
}
function renderAuth(setup) {
  $('#app').innerHTML=`<div class="auth-wrap"><section class="auth-info"><div class="brand"><img src="/icon.svg" alt=""><div>Business Desk<small>YOUR BUSINESS, CONNECTED.</small></div></div><h1>Less chasing.<br><span>More getting done.</span></h1><p>From the first quotation to the final collection. A practical desk for garages, service teams, and local businesses.</p><div class="auth-feature"><span>✓</span> Quotes, job cards, and VAT bills</div><div class="auth-feature"><span>✓</span> Stock, attendance, commissions, and payroll</div><div class="auth-feature"><span>✓</span> Enquiries, collections and daily follow-ups</div></section><section class="auth-form-wrap"><form id="auth-form" class="auth-form"><div class="eyebrow">${setup?'FIRST-TIME SETUP':'WELCOME BACK'}</div><h2>${setup?'Create your owner account':'Open your business desk'}</h2><p>${setup?'This owner account manages your business and staff access.':'Sign in to your business workspace.'}</p><div class="form-error" id="auth-error"></div>${setup?`<div class="field"><label for="owner-name">Your name</label><input id="owner-name" name="name" required autocomplete="name"></div>`:''}${setup&&S.health?.setup_key_required?'<div class="field"><label for="setup-key">Server setup key</label><input id="setup-key" name="setup_key" type="password" required autocomplete="off"></div>':''}<div class="field"><label for="username">Username</label><input id="username" name="username" required autocomplete="username" autocapitalize="none"></div><div class="field"><label for="password">Password</label><input id="password" name="password" type="password" required minlength="${setup?12:8}" autocomplete="${setup?'new-password':'current-password'}"><small>${setup?'At least 12 characters. Keep it safe; there is no cloud password recovery.':''}</small></div><button class="btn primary" type="submit">${setup?'Create owner account':'Sign in'} <span>→</span></button><div class="auth-foot">Business Desk · Local or private server workspace</div></form></section></div>`;
  if(S.health?.cloud&&S.health.registration_enabled){$('#auth-form').insertAdjacentHTML('beforeend',`<button class="btn auth-register" type="button" id="auth-register">${setup?'Back to sign in':'Register your business with an invite'}</button>`);$('#auth-register').onclick=()=>renderAuth(!setup);}
  $('#auth-form').addEventListener('submit',async event=>{
    event.preventDefault(); const button=$('button',event.target); button.disabled=true;
    try { const result=await api(setup?'setup':'login',Object.fromEntries(new FormData(event.target))); S.user=result.user; S.csrf=result.csrf; S.page='today'; S.tab=''; await loadBusinesses(); }
    catch(error) { $('#auth-error').textContent=error.message; }
    finally { button.disabled=false; }
  });
}
function renderNoBusiness() {
  $('#app').innerHTML=`<div class="setup-page"><div class="brand"><img src="/icon.svg" alt="">Business Desk</div><div class="card"><div class="card-body"><div class="eyebrow">LET'S SET UP YOUR BUSINESS</div><h1>Make this desk yours.</h1><p class="muted" style="margin:15px 0 24px">Choose your sector, billing preferences, and what you want to keep on top of. You can manage several businesses separately.</p>${owner()?'<button class="btn primary" data-action="new-business">Set up a business →</button>':'<div class="notice">Ask the owner to assign a business to your account.</div>'}<button class="btn text" data-action="logout">Sign out</button></div></div></div>`;
}
function visibleSections() { return enabledSections(); }
function renderShell() {
  applyBusinessExperience();
  const b=S.state.business; if(!visibleSections().some(([key])=>key===S.page)){S.page='today';S.tab='';} const section=sections[S.page] || sections.today;
  if (!visibleSections().some(([key])=>key===S.page)) { S.page='today'; S.tab=''; }
  $('#app').innerHTML=`<div class="layout"><aside class="sidebar"><div class="brand"><img src="${e(ownIcon(b))}" alt=""><div>${e(ownName(b))}<small>${e(b.speciality||profileChoices[b.profile]?.name||'Business workspace')}</small></div></div><label class="sr-only" for="business-picker" hidden>Active business</label><select id="business-picker" class="business-picker" aria-label="Active business">${S.businesses.map(x=>`<option value="${e(x.id)}" ${x.id===S.bid?'selected':''}>${e(ownName(x))}</option>`).join('')}</select><div class="nav-label">Workspace</div><nav aria-label="Main navigation">${visibleSections().filter(([key])=>key!=='settings').map(([key,value])=>`<button class="nav-button ${key===S.page?'active':''}" data-action="navigate" data-page="${key}"><span class="icon" aria-hidden="true">${value.icon}</span>${value.name}${key==='today'&&S.state.alerts.length?`<span class="nav-count">${S.state.alerts.length}</span>`:''}</button>`).join('')}</nav><div class="sidebar-bottom"><button class="nav-button ${S.page==='settings'?'active':''}" data-action="navigate" data-page="settings">${icon('settings')}Settings & backups</button><div class="plan-label">Free pilot <small>No charges</small></div><div class="local-pill"><span class="dot"></span>${S.health?.hosted?'Connected to your server':'Local business server'}</div><div class="profile"><span class="avatar">${e(S.user.name.slice(0,1).toUpperCase())}</span><div class="profile-text"><b>${e(S.user.name)}</b><small>${e(S.user.role)}</small></div><button class="icon-button" data-action="logout" title="Sign out" aria-label="Sign out">${icon('logout')}</button></div></div></aside><div class="workspace"><header class="topbar"><button class="icon-button mobile-menu" data-action="mobile-menu" aria-label="Toggle navigation">${icon('menu')}</button><div class="crumb">${e(ownName(b))} <span class="muted"> / </span> <strong>${e(section.name)}</strong></div><div class="topbar-tools"><button class="icon-button command-button" data-action="command" aria-label="Open command search" title="Search · Ctrl / Command K">${icon('command')}</button><label class="searchbox">${icon('search')}<input id="global-search" value="${e(S.query)}" placeholder="Search your business…" aria-label="Search records"><span class="kbd">/</span></label><button id="sync-indicator" class="sync-indicator" data-action="sync">Synced</button><span class="today-chip">${e(dateLabel(S.state.today))}</span><button class="btn small" data-action="refresh" title="Refresh records">${icon('refresh')} Refresh</button></div></header><main id="content" class="content"></main><nav class="mobile-tabs" aria-label="Quick navigation">${['today','customers','money','followups'].filter(key=>visibleSections().some(([k])=>key===k)).map(key=>`<button class="${S.page===key?'active':''}" data-action="navigate" data-page="${key}">${icon(key)}<span>${{today:'Home',customers:'Clients',money:'Billing',followups:'Actions'}[key]}</span></button>`).join('')}</nav></div></div>`;
  $('#business-picker').addEventListener('change',async event=>{S.bid=event.target.value; S.query=''; S.filter=''; S.listQuery=''; localStorage.setItem('bd_business_'+S.user.id,S.bid); try {await reload();} catch(error){toast(error.message,true);} });
  $('#global-search').addEventListener('input',event=>{S.query=event.target.value; renderContent();});
  applyOwnedIdentity();renderContent(); DeskSync.updateIndicator();
}
function pageHead(title,description,actions='',eyebrow='WORKSPACE') { return `<div class="pagehead"><div><div class="eyebrow">${eyebrow}</div><h1>${e(title)}</h1><p>${e(description)}</p></div><div class="actions">${actions}</div></div>`; }
function stat(title,value,note='',accent=false) {
  const money=String(value).match(/^(NPR|INR)\s(.+)$/);
  const display=money?`<small class="stat-currency">${e(money[1])}</small><span class="stat-amount ${money[2].length>13?'compact':''}">${e(money[2])}</span>`:e(value);
  return `<div class="stat ${accent?'accent':''}"><div class="stat-label">${e(localLabel(title))}</div><div class="stat-value mono">${display}</div><div class="stat-note">${e(note)}</div></div>`;
}
function empty(title,text,button='') {return `<div class="empty"><div class="empty-icon">▤</div><h3>${e(title)}</h3><p>${e(text)}</p>${button}</div>`;}
function renderContent() {
  if (S.query.trim()) { renderSearch(); return; }
  if (S.page==='today') {renderToday();$('#content').insertAdjacentHTML('afterbegin',studioSetupBanner());}
  else if (S.page==='settings') renderSettings();
  else if (S.page==='reports') renderReports();
  else renderList();
}
function renderToday() { renderWorkspaceToday(); }
function alertHTML(alert) {return `<li class="alert-row"><span class="alert-icon ${alert.priority===1?'urgent':''}" aria-hidden="true">${alert.priority===1?'!':'↗'}</span><div class="alert-text"><b>${e(alert.title)}</b><p>${e(alert.detail)}</p><small>${e(alert.last_note || alert.next_action)}</small></div><div class="actions"><button class="btn small" data-action="open" data-kind="${e(alert.type)}" data-id="${e(alert.record_id)}">Open</button>${can('followups')?`<button class="btn text small" data-action="follow-alert" data-key="${e(alert.key)}">Follow up</button>`:''}</div></li>`;}
function renderSearch() {
  const q=S.query.toLowerCase().trim();const results=[];
  Object.entries(S.state.records).forEach(([kind,list])=>list.forEach(record=>{
    const values=Object.entries(record).filter(([key,value])=>!key.startsWith('_')&&typeof value==='string'&&!/^(id|.*_id|.*_at)$/.test(key)).map(([,value])=>value).join(' ').toLowerCase();
    if (values.includes(q)||label(record).toLowerCase().includes(q)) results.push({kind,record});
  }));
  $('#content').innerHTML=pageHead('Search your business',`${results.length} matching records for “${S.query}”`,'','SEARCH')+`<div class="card">${results.length?results.slice(0,100).map(({kind,record})=>`<div class="search-result"><div><button class="record-link" data-action="open" data-kind="${kind}" data-id="${record.id}">${e(label(record))}</button><div class="cell-sub">${e(models[kind]?.name||kind)} · ${e(record.number||record.date||'')}</div></div>${record.status?status(record.status):''}</div>`).join(''):empty('No records found','Try a customer, vehicle registration, invoice reference, or job title.')}</div>`;
}
function valueCell(kind,record,key) {
  if (key==='balance') { const amount=customerMetrics(record).balance; return `<span class="mono ${amount<0?'negative':''}">${rupees(amount)}</span>`; }
  if(key==='_source_changed')return status(record[key]?'Review needed':'Current');
  if (refs[key]) return e(refLabel(refs[key],record[key]));
  if (key==='total') return fmt(record._totals?.total??record.total);
  if (key==='source') return status(record.simulation?'Hypothetical':'Original issuer');
  if (key==='timer_status') return status(record.end_at?'completed':'running');
  if (key==='active') return status(record[key]?'active':'inactive');
  if (['status','stage','direction','kind'].includes(key)) return status(record[key]);
  if (key.endsWith('_date')||key==='date') return e(dateLabel(record[key]));
  if (key==='start_at') return e(record[key]?new Date(record[key]).toLocaleString('en-GB',{timeZone:'Asia/Kathmandu',month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}):'—');
  if (['rate','cost','amount','_paid','_balance','_eligible','total_net','total_cost','approved','opening_float','expected_cash','counted_cash','variance'].includes(key)) return `<span class="mono ${record[key]<0?'negative':''}">${fmt(record[key])}</span>`;
  if (['_quantity','qty','reorder_at','hours'].includes(key)) return count(record[key]);
  return e(record[key]??'—');
}
function moduleNotice(kind) {
  const messages={supplier_bills:'Record the supplier document and its due date here. Stock enters separately through a purchase-order receipt or stock movement, so a bill cannot receive the same goods twice.',supplier_payments:'Record an actual payment against a supplier bill. It reduces that bill’s balance and does not send a bank transfer.',leads:'Open enquiries need a dated next action. Reserve a specific vehicle before invoicing it; delivery checks collection and handover.',vehicles:'Each chassis is unique. Availability changes through the enquiry reservation and invoice workflow.',external_quotes:'Attach the actual issuer’s document for independent comparisons. Hypothetical scenarios stay visibly labelled on screen and print.',commissions:'Earning = agreed basis × percentage + fixed amount. The eligible amount follows net collections of the linked job. Approve the agreement before payment.',payroll:'Prepare → review → approve → record payment. Pay units, overtime, contribution basis, and withholding are owner reviewed. No automatic statutory tax calculation.',movements:'Quantity changes use retained ledger entries. Issues cannot take stock below zero; returns and adjustments correct actual quantities.',payments:'Receipts, refunds, and advances are retained. Allocate a customer advance to that same customer’s issued invoice from the receipt details.',claims:'Expected customer and insurer shares are tracked separately. Link receipts to this claim to see settlement progress.',contracts:'Renewal alerts appear 30 days before expiry. Use appointments to reserve individual service visits.',attendance:'Clock-in/out and breaks calculate hours. Overnight shifts are supported. Approve attendance before using it as a payroll suggestion.'};
  return messages[kind]?`<div class="notice ${['external_quotes','payroll'].includes(kind)?'warning':''}">${e(messages[kind])}</div>`:'';
}
function renderList() {
  const section=sections[S.page]; const tabs=section.tabs.filter(k=>S.state.permissions.read.includes(k));
  if (!tabs.includes(S.tab)) S.tab=tabs[0];
  const kind=S.tab, model=models[kind];
  let list=rows(kind).filter(x=>!S.filter||String(x.status||x.stage||x.kind||x.direction||'draft')===S.filter);
  if (S.listQuery.trim()) { const q=S.listQuery.toLowerCase(); list=list.filter(x=>(Object.values(x).filter(v=>typeof v==='string').join(' ')+' '+Object.entries(refs).map(([key,ref])=>refLabel(ref,x[key])).join(' ')).toLowerCase().includes(q)); }
  const segment=kind==='customers'?customerSegments(list):null;if(segment)list=segment.list;
  const statuses=[...new Set(rows(kind).map(x=>x.status||x.stage||x.kind||x.direction).filter(Boolean))].sort();
  let primary=kind==='stock'&&can('movements')?'<button class="btn" data-action="stock-count">'+icon('stock')+' Count stock</button>':'';
  if (can(kind)&&!['allocations'].includes(kind)) primary+=`<button class="btn primary" data-action="${kind==='time_entries'?'timer':kind==='payroll'?'payroll':'new'}" data-kind="${kind}">+ ${kind==='time_entries'?'Start / stop task':kind==='payroll'?'Prepare payroll':'New '+model.singular}</button>`;
  $('#content').innerHTML=pageHead(section.name,section.hint,primary)+`<div class="tabs" role="tablist">${tabs.map(k=>`<button class="tab ${kind===k?'active':''}" data-action="tab" data-kind="${k}" role="tab" aria-selected="${kind===k}">${e(models[k].name)} <small>(${rows(k).length})</small></button>`).join('')}</div>`+moduleNotice(kind)+(segment?.html||'')+
    (kind==='followups'?`<div class="card"><div class="card-head"><div><h2>Actions generated from your business</h2><p>Unresolved issues return when their next action is due.</p></div><span class="badge amber">${S.state.alerts.length} due</span></div>${S.state.alerts.length?`<ul class="row-list">${S.state.alerts.slice(0,20).map(alertHTML).join('')}</ul>`:empty('No due actions','Your saved follow-up dates and record conditions drive this list.')}</div>`:'')+
    `<div class="card"><div class="filterbar"><div class="actions"><input class="filter-input" id="list-search" value="${e(S.listQuery)}" placeholder="Search ${e(model.name.toLowerCase())}…" aria-label="Search this list">${statuses.length?`<select class="filter-input" id="status-filter" aria-label="Filter by status"><option value="">All statuses</option>${statuses.map(v=>`<option value="${e(v)}" ${S.filter===v?'selected':''}>${e(String(v).replaceAll('_',' '))}</option>`).join('')}</select>`:''}</div><div class="actions">${['jobs','leads'].includes(kind)?`<button class="btn small" data-action="board">${S.board?'Table view':'Board view'}</button>`:''}<button class="btn small" data-action="csv" data-kind="${kind}">↓ CSV</button><span class="muted"><small>${list.length} records</small></span></div></div><div id="list-data">${S.board&&kind==='leads'?leadBoard(list):kind==='jobs'&&S.board?boardHTML(list):tableHTML(kind,list)}</div></div>`;
  $('#list-search').addEventListener('input',event=>{S.listQuery=event.target.value; const q=S.listQuery.toLowerCase();const filtered=rows(kind).filter(x=>(!S.filter||String(x.status||x.stage||x.kind||x.direction||'draft')===S.filter)&&(!q||(Object.values(x).filter(v=>typeof v==='string').join(' ')+' '+Object.entries(refs).map(([key,ref])=>refLabel(ref,x[key])).join(' ')).toLowerCase().includes(q)));$('#list-data').innerHTML=S.board&&kind==='leads'?leadBoard(filtered):kind==='jobs'&&S.board?boardHTML(filtered):tableHTML(kind,kind==='customers'?customerSegments(filtered).list:filtered);});
  $('#status-filter')?.addEventListener('change',event=>{S.filter=event.target.value;renderContent();});
}
function fullTableHTML(kind,list) {
  const model=models[kind];
  if(kind==='vehicles')return vehicleCards(list);
  if (!list.length) return empty(`No ${model.name.toLowerCase()} here yet`,`Add a ${model.singular} to start connecting your business records.`,can(kind)&&!immutable.has(kind)?`<button class="btn" data-action="new" data-kind="${kind}">+ New ${model.singular}</button>`:'');
  return `<div class="table-wrap"><table><thead><tr>${model.columns.map(key=>`<th class="${['total','amount','_paid','_balance','_eligible','rate','cost','total_net','total_cost'].includes(key)?'num':''}">${e(localLabel(headers[key]||key))}</th>`).join('')}<th></th></tr></thead><tbody>${list.map(record=>`<tr>${model.columns.map((key,index)=>`<td class="${['total','amount','_paid','_balance','_eligible','rate','cost','total_net','total_cost'].includes(key)?'num':''}">${index===0?`<button class="record-link" data-action="open" data-kind="${kind}" data-id="${record.id}">${valueCell(kind,record,key)}</button>${kind==='quotes'?`<div class="cell-sub">${e(record.number?'Revision '+(record.revision||1):'Saved draft')} · ${e(dateLabel(record.date))}</div>`:''}`:valueCell(kind,record,key)}</td>`).join('')}<td class="num"><button class="btn small" data-action="open" data-kind="${kind}" data-id="${record.id}">Open →</button></td></tr>`).join('')}</tbody></table></div>`;
}
function boardHTML(jobs) {
  const stages=S.state.stages.filter(stage=>jobs.some(x=>x.stage===stage));
  if (!jobs.length) return empty('No open job cards','Create your first job from a quotation or the New job button.');
  return `<div class="card-body board">${[...new Set([...stages,...jobs.map(x=>x.stage||'Intake')])].map(stage=>`<div class="board-column"><h3>${e(stage)} <span>${jobs.filter(x=>(x.stage||'Intake')===stage).length}</span></h3>${jobs.filter(x=>(x.stage||'Intake')===stage).map(job=>`<div class="job-tile"><button class="record-link" data-action="open" data-kind="jobs" data-id="${job.id}">${e(job.name)}</button><div class="cell-sub">${e(refLabel('customers',job.customer_id))}</div><div class="cell-sub">Due ${e(dateLabel(job.due_date))}</div>${job.blocker?`<div class="notice warning" style="margin:10px 0 0;padding:6px 9px">${e(job.blocker)}</div>`:''}<div class="actions"><button class="btn small" data-action="open" data-kind="jobs" data-id="${job.id}">Job card →</button></div></div>`).join('')}</div>`).join('')}</div>`;
}

function showDialog(title,body,footer='',wide=false,subtitle='') {
  if (dialogCleanup) {dialogCleanup();dialogCleanup=null;}
  const dialog=$('#editor');
  dialog.className=wide?'wide':'';
  dialog.innerHTML=`<div class="dialog-head"><div><h2>${e(title)}</h2>${subtitle?`<p>${e(subtitle)}</p>`:''}</div><button class="icon-button" data-action="close" aria-label="Close dialog">✕</button></div><div class="dialog-body">${body}</div>${footer?`<div class="dialog-foot">${footer}</div>`:''}`;
  if (!dialog.open) dialog.showModal();
  dialog.onclose=()=>{if(!dialog.open&&dialogCleanup){dialogCleanup();dialogCleanup=null;}};
}
function fieldHTML(field,value='',kind='',record={}) {
  let [key,title,type,options,hint]=field;
  title=localLabel(title);
  if(kind&&['gstin','state_code','hsn_sac','cess_rate'].includes(key)&&!indian())return '';
  if(kind==='leads'&&S.state?.business.profile!=='showroom'&&['vehicle_id','finance_status','pdi_complete','documents_complete','handover_signed'].includes(key))return '';
  if(key==='tags'&&Array.isArray(value))value=value.join(', ');
  if(type==='india-state')return stateChoices(value,false,key,title);
  if (type.startsWith('owner-')) {if(!owner())return '';type=type.slice(6);}
  if (type==='stages') {type='select';options=S.state?.stages||['Intake'];}
  const isRequired=(required[kind]||[]).includes(key); const attrs=`id="field-${e(key)}" name="${e(key)}" ${isRequired?'required':''}`;
  if (type==='checkbox') return `<div class="field checkbox"><input ${attrs} type="checkbox" ${value?'checked':''}><label for="field-${e(key)}">${e(title)}</label></div>`;
  let control='';
  if (type==='textarea') control=`<textarea ${attrs} rows="3">${e(value)}</textarea>`;
  else if (type==='ref'||type==='multi') {
    let choices=rows(options);
    if (key==='invoice_id') choices=choices.filter(x=>x.status==='issued');
    if (key==='quote_id'&&kind==='jobs') choices=choices.filter(x=>x.status==='accepted');
    if (key==='employee_id'&&S.user.role==='technician') choices=choices.filter(x=>x.id===S.user.employee_id);
    if (key==='asset_id'&&record.customer_id) choices=choices.filter(x=>!x.customer_id||x.customer_id===record.customer_id);
    const selected=type==='multi'?(value||[]):[value];
    control=`<select ${attrs} ${type==='multi'?'multiple class="select-multiple"':''}>${type==='multi'?'':'<option value="">Choose…</option>'}${choices.map(x=>`<option value="${x.id}" ${selected.includes(x.id)?'selected':''}>${e(label(x))}${x.number&&label(x)!==x.number?' · '+e(x.number):''}</option>`).join('')}</select>`;
    if(type==='multi')hint=hint||'Use Ctrl / Command to select more than one person.';
  } else if (type==='select') control=`<select ${attrs}>${(options||[]).map(option=>`<option value="${e(option)}" ${String(value)===String(option)?'selected':''}>${e(option.replaceAll('_',' '))}</option>`).join('')}</select>`;
  else control=`<input ${attrs} type="${type==='signed-number'?'number':type}" value="${e(value)}" ${type.includes('number')?'step="any"'+(type!=='signed-number'?' min="0"':''):''} ${type==='text'?'maxlength="2000"':''}>`;
  return `<div class="field ${type==='textarea'?'full':''}"><label for="field-${e(key)}">${e(title)}${isRequired?' *':''}</label>${control}${hint?`<small>${e(hint)}</small>`:''}</div>`;
}
function readFields(form,fields,base={}) {
  const data={...base};const values=new FormData(form);
  fields.forEach(([key,,type])=>{
    if(type.startsWith('owner-')&&!owner())return;
    type=type.replace('owner-','');
    data[key]=type==='checkbox'?values.has(key):type==='multi'?values.getAll(key):type.includes('number')?Number(values.get(key)||0):values.get(key)??data[key]??'';
  });
  return data;
}
function isEditable(kind,record) {return !record._pending&&can(kind)&&!immutable.has(kind)&&(!['quotes','invoices'].includes(kind)||record.status==='draft')&&(kind!=='commissions'||record.status==='earned')&&(kind!=='purchases'||!rows('movements').some(x=>x.purchase_id===record.id));}
function formError(message) { const node=$('#form-error'); if(node){node.textContent=message;node.scrollIntoView({block:'nearest'});}else toast(message,true); }
async function saveForm(kind,record,event) {
  event.preventDefault();const form=event.target;const button=$('[type=submit]',form)||$('[type=submit][form=record-form]');if(button)button.disabled=true;
  try {
    const data=readFields(form,models[kind].fields,record||{});
    data.custom_fields=readCustomFields(form,kind,record?.custom_fields||{});
    if(kind==='jobs')data.handover_override_reason=String(new FormData(form).get('handover_override_reason')||'');
    if(kind==='jobs')data.tasks=$$('[data-task-name]',form).map(input=>({id:input.dataset.taskId||crypto.randomUUID(),name:input.value,done:$(`[data-task-done="${input.dataset.taskIndex}"]`,form)?.checked})).filter(x=>x.name.trim());
    const saved=await api('record',{business_id:S.bid,kind,id:record?.id,version:record?.version,data});
    $('#editor').close();await reload();toast(saved._pending?'Draft saved on this device; awaiting sync.':`${models[kind].singular[0].toUpperCase()+models[kind].singular.slice(1)} saved.`);
  } catch(error){formError(error.message);} finally {if(button)button.disabled=false;}
}
function editRecord(kind,id='',prefill={}) {
  if(!can(kind))throw new Error('Your role cannot edit this area.');
  if(['quotes','invoices','external_quotes'].includes(kind)){editDocument(kind,id,prefill);return;}
  if(kind==='purchases'){editPurchase(id);return;}
  if(kind==='payroll'){preparePayroll();return;}
  if(kind==='time_entries'){timerDialog();return;}
  const record=id?find(kind,id):null;
  if(record&&!isEditable(kind,record)){openRecord(kind,id);return;}
  const data={date:S.state.today,due_date:S.state.today,...models[kind].defaults,...(record||{}),...prefill};
  if(kind==='jobs'&&!record&&!data.tasks?.length)data.tasks=(S.state.business.job_checklist||[]).map(name=>({name,done:false}));
  if(S.user.role==='technician'&&['attendance'].includes(kind))data.employee_id=S.user.employee_id;
  let fields=models[kind].fields.map(field=>fieldHTML(field,data[field[0]],kind,data)).join('');
  fields+=customRecordFields(kind,data);
  if(kind==='jobs'&&owner())fields+=fieldHTML(['handover_override_reason','Owner handover override reason (only if checks / collection cannot be completed)','textarea'],'');
  if(kind==='cash_closures')fields+='<div class="notice full">Expected = opening float + cash receipts − cash refunds − cash expenses − cash supplier payments. Payroll paid markers and unrecorded cash drawings are excluded. Record cash expenses / staff advances before counting.</div>';
  if(kind==='jobs') fields+=`<div class="full form-section"><h3>Work and quality checklist</h3><div id="task-fields">${(data.tasks.length?data.tasks:[{name:'',done:false}]).map((x,i)=>taskField(x,i)).join('')}</div><button class="btn small" type="button" id="add-task">+ Checklist item</button><p class="inline-note">Add service tasks and the final quality checks required before delivery.</p></div>`;
  showDialog(`${record?'Edit':'New'} ${models[kind].singular}`,`<form id="record-form"><div id="form-error" class="form-error"></div><div class="form-grid">${fields}</div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="record-form">Save ${models[kind].singular}</button>`,false,record?.number||'Saved in the active business only.');
  $('#record-form').addEventListener('submit',event=>saveForm(kind,record,event));
  $('#add-task')?.addEventListener('click',()=>{const i=$$('[data-task-name]').length;$('#task-fields').insertAdjacentHTML('beforeend',taskField({name:'',done:false},i));});
  $('#field-customer_id')?.addEventListener('change',event=>{
    const select=$('#field-asset_id');if(select)select.innerHTML='<option value="">Choose…</option>'+rows('assets').filter(x=>x.customer_id===event.target.value).map(x=>`<option value="${x.id}">${e(label(x))} · ${e(x.registration||'')}</option>`).join('');
  });
  if(kind==='payments')$('#field-invoice_id').addEventListener('change',event=>{const invoice=find('invoices',event.target.value);if(invoice){$('#field-customer_id').value=invoice.customer_id;$('#field-amount').value=Math.max(0,invoice._balance).toFixed(2);}});
  if(kind==='movements')$('#field-item_id').addEventListener('change',event=>{const item=find('stock',event.target.value);if(item)$('#field-unit_cost').value=item.cost;});
}
function taskField(task,index) {return `<div class="inline-fields" style="margin-bottom:8px"><input type="checkbox" data-task-done="${index}" aria-label="Task ${index+1} completed" ${task.done?'checked':''}><input style="flex:1" data-task-name data-task-index="${index}" data-task-id="${e(task.id||'')}" value="${e(task.name)}" placeholder="Work task or quality check"></div>`;}

function detailSummary(kind,record) {
  const fields=models[kind].fields.filter(([key,,type])=>!type.startsWith('owner-')||owner());
  if(!fields.length)return `<div class="detail-summary">${models[kind].columns.map(key=>`<div><small>${e(localLabel(headers[key]||key))}</small><b>${valueCell(kind,record,key)}</b></div>`).join('')}</div>`;
  return `<div class="detail-summary">${fields.filter(([key,,type])=>!['textarea','multi','checkbox','owner-checkbox'].includes(type)&&record[key]!==undefined&&record[key]!=='').map(([key,title,type,options])=>`<div><small>${e(localLabel(title))}</small><b>${type==='ref'?e(refLabel(options,record[key])):type.includes('number')?count(record[key]):type==='date'?e(dateLabel(record[key])):e(String(record[key]).replaceAll('_',' '))}</b></div>`).join('')}</div>`;
}
function attachmentHTML(kind,record) {
  const attachments=S.state.attachments.filter(x=>x.record_id===record.id);
  return `<div class="form-section"><h3>Original files & evidence</h3><p class="help-text">Photos, approvals, bills and source documents are retained on your business server. Each upload keeps a SHA-256 fingerprint.</p><div class="attachments">${attachments.map(x=>`<div class="file-row"><span>▤</span><a href="/api/attachment?business=${S.bid}&id=${x.id}">${e(x.filename)}</a><small class="muted">${e(x.hash.slice(0,10))}…</small></div>`).join('')}</div>${can(kind)?`<div class="field" style="margin-top:13px"><label for="attachment-input">Add an original file (up to ${S.health?.cloud?'2.5':'12'} MB)</label><input id="attachment-input" type="file"></div>`:''}</div>`;
}
function relatedHTML(kind,record) {
  const relations=[];
  if(kind==='customers')['assets','quotes','jobs','invoices','payments','appointments','contracts'].forEach(type=>{const list=rows(type).filter(x=>x.customer_id===record.id);if(list.length)relations.push([type,list]);});
  if(kind==='assets')['quotes','jobs','appointments','contracts'].forEach(type=>{const list=rows(type).filter(x=>x.asset_id===record.id);if(list.length)relations.push([type,list]);});
  if(kind==='jobs')['invoices','claims','movements','time_entries','commissions'].forEach(type=>{const list=rows(type).filter(x=>x.job_id===record.id);if(list.length)relations.push([type,list]);});
  if(kind==='invoices')['payments','credits','allocations'].forEach(type=>{const list=rows(type).filter(x=>x.invoice_id===record.id);if(list.length)relations.push([type,list]);});
  if(kind==='quotes'){const list=rows('external_quotes').filter(x=>x.quote_id===record.id);if(list.length)relations.push(['external_quotes',list]);const jobs=rows('jobs').filter(x=>x.quote_id===record.id);if(jobs.length)relations.push(['jobs',jobs]);}
  if(kind==='employees')['attendance','time_entries','commissions'].forEach(type=>{const list=rows(type).filter(x=>x.employee_id===record.id);if(list.length)relations.push([type,list.slice(0,12)]);});
  return relations.map(([type,list])=>`<div class="form-section"><h3>${e(models[type].name)} (${list.length})</h3>${list.map(x=>`<div class="mini-row"><div class="grow"><button class="record-link" data-action="open" data-kind="${type}" data-id="${x.id}">${e(label(x))}</button><p>${e(x.number||x.date||x.kind||'')}</p></div>${x.status?status(x.status):''}${x.amount!==undefined?`<b class="mono">${rupees(x.amount)}</b>`:''}${x._totals?`<b class="mono">${rupees(x._totals.total)}</b>`:''}</div>`).join('')}</div>`).join('');
}
function documentReadHTML(record) {
  const totals=record._totals;
  return `<div class="detail-summary"><div><small>Customer</small><b>${e(record.customer_snapshot?.name||refLabel('customers',record.customer_id))}</b></div><div><small>Work / service</small><b>${e(record.subject||'')}</b></div><div><small>Document date</small><b>${e(dateLabel(record.date))}${record.bs_date?' · BS '+e(record.bs_date):''}</b></div><div><small>Asset</small><b>${e(record.asset_snapshot?.registration||refLabel('assets',record.asset_id))}</b></div></div><div class="table-wrap"><table><thead><tr><th>Description</th><th>Qty / unit</th><th class="num">Rate</th><th class="num">Net</th><th class="num">${indian()?'GST + cess':'VAT'}</th><th class="num">Total</th></tr></thead><tbody>${totals.lines.map(x=>`<tr><td>${e(x.description)}</td><td>${count(x.qty)} ${e(x.unit||'pc')}</td><td class="num">${fmt(x.rate)}</td><td class="num">${fmt(x.net)}</td><td class="num">${fmt(x.tax)}</td><td class="num">${fmt(x.total)}</td></tr>`).join('')}</tbody></table></div><div class="doc-bottom"><div><p class="help-text">${e(totals.words)}</p>${record.approved_by?`<div class="notice" style="margin-top:15px">Approval recorded from ${e(record.approved_by)} · ${e(record.approval_channel||'Recorded by staff')}</div>`:''}</div><div class="totals-box"><div class="summary-line"><span>Net amount</span><b>${rupees(totals.net)}</b></div><div class="summary-line"><span>${indian()?'GST + cess':'VAT'}</span><b>${rupees(totals.tax)}</b></div>${taxBreakdown(totals)}<div class="summary-line grand"><span>Total</span><b>${rupees(totals.total)}</b></div>${record.type==='invoices'&&record.status==='issued'?`<div class="summary-line"><span>Credit notes</span><b>${rupees(record._credited)}</b></div><div class="summary-line"><span>Net receipts & allocations</span><b>${rupees(record._paid)}</b></div><div class="summary-line"><span>Outstanding / (credit)</span><b>${rupees(record._balance)}</b></div>`:''}</div></div>`;
}
function recordButtons(kind,record) {
  let buttons=extraRecordButtons(kind,record)+operationsRecordButtons(kind,record);
  if(kind==='invoices'&&record.status==='issued'&&can('credits')&&!record.vehicle_id)buttons+=`<button class="btn" data-action="return-items" data-id="${record.id}">${icon('return')} Return / credit items</button>`;
  if(record._pending)return buttons;
  if(isEditable(kind,record))buttons+=`<button class="btn" data-action="edit" data-kind="${kind}" data-id="${record.id}">Edit</button>`;
  if(['quotes','invoices','external_quotes','payments','credits','jobs','purchases','payroll'].includes(kind))buttons+=`<button class="btn" data-action="print" data-kind="${kind}" data-id="${record.id}">Print / PDF</button>`;
  if(kind==='invoices'&&record.status==='issued'&&can('payments'))buttons+=`<button class="btn primary" data-action="invoice-payment" data-id="${record.id}">Record receipt / refund</button>${can('credits')&&!indian()?`<button class="btn" data-action="invoice-credit" data-id="${record.id}">Credit note</button>`:''}`;
  if(!can(kind))return buttons;
  const a=(name,act,primary=false)=>`<button class="btn ${primary?'primary':''}" data-action="record-action" data-kind="${kind}" data-id="${record.id}" data-operation="${act}">${name}</button>`;
  if(kind==='quotes'){
    if(record.status==='draft')buttons+=a('Mark sent & retain','send',true);
    if(record.status==='sent')buttons+=a('Record approval','accept',true)+a('Record declined','decline');
    if(record.status==='accepted')buttons+=a('Create / open job','job',true);
    if(record.status!=='draft')buttons+=a('Create revision','revise');
    buttons+=`<button class="btn" data-action="comparison" data-id="${record.id}">Compare quotes</button>`;
  }
  if(kind==='invoices'){
    if(record.status==='draft')buttons+=a('Issue & retain invoice','issue',true);
  }
  if(kind==='jobs'&&can('invoices'))buttons+=a('Create / open invoice','invoice',true);
  if(kind==='jobs'&&can('time_entries'))buttons+=`<button class="btn" data-action="timer" data-job="${record.id}">Task timer</button>`;
  if(kind==='jobs'&&can('movements'))buttons+=`<button class="btn" data-action="job-stock" data-id="${record.id}">Issue / return stock</button>`;
  if(kind==='attendance'&&record.status==='pending'&&S.user.role!=='technician')buttons+=a('Approve attendance','approve',true);
  if(kind==='commissions'){if(record.status==='earned')buttons+=a('Approve earning','approve',true);if(record.status==='approved'&&!record.reserved_payroll_id)buttons+=a('Record paid','pay',true);}
  if(kind==='payroll'){if(record.status==='draft')buttons+=a('Approve payroll','approve',true);if(record.status==='approved')buttons+=a('Record payroll paid','pay',true);}
  if(kind==='purchases'&&record.status!=='received')buttons+=a('Receive delivery','receive',true);
  if(kind==='payments'&&!record.invoice_id&&!record.opening_balance_id&&record._unallocated>0)buttons+=a('Allocate advance','allocate',true);
  if(kind==='customers')buttons+=`<button class="btn primary" data-action="customer-quote" data-id="${record.id}">New quotation</button>`;
  return buttons;
}
function openRecord(kind,id) {
  const record=find(kind,id);if(!record)throw new Error('Record is no longer available. Refresh the app.');
  let body=`<div id="form-error" class="form-error"></div><div class="detail-title"><h2>${e(label(record))}</h2>${status(record.status||record.stage||record.direction||'saved')}${record.revision?`<span class="muted">Revision ${record.revision}</span>`:''}</div><div class="actions" style="margin-bottom:23px">${recordButtons(kind,record)}</div>`;
  if(['quotes','invoices','external_quotes'].includes(kind))body+=documentReadHTML(record);
  else body+=(kind==='customers'?customerHub(record):'')+detailSummary(kind,record);
  body+=customDetails(kind,record)+operationsDetails(kind,record);
  if(kind==='external_quotes')body=`<div class="notice warning">${record.simulation?'HYPOTHETICAL SCENARIO — This is not a quotation independently issued by another business.':'External quotation transcription. Check the original uploaded document and issuer.'}</div>`+body;
  if(kind==='jobs'){
    body+=`<div class="form-section"><h3>Work & quality checks</h3><ul class="checklist">${(record.tasks||[]).map((task,i)=>`<li><input type="checkbox" ${task.done?'checked':''} ${can('jobs')?'':'disabled'} data-action="task-toggle" data-id="${record.id}" data-index="${i}" aria-label="${e(task.name)} completed"><span>${e(task.name)}</span>${status(task.done?'completed':'pending')}</li>`).join('')}</ul></div>`;
    if(owner())body+=`<div class="form-section"><h3>Job contribution</h3><div class="stats" style="grid-template-columns:repeat(3,1fr);margin-top:15px">${stat('Billed revenue, excl. VAT',rupees(record._revenue),'After credit notes')}${stat('Recorded direct costs',rupees(record._cost),'Materials, labour, expenses, incentives')}${stat('Contribution',rupees(record._contribution),record._cost_provisional?'Costs still provisional':'Direct costs checked',true)}</div><p class="help-text">Contribution excludes general overhead. Payroll is shown separately; task-hour labour estimates are already in job costs. Avoid counting the same cost twice.</p></div>`;
  }
  if(kind==='claims'){
    const received=payer=>rows('payments').filter(x=>x.claim_id===id&&x.payer_type===payer).reduce((n,x)=>n+(x.direction==='refund'?-1:1)*x.amount,0);
    body+=`<div class="form-section"><h3>Settlement by payer</h3><div class="summary-line"><span>Insurer: expected / net received</span><b>${rupees(record.insurer_share)} / ${rupees(received('Insurer'))}</b></div><div class="summary-line"><span>Customer: expected / net received</span><b>${rupees(record.customer_share)} / ${rupees(received('Customer'))}</b></div><p class="inline-note">Based on receipts explicitly tagged to this claim. Approval is not a receipt.</p></div>`;
  }
  if(kind==='stock')body+=`<div class="notice">Current stock: <b>${count(record._quantity)} ${e(record.unit)}</b> · Reorder at ${count(record.reorder_at)}. <button class="btn text small" data-action="stock-movement" data-id="${record.id}">Record movement →</button></div>`;
  if(kind==='payments'&&!record.invoice_id&&!record.opening_balance_id)body+=`<div class="notice">Advance remaining to allocate: <b>${rupees(record._unallocated)}</b></div>`;
  if(kind==='commissions')body+=`<div class="notice">Earned: <b>${rupees(record.amount)}</b> · Collection eligible: <b>${rupees(record._eligible)}</b>${record.reserved_payroll_id?' · Reserved in payroll':''}</div>`;
  if(kind==='payroll')body+=payrollReadHTML(record);
  if(kind==='purchases')body+=`<div class="table-wrap"><table><thead><tr><th>Item</th><th>Ordered</th><th>Received</th><th class="num">Unit cost</th></tr></thead><tbody>${record.items.map(x=>`<tr><td>${e(refLabel('stock',x.item_id))}</td><td>${count(x.qty)}</td><td>${count(rows('movements').filter(y=>y.purchase_id===record.id&&y.item_id===x.item_id).reduce((n,y)=>n+y.qty,0))}</td><td class="num">${fmt(x.cost)}</td></tr>`).join('')}</tbody></table></div>`;
  if(record.terms)body+=`<div class="form-section"><h3>Terms</h3><p style="white-space:pre-line" class="help-text">${e(record.terms)}</p></div>`;
  if(record.notes)body+=`<div class="form-section"><h3>Notes</h3><p style="white-space:pre-line" class="help-text">${e(record.notes)}</p></div>`;
  body+=relatedHTML(kind,record)+attachmentHTML(kind,record);
  const audit=S.state.audit.filter(x=>x.record_id===id);
  if(audit.length)body+=`<div class="form-section"><h3>Recent changes</h3><ul class="timeline">${audit.slice(0,7).map(x=>`<li><b>${e(x.action)}</b><small>${e(x.user_name)} · ${e(new Date(x.created_at).toLocaleString())}</small></li>`).join('')}</ul></div>`;
  const archive=can(kind)&&!immutable.has(kind)&&isEditable(kind,record)?`<button class="btn text grow danger-text" data-action="archive" data-kind="${kind}" data-id="${id}">Archive unused record</button>`:'';
  showDialog(models[kind].singular[0].toUpperCase()+models[kind].singular.slice(1),body,archive+'<button class="btn" data-action="close">Close</button>',true,record.number||'Connected to the active business.');
  $('#attachment-input')?.addEventListener('change',event=>uploadAttachment(event,record));
}
async function uploadAttachment(event,record) {
  const file=event.target.files[0];if(!file)return;
  const fileLimit=S.health?.cloud?2_500_000:12*1024*1024;
  if(file.size>fileLimit){formError(S.health?.cloud?'Choose a file smaller than 2.5 MB.':'Choose a file smaller than 12 MB.');return;}
  event.target.disabled=true;
  try {await api('attachment',{business_id:S.bid,record_id:record.id,filename:file.name,mime:file.type,content:await fileBase64(file)});await reload();openRecord(record.type,record.id);toast('Original file attached.');}catch(error){formError(error.message);}finally{event.target.disabled=false;}
}
function fileBase64(file) {return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(String(reader.result).split(',')[1]);reader.onerror=()=>reject(new Error('Could not read that file.'));reader.readAsDataURL(file);});}

function editDocument(kind,id='',prefill={}) {
  const record=id?find(kind,id):null;
  if(record&&!isEditable(kind,record)){openRecord(kind,id);return;}
  const b=S.state.business;
  const key=`bd_draft_${S.user.id}_${S.bid}_${kind}_${id||'new'}`;
  let recovered=null;try{recovered=JSON.parse(sessionStorage.getItem(key)||'null');}catch(_){/* Ignore an incomplete browser draft. */}
  if(recovered&&((record&&recovered.version!==record.version)||Object.keys(prefill).length))recovered=null;
  let data={country:b.country||'NP',currency:b.currency||'NPR',seller_state:b.state_code||'',place_of_supply:b.state_code||'',date:S.state.today,due_date:addDays(S.state.today,b.payment_terms_days||7),customer_id:'',asset_id:'',subject:'',status:'draft',revision:1,items:[],vat_mode:b.vat_registered===false?'none':'added',vat_rate:b.vat_rate??13,discount_percent:0,terms:b.terms||'',bs_date:'',show_chassis:true,font_size:b.print_font_size||11,print_style:b.print_style||'classic',...record,...prefill,...recovered};
  if(!record&&!recovered&&prefill.customer_id)data=applyClientDefaults(data,prefill.customer_id);
  if(kind==='external_quotes')data={...data,issuer:data.issuer||'',quote_id:data.quote_id||prefill.quote_id||'',simulation:!!data.simulation,reference:data.reference||''};
  data.items=(data.items||[]).map(item=>({qty:1,unit:'pc',discount:0,tax_rate:data.vat_rate,unit_cost:0,...item}));
  if(!data.items?.length)data.items=[{description:'',qty:1,unit:'pc',rate:0,discount:0,tax_rate:data.vat_rate,unit_cost:0}];
  const field=(key,title,type,options,hint)=>fieldHTML([key,title,type,options,hint],data[key],'',data);
  const top=kind==='external_quotes'?`<div class="span2">${field('issuer','Actual issuer / hypothetical label','text')}</div>${field('quote_id','Own quotation being compared','ref','quotes')}${field('reference','Issuer reference','text')}<div class="span2">${field('simulation','This is a hypothetical scenario, not independently issued','checkbox')}</div>`:`<div class="span2">${field('customer_id','Customer *','ref','customers')}</div><div class="span2">${field('asset_id','Vehicle / asset','ref','assets')}</div><div class="span2">${field('subject','Work / service scope','text')}</div>`;
  showDialog(`${record?'Edit':'New'} ${models[kind].singular}`,`<form id="document-form"><div id="form-error" class="form-error"></div><div class="doc-state"><span id="draft-status">${recovered?'Recovered the typing saved on this browser.':'Typing saves on this browser. Save draft to store it in the database.'}</span><button class="btn text small" type="button" id="discard-browser-draft">Clear browser recovery</button></div>${kind==='external_quotes'?'<div class="notice warning">Keep actual competitor documents unchanged as attachments. Scenario printouts remain visibly marked as hypothetical.</div>':''}<div class="doc-meta">${top}${field('date','Document date, AD','date')}${indian()?field('place_of_supply','Place of supply','india-state'):field('bs_date','BS date (manual entry)','text')}${kind!=='external_quotes'?field('show_chassis','Print chassis / serial number','checkbox'):''}${kind==='invoices'?field('due_date','Payment due, AD','date'):''}${field('vat_mode','VAT treatment','select',['added','included','none'])}${field('vat_rate','Default VAT rate, %','number')}${field('discount_percent','Overall discount, %','number')}</div><div class="table-wrap"><table class="line-table"><thead><tr><th>#</th><th>Description</th><th>Qty</th><th>Unit</th><th class="num">Rate, ${currency()}</th><th>Disc. %</th><th>${indian()?'GST':'VAT'} %</th>${indian()?'<th>HSN / SAC</th><th>Cess %</th>':''}${owner()?'<th>Unit cost</th>':''}<th class="num">Total</th><th></th></tr></thead><tbody id="document-lines"></tbody></table></div><div class="line-tools"><div class="actions"><button type="button" class="btn small" id="add-line">+ Add line</button><select id="catalog-picker" aria-label="Add a catalogue service or stock item"><option value="">Add from catalogue…</option><optgroup label="Services">${rows('services').map(x=>`<option value="services:${x.id}">${e(x.name)} · ${fmt(x.rate)}</option>`).join('')}</optgroup><optgroup label="Stock">${rows('stock').map(x=>`<option value="stock:${x.id}">${e(x.name)} · ${fmt(x.rate)}</option>`).join('')}</optgroup></select><button type="button" class="btn small" id="paste-lines">Paste spreadsheet</button></div><small class="muted">Tab to move · ↑ / ↓ between rows</small></div><div id="paste-area" hidden><div class="notice">Paste tab-separated columns: <b>Description, Qty, Unit, Rate</b> (optional: Discount %, VAT %, Unit cost).<textarea id="paste-text" style="width:100%;margin-top:10px" rows="4" placeholder="Bumper repair&#9;1&#9;job&#9;4500"></textarea><button class="btn small" type="button" id="apply-paste">Add pasted rows</button></div></div><div class="doc-bottom"><div>${field('terms','Terms and conditions','textarea')}${field('notes','Internal / document notes','textarea')}<div class="inline-fields">${field('print_style','Print layout','select',['classic','compact','modern'])}${field('font_size','Print font size, pt (8–16)','number')}</div></div><div id="document-totals" class="totals-box"><p class="muted">Calculating…</p></div></div></form>`,`<span class="grow help-text">${kind==='external_quotes'?'Save the record, then attach its original source.':'Drafts remain editable. Sent quotes and issued bills retain their details.'}</span><button class="btn" data-action="close">Close</button><button class="btn primary" type="submit" form="document-form">${kind==='external_quotes'?'Save comparison':'Save draft'}</button>`,true,record?.number||currency()+' · Review before issuing');
  const form=$('#document-form');
  if($('#field-customer_id')&&can('customers'))$('#field-customer_id').insertAdjacentHTML('afterend','<button type="button" class="btn text quick-customer" data-action="quick-customer">+ Add a customer without leaving this bill</button>');
  let calcTimer=null,calcSequence=0;
  function readDoc() {
    const values=Object.fromEntries(new FormData(form));
    const items=$$('#document-lines tr').map((tr,index)=>{
      const item={...(data.items[index]||{})};$$('[data-col]',tr).forEach(input=>{item[input.name]=['description','unit','hsn_sac'].includes(input.name)?input.value:Number(input.value||0);});return item;
    });
    return {...data,...values,vat_rate:Number(values.vat_rate),discount_percent:Number(values.discount_percent),font_size:Number(values.font_size),simulation:$('#field-simulation')?.checked||false,show_chassis:$('#field-show_chassis')?.checked??true,items};
  }
  function lineHTML(item,index) {
    const cell=(key,type,cls)=>`<td class="${cls}" data-label="${e({qty:'Quantity',rate:'Rate, '+currency(),discount:'Discount %',tax_rate:indian()?'GST %':'VAT %',hsn_sac:'HSN / SAC',cess_rate:'Cess %',unit_cost:'Unit cost'}[key]||key)}"><input name="${key}" type="${type}" ${type==='number'?'step="any" min="0"':''} value="${e(item[key]??(type==='text'?'':['qty'].includes(key)?1:0))}" data-row="${index}" data-col="${key}" aria-label="Line ${index+1} ${key}"></td>`;
    return `<tr><td class="muted">${index+1}</td><td class="desc-cell" data-label="Description"><textarea name="description" data-row="${index}" data-col="description" aria-label="Line ${index+1} description" rows="1">${e(item.description||'')}</textarea></td>${cell('qty','number','qty-cell')}<td class="unit-cell" data-label="Unit"><input name="unit" value="${e(item.unit||'pc')}" data-row="${index}" data-col="unit" aria-label="Line ${index+1} unit"></td>${cell('rate','number','rate-cell')}${cell('discount','number','pct-cell')}${cell('tax_rate','number','pct-cell')}${indian()?cell('hsn_sac','text','rate-cell')+cell('cess_rate','number','pct-cell'):''}${owner()?cell('unit_cost','number','rate-cell'):''}<td class="num" data-label="Line total" data-line-total="${index}">—</td><td><button class="icon-button" type="button" data-move-line="${index}" data-delta="-1" aria-label="Move line ${index+1} up" ${index===0?'disabled':''}>↑</button><button class="icon-button" type="button" data-move-line="${index}" data-delta="1" aria-label="Move line ${index+1} down" ${index===data.items.length-1?'disabled':''}>↓</button><button class="icon-button remove-line" type="button" data-remove-line="${index}" aria-label="Remove line ${index+1}">×</button></td></tr>`;
  }
  function renderLines() {$('#document-lines').innerHTML=data.items.map(lineHTML).join('');}
  function recoverSave() {data=readDoc();try{sessionStorage.setItem(key,JSON.stringify(data));$('#draft-status').textContent='Typing saved on this browser · '+new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});}catch(_){$('#draft-status').textContent='Browser recovery is unavailable. Save draft to retain changes.';}}
  async function recalc() {
    const sequence=++calcSequence;
    try {
      const totals=await api('calculate',{data:readDoc()});if(sequence!==calcSequence||!$('#document-totals'))return;
      $('#document-totals').innerHTML=`<div class="summary-line"><span>Net amount</span><b>${rupees(totals.net)}</b></div><div class="summary-line"><span>${indian()?'GST + cess':'VAT'}</span><b>${rupees(totals.tax)}</b></div>${taxBreakdown(totals)}<div class="summary-line"><span>Discounts applied</span><b>${rupees(totals.discount)}</b></div><div class="summary-line grand"><span>Total</span><b>${rupees(totals.total)}</b></div>${owner()?`<div class="summary-line"><span>Estimated cost</span><b>${rupees(totals.estimated_cost)}</b></div><div class="summary-line"><span>Estimated contribution</span><b>${rupees(totals.estimated_contribution)}</b></div>`:''}<small>${e(totals.words)}</small><small>Each line rounds to two decimal places; totals sum those lines.</small>`;
      let lineIndex=0;$$('#document-lines tr').forEach(tr=>{const priced=$('[name=description]',tr).value.trim()||Number($('[name=rate]',tr).value);$('[data-line-total]',tr).textContent=priced&&totals.lines[lineIndex]?fmt(totals.lines[lineIndex++].total):'—';});
    }catch(error){if(sequence===calcSequence&&$('#document-totals'))$('#document-totals').innerHTML=`<p class="danger-text">${e(error.message)}</p>`;}
  }
  function changed() {recoverSave();clearTimeout(calcTimer);calcTimer=setTimeout(recalc,180);}
  function append(items) {data=readDoc();data.items=data.items.filter(x=>x.description.trim()||x.rate);data.items.push(...items);renderLines();changed();}
  function parsePaste(text) {
    const result=text.trim().split(/\r?\n/).filter(Boolean).map(line=>line.split('\t')).filter(columns=>!/^description$/i.test(columns[0]?.trim())).map(columns=>({description:columns[0]?.trim()||'',qty:columns[1]?.trim()?Number(columns[1].replaceAll(',','')):1,unit:columns[2]?.trim()||'pc',rate:Number((columns[3]||'0').replaceAll(',','')),discount:Number(columns[4]||0),tax_rate:columns[5]?.trim()?Number(columns[5]):Number($('#field-vat_rate').value),unit_cost:Number((columns[6]||'0').replaceAll(',',''))}));
    if(result.some(item=>['qty','rate','discount','tax_rate','unit_cost'].some(key=>!Number.isFinite(item[key]))))throw new Error('Pasted quantities, rates, and percentages must be numbers.');return result;
  }
  renderLines();recalc();
  form.addEventListener('input',changed);
  form.addEventListener('change',changed);
  $('#field-vat_rate').addEventListener('change',()=>{data=readDoc();data.items.forEach(x=>x.tax_rate=data.vat_rate);renderLines();changed();});
  $('#field-customer_id')?.addEventListener('change',event=>{const defaults=applyClientDefaults(readDoc(),event.target.value);$('#field-discount_percent').value=defaults.discount_percent;if($('#field-due_date'))$('#field-due_date').value=defaults.due_date;if($('#field-place_of_supply'))$('#field-place_of_supply').value=defaults.place_of_supply;const asset=$('#field-asset_id');asset.innerHTML='<option value="">Choose…</option>'+rows('assets').filter(x=>x.customer_id===event.target.value).map(x=>`<option value="${x.id}">${e(label(x))} · ${e(x.registration||'')}</option>`).join('');changed();});
  $('#add-line').addEventListener('click',()=>{append([{description:'',qty:1,unit:'pc',rate:0,discount:0,tax_rate:Number($('#field-vat_rate').value),unit_cost:0}]);$$('[data-col="description"]').at(-1)?.focus();});
  $('#catalog-picker').addEventListener('change',event=>{if(!event.target.value)return;const [type,rid]=event.target.value.split(':');const item=find(type,rid);append([{description:item.name,qty:1,unit:item.unit||'pc',rate:item.rate||0,unit_cost:item.cost||0,discount:0,tax_rate:item.tax_rate??Number($('#field-vat_rate').value),hsn_sac:item.hsn_sac||'',cess_rate:item.cess_rate||0,category:item.category||'Part',...(type==='stock'?{item_id:item.id}:{service_id:item.id})}]);event.target.value='';});
  $('#document-lines').addEventListener('click',event=>{const move=event.target.closest('[data-move-line]');if(move){data=readDoc();const from=Number(move.dataset.moveLine),to=from+Number(move.dataset.delta);if(to>=0&&to<data.items.length){[data.items[from],data.items[to]]=[data.items[to],data.items[from]];renderLines();changed();}return;}const remove=event.target.closest('[data-remove-line]');if(remove){data=readDoc();data.items.splice(Number(remove.dataset.removeLine),1);if(!data.items.length)data.items=[{description:'',qty:1,unit:'pc',rate:0,tax_rate:data.vat_rate}];renderLines();changed();}});
  $('#document-lines').addEventListener('keydown',event=>{
    const input=event.target;if(!input.dataset.col)return;
    if(['ArrowUp','ArrowDown'].includes(event.key)){const next=Number(input.dataset.row)+(event.key==='ArrowDown'?1:-1);const target=$(`[data-row="${next}"][data-col="${input.dataset.col}"]`);if(target){event.preventDefault();target.focus();target.select();}}
  });
  $('#document-lines').addEventListener('paste',event=>{const text=event.clipboardData?.getData('text/plain')||'';if(text.includes('\t')){event.preventDefault();try{append(parsePaste(text));}catch(error){formError(error.message);}}});
  $('#paste-lines').addEventListener('click',()=>{$('#paste-area').hidden=!$('#paste-area').hidden;if(!$('#paste-area').hidden)$('#paste-text').focus();});
  $('#apply-paste').addEventListener('click',()=>{try{append(parsePaste($('#paste-text').value));$('#paste-text').value='';$('#paste-area').hidden=true;}catch(error){formError(error.message);}});
  $('#discard-browser-draft').addEventListener('click',()=>{sessionStorage.removeItem(key);$('#draft-status').textContent='Browser recovery cleared. The current form is still open.';});
  form.addEventListener('submit',async event=>{
    event.preventDefault();const button=$('[type=submit][form=document-form]');button.disabled=true;
    try{
      const input=readDoc();if(kind!=='external_quotes'&&!input.customer_id)throw new Error('Choose a customer before saving.');
      const result=await api('record',{business_id:S.bid,kind,id:record?.id,version:record?.version,data:input});sessionStorage.removeItem(key);$('#editor').close();await reload();openRecord(kind,result.id);toast(kind==='external_quotes'?'Comparison saved. Attach its original source.':'Draft saved in your local database.');
    }catch(error){formError(error.message);}finally{button.disabled=false;}
  });
  dialogCleanup=()=>{clearTimeout(calcTimer);calcSequence++;};
}

async function runAction(kind,id,operation,payload={}) {
  const record=find(kind,id);const result=await api('action',{business_id:S.bid,kind,id,version:record.version,action:operation,...payload});await reload();
  if(result?.id)openRecord(result.type||kind,result.id);
  toast({send:'Quotation marked sent. No message was sent automatically.',issue:'Invoice issued and retained.',accept:'Approval recorded.',decline:'Decision recorded.',revise:'New revision created.',job:'Job card ready.',invoice:'Invoice draft ready.',approve:'Review approved.',pay:'Payment status recorded.',receive:'Stock receipt recorded.',allocate:'Advance allocated to the invoice.'}[operation]||'Action saved.');
}
function actionDialog(kind,id,operation) {
  const record=find(kind,id);
  if(operation==='release') {
    showDialog('Release vehicle reservation',`<form id="release-form"><div id="form-error" class="form-error"></div>${fieldHTML(['reason','Reason for releasing this booking','textarea'])}</form>`, '<button class="btn" data-action="close">Cancel</button><button class="btn danger" type="submit" form="release-form">Release reservation</button>');
    $('#release-form').onsubmit=async event=>{event.preventDefault();try{await runAction(kind,id,operation,Object.fromEntries(new FormData(event.target)));}catch(error){formError(error.message);}};return;
  }
  if(operation==='accept') {
    showDialog('Record quotation approval',`<form id="action-form"><div id="form-error" class="form-error"></div><div class="notice">${e(record.number)} · Revision ${record.revision||1} · ${rupees(record._totals.total)}. This records approval of this exact saved quotation.</div>${fieldHTML(['approved_by','Approved by *','text'])}${fieldHTML(['channel','Approval received through','select',['In person','Phone','Email','Written document','Message']],'In person')}${fieldHTML(['notes','Approval details','textarea'])}</form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="action-form">Record approval</button>`);
    $('#action-form').addEventListener('submit',async event=>{event.preventDefault();try{await runAction(kind,id,operation,Object.fromEntries(new FormData(event.target)));}catch(error){formError(error.message);}});return;
  }
  if(operation==='job') {
    showDialog('Create a job from this quote',`<form id="action-form"><div id="form-error" class="form-error"></div><div class="notice">The approved scope becomes a work checklist. Assign a team and bay on the job card.</div>${fieldHTML(['due_date','Promised delivery, AD','date'],addDays(S.state.today,3))}</form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="action-form">Create / open job</button>`);
    $('#action-form').addEventListener('submit',async event=>{event.preventDefault();try{await runAction(kind,id,operation,Object.fromEntries(new FormData(event.target)));}catch(error){formError(error.message);}});return;
  }
  if(operation==='receive'){receiveDialog(record);return;}
  if(operation==='allocate'){allocateDialog(record);return;}
  const override=operation==='issue'&&kind==='invoices'&&owner()&&S.state.business.operating_rules?.credit_limit_enforced?fieldHTML(['credit_override_reason','Owner reason if this bill exceeds the customer credit limit','textarea']):'';
  const descriptions={reserve:'Reserve this chassis for this customer. Another enquiry cannot reserve it while this booking is active.',deliver:'Confirm delivery after full collection, PDI, document checks and signed handover.',quote:'Create or open the enquiry quotation.',send:'Retain this quotation’s details and start its follow-up clock. Use Print / PDF to share it with the customer.',issue:'Assign the next invoice number and retain this bill’s business, customer, prices, VAT, and terms.',decline:'Record the customer’s decision on this saved quotation.',approve:kind==='payroll'?'Review every pay unit, deduction, contribution, and withholding first. Approving reserves the included commission earnings.':'Record that this entry has been reviewed.',pay:'Record that you have actually made this payment. This does not initiate a bank or wallet transfer.',revise:'Create a new editable revision while keeping this saved quotation unchanged.',invoice:'Open the existing job invoice, or create a new draft from the approved quotation.'};
  showDialog(({send:'Mark quotation sent',issue:'Issue invoice',decline:'Record declined',approve:'Approve reviewed entry',pay:'Record payment made',revise:'Create a quotation revision',invoice:'Create / open job invoice'})[operation]||'Update record',`<div id="form-error" class="form-error"></div><div class="notice">${e(descriptions[operation]||'Save this action in the local record.')}</div><h3>${e(record.number||label(record))}</h3>${override}`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" id="confirm-action">${operation==='pay'?'Record paid':'Confirm'}</button>`);
  $('#confirm-action').addEventListener('click',async event=>{event.target.disabled=true;try{await runAction(kind,id,operation,{credit_override_reason:$('#field-credit_override_reason')?.value||''});}catch(error){formError(error.message);event.target.disabled=false;}});
}
function printDialog(kind,id) {
  if(S.offline||find(kind,id)?._pending)throw new Error('Reconnect and sync before opening an official print view.');
  const record=find(kind,id),b=S.state.business;
  showDialog('Print or save a PDF',`<form id="print-form"><div class="form-grid">${fieldHTML(['style','Layout','select',['classic','compact','modern']],record.print_style||b.print_style||'classic')}${fieldHTML(['font','Font size, pt','number'],record.font_size||b.print_font_size||11)}</div>${kind==='quotes'?fieldHTML(['bundle','Include all linked comparison records (source labels retained)','checkbox'],false):''}<div class="notice">A4 layout with all saved lines and terms. Your browser’s print dialog can save a PDF. Drafts and hypothetical comparisons retain their labels.</div></form>`,`<button class="btn" data-action="close">Close</button><button class="btn primary" type="submit" form="print-form">Open print view ↗</button>`);
  $('#print-form').addEventListener('submit',event=>{event.preventDefault();const values=Object.fromEntries(new FormData(event.target));window.open(`/print?business=${encodeURIComponent(S.bid)}&kind=${kind}&id=${id}&style=${encodeURIComponent(values.style)}&font=${encodeURIComponent(values.font)}&bundle=${values.bundle?'1':'0'}`,'_blank','noopener');});
}
function comparisonDialog(quoteId) {
  const quote=find('quotes',quoteId);const comparisons=rows('external_quotes').filter(x=>x.quote_id===quoteId);const own=quote._totals;
  const body=`<div class="notice warning">Use original issuer documents for insurance evidence. Generated scenarios are planning calculations and remain visibly labelled.</div><div class="table-wrap"><table><thead><tr><th>Issuer / source</th><th class="num">Net</th><th class="num">${indian()?'GST + cess':'VAT'}</th><th class="num">Total</th><th class="num">Difference vs own</th><th>Source file</th></tr></thead><tbody><tr><td><b>${e(S.state.business.name)}</b><div class="cell-sub">${e(quote.number||'Own draft')} · Revision ${quote.revision||1}</div></td><td class="num">${fmt(own.net)}</td><td class="num">${fmt(own.tax)}</td><td class="num">${fmt(own.total)}</td><td class="num">—</td><td>Own quotation</td></tr>${comparisons.map(x=>`<tr><td><button class="record-link" data-action="open" data-kind="external_quotes" data-id="${x.id}">${e(x.issuer)}</button><div class="cell-sub">${x.simulation?'Hypothetical scenario':'External transcription'}</div></td><td class="num">${fmt(x._totals.net)}</td><td class="num">${fmt(x._totals.tax)}</td><td class="num">${fmt(x._totals.total)}</td><td class="num">${fmt(x._totals.total-own.total)}</td><td>${x.simulation?status('Hypothetical'):S.state.attachments.some(file=>file.record_id===x.id)?status('Original attached'):status('Source missing')}</td></tr>`).join('')}</tbody></table></div>`;
  showDialog('Quotation comparison',body,`<button class="btn" data-action="comparison-add" data-id="${quoteId}">+ Actual issuer record</button><button class="btn" data-action="scenario" data-id="${quoteId}">+ Hypothetical scenario</button><button class="btn" data-action="close">Close</button>`,true,quote.number||quote.subject);
}
function scenarioDialog(quoteId) {
  const quote=find('quotes',quoteId);
  showDialog('Create a hypothetical comparison',`<form id="scenario-form"><div id="form-error" class="form-error"></div><div class="notice warning">This creates a clearly labelled planning scenario. It cannot establish a real third party’s price.</div>${fieldHTML(['issuer','Scenario label','text'],'Hypothetical scenario A')}${fieldHTML(['markup','Rate increase, %','number'],10)}</form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="scenario-form">Create scenario</button>`);
  $('#scenario-form').addEventListener('submit',event=>{event.preventDefault();const values=Object.fromEntries(new FormData(event.target));const multiplier=1+Number(values.markup)/100;editDocument('external_quotes','',{quote_id:quoteId,issuer:values.issuer,simulation:true,items:quote.items.map(x=>({...x,rate:Math.round(x.rate*multiplier*100)/100})),vat_mode:quote.vat_mode,vat_rate:quote.vat_rate,discount_percent:quote.discount_percent,notes:'Hypothetical planning scenario. Not independently issued by another business.'});});
}

function editPurchase(id='') {
  const record=id?find('purchases',id):null;
  if(record&&!isEditable('purchases',record)){openRecord('purchases',id);return;}
  let data={supplier_id:'',date:S.state.today,expected_date:addDays(S.state.today,2),items:[],notes:'',...record};
  if(!data.items.length)data.items=[{item_id:'',qty:1,cost:0}];
  const fields=[['supplier_id','Supplier','ref','suppliers'],['date','Order date, AD','date'],['expected_date','Expected delivery, AD','date'],['notes','Order / delivery instructions','textarea']];
  showDialog(record?'Edit purchase order':'New purchase order',`<form id="purchase-form"><div id="form-error" class="form-error"></div><div class="form-grid">${fields.slice(0,3).map(field=>fieldHTML(field,data[field[0]])).join('')}</div><div class="table-wrap"><table><thead><tr><th>Stock item</th><th>Quantity</th><th>Unit cost, ${currency()}</th><th></th></tr></thead><tbody id="purchase-lines"></tbody></table></div><button type="button" class="btn small" id="purchase-add" style="margin:13px 0">+ Order line</button>${fieldHTML(fields[3],data.notes)}<div class="notice">Receiving a delivery creates stock receipts for the actual quantities supplied. This order is not a supplier invoice or payment.</div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="purchase-form">Save purchase order</button>`,true);
  const read=()=>$$('#purchase-lines tr').map(tr=>({item_id:$('[name=item_id]',tr).value,qty:Number($('[name=qty]',tr).value),cost:Number($('[name=cost]',tr).value)}));
  const render=()=>{$('#purchase-lines').innerHTML=data.items.map((x,i)=>`<tr><td><select name="item_id" aria-label="Order line ${i+1} stock item" required><option value="">Choose…</option>${rows('stock').map(item=>`<option value="${item.id}" ${item.id===x.item_id?'selected':''}>${e(item.name)}</option>`).join('')}</select></td><td><input name="qty" value="${e(x.qty)}" type="number" step="any" min="0.0001" required aria-label="Order line ${i+1} quantity"></td><td><input name="cost" value="${e(x.cost)}" type="number" step="any" min="0" aria-label="Order line ${i+1} unit cost"></td><td><button type="button" class="icon-button" data-purchase-remove="${i}" aria-label="Remove order line">×</button></td></tr>`).join('');};
  render();$('#purchase-add').addEventListener('click',()=>{data.items=read();data.items.push({item_id:'',qty:1,cost:0});render();});
  $('#purchase-lines').addEventListener('change',event=>{if(event.target.name==='item_id'){const item=find('stock',event.target.value);if(item)$('[name=cost]',event.target.closest('tr')).value=item.cost;}});
  $('#purchase-lines').addEventListener('click',event=>{const remove=event.target.closest('[data-purchase-remove]');if(remove){data.items=read();data.items.splice(Number(remove.dataset.purchaseRemove),1);render();}});
  $('#purchase-form').addEventListener('submit',async event=>{event.preventDefault();try{const input=readFields(event.target,fields,data);input.items=read();const result=await api('record',{business_id:S.bid,kind:'purchases',id:record?.id,version:record?.version,data:input});await reload();openRecord('purchases',result.id);toast('Purchase order saved.');}catch(error){formError(error.message);}});
}
function receiveDialog(order) {
  showDialog('Receive supplier delivery',`<form id="receive-form"><div id="form-error" class="form-error"></div><div class="notice">Enter only what arrived. Partial receipts leave the rest of the order outstanding.</div><div class="table-wrap"><table><thead><tr><th>Item</th><th>Remaining</th><th>Received now</th></tr></thead><tbody>${order.items.map(x=>{const received=rows('movements').filter(y=>y.purchase_id===order.id&&y.item_id===x.item_id).reduce((n,y)=>n+y.qty,0),remaining=x.qty-received;return `<tr><td>${e(refLabel('stock',x.item_id))}</td><td>${count(remaining)}</td><td><input data-receive-item="${x.item_id}" type="number" min="0" max="${remaining}" step="any" value="${remaining}" aria-label="Quantity received for ${e(refLabel('stock',x.item_id))}"></td></tr>`;}).join('')}</tbody></table></div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="receive-form">Record receipt</button>`);
  $('#receive-form').addEventListener('submit',async event=>{event.preventDefault();try{await runAction('purchases',order.id,'receive',{items:$$('[data-receive-item]').map(input=>({item_id:input.dataset.receiveItem,qty:Number(input.value)}))});}catch(error){formError(error.message);}});
}
function allocateDialog(payment) {
  const invoices=rows('invoices').filter(x=>x.customer_id===payment.customer_id&&x.status==='issued'&&x._balance>0);
  showDialog('Allocate a customer advance',`<form id="allocate-form"><div id="form-error" class="form-error"></div><div class="notice">${e(payment.number)} · ${e(refLabel('customers',payment.customer_id))} · Available ${rupees(payment._unallocated)}. Allocation records no new cash receipt.</div><div class="field"><label for="allocate-invoice">Same customer’s issued invoice</label><select name="invoice_id" id="allocate-invoice" required><option value="">Choose…</option>${invoices.map(x=>`<option value="${x.id}">${e(x.number)} · outstanding ${fmt(x._balance)}</option>`).join('')}</select></div>${fieldHTML(['amount','Allocate, NPR','number'],payment._unallocated)}</form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="allocate-form">Record allocation</button>`);
  $('#allocate-invoice').addEventListener('change',event=>{const invoice=find('invoices',event.target.value);if(invoice)$('#field-amount').value=Math.min(payment._unallocated,invoice._balance).toFixed(2);});
  $('#allocate-form').addEventListener('submit',async event=>{event.preventDefault();try{await runAction('payments',payment.id,'allocate',Object.fromEntries(new FormData(event.target)));}catch(error){formError(error.message);}});
}

function timerDialog(jobId='') {
  const eid=S.user.role==='technician'?S.user.employee_id:rows('employees').find(x=>x.active!==false)?.id||'';
  showDialog('Track actual task time',`<form id="timer-form"><div id="form-error" class="form-error"></div>${fieldHTML(['employee_id','Employee','ref','employees'],eid)}<div id="active-timer"></div><div id="timer-start-fields">${fieldHTML(['job_id','Assigned job','ref','jobs'],jobId)}${fieldHTML(['task','Task / operation','text'],'Service work')}</div>${fieldHTML(['notes','Completion note (when stopping)','textarea'])}</form>`,`<button class="btn" data-action="close">Close</button><button class="btn primary" type="submit" form="timer-form" id="timer-submit">Start task</button>`,false,'A staff member can have one running task at a time.');
  const update=()=>{const selected=$('#field-employee_id').value;const active=rows('time_entries').find(x=>x.employee_id===selected&&!x.end_at);$('#active-timer').innerHTML=active?`<div class="notice">Running: <b>${e(active.task)}</b> · ${e(refLabel('jobs',active.job_id))}<p>Started ${e(new Date(active.start_at).toLocaleString())}</p></div>`:'';$('#timer-start-fields').hidden=!!active;$('#timer-submit').textContent=active?'Stop task & save time':'Start task';};
  update();$('#field-employee_id').addEventListener('change',update);
  $('#timer-form').addEventListener('submit',async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));data.action=rows('time_entries').some(x=>x.employee_id===data.employee_id&&!x.end_at)?'stop':'start';try{await api('time',{business_id:S.bid,...data});$('#editor').close();await reload();toast(data.action==='stop'?'Task stopped; time saved.':'Task timer started.');}catch(error){formError(error.message);}});
}
function payrollReadHTML(record) {
  return `<div class="table-wrap"><table><thead><tr><th>Employee</th><th>Units / basis</th><th class="num">Base</th><th class="num">OT + bonus + commission</th><th class="num">Gross</th><th class="num">Deductions / withholding / employee contribution</th><th class="num">Net</th><th class="num">Employer cost</th></tr></thead><tbody>${record.lines.map(x=>`<tr><td>${e(x.name)}<div class="cell-sub">${e(x.deduction_note||'')}</div></td><td>${count(x.units)} ${e(x.basis)}</td><td class="num">${fmt(x.base)}</td><td class="num">${fmt(x.overtime+x.bonus+x.commission)}</td><td class="num">${fmt(x.gross)}</td><td class="num">${fmt(x.deductions+x.withholding+x.employee_contribution)}</td><td class="num">${fmt(x.net)}</td><td class="num">${fmt(x.employer_cost)}</td></tr>`).join('')}</tbody></table></div><div class="notice" style="margin-top:17px">Net pay: <b>${rupees(record.total_net)}</b> · Employer cost: <b>${rupees(record.total_cost)}</b></div>`;
}
function preparePayroll() {
  const first=S.state.today.slice(0,7)+'-01';let settings={};
  const employees=rows('employees').filter(x=>x.active!==false);
  if(!employees.length){toast('Add an employee and configure pay rates first.',true);editRecord('employees');return;}
  showDialog('Prepare payroll for review',`<form id="payroll-form"><div id="form-error" class="form-error"></div><div class="notice warning">Attendance suggests pay units and overtime; check them against your agreements. Contribution rates come from the employee profile. Enter applicable withholding and authorised deductions manually.</div><div class="inline-fields">${fieldHTML(['start_date','Pay period from, AD','date'],first)}${fieldHTML(['end_date','Pay period to, AD','date'],S.state.today)}<div class="field"><button type="button" class="btn" id="refresh-payroll-units">Suggest from attendance</button></div></div><div class="table-wrap"><table class="payroll-table"><thead><tr><th>Include / employee</th><th>Pay units</th><th>OT hours</th><th>Bonus</th><th>Withholding</th><th>Authorised deduction</th><th>Deduction reason</th><th>Contribution base</th><th>Eligible approved commissions</th></tr></thead><tbody id="payroll-lines"></tbody></table></div>${fieldHTML(['notes','Payroll review notes','textarea'])}<p class="inline-note">Monthly pay uses 1 unit for a full agreed month. Daily and hourly pay use approved days and hours. Review partial months and paid leave yourself. Overlapping approved runs for the same employee are blocked.</p></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="payroll-form">Calculate & save draft payroll</button>`,true);
  function suggest() {
    const start=$('#field-start_date').value,end=$('#field-end_date').value;
    employees.forEach(emp=>{const attendance=rows('attendance').filter(x=>x.employee_id===emp.id&&x.status==='approved'&&x.date>=start&&x.date<=end);const hours=attendance.reduce((n,x)=>n+x.hours,0);const units=emp.salary_type==='daily'?attendance.length:emp.salary_type==='hourly'?hours:1;const ot=emp.salary_type==='hourly'?0:attendance.reduce((n,x)=>n+Math.max(0,x.hours-(emp.shift_hours||8)),0);settings[emp.id]={include:true,units,ot:Math.round(ot*100)/100,bonus:0,withholding:0,deductions:0,deduction_note:'',contribution_base:Math.round(emp.base_salary*units*100)/100};});render();
  }
  function render() {
    const input=(emp,key,min=0)=>`<input name="${key}" type="${key==='deduction_note'?'text':'number'}" ${key==='deduction_note'?'class="deduction-note"':'step="any" min="'+min+'"'} value="${e(settings[emp.id][key])}" aria-label="${e(emp.name+' '+key.replaceAll('_',' '))}">`;
    $('#payroll-lines').innerHTML=employees.map(emp=>{const eligible=rows('commissions').filter(x=>x.employee_id===emp.id&&x.status==='approved'&&!x.reserved_payroll_id&&x._eligible>=x.amount);return `<tr data-payroll-employee="${emp.id}"><td class="person"><label><input name="include" type="checkbox" checked> ${e(emp.name)}</label><small>${e(emp.salary_type)} · ${rupees(emp.base_salary)} / unit</small><small>Contributions ${emp.employee_percent||0}% + ${emp.employer_percent||0}%</small></td><td>${input(emp,'units')}</td><td>${input(emp,'ot')}</td><td>${input(emp,'bonus')}</td><td>${input(emp,'withholding')}</td><td>${input(emp,'deductions')}</td><td>${input(emp,'deduction_note')}</td><td>${input(emp,'contribution_base')}</td><td><select name="commission_ids" multiple aria-label="${e(emp.name)} commissions">${eligible.map(x=>`<option value="${x.id}">${e(x.name)} · ${fmt(x.amount)}</option>`).join('')}</select></td></tr>`;}).join('');
  }
  suggest();$('#refresh-payroll-units').addEventListener('click',suggest);
  $('#payroll-form').addEventListener('submit',async event=>{event.preventDefault();const values=Object.fromEntries(new FormData(event.target));const lines=$$('[data-payroll-employee]').filter(tr=>$('[name=include]',tr).checked).map(tr=>{const value=name=>$(`[name=${name}]`,tr).value;return {employee_id:tr.dataset.payrollEmployee,units:Number(value('units')),overtime_hours:Number(value('ot')),bonus:Number(value('bonus')),withholding:Number(value('withholding')),deductions:Number(value('deductions')),deduction_note:value('deduction_note'),contribution_base:Number(value('contribution_base')),commission_ids:[...$('[name=commission_ids]',tr).selectedOptions].map(x=>x.value)};});const button=$('[type=submit][form=payroll-form]');button.disabled=true;try{const result=await api('payroll',{business_id:S.bid,start_date:values.start_date,end_date:values.end_date,notes:values.notes,lines});await reload();openRecord('payroll',result.id);toast('Payroll draft calculated. Review before approving.');}catch(error){formError(error.message);}finally{button.disabled=false;}});
}

function followAlert(key) {
  const alert=S.state.alerts.find(x=>x.key===key);if(!alert)return;
  const existing=rows('followups').find(x=>x.alert_key===key);
  const source=find(alert.type,alert.record_id);const customer=source?.customer_id?find('customers',source.customer_id):null;
  let message=`Hello${customer?.name?' '+customer.name:''}, following up from ${S.state.business.name}. `;
  if(alert.type==='invoices')message+=`Invoice ${source.number} has ${rupees(source._balance)} outstanding. Please confirm when payment can be made. Thank you.`;
  else if(alert.type==='quotes')message+=`Have you had a chance to review quotation ${source.number}, revision ${source.revision||1}, for ${rupees(source._totals.total)}? Please let us know whether you would like to proceed. Thank you.`;
  else if(alert.type==='jobs')message+=`We are checking the progress of ${source.name}. ${source.blocker?'Current update: '+source.blocker+'. ':''}We will confirm the next delivery update with you.`;
  else if(alert.type==='claims')message+=`Please share an update on claim ${source.reference||source.name}. ${source.next_action||'Please confirm the next approval or settlement step.'}`;
  else message+=alert.next_action;
  showDialog('Record a useful follow-up',`<form id="follow-alert-form"><div id="form-error" class="form-error"></div><div class="notice"><b>${e(alert.title)}</b><p>${e(alert.detail)}</p><p>${e(alert.next_action)}</p></div>${customer?.phone?`<p class="help-text" style="margin-bottom:15px">Customer contact: <b>${e(customer.phone)}</b> · ${e(customer.preferred_channel||'Phone')}</p>`:''}${fieldHTML(['message','Suggested message — review before sharing','textarea'],message)}<button type="button" id="copy-followup" class="btn small" style="margin-bottom:20px">Copy message</button><div class="form-grid">${fieldHTML(['due_date','Next follow-up, AD','date'],addDays(S.state.today,customer?.reminder_days||S.state.business.quote_followup_days||1))}${fieldHTML(['status','Outcome','select',['waiting','open','completed']],existing?.status||'waiting')}${fieldHTML(['employee_id','Responsible employee','ref','employees'],existing?.employee_id||'')}${fieldHTML(['channel','Contacted through','select',['Phone','SMS','WhatsApp','Email','In person','Internal']],existing?.channel||'Phone')}${fieldHTML(['notes','What happened? / agreed next step','textarea'],existing?.notes||'')}</div><p class="help-text">Waiting actions return on the next due date. Completed reminders stay hidden today; an unresolved underlying issue can return tomorrow.</p></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="follow-alert-form">Save follow-up</button>`);
  $('#copy-followup').addEventListener('click',()=>copyText($('#field-message').value));
  $('#follow-alert-form').addEventListener('submit',async event=>{event.preventDefault();const values=Object.fromEntries(new FormData(event.target));try{await api('record',{business_id:S.bid,kind:'followups',id:existing?.id,version:existing?.version,data:{...existing,...values,alert_key:key,name:alert.title,date:S.state.today,customer_id:source?.customer_id||'',job_id:alert.type==='jobs'?source.id:source?.job_id||'',next_action:alert.next_action}});$('#editor').close();await reload();toast('Follow-up saved with its next date.');}catch(error){formError(error.message);}});
}
async function copyText(text) {
  try {await navigator.clipboard.writeText(text);toast('Message copied.');}
  catch(_){const area=document.createElement('textarea');area.value=text;document.body.append(area);area.select();const success=document.execCommand('copy');area.remove();toast(success?'Message copied.':'Select the message text and copy it.',!success);}
}
async function ask(question) {
  if(S.offline){toast('Connect to refresh the assistant’s answers.',true);return;}
  if(!$('#assistant-answer')){S.page='today';S.tab='';S.query='';renderShell();}
  $('#assistant-answer').innerHTML='<div class="assistant-answer muted">Checking your saved records…</div>';
  try{const result=await api('assistant',{business_id:S.bid,question});if($('#assistant-answer'))$('#assistant-answer').innerHTML=`<div class="assistant-answer">${e(result.answer)}<small>${e(result.basis)}</small></div>`;}
  catch(error){if($('#assistant-answer'))$('#assistant-answer').innerHTML=`<div class="assistant-answer danger-text">${e(error.message)}</div>`;}
}
function renderReports() {
  if(!owner())return;
  if(!S.reportStart)S.reportStart=S.state.today.slice(0,7)+'-01';if(!S.reportEnd)S.reportEnd=S.state.today;
  const inPeriod=value=>value&&value.slice(0,10)>=S.reportStart&&value.slice(0,10)<=S.reportEnd;
  const invoices=rows('invoices').filter(x=>x.status==='issued'&&inPeriod(x.date));const credits=rows('credits').filter(x=>inPeriod(x.date));
  const net=invoices.reduce((n,x)=>n+x._totals.net,0)-credits.reduce((n,x)=>n+x.net,0);
  const tax=invoices.reduce((n,x)=>n+x._totals.tax,0)-credits.reduce((n,x)=>n+x.tax,0);
  const receipts=rows('payments').filter(x=>inPeriod(x.date));const cash=receipts.reduce((n,x)=>n+(x.direction==='refund'?-1:1)*x.amount,0);
  const expenses=rows('expenses').filter(x=>inPeriod(x.date));const spent=expenses.reduce((n,x)=>n+x.amount,0);
  const payroll=rows('payroll').filter(x=>x.status==='paid'&&inPeriod(x.pay_at||x.paid_at));const salaries=payroll.reduce((n,x)=>n+x.total_net,0);
  const incentives=rows('commissions').filter(x=>x.status==='paid'&&!x.payroll_id&&inPeriod(x.paid_at)).reduce((n,x)=>n+x.amount,0);
  const billedIds=new Set(invoices.map(x=>x.job_id));const jobs=rows('jobs').filter(x=>billedIds.has(x.id));
  const outstanding=rows('invoices').filter(x=>x.status==='issued'&&x._balance>0);
  const ageing=[['Not yet due',0],['1–30 days',0],['31–60 days',0],['61–90 days',0],['Over 90 days',0]];
  outstanding.forEach(invoice=>{const days=invoice.due_date?Math.floor((new Date(S.state.today+'T12:00:00Z')-new Date(invoice.due_date+'T12:00:00Z'))/86400000):0;ageing[days<=0?0:days<=30?1:days<=60?2:days<=90?3:4][1]+=invoice._balance;});
  const maxAge=Math.max(1,...ageing.map(x=>x[1]));
  const stageCount=Object.entries(rows('jobs').filter(x=>x.stage!=='Delivered').reduce((all,x)=>{all[x.stage]=(all[x.stage]||0)+1;return all;},{}));const maxStage=Math.max(1,...stageCount.map(x=>x[1]));
  const sources=Object.entries(expenses.reduce((all,x)=>{all[x.category||'Other']=(all[x.category||'Other']||0)+x.amount;return all;},{})).sort((a,b)=>b[1]-a[1]);
  $('#content').innerHTML=pageHead('Read your business numbers.','Billed revenue, cash collections, job contribution, and current receivables.',`<button class="btn" data-action="export">↓ Export business records</button>`,'REPORTS')+`<div class="card"><div class="filterbar"><div class="month-filter"><label for="report-start">From</label><input id="report-start" type="date" value="${e(S.reportStart)}"><label for="report-end">To</label><input id="report-end" type="date" value="${e(S.reportEnd)}"><button class="btn small" id="report-apply">Apply</button></div><span class="muted"><small>Document dates in AD · ${currency()}</small></span></div></div><div class="stats">${stat('Net billed revenue',rupees(net),'Invoice net amounts less dated credits')}${stat('Output VAT',rupees(tax),'Billed VAT less credit VAT')}${stat('Net receipts',rupees(cash),'Receipts less refunds; includes advances')}${stat('Recorded cash movement',rupees(cash-spent-salaries-incentives),'After expenses and marked-paid net payroll',true)}</div><div class="notice warning">This is an operating report, not a full general ledger or VAT return. Purchase orders do not post supplier bills; input VAT, unrecorded remittances, depreciation, and statutory filings are outside this report.</div><div class="grid-2"><div><section class="card"><div class="card-head"><div><h2>Job contribution</h2><p>Whole-job figures for jobs invoiced during this period.</p></div><span class="badge amber">${jobs.filter(x=>x._cost_provisional).length} provisional</span></div><div class="table-wrap"><table><thead><tr><th>Job</th><th class="num">Net revenue</th><th class="num">Direct costs</th><th class="num">Contribution</th></tr></thead><tbody>${jobs.map(x=>`<tr><td><button class="record-link" data-action="open" data-kind="jobs" data-id="${x.id}">${e(x.name)}</button><div class="cell-sub">${x._cost_provisional?'Costs provisional':'Costs checked'}</div></td><td class="num">${fmt(x._revenue)}</td><td class="num">${fmt(x._cost)}</td><td class="num ${x._contribution<0?'negative':''}">${fmt(x._contribution)}</td></tr>`).join('')}</tbody></table>${jobs.length?'':empty('No billed jobs in this period','Issue an invoice linked to a job to measure its recorded contribution.')}</div><div class="card-footer">Excludes business overhead. Avoid adding payroll again to costs already estimated from task time.</div></section><section class="card"><div class="card-head"><h2>Current receivables by customer</h2><button class="btn text small" data-action="csv" data-kind="invoices">Invoice CSV →</button></div><div class="card-body">${rows('customers').map(customer=>({customer,balance:outstanding.filter(x=>x.customer_id===customer.id).reduce((n,x)=>n+x._balance,0)})).filter(x=>x.balance>0).sort((a,b)=>b.balance-a.balance).map(({customer,balance})=>`<div class="summary-line"><button class="record-link" data-action="open" data-kind="customers" data-id="${customer.id}">${e(customer.name)}</button><b>${rupees(balance)}</b></div>`).join('')||'<p class="help-text">No outstanding issued invoices.</p>'}</div></section></div><div><section class="card"><div class="card-head"><h2>Receivable ageing · as of today</h2></div><div class="card-body">${ageing.map(([name,value])=>`<div class="chartbar"><span>${name}</span><div class="track"><div class="fill" style="width:${value/maxAge*100}%"></div></div><b class="num">${count(value)}</b></div>`).join('')}<p class="help-text">Measured from the invoice due date. Missing due dates appear in “not yet due”.</p></div></section><section class="card"><div class="card-head"><h2>Recorded outflow in this period</h2></div><div class="card-body">${sources.map(([name,value])=>`<div class="summary-line"><span>${e(name)}</span><b>${rupees(value)}</b></div>`).join('')}<div class="summary-line"><span>Marked-paid net payroll</span><b>${rupees(salaries)}</b></div><div class="summary-line"><span>Commissions paid outside payroll</span><b>${rupees(incentives)}</b></div></div></section><section class="card"><div class="card-head"><h2>Current workshop load</h2></div><div class="card-body">${stageCount.map(([name,value])=>`<div class="chartbar"><span>${e(name)}</span><div class="track"><div class="fill alt" style="width:${value/maxStage*100}%"></div></div><b class="num">${value}</b></div>`).join('')||'<p class="help-text">No open job cards.</p>'}</div></section></div></div>`;
  $('#report-apply').addEventListener('click',()=>{const start=$('#report-start').value,end=$('#report-end').value;if(!start||!end||start>end){toast('Choose a valid date range.',true);return;}S.reportStart=start;S.reportEnd=end;renderReports();});
}

const businessFields=[
  ['name','Business name *','text'],['sector','Business type','select',['Garage / collision / paint','Garage & collision repair','Vehicle showroom','Retail & trading','Service & repair business','Vehicle service','Equipment / appliance repair','Professional services','Retail / trades','Other local business']],['address','Business address','text'],['phone','Business phone','tel'],['email','Business email','email'],['pan','PAN / VAT number','text'],['fiscal_label','Fiscal year label (manual, optional)','text'],['vat_registered','VAT registered','checkbox'],['vat_rate','Default VAT rate, %','number'],['quote_followup_days','Follow up unanswered quotes after, days','number'],['payment_terms_days','Default payment terms, days','number'],['goal','What do you want to improve?','text',null,'For example: collect insurance balances, shorten painting delays, or increase repeat customers.'],['services_summary','Main services / business context','textarea'],['stages_text','Job stages — one per line','textarea',null,'Include Ready and Delivered if you use the delivery workflow.'],['bays_text','Bays / service areas — one per line','textarea'],['daily_capacity','Typical appointments per day','number'],['terms','Default quotation / invoice terms','textarea'],['print_style','Default print layout','select',['classic','compact','modern']],['print_font_size','Default print font, pt','number'],
];
function editBusiness(id='') {
  if(!id)return setupWizard();
  const existing=S.businesses.find(x=>x.id===id);
  const stages=['Intake','Awaiting approval','Awaiting parts','Body repair','Preparation','Painting','Curing','Reassembly','Quality check','Ready','Delivered'];
  const data={name:'',sector:'Garage / collision / paint',address:'',phone:'',email:'',pan:'',vat_registered:true,vat_rate:13,quote_followup_days:3,payment_terms_days:7,goal:'Keep jobs on time and collect outstanding payments.',daily_capacity:8,terms:'Prices apply to the scope listed. Additional work requires customer approval.\nParts and material availability may affect the delivery date.\nPayment is due as agreed on the invoice.',print_style:'classic',print_font_size:11,...existing};
  data.stages_text=(data.stages||stages).join('\n');data.bays_text=(data.bays||['Body bay','Paint booth','Service bay']).join('\n');
  showDialog(existing?'Business settings':'Set up your business',`<form id="business-form"><div id="form-error" class="form-error"></div><div class="form-grid">${businessFields.filter(x=>!['pan','vat_registered','vat_rate'].includes(x[0])).map(field=>fieldHTML(field,data[field[0]])).join('')}${regionFields(data)}</div>${existing?'':fieldHTML(['demo','Start with clearly fictional demo records','checkbox'],false)}<div class="notice warning">AD dates drive reminders. BS dates and the fiscal label are manually entered. Review tax and payroll with your accountant. Government filing and electronic invoice integrations are separate. Country and currency are retained once monetary records exist.</div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="business-form">${existing?'Save settings':'Create business'}</button>`,true,'Each business has separate records, numbering, and role access.');
  $('#field-sector').addEventListener('change',event=>{
    const garage=event.target.value.includes('Garage');const suggested=garage?stages:['Intake','Awaiting approval','Awaiting parts','In progress','Quality check','Ready','Delivered'];$('#field-stages_text').value=suggested.join('\n');
  });
  $('#business-form').addEventListener('submit',async event=>{event.preventDefault();const input=readFields(event.target,businessFields,data);input.stages=input.stages_text.split('\n').map(x=>x.trim()).filter(Boolean);input.bays=input.bays_text.split('\n').map(x=>x.trim()).filter(Boolean);delete input.stages_text;delete input.bays_text;input.country=data.country||'NP';for(const key of ['state_code','gst_registration','gstin','vat_rate','pan'])if(event.target.elements[key])input[key]=event.target.elements[key].value;if(event.target.elements.einvoice_required)input.einvoice_required=event.target.elements.einvoice_required.checked;if(event.target.elements.vat_registered)input.vat_registered=event.target.elements.vat_registered.checked;input.demo=existing?!!existing.demo:!!$('#field-demo')?.checked;const demo=!existing&&input.demo;try{const result=await api('businesses',{id:existing?.id,version:existing?.version,data:input,demo});S.bid=result.id;$('#editor').close();await loadBusinesses();toast(existing?'Business settings saved.':'Business created. Start with a customer or quotation.');}catch(error){formError(error.message);}});
}
function renderSettings() {
  const b=S.state.business;
  $('#content').innerHTML=pageHead('Make your desk work for you.','Business preferences, staff access, data backups, and migration.',owner()?'<button class="btn" data-action="new-business">+ Add another business</button>':'','SETTINGS')+`<div class="split-settings"><div><section class="card"><div class="card-head"><h2>Business profile</h2>${owner()?'<button class="btn small" data-action="edit-business">Edit profile</button>':''}</div><div class="card-body"><h2>${e(b.name)}</h2><p class="muted" style="margin:8px 0 18px">${e(b.sector)} · ${e(b.address||(indian()?'India':'Nepal'))}</p><div class="summary-line"><span>${indian()?'GSTIN':'PAN / VAT'}</span><b>${e((indian()?b.gstin:b.pan)||'Not entered')}</b></div><div class="summary-line"><span>${indian()?'GST':'VAT'} default</span><b>${b.vat_registered===false?'No VAT':e(b.vat_rate)+'%'}</b></div><div class="summary-line"><span>Quote follow-up</span><b>${count(b.quote_followup_days)} days</b></div><div class="summary-line"><span>Payment terms</span><b>${count(b.payment_terms_days)} days</b></div><div class="form-section"><h3>Your business focus</h3><p class="help-text" style="margin-top:8px">${e(b.goal||'Keep work moving and collections on time.')}</p><p class="help-text" style="margin-top:8px">${e(b.services_summary||'')}</p></div><div class="form-section"><h3>Work stages</h3><div class="pill-group" style="margin-top:12px">${S.state.stages.map(x=>`<span>${e(x)}</span>`).join('')}</div></div></div></section><section class="card"><div class="card-head"><h2>Your account</h2></div><div class="card-body"><p><b>${e(S.user.name)}</b> · ${e(S.user.username)}</p><p class="help-text" style="margin:6px 0 15px">Role: ${e(S.user.role)}. Accounts and passwords are managed by your business server.</p><button class="btn" data-action="password">Change password</button></div></section>${owner()?`<section class="card"><div class="card-head"><h2>Import older quotations</h2></div><div class="card-body"><p class="help-text">Import saved quotation JSON from the older app. Original dates and references are kept for review. Generated competitor variants become labelled hypothetical scenarios.</p><div class="actions" style="margin-top:16px"><button class="btn" data-action="legacy-import">Import JSON</button><button class="btn" data-action="legacy-help">Export guide</button></div></div></section>`:''}</div><div>${owner()?`<section class="card"><div class="card-head"><h2>Backups & data</h2></div><div class="card-body"><div class="notice">All businesses, accounts, original files, and records are on this server. Only the owner can download its complete database. Keep a backup on a separate device.</div><div class="quick-grid"><button class="btn" data-action="backup">↓ Full backup</button><button class="btn" data-action="restore">Restore backup</button><button class="btn" data-action="export">↓ Record JSON</button><button class="btn" data-action="csv" data-kind="invoices">↓ Invoice CSV</button></div><p class="inline-note">A backup is taken at startup and daily while the server runs. The latest 14 daily backups are retained in the data/backups folder. A safety backup is taken before restore.</p><p class="help-text">Record JSON is a readable export, not a full restore file; use the SQLite backup for recovery.</p></div></section><section class="card"><div class="card-head"><div><h2>Staff accounts</h2><p>Access is restricted by role and business.</p></div><button class="btn small" data-action="add-account">+ Account</button></div><div class="card-body" id="accounts-list"><p class="muted">Loading accounts…</p></div></section>`:''}<section class="card"><div class="card-head"><h2>How this workspace runs</h2></div><div class="card-body"><p class="help-text">Local installation: keep the server running. Private hosting: staff share the HTTPS server. Saved browser drafts can sync when the connection returns.</p><p class="help-text" style="margin-top:12px">Hosted workspaces keep each organisation’s records separate. Bank transfers, payroll remittances, SMS, WhatsApp and tax submissions are recorded or handled separately.</p></div></section>${owner()?`<section class="card"><div class="card-head"><h2>Recent audit trail</h2></div><div class="card-body"><ul class="timeline">${S.state.audit.slice(0,8).map(x=>`<li><b>${e(x.action)} · ${e(models[x.kind]?.singular||'Business')}</b><small>${e(x.user_name)} · ${e(new Date(x.created_at).toLocaleString())}</small><div class="audit-detail">${e(x.detail)}</div></li>`).join('')||'<li>No changes recorded yet.</li>'}</ul></div></section>`:''}</div></div>`;
  $('#content').insertAdjacentHTML('afterbegin',`<div class="workspace-tools">${owner()?'<button class="btn" data-action="personalise">Personalise this business</button><button class="btn" data-action="customise-workspace">Choose workspace modules</button>':''}<button class="btn" data-action="offline-settings">Offline drafts on this device</button><button class="btn" data-action="sync">Review sync</button></div>`);
  if(owner()){$('#content').insertAdjacentHTML('afterbegin',studioSettings());loadAccounts();}
  if(S.health?.cloud){const restore=$('[data-action=restore]');restore?.remove();const backupButton=$('[data-action=backup]');if(backupButton){backupButton.textContent='Download organisation export';const card=backupButton.closest('.card-body');$('.notice',card).textContent='This export contains your organisation’s business records and original attachments. Accounts and passwords are excluded. It is not a database restore file.';for(const node of $$('.inline-note,.help-text',card))node.textContent='Hosted recovery requires database-provider backups and a verified restore. Ask your administrator for retention and recovery results.';}}
}
async function loadAccounts() {
  try{S.accounts=await api('users');if(!$('#accounts-list'))return;$('#accounts-list').innerHTML=S.accounts.map(account=>`<div class="mini-row"><div class="grow"><b>${e(account.name)}</b><p>${e(account.username)} · ${e(account.role)} · ${account.role==='owner'?'All businesses':account.business_ids.map(id=>e(S.businesses.find(x=>x.id===id)?.name||'Business')).join(', ')}</p></div>${status(account.active?'active':'inactive')}${account.id!==S.user.id?`<button class="btn small" data-action="account-status" data-id="${account.id}">${account.active?'Disable':'Enable'}</button><button class="btn text small" data-action="reset-password" data-id="${account.id}">Password</button>`:''}</div>`).join('');}
  catch(error){if($('#accounts-list'))$('#accounts-list').textContent=error.message;}
}
function addAccount() {
  showDialog('Create a local account',`<form id="account-form"><div id="form-error" class="form-error"></div><div class="form-grid">${fieldHTML(['name','Full name','text'])}${fieldHTML(['username','Username','text'])}${fieldHTML(['password','Initial password, at least 12 characters','password'])}${fieldHTML(['role','Access role','select',['frontdesk','technician','cashier','stock_clerk','manager','owner']],'frontdesk')}<div class="field full"><label for="account-businesses">Business access (Ctrl / Command for multiple)</label><select id="account-businesses" name="business_ids" multiple class="select-multiple">${S.businesses.map(x=>`<option value="${x.id}" ${x.id===S.bid?'selected':''}>${e(x.name)}</option>`).join('')}</select></div>${fieldHTML(['employee_id','Employee link (required for a technician)','ref','employees'])}</div><div class="notice">Owners can see all businesses and payroll. Managers cannot see salary or commission records. Front desk handles customers, quotes, jobs and claims. Cashiers issue bills and record receipts, supplier payments and expenses. Technicians see assigned jobs and their own attendance and timers.</div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="account-form">Create account</button>`);
  $('#account-form').addEventListener('submit',async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));data.business_ids=new FormData(event.target).getAll('business_ids');try{await api('users',data);$('#editor').close();await loadAccounts();toast('Local account created.');}catch(error){formError(error.message);}});
}
function passwordDialog(id='') {
  const own=!id||id===S.user.id;
  showDialog(own?'Change your password':'Reset local account password',`<form id="password-form"><div id="form-error" class="form-error"></div>${own?fieldHTML(['current_password','Current password','password']):''}${fieldHTML(['password','New password (at least 12 characters)','password'])}${fieldHTML(['repeat','Repeat new password','password'])}</form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="password-form">Save password</button>`);
  $('#password-form').addEventListener('submit',async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));if(data.password!==data.repeat){formError('The two passwords do not match.');return;}try{await api('account',{...data,id:id||S.user.id});$('#editor').close();toast('Password updated.');}catch(error){formError(error.message);}});
}
function download(blob,name) {const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);}
async function backup() {const blob=await api('backup',{});download(blob,S.health?.cloud?`organisation-export-${S.state.today}.json`:`business-desk-backup-${S.state.today}.sqlite3`);toast('Backup downloaded. Keep a copy on a separate device.');}
function restoreDialog() {
  showDialog('Restore a complete local backup',`<form id="restore-form"><div id="form-error" class="form-error"></div><div class="notice warning">This replaces all businesses, users, files, and records with the selected backup. The current database is backed up first. You will sign in using the account stored in the restored backup.</div><div class="field"><label for="restore-file">Business Desk SQLite backup (up to 100 MB)</label><input id="restore-file" type="file" accept=".sqlite3,.db" required></div><div class="field"><label for="restore-confirm">Type RESTORE to confirm replacement</label><input id="restore-confirm" required autocomplete="off"></div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn danger" type="submit" form="restore-form">Restore selected backup</button>`);
  $('#restore-form').addEventListener('submit',async event=>{event.preventDefault();const file=$('#restore-file').files[0];if($('#restore-confirm').value!=='RESTORE'){formError('Type RESTORE to confirm.');return;}if(file.size>100*1024*1024){formError('Choose a backup smaller than 100 MB.');return;}const button=$('[type=submit][form=restore-form]');button.disabled=true;try{await api('restore',{content:await fileBase64(file)});$('#editor').close();S.user=null;S.state=null;S.bid='';renderAuth(false);toast('Backup restored. Sign in using its stored account.');}catch(error){formError(error.message);}finally{button.disabled=false;}});
}
function importDialog() {
  showDialog('Import older saved quotations',`<form id="import-form"><div id="form-error" class="form-error"></div><div class="notice">Imported quotations are editable drafts. Duplicate source records are skipped. Review each customer, original date, and price before sending.</div><div class="field"><label for="import-file">Older saved quotation JSON</label><input id="import-file" type="file" accept=".json,application/json" required></div></form>`,`<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="import-form">Import into this business</button>`);
  $('#import-form').addEventListener('submit',async event=>{event.preventDefault();try{const input=JSON.parse(await $('#import-file').files[0].text());const quotes=Array.isArray(input)?input:input.qg_saved_v9||input.quotes;if(!Array.isArray(quotes))throw new Error('Expected an array of old saved quotation records.');const result=await api('import',{business_id:S.bid,quotes});$('#editor').close();await reload();toast(`${result.imported} quotations imported; ${result.skipped} duplicates skipped.`);}catch(error){formError(error.message);}});
}
function legacyHelp() {
  const script=`const saved = localStorage.getItem('qg_saved_v9') || '[]';\nconst a = document.createElement('a');\na.href = URL.createObjectURL(new Blob([saved], {type: 'application/json'}));\na.download = 'older-quotations.json';\na.click();`;
  showDialog('Export from the older quotation app',`<p class="help-text">Open your older app in the browser that contains your saved quotations. If it has a JSON export, use that. For the known older code, its saved list uses the browser key <b>qg_saved_v9</b>.</p><p class="help-text" style="margin:15px 0">You can review and run the following small snippet in that app’s browser developer console to download only that saved list, then import the JSON here.</p><textarea readonly id="legacy-script" rows="8" style="width:100%;font-family:monospace">${e(script)}</textarea><p class="inline-note">This migration targets the older repository format. The current working site may use a different storage format.</p>`,`<button class="btn" id="copy-legacy">Copy export snippet</button><button class="btn" data-action="close">Close</button>`);
  $('#copy-legacy').addEventListener('click',()=>copyText(script));
}

document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
  const {action,kind,id,page,operation,key}=button.dataset;
  try {
    if(await studioAction(button))return;
    if(action==='close'){$('#editor').close();return;}
    if(action==='reload-page'){location.reload();return;}
    if(action==='mobile-menu'){$('.layout').classList.toggle('nav-open');return;}
    if(action==='navigate'){S.page=page;S.tab='';S.query='';S.filter='';S.listQuery='';renderShell();return;}
    if(action==='tab'){S.tab=kind;S.filter='';S.listQuery='';renderContent();return;}
    if(action==='refresh'){await reload();toast('Records refreshed.');return;}
    if(action==='new'){editRecord(kind);return;}
    if(action==='open'){openRecord(kind,id);return;}
    if(action==='edit'){editRecord(kind,id);return;}
    if(action==='board'){S.board=!S.board;renderContent();return;}
    if(action==='new-business'){editBusiness();return;}
    if(action==='edit-business'){editBusiness(S.bid);return;}
    if(action==='timer'){timerDialog(button.dataset.job||'');return;}
    if(action==='payroll'){preparePayroll();return;}
    if(action==='record-action'){actionDialog(kind,id,operation);return;}
    if(action==='print'){printDialog(kind,id);return;}
    if(action==='comparison'){comparisonDialog(id);return;}
    if(action==='comparison-add'){editDocument('external_quotes','',{quote_id:id,vat_mode:find('quotes',id).vat_mode,vat_rate:find('quotes',id).vat_rate,simulation:false});return;}
    if(action==='scenario'){scenarioDialog(id);return;}
    if(action==='customer-quote'){editDocument('quotes','',{customer_id:id});return;}
    if(action==='invoice-payment'){const invoice=find('invoices',id);editRecord('payments','',{invoice_id:id,customer_id:invoice.customer_id,amount:Math.max(0,invoice._balance)});return;}
    if(action==='invoice-credit'){editRecord('credits','',{invoice_id:id});return;}
    if(action==='job-stock'){editRecord('movements','',{job_id:id,kind:'issue'});return;}
    if(action==='stock-movement'){const stock=find('stock',id);editRecord('movements','',{item_id:id,unit_cost:stock.cost});return;}
    if(action==='task-toggle'){const job=find('jobs',id);const data={...job,tasks:job.tasks.map((task,index)=>index===Number(button.dataset.index)?{...task,done:button.checked}:task)};await api('record',{business_id:S.bid,kind:'jobs',id,version:job.version,data});await reload();openRecord('jobs',id);return;}
    if(action==='archive'){showDialog('Archive an unused record',`<div id="form-error" class="form-error"></div><p class="help-text">Archive ${e(label(find(kind,id)))}? Posted entries and records linked to other work are retained.</p>`,`<button class="btn" data-action="close">Cancel</button><button class="btn danger" id="archive-confirm">Archive</button>`);$('#archive-confirm').addEventListener('click',async()=>{try{await api('archive',{business_id:S.bid,kind,id,version:find(kind,id).version});$('#editor').close();await reload();toast('Unused record archived.');}catch(error){formError(error.message);}});return;}
    if(action==='follow-alert'){followAlert(key);return;}
    if(action==='all-alerts'){S.page='followups';S.tab='followups';renderShell();return;}
    if(action==='ask'){await ask(button.dataset.question);return;}
    if(action==='add-account'){addAccount();return;}
    if(action==='password'){passwordDialog();return;}
    if(action==='reset-password'){passwordDialog(id);return;}
    if(action==='account-status'){const account=S.accounts.find(x=>x.id===id);await api('account',{id,active:!account.active});await loadAccounts();toast('Account access updated.');return;}
    if(action==='backup'){button.disabled=true;try{await backup();}finally{button.disabled=false;}return;}
    if(action==='restore'){restoreDialog();return;}
    if(action==='export'){const response=await fetch(`/api/export?business=${S.bid}&format=json`);if(!response.ok)throw new Error('Could not export records.');download(await response.blob(),`business-desk-records-${S.state.today}.json`);return;}
    if(action==='csv'){const response=await fetch(`/api/export?business=${S.bid}&format=csv&kind=${kind}`);if(!response.ok)throw new Error('Could not export this list.');download(await response.blob(),`${kind}-${S.state.today}.csv`);return;}
    if(action==='legacy-import'){importDialog();return;}
    if(action==='legacy-help'){legacyHelp();return;}
    if(action==='logout'){await DeskSync.logout();await api('logout',{});S.user=null;S.csrf='';S.state=null;S.query='';$('#editor').close();renderAuth(false);return;}
  }catch(error){toast(error.message,true);}
});
document.addEventListener('keydown',event=>{if(event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!$('#editor').open){event.preventDefault();$('#global-search')?.focus();}if(event.key==='Escape'&&S.query&&!$('#editor').open){S.query='';$('#global-search').value='';renderContent();}});
extendModels();
extendExperienceModels();
extendStudioModels();
init();
