import {verifyStudio} from './studio.mjs';
import {verifyPremium} from './premium.mjs';
import {verifyExperience} from './experience.mjs';
import {createRequire} from 'node:module';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const require=createRequire(process.env.DESK_TEST_DEPS || import.meta.url);
const {chromium}=require('playwright');
const base=process.env.DESK_TEST_URL;
const out=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../verification');
await fs.mkdir(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.DESK_CHROMIUM||undefined,headless:true,args:['--no-sandbox','--no-zygote','--single-process','--disable-gpu','--disable-dev-shm-usage','--remote-debugging-port=9223']});
const context=await browser.newContext({viewport:{width:1440,height:1100}});
const page=await context.newPage();page.setDefaultTimeout(12000);
const errors=[];page.on('pageerror',error=>errors.push(error.message));
let checks=0;
const check=(truth,message)=>{if(!truth)throw new Error(message);checks++;};
const api=async(endpoint,data)=>page.evaluate(async({endpoint,data})=>{
  const health=await (await fetch('/api/health')).json();
  const r=await fetch('/api/'+endpoint,{method:data?'POST':'GET',headers:data?{'Content-Type':'application/json','X-CSRF-Token':health.csrf}:{},body:data?JSON.stringify(data):undefined});
  const body=await r.json();if(!r.ok)throw new Error(body.error);return body;
},{endpoint,data});
async function formSave(kind,values={}){
  await page.locator(`[data-action="new"][data-kind="${kind}"]`).first().click();
  for(const [key,value] of Object.entries(values)){
    const input=page.locator('#field-'+key);
    if(typeof value==='boolean')await input.setChecked(value);else if(await input.evaluate(node=>node.tagName)==='SELECT')await input.selectOption(value);else await input.fill(value);
  }
  await page.locator('[form="record-form"][type="submit"]').click();
  await page.waitForFunction(()=>!document.querySelector('#editor').open);
}
async function nav(name){const button=page.locator(`.sidebar [data-action="navigate"][data-page="${name}"]`);if(!await button.isVisible())await page.locator('[data-action=mobile-menu]').click();await button.click();}
async function close(){if(await page.locator('#editor').evaluate(x=>x.open))await page.locator('#editor [data-action="close"]').last().click();}
try{
  await page.goto(base);
  await page.getByLabel('Your name').fill('Fictional Pilot Owner');
  await page.getByLabel('Username',{exact:true}).fill('pilot-owner');
  await page.getByLabel('Password',{exact:true}).fill('test-only-password');
  await page.getByRole('button',{name:'Create owner account'}).click();
  await page.getByRole('button',{name:'Set up a business'}).click();
  await page.locator('[data-profile-choice="showroom"]').click();
  await page.getByLabel('Business name',{exact:true}).fill('H.R. Motors · Pilot demo');
  await page.getByLabel('Business phone').fill('9800000000');
  await page.getByLabel('Address',{exact:true}).fill('Kathmandu · fictional test data');
  await page.getByRole('button',{name:'Create my workspace'}).click();
  await page.locator('#sync-indicator').waitFor();
  check(await page.locator('.sidebar [data-page="vehicles"]').count()===1,'Showroom inventory navigation missing');
  check(await page.locator('.sidebar [data-page="insurance"]').count()===0,'Unselected garage module visible in showroom');
  if(process.env.DESK_AGENT_BROWSER){
    const result=await promisify(execFile)(process.env.DESK_AGENT_BROWSER,['--cdp','http://127.0.0.1:9223','snapshot','-i'],{timeout:20000});
    await fs.writeFile(path.join(out,'agent-browser-snapshot.txt'),result.stdout);check(result.stdout.includes('New bill'),'Agent browser could not see dashboard');
  }
  await nav('customers');await formSave('customers',{name:'Fictional Sita Sharma',phone:'9800000001'});
  let businesses=await api('businesses');const bid=businesses[0].id;
  let state=await api('state?business='+bid);const customer=state.records.customers[0];
  check(customer.name==='Fictional Sita Sharma','Customer form did not persist');
  await nav('vehicles');await formSave('vehicles',{name:'Fictional City EV · Premium',vin:'PILOT-CHASSIS-001',color:'Pearl white',model_year:'2026',sale_price:'4200000',purchase_cost:'3800000',location:'Main showroom'});
  state=await api('state?business='+bid);const vehicle=state.records.vehicles[0];
  check(vehicle.vin==='PILOT-CHASSIS-001','Vehicle did not persist');
  await page.getByRole('button',{name:'Dismiss notification'}).click();
  await page.screenshot({path:path.join(out,'vehicle-inventory-desktop.png'),fullPage:true});
  await nav('pipeline');await formSave('leads',{name:'Sita · City EV enquiry',customer_id:customer.id,vehicle_id:vehicle.id,expected_value:'4200000',next_action:'Confirm test drive and finance documents'});
  state=await api('state?business='+bid);let lead=state.records.leads[0];
  await page.locator(`[data-action="open"][data-id="${lead.id}"]`).first().click();
  await page.getByRole('button',{name:'Reserve vehicle',exact:true}).click();await page.locator('#confirm-action').click();
  await page.getByRole('button',{name:'Create / open invoice',exact:true}).click();await page.locator('#confirm-action').click();
  await page.getByRole('button',{name:'Issue & retain invoice',exact:true}).click();await page.locator('#confirm-action').click();
  await page.getByRole('button',{name:'Record receipt / refund',exact:true}).waitFor();
  state=await api('state?business='+bid);const invoice=state.records.invoices[0];
  check(invoice.status==='issued','Invoice did not issue');check(state.records.vehicles[0].status==='sold','Issued showroom invoice did not allocate vehicle');
  await page.getByRole('button',{name:'Record receipt / refund',exact:true}).click();
  await page.locator('#field-amount').fill('1000000');
  // Let the server commit, then lose its response. Sync must reuse the command ID.
  let dropped=false;
  await page.route('**/api/command',async route=>{if(!dropped){dropped=true;await route.fetch();await route.abort('failed');}else await route.continue();});
  await page.locator('[form="record-form"][type="submit"]').click();
  await page.getByText('Connection interrupted.',{exact:false}).waitFor();
  await close();await page.unroute('**/api/command');
  await page.locator('#sync-indicator').click();await page.locator('#sync-now').click();
  await page.getByText('No pending changes.',{exact:true}).waitFor();await close();
  state=await api('state?business='+bid);
  check(state.records.payments.length===1,'Lost response duplicated receipt');check(state.records.invoices[0]._balance===3200000,'Receipt balance incorrect');
  await nav('settings');await page.getByRole('button',{name:'Offline drafts on this device',exact:true}).click();
  await page.locator('#offline-pass').fill('offline-test-passphrase');await page.getByRole('button',{name:'Enable encrypted offline drafts'}).click();
  await page.waitForFunction(()=>!document.querySelector('#editor').open);
  await page.evaluate(()=>navigator.serviceWorker.ready);
  await nav('customers');await context.setOffline(true);
  await formSave('customers',{name:'Offline customer draft',phone:'9800000002'});
  check((await page.locator('#sync-indicator').textContent()).includes('1 pending'),'Offline draft not queued');
  await page.reload();await page.getByLabel('Offline passphrase',{exact:true}).fill('offline-test-passphrase');await page.getByRole('button',{name:'Unlock offline drafts'}).click();
  await page.locator('#sync-indicator').waitFor();check((await page.locator('#sync-indicator').textContent()).includes('1 pending'),'Offline reload lost pending draft');
  await context.setOffline(false);await page.waitForFunction(()=>document.querySelector('#sync-indicator')?.textContent==='Synced');
  state=await api('state?business='+bid);check(state.records.customers.filter(x=>x.name==='Offline customer draft').length===1,'Offline draft did not synchronise exactly once');
  // A conflicting edit must be retained for review, without changing the server.
  await nav('customers');await page.locator(`[data-action="open"][data-id="${customer.id}"]`).first().click();await page.getByRole('button',{name:'Edit',exact:true}).click();
  await context.setOffline(true);await page.locator('#field-phone').fill('local-offline-edit');await page.locator('[form="record-form"][type="submit"]').click();await page.waitForFunction(()=>!document.querySelector('#editor').open);
  // An independent API session represents a second staff device.
  const second=await require('playwright').request.newContext({baseURL:base});
  const login=await second.post('/api/login',{data:{username:'pilot-owner',password:'test-only-password'}});const auth=await login.json();
  const fresh=await (await second.get('/api/state?business='+bid)).json();const latest=fresh.records.customers.find(x=>x.id===customer.id);
  const update=await second.post('/api/command',{headers:{'X-CSRF-Token':auth.csrf},data:{operation_id:crypto.randomUUID(),endpoint:'record',data_epoch:fresh.data_epoch,payload:{business_id:bid,kind:'customers',id:latest.id,version:latest.version,data:{...latest,phone:'other-device-edit'}}}});
  check(update.ok(),'Second-device update failed');await second.dispose();
  await context.setOffline(false);await page.waitForFunction(()=>DeskSync.pending()[0]?.status==='conflict');
  await page.locator('#sync-indicator').click();await page.getByRole('button',{name:'Review saved change'}).click();
  check((await page.locator('textarea').last().inputValue()).includes('other-device-edit'),'Conflict review did not show server version');
  await page.getByRole('button',{name:'Discard this rejected change'}).click();await page.waitForFunction(()=>!document.querySelector('#editor').open);
  state=await api('state?business='+bid);check(state.records.customers.find(x=>x.id===customer.id).phone==='other-device-edit','Conflict overwrote server data');
  await nav('today');await page.getByRole('button',{name:'Dismiss notification'}).click();await page.screenshot({path:path.join(out,'dashboard-desktop.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:path.join(out,'dashboard-phone.png'),fullPage:true});
  check(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1),'Phone dashboard overflows viewport');
  check(await page.locator('.stat-amount').evaluateAll(nodes=>nodes.every(x=>x.scrollWidth<=x.clientWidth+1)),'Phone financial amounts do not fit their cards');
  await page.getByRole('button',{name:'New bill',exact:true}).click();
  await page.locator('#field-customer_id').selectOption(customer.id);
  await page.locator('[data-col="description"]').fill('Phone-entered service');
  await page.locator('[data-col="rate"]').fill('500');
  await page.locator('#document-totals').getByText('500.00',{exact:false}).first().waitFor();
  check(await page.locator('.line-table').evaluate(x=>x.scrollWidth<=window.innerWidth),'Phone bill editor requires horizontal scrolling');
  await page.screenshot({path:path.join(out,'billing-phone.png'),fullPage:true});
  await close();
  await verifyExperience({page,api,check,nav,close,formSave,out,fs});
  await verifyStudio({page,api,check,nav,close,formSave,out,fs});
  await verifyPremium({page,api,check,nav,close,formSave,out,fs});
  check(errors.length===0,'Browser exceptions: '+errors.join('; '));
  await fs.writeFile(path.join(out,'browser-results.json'),JSON.stringify({checks,errors,browser:await browser.version(),flows:['setup','showroom','invoice','lost-payment-response','offline-reload','sync','conflict-review','responsive-ui','india-gst','quick-billing','line-returns','client-personalisation','four-sectors','owned-branding','guided-configuration','csv-preview-import','agreed-prices','stock-count','opening-collections','customer-statement','cash-closing','inspection','large-list-rendering','dashboard-targets','focus-inbox','owner-portfolio','display-preferences','failed-business-switch','staff-ui-permissions','touch-layout','navigation-breakpoints','reduced-motion']},null,2));
  console.log(JSON.stringify({checks,errors,output:out}));
}catch(error){
  await page.screenshot({path:path.join(out,'failure.png'),fullPage:true}).catch(()=>{});
  const layout=await page.evaluate(()=>({width:innerWidth,height:innerHeight,page:S.page,business:S.state?.business?.profile,nodes:['.layout','.sidebar','.mobile-menu','.mobile-tabs','.workspace'].map(selector=>{const x=document.querySelector(selector);if(!x)return {selector,missing:true};const style=getComputedStyle(x),r=x.getBoundingClientRect();return {selector,display:style.display,visibility:style.visibility,position:style.position,transform:style.transform,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};})})).catch(()=>null);
  await fs.writeFile(path.join(out,'failure-layout.json'),JSON.stringify(layout,null,2));console.error(error);console.error('PAGE ERRORS',errors);process.exitCode=1;
}
finally{if(process.env.DESK_AGENT_BROWSER)await promisify(execFile)(process.env.DESK_AGENT_BROWSER,['close'],{timeout:10000}).catch(()=>{});await context.close().catch(()=>{});await browser.close();}
