'use strict';

// Small, locally rendered SVGs share one grid and stroke; no icon font or CDN.
const iconPaths={
  today:'<rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="7" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/><rect x="14" y="14" width="7" height="7" rx="2"/>',
  customers:'<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m3 10v-3a5 5 0 0 0-3-4"/>',
  sales:'<path d="M6 3h9l4 4v14H6zM14 3v5h5M9 12h7M9 16h5"/>',
  workshop:'<path d="m14 6 4 4m-4-4 1-3a6 6 0 0 0-7 8L3 17a3 3 0 0 0 4 4l6-7a6 6 0 0 0 8-7l-3 3"/>',
  insurance:'<path d="m12 3 8 3v6c0 4-5 8-8 9-3-1-8-5-8-9V6zM8 12l3 3 5-6"/>',
  money:'<rect x="3" y="5" width="18" height="15" rx="3"/><path d="M3 9h18m-5 5h3M7 3h10"/>',
  stock:'<path d="m12 3 9 5v9l-9 5-9-5V8zM3 8l9 5 9-5M12 13v9M8 5l9 5"/>',
  team:'<circle cx="12" cy="8" r="3"/><path d="M5 21v-3a7 7 0 0 1 14 0v3M4 4v7M1 7h6M19 7h3"/>',
  followups:'<rect x="4" y="5" width="16" height="16" rx="3"/><path d="M8 3v4m8-4v4M4 11h16m-11 5 2 2 4-4"/>',
  reports:'<path d="M4 3v18h17M8 17v-5m5 5V8m5 9V4"/>',
  settings:'<path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="16" cy="17" r="3"/>',
  pipeline:'<rect x="3" y="4" width="5" height="14" rx="1"/><rect x="10" y="4" width="5" height="9" rx="1"/><rect x="17" y="4" width="4" height="17" rx="1"/>',
  vehicles:'<path d="m5 9 2-5h10l2 5M3 10h18v8H3zM5 18v3m14-3v3M6 13h2m8 0h2"/>',
  search:'<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
  arrow:'<path d="M5 12h14m-6-6 6 6-6 6"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  refresh:'<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5"/>',
  logout:'<path d="M9 4H4v16h5m0-8h12m-4-4 4 4-4 4"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',
  spark:'<path d="m12 3 3 6 6 3-6 3-3 6-3-6-6-3 6-3z"/>',
  return:'<path d="M8 5 3 10l5 5M3 10h12a6 6 0 0 1 0 12"/>',
  command:'<path d="M8 8h8v8H8zM8 8H5a3 3 0 1 1 3-3v3m8 0V5a3 3 0 1 1 3 3h-3m0 8h3a3 3 0 1 1-3 3v-3m-8 0v3a3 3 0 1 1-3-3h3"/>',
};
function icon(name,cls=''){return `<svg class="app-icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${iconPaths[name]||iconPaths.sales}</svg>`;}
function currency(){return S.state?.business?.currency||'NPR';}
function indian(){return S.state?.business?.country==='IN';}
function localLabel(text){return String(text).replaceAll('NPR',currency()).replaceAll('PAN / VAT',indian()?'PAN':'PAN / VAT').replaceAll('VAT',indian()?'GST':'VAT');}
function stateChoices(value='',required=false,id='state_code',title='Registration state'){
  const options=S.state?.india_states||S.health?.india_states||{};
  return `<div class="field"><label for="field-${id}">${e(title)}</label><select id="field-${id}" name="${id}" ${required?'required':''}><option value="">Choose state…</option>${Object.entries(options).sort((a,b)=>a[1].localeCompare(b[1])).map(([code,name])=>`<option value="${code}" ${code===value?'selected':''}>${e(name)} (${code})</option>`).join('')}</select></div>`;
}
function regionFields(data,country=data.country||'NP'){
  if(country==='IN')return stateChoices(data.state_code||'')+fieldHTML(['gst_registration','GST registration','select',['unregistered','regular','composition']],data.gst_registration||'unregistered')+fieldHTML(['gstin','GSTIN','text'],data.gstin||'')+fieldHTML(['vat_rate','Default GST rate, % — confirm for your items','number'],data.vat_rate??0)+fieldHTML(['einvoice_required','My accountant says e-invoicing is required','checkbox'],data.einvoice_required||false);
  return fieldHTML(['pan','PAN / VAT number','text'],data.pan||'')+fieldHTML(['vat_registered','This business is VAT registered','checkbox'],data.vat_registered||false)+fieldHTML(['vat_rate','Default VAT rate, %','number'],data.vat_rate??13);
}
function workspaceOnboarding(profile='garage',draft={}){
  const country=draft.country||'NP',choice=profileChoices[profile];
  const field=(key,title,type='text')=>`<div class="field"><label for="setup-${key}">${title}</label><input id="setup-${key}" name="${key}" type="${type}" value="${e(draft[key]||'')}" ${key==='name'?'required':''}></div>`;
  showDialog('Your business. Your workspace.',`<form id="setup-business"><div id="form-error" class="form-error"></div><p class="help-text">Choose your work. We’ll organise the tools around it.</p><div class="profile-grid">${Object.entries(profileChoices).map(([key,p])=>`<button type="button" class="profile-choice ${profile===key?'selected':''}" data-profile-choice="${key}" aria-pressed="${profile===key}">${icon({garage:'workshop',showroom:'vehicles',retail:'stock',service:'followups'}[key])}<b>${p.name}</b><small>${p.description}</small></button>`).join('')}</div><div class="form-grid">${field('name','Business name')}${field('phone','Business phone','tel')}${field('address','Address')}<div class="field"><label for="setup-country">Country</label><select id="setup-country" name="country"><option value="NP" ${country==='NP'?'selected':''}>Nepal · NPR</option><option value="IN" ${country==='IN'?'selected':''}>India · INR</option></select></div>${field('speciality','Your speciality, e.g. dent and paint / appliance repair')}<div class="field"><label for="setup-goal">Your main business goal</label><input id="setup-goal" name="goal" value="${e(draft.goal||choice.focus)}"></div><div class="full form-section"><h3>Billing setup</h3><div class="form-grid" id="region-fields">${regionFields({...draft,vat_rate:draft.vat_rate??(country==='IN'?0:13)},country)}</div><p class="inline-note">Use rates and invoice details reviewed for your business. Government filing and e-invoicing are handled separately.</p></div></div></form>`, '<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="setup-business">Create my workspace</button>',true,'Free pilot · No payment details required');
  const read=()=>{const values=Object.fromEntries(new FormData($('#setup-business')));values.vat_registered=!!$('#field-vat_registered')?.checked;values.einvoice_required=!!$('#field-einvoice_required')?.checked;return values;};
  $$('[data-profile-choice]').forEach(button=>button.onclick=()=>workspaceOnboarding(button.dataset.profileChoice,{...read(),goal:''}));
  $('#setup-country').onchange=()=>{const next=read();next.vat_rate=next.country==='IN'?0:13;workspaceOnboarding(profile,next);};
  $('#setup-business').onsubmit=async event=>{event.preventDefault();const button=$('[form="setup-business"]');button.disabled=true;try{
    const result=await api('businesses',{data:{...read(),profile,quote_followup_days:2,payment_terms_days:7,print_style:'modern'}});S.bid=result.id;S.page='today';S.tab='';$('#editor').close();await loadBusinesses();toast('Workspace ready. Start with your first customer.');
  }catch(error){formError(error.message);button.disabled=false;}};
}

function extendExperienceModels(){
  Object.entries(sections).forEach(([key,value])=>value.icon=icon(key));
  models.customers.fields.push(['tags','Tags, separated by commas','text'],['preferred_language','Preferred language for contact','select',['English','Hindi','Nepali','Bengali','Tamil','Telugu','Marathi','Gujarati','Kannada','Malayalam','Punjabi','Other']],['discount_percent','Agreed default discount, %','number'],['payment_terms_days','Agreed payment terms, days','number'],['reminder_days','Follow up again after, days (0 = business default)','number'],['marketing_opt_in','Customer agreed to marketing contact','checkbox'],['gstin','GSTIN (India)','text'],['state_code','Customer state','india-state']);
  models.customers.defaults={...models.customers.defaults,preferred_language:'English',discount_percent:0,payment_terms_days:7,reminder_days:0,tags:[]};
  for(const kind of ['stock','services'])models[kind].fields.push(['category_label','Category / collection','text'],['tax_rate','Default line tax rate, %','number'],['hsn_sac','HSN / SAC (India)','text'],['cess_rate','Percentage cess, % (India)','number']);
  models.stock.fields.splice(2,0,['barcode','Barcode / scan code','text']);
  models.vehicles.fields.push(['hsn_sac','HSN (India)','text'],['tax_rate','GST rate, % (India)','number'],['cess_rate','Percentage cess, % (India)','number']);
  models.payments.fields.find(x=>x[0]==='method')[3].splice(3,0,'UPI');
  Object.assign(headers,{tags:'Tags',category_label:'Collection',barcode:'Barcode'});
}
function applyBusinessExperience(){
  const b=S.state.business,profile=b.profile||'garage';
  document.documentElement.dataset.brand=b.brand_color||'indigo';
  document.title=(b.workspace_name||b.name)+' · Business Desk';
  sections.workshop.name={garage:'Workshop',showroom:'Preparation',retail:'Order fulfilment',service:'Service work'}[profile];
  sections.sales.name={garage:'Estimates',showroom:'Quotations',retail:'Quotes & catalogue',service:'Proposals & catalogue'}[profile];
  sections.customers.name=profile==='service'?'Clients & assets':'Customers';
  models.jobs.name={garage:'Job cards',showroom:'Preparation jobs',retail:'Fulfilment orders',service:'Work orders'}[profile];
  models.jobs.singular={garage:'job card',showroom:'preparation job',retail:'fulfilment order',service:'work order'}[profile];
  models.jobs.defaults.stage=S.state.stages[0];
  models.customers.defaults.payment_terms_days=b.payment_terms_days??7;
  models.assets.defaults.asset_type=profile==='service'?'Equipment':'Vehicle';
  for(const kind of ['services','stock'])models[kind].defaults.tax_rate=b.vat_rate??(indian()?0:13);
}
function businessTools(){
  const b=S.state.business;
  showDialog('Personalise this business',`<form id="personalise-form"><div id="form-error" class="form-error"></div><div class="form-grid">${fieldHTML(['workspace_name','Workspace name','text'],b.workspace_name||b.name)}${fieldHTML(['speciality','Business speciality','text'],b.speciality)}${fieldHTML(['brand_color','Accent colour','select',['indigo','blue','emerald','orange']],b.brand_color||'indigo')}${fieldHTML(['goal','Your main business goal','text'],b.goal)}${fieldHTML(['job_checklist_text','Default work / handover checks — one per line','textarea'],(b.job_checklist||[]).join('\n'))}${fieldHTML(['terms','Default quotation / invoice terms','textarea'],b.terms)}<div class="full"><h3>Extra information your team needs</h3><p class="help-text">Add up to 20 fields to client, work, enquiry or asset records. Existing values stay with their records.</p><div id="custom-field-editor">${(b.custom_fields||[]).map(customDefinitionRow).join('')}</div><button class="btn small" id="add-custom-definition" type="button">${icon('plus')} Add field</button></div></div></form>`, '<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="personalise-form">Save personalisation</button>',true,'Shared across this business’s staff devices');
  $('#add-custom-definition').onclick=()=>{if($$('[data-definition]').length>=20)return toast('Use at most 20 custom fields.',true);$('#custom-field-editor').insertAdjacentHTML('beforeend',customDefinitionRow({}));};
  $('#custom-field-editor').onclick=event=>{const button=event.target.closest('[data-remove-definition]');if(button)button.closest('[data-definition]').remove();};
  $('#personalise-form').onsubmit=async event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));for(const key of ['kind','label','key','type'])delete data[key];data.custom_fields=$$('[data-definition]').map(row=>Object.fromEntries($$('input,select',row).map(x=>[x.name,x.value])));data.job_checklist=data.job_checklist_text.split('\n').map(x=>x.trim()).filter(Boolean);delete data.job_checklist_text;try{await api('businesses',{id:b.id,version:b.version,data:{...b,...data}});$('#editor').close();await reload();toast('Your business preferences are saved.');}catch(error){formError(error.message);}};
}
function customDefinitionRow(x){return `<div class="custom-definition" data-definition><select name="kind" aria-label="Field area">${[['customers','Customers'],['jobs','Work orders'],['leads','Enquiries'],['assets','Assets']].map(([k,t])=>`<option value="${k}" ${x.kind===k?'selected':''}>${t}</option>`).join('')}</select><input name="label" value="${e(x.label||'')}" placeholder="Label, e.g. preferred oil" aria-label="Field label" required maxlength="80"><input name="key" value="${e(x.key||'')}" placeholder="Key, e.g. preferred_oil" aria-label="Stable field key" pattern="[a-z][a-z0-9_]{0,30}" required><select name="type" aria-label="Field type">${['text','number','date'].map(t=>`<option ${t===x.type?'selected':''}>${t}</option>`).join('')}</select><button class="icon-button" type="button" data-remove-definition aria-label="Remove custom field">${icon('close')}</button></div>`;}
function customRecordFields(kind,data){return (S.state.business.custom_fields||[]).filter(x=>x.kind===kind).map(x=>fieldHTML(['custom__'+x.key,x.label,x.type],data.custom_fields?.[x.key]??'')).join('');}
function readCustomFields(form,kind,base={}){const data={...base};for(const field of S.state.business.custom_fields||[])if(field.kind===kind)data[field.key]=new FormData(form).get('custom__'+field.key)??data[field.key]??'';return data;}
function customDetails(kind,record){const fields=(S.state.business.custom_fields||[]).filter(x=>x.kind===kind&&record.custom_fields?.[x.key]!==undefined);return fields.length?`<div class="form-section"><h3>Your business details</h3><div class="detail-summary">${fields.map(x=>`<div><small>${e(x.label)}</small><b>${e(record.custom_fields[x.key])}</b></div>`).join('')}</div></div>`:'';}

let clientMetricCache=null;
function customerMetrics(customer){
  if(!clientMetricCache||clientMetricCache.state!==S.state){const map=new Map();for(const client of rows('customers'))map.set(client.id,{balance:0,spend:0,count:0,last:'',overdue:false,inactive:false,repeat:false});for(const invoice of rows('invoices')){if(invoice.status!=='issued')continue;const m=map.get(invoice.customer_id);if(!m)continue;m.balance+=invoice._balance;m.spend+=invoice._totals.total-invoice._credited;m.count++;if(invoice.date>m.last)m.last=invoice.date;m.overdue ||= invoice._balance>0&&invoice.due_date&&invoice.due_date<S.state.today;}for(const opening of rows('opening_balances')){const m=map.get(opening.customer_id);if(m)m.balance+=opening._balance;}for(const m of map.values()){m.inactive=!!m.last&&m.last<addDays(S.state.today,-90);m.repeat=m.count>1;}clientMetricCache={state:S.state,map};}
  return clientMetricCache.map.get(customer.id)||{balance:0,spend:0,count:0,last:'',overdue:false,inactive:false,repeat:false};
}
function customerSegments(list){
  const names={all:'All customers',owing:'Outstanding',repeat:'Repeat customers',inactive:'No sale in 90 days',consented:'Marketing consent'};
  const matches=(customer,key)=>{const m=customerMetrics(customer);return key==='all'||key==='owing'&&m.balance>0||key==='repeat'&&m.repeat||key==='inactive'&&m.inactive||key==='consented'&&customer.marketing_opt_in;};
  const selected=S.customerSegment||'all';
  const html=`<div class="segment-tabs" aria-label="Customer segments">${Object.entries(names).map(([key,name])=>`<button class="segment ${selected===key?'selected':''}" data-action="customer-segment" data-segment="${key}" aria-pressed="${selected===key}">${name}<span>${rows('customers').filter(x=>matches(x,key)).length}</span></button>`).join('')}</div>`;
  return {html,list:list.filter(x=>matches(x,selected))};
}
function customerHub(record){
  const m=customerMetrics(record);
  const timeline=['quotes','invoices','payments','jobs','leads','followups','appointments'].flatMap(kind=>rows(kind).filter(x=>x.customer_id===record.id).map(x=>({kind,...x}))).sort((a,b)=>(b.updated_at||b.date||'').localeCompare(a.updated_at||a.date||'')).slice(0,12);
  return `<div class="client-hub"><div class="client-identity"><span class="client-avatar">${e(record.name.slice(0,2).toUpperCase())}</span><div><h3>${e(record.name)}</h3><p>${e(record.preferred_language||'English')} · ${e(record.preferred_channel||'Phone')} · ${e(record.payment_terms_days??S.state.business.payment_terms_days)} day terms</p></div></div><div class="client-stats"><div><small>Net billed</small><strong>${rupees(m.spend)}</strong></div><div><small>Outstanding</small><strong>${rupees(m.balance)}</strong></div><div><small>Issued invoices</small><strong>${m.count}</strong></div></div><div class="chips">${(record.tags||[]).map(x=>`<span class="badge blue">${e(x)}</span>`).join('')}${m.overdue?'<span class="badge amber">Payment overdue</span>':''}</div><div class="actions">${can('invoices')?`<button class="btn primary" data-action="client-bill" data-id="${record.id}">New bill</button>`:''}${can('followups')?`<button class="btn" data-action="client-followup" data-id="${record.id}">Schedule follow-up</button>`:''}</div></div><div class="form-section"><h3>Relationship timeline</h3>${timeline.length?`<ul class="client-timeline">${timeline.map(x=>`<li><span class="timeline-icon">${icon({payments:'money',jobs:'workshop',followups:'followups',leads:'pipeline'}[x.kind]||'sales')}</span><div><button class="record-link" data-action="open" data-kind="${x.kind}" data-id="${x.id}">${e(label(x))}</button><small>${e(models[x.kind].singular)} · ${e(dateLabel(x.date||x.updated_at?.slice(0,10)))}</small></div>${x.status?status(x.status):''}</li>`).join('')}</ul>`:empty('A new relationship','Their enquiries, work, bills and follow-ups will appear here.')}</div>`;
}
function applyClientDefaults(data,customerId){const customer=find('customers',customerId);if(!customer)return data;return {...data,customer_id:customer.id,discount_percent:customer.discount_percent??0,due_date:addDays(data.date||S.state.today,customer.payment_terms_days??S.state.business.payment_terms_days??7),place_of_supply:customer.state_code||S.state.business.state_code||''};}
function quickBilling(customerId=''){
  if(!can('invoices'))throw new Error('Your role cannot create bills.');
  const b=S.state.business;let cart=[],selected=customerId,query='',category='';
  const catalogue=[...rows('stock').map(x=>({...x,kind:'stock'})),...rows('services').map(x=>({...x,kind:'services'}))];
  showDialog('Quick bill',`<div id="form-error" class="form-error"></div><div class="checkout"><section><label class="catalogue-search">${icon('search')}<input id="checkout-search" placeholder="Search item, SKU or scan barcode" aria-label="Search item, SKU or scan barcode" autocomplete="off"></label><div class="chips" id="catalogue-categories"></div><div class="catalogue-grid" id="checkout-catalogue"></div></section><aside class="checkout-cart"><h3>Current sale</h3>${fieldHTML(['checkout_customer','Customer','ref','customers'],customerId)}<div id="checkout-cart"></div><div class="notice" id="checkout-terms"></div><p class="inline-note">Review tax, quantities and totals on the bill before issuing. Saving a draft does not reserve stock.</p></aside></div>`, '<button class="btn" data-action="close">Close</button><button class="btn primary" id="checkout-review">Review bill</button>',true,'Catalogue prices and your customer’s agreed terms');
  function draw(){
    const customerForPrices=find('customers',selected);for(const item of cart)item.rate=agreedPrice(customerForPrices,item,item.qty);
    const categories=[...new Set(catalogue.map(x=>x.category_label).filter(Boolean))];
    $('#catalogue-categories').innerHTML=['',...categories].map(x=>`<button class="chip ${x===category?'selected':''}" data-category="${e(x)}">${e(x||'All items')}</button>`).join('');
    const filtered=catalogue.filter(x=>(!category||x.category_label===category)&&(!query||[x.name,x.sku,x.barcode].join(' ').toLowerCase().includes(query.toLowerCase())));
    $('#checkout-catalogue').innerHTML=filtered.length?filtered.slice(0,100).map(x=>`<button class="catalogue-item" data-catalogue-id="${x.id}" ${x.kind==='stock'&&x._quantity<=0?'disabled':''}><span class="catalogue-mark">${icon(x.kind==='stock'?'stock':'workshop')}</span><b>${e(x.name)}</b><small>${e(x.sku||x.category_label||x.category||'Service')}${x.kind==='stock'?' · '+count(x._quantity)+' in stock':''}</small><strong>${rupees(x.rate)}</strong></button>`).join(''):empty('No matching items',catalogue.length?'Try another name or barcode.':'Add services or stock from your catalogue first.');
    $('#checkout-cart').innerHTML=cart.length?cart.map((x,i)=>`<div class="cart-item"><div><b>${e(x.name)}</b><small>${rupees(x.rate)} / ${e(x.unit||'pc')}</small></div><label><span class="sr-only">Quantity for ${e(x.name)}</span><input type="number" step="any" min="0.0001" data-cart-qty="${i}" value="${x.qty}" aria-label="Quantity for ${e(x.name)}"></label><button class="icon-button" data-cart-remove="${i}" aria-label="Remove ${e(x.name)}">${icon('close')}</button></div>`).join(''):empty('Your sale starts here','Choose items from the catalogue.');
    const customer=find('customers',selected);$('#checkout-terms').textContent=customer?`${customer.discount_percent||0}% agreed discount · ${customer.payment_terms_days??b.payment_terms_days??7} day terms`:'Choose a customer to apply their terms.';
    $('#checkout-review').disabled=!cart.length||!selected;
  }
  function add(id){const item=catalogue.find(x=>x.id===id);if(!item)return;if(item.kind==='stock'&&item._quantity<=0)return toast('This item is out of stock.',true);const existing=cart.find(x=>x.id===id);if(existing)existing.qty++;else cart.push({...item,qty:1});draw();}
  $('#checkout-search').oninput=event=>{query=event.target.value;draw();};
  $('#checkout-search').onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();const exact=catalogue.filter(x=>x.barcode===event.target.value.trim()||x.sku===event.target.value.trim());if(exact.length===1){add(exact[0].id);query='';event.target.value='';draw();}else toast('Choose a matching item from the list.',true);}};
  $('#catalogue-categories').onclick=event=>{const button=event.target.closest('[data-category]');if(button){category=button.dataset.category;draw();}};
  $('#checkout-catalogue').onclick=event=>{const button=event.target.closest('[data-catalogue-id]');if(button)add(button.dataset.catalogueId);};
  $('#checkout-cart').onclick=event=>{const button=event.target.closest('[data-cart-remove]');if(button){cart.splice(Number(button.dataset.cartRemove),1);draw();}};
  $('#checkout-cart').onchange=event=>{if(event.target.matches('[data-cart-qty]')){const value=Number(event.target.value);if(!(value>0))return toast('Use a positive quantity.',true);cart[Number(event.target.dataset.cartQty)].qty=value;draw();}};
  $('#field-checkout_customer').onchange=event=>{selected=event.target.value;draw();};
  $('#checkout-review').onclick=()=>{if(cart.some(x=>x.kind==='stock'&&x.qty>x._quantity))return toast('A quantity exceeds the available stock. Review the cart.',true);editDocument('invoices','',applyClientDefaults({subject:b.profile==='retail'?'Counter sale':'Products and services',items:cart.map(x=>({description:x.name,qty:x.qty,unit:x.unit||'pc',rate:x.rate,discount:0,unit_cost:x.cost||0,tax_rate:x.tax_rate??b.vat_rate??0,hsn_sac:x.hsn_sac||'',cess_rate:x.cess_rate||0,category:x.category||'Part',...(x.kind==='stock'?{item_id:x.id}:{service_id:x.id})}))},selected));};
  draw();$('#checkout-search').focus();
}

function returnItems(invoice){
  const credits=rows('credits').filter(x=>x.invoice_id===invoice.id),lines=invoice._totals.lines;
  showDialog('Return / credit items',`<form id="return-form"><div id="form-error" class="form-error"></div><div class="notice">Credit the original invoice prices and tax. A credit reduces the balance; record an actual cash refund separately.</div><div class="return-items">${lines.map((x,i)=>{const returned=credits.flatMap(c=>c.return_lines||[]).filter(c=>c.line_index===i).reduce((n,c)=>n+c.qty,0),left=Math.max(0,x.qty-returned);return `<div class="return-item"><div><b>${e(x.description)}</b><small>${count(left)} remaining · original total ${rupees(x.total)}</small></div><div class="field"><label for="return-${i}">Return quantity</label><input id="return-${i}" data-return-index="${i}" type="number" min="0" max="${left}" step="any" value="0"></div>${x.item_id&&!invoice.job_id&&can('movements')?`<label class="return-restock"><input type="checkbox" data-restock-index="${i}"> Return to sellable stock</label>`:'<small>Credit only; no stock movement</small>'}</div>`;}).join('')}</div>${fieldHTML(['reason','Reason for return / credit','textarea'])}</form>`, '<button class="btn" data-action="close">Cancel</button><button class="btn primary" type="submit" form="return-form">Post credit</button>',true,invoice.number);
  $('#return-form').onsubmit=async event=>{event.preventDefault();const button=$('[form="return-form"]');button.disabled=true;try{const items=$$('[data-return-index]').map(input=>({line_index:Number(input.dataset.returnIndex),qty:Number(input.value),restock:!!$(`[data-restock-index="${input.dataset.returnIndex}"]`)?.checked})).filter(x=>x.qty>0);await runAction('invoices',invoice.id,'return',{items,reason:$('#field-reason').value});}catch(error){formError(error.message);button.disabled=false;}};
}
function taxBreakdown(totals){return Object.entries(totals.tax_components||{}).map(([key,amount])=>`<div class="summary-line tax-component"><span>${e(key)}</span><b>${rupees(amount)}</b></div>`).join('');}
function sectorFocus(){
  const profile=S.state.business.profile||'garage';
  if(profile==='retail')return `<section class="card"><div class="card-head"><div><h2>Restock before you run out</h2><p>Items at or below their reorder level.</p></div></div>${rows('stock').filter(x=>x._quantity<=x.reorder_at).slice(0,5).map(x=>`<div class="mini-row"><span class="catalogue-mark">${icon('stock')}</span><div class="grow"><button class="record-link" data-action="open" data-kind="stock" data-id="${x.id}">${e(x.name)}</button><p>${count(x._quantity)} ${e(x.unit)} available · reorder at ${count(x.reorder_at)}</p></div></div>`).join('')||empty('Stock levels look healthy','Set reorder levels on the products you track.')}</section>`;
  if(profile==='service')return `<section class="card"><div class="card-head"><div><h2>Upcoming visits</h2><p>Appointments for the next seven days.</p></div>${can('appointments')?'<button class="btn small" data-action="new" data-kind="appointments">Book visit</button>':''}</div>${rows('appointments').filter(x=>x.date>=S.state.today&&x.date<=addDays(S.state.today,7)&&!['cancelled','completed'].includes(x.status)).sort((a,b)=>(a.date+a.time).localeCompare(b.date+b.time)).slice(0,6).map(x=>`<div class="mini-row"><span class="visit-date">${e(dateLabel(x.date).split(' ').slice(0,2).join(' '))}<small>${e(x.time)}</small></span><div class="grow"><button class="record-link" data-action="open" data-kind="appointments" data-id="${x.id}">${e(x.name)}</button><p>${e(refLabel('customers',x.customer_id))}</p></div>${status(x.status)}</div>`).join('')||empty('No upcoming visits','Book a service visit and assign the team.')}</section>`;
  if(profile==='garage')return `<section class="card"><div class="card-head"><div><h2>Workshop queue</h2><p>Promised dates and blockers, together.</p></div><button class="btn small" data-action="navigate" data-page="workshop">View work</button></div>${rows('jobs').filter(x=>x.stage!==S.state.stages.at(-1)).sort((a,b)=>(a.due_date||'9999').localeCompare(b.due_date||'9999')).slice(0,5).map(x=>`<div class="mini-row"><span class="catalogue-mark">${icon('workshop')}</span><div class="grow"><button class="record-link" data-action="open" data-kind="jobs" data-id="${x.id}">${e(x.name)}</button><p>${e(x.blocker||refLabel('customers',x.customer_id))} · ${x.due_date?e(dateLabel(x.due_date)):'Set promised date'}</p></div>${status(x.stage)}</div>`).join('')||empty('Ready for your next job','Capture the complaint, agreed scope and delivery date.')}</section>`;
  return '';
}
function commandPalette(){
  if(!S.state)return;
  showDialog('Find something or take action',`<label class="command-search">${icon('search')}<input id="command-search" placeholder="Customer, invoice, action…" aria-label="Search commands and records" autocomplete="off"></label><div id="command-results"></div>`, '<span class="help-text">Enter to open the first result · Esc to close</span>',false);
  const draw=()=>{const q=$('#command-search').value.toLowerCase().trim();const actions=[{title:'Quick bill',kind:'invoices',action:'quick-bill'},...['customers','quotes','jobs','leads','followups','appointments'].map(kind=>({title:'New '+models[kind].singular,kind,action:'new'}))].filter(x=>can(x.kind)&&(!q||x.title.toLowerCase().includes(q)));
    const records=q?Object.entries(S.state.records).flatMap(([kind,list])=>list.filter(x=>[label(x),x.number,x.phone,x.registration,x.sku].join(' ').toLowerCase().includes(q)).map(x=>({kind,record:x}))).slice(0,12):[];
    $('#command-results').innerHTML=actions.map(x=>`<button class="command-result" data-command-action="${x.action}" data-kind="${x.kind}">${icon('plus')}<b>${e(x.title)}</b></button>`).join('')+records.map(({kind,record})=>`<button class="command-result" data-command-id="${record.id}" data-kind="${kind}">${icon('sales')}<span><b>${e(label(record))}</b><small>${e(models[kind]?.singular||kind)} · ${e(record.number||'')}</small></span></button>`).join('')||empty('No results','Try a name, phone number or invoice reference.');};
  $('#command-search').oninput=draw;$('#command-search').onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();$('#command-results button')?.click();}};
  $('#command-results').onclick=event=>{const button=event.target.closest('button');if(!button)return;if(button.dataset.commandId)openRecord(button.dataset.kind,button.dataset.commandId);else if(button.dataset.commandAction==='quick-bill')quickBilling();else editRecord(button.dataset.kind);};draw();$('#command-search').focus();
}
document.addEventListener('keydown',event=>{if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();commandPalette();}});
document.addEventListener('click',event=>{
  const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
  try{
    if(button.dataset.action==='personalise')businessTools();
    if(button.dataset.action==='quick-bill')quickBilling();
    if(button.dataset.action==='command')commandPalette();
    if(button.dataset.action==='return-items')returnItems(find('invoices',button.dataset.id));
    if(button.dataset.action==='customer-segment'){S.customerSegment=button.dataset.segment;renderContent();}
    if(button.dataset.action==='client-bill')quickBilling(button.dataset.id);
    if(button.dataset.action==='client-followup'){const c=find('customers',button.dataset.id);editRecord('followups','',{customer_id:c.id,name:'Follow up with '+c.name,channel:c.preferred_channel||'Phone',due_date:addDays(S.state.today,c.reminder_days||S.state.business.quote_followup_days||2)});}
  }catch(error){toast(error.message,true);}
});
