'use strict';

// The server is authoritative. Offline drafts never issue invoices, reserve
// stock/vehicles, pay payroll, or claim to have posted a receipt.
const DeskSync = (() => {
  const commandPaths = new Set(['record', 'action', 'archive', 'time', 'payroll']);
  const draftKinds = new Set(['customers', 'quotes', 'leads', 'followups', 'attendance']);
  let pending = [], snapshot = null, key = null, salt = null, userId = '', syncing = false;
  let lastOnline = 0;
  let writerPromise = null, releaseWriter = null;
  const encoder = new TextEncoder(), decoder = new TextDecoder();
  const clone = value => JSON.parse(JSON.stringify(value));
  const uuid = () => crypto.randomUUID().replaceAll('-', '');
  const bucket = () => 'bd_pending_' + userId;
  function writer() {
    if (!navigator.locks) return Promise.resolve(!key);
    if (!writerPromise) writerPromise = new Promise(resolve => {
      navigator.locks.request('business-desk-writer-' + userId, {ifAvailable:true}, async lock => {
        resolve(!!lock);
        if (lock) await new Promise(done => { releaseWriter = done; });
      }).catch(() => resolve(false));
    });
    return writerPromise;
  }

  function storage() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('business-desk-v2', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('vaults', {keyPath: 'id'});
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }
  async function vault(method, value) {
    const db = await storage();
    try {
      return await new Promise((resolve, reject) => {
        const tx = db.transaction('vaults', method === 'getAll' ? 'readonly' : 'readwrite');
        const request = tx.objectStore('vaults')[method](value);
        let result;
        request.onsuccess = () => { result = request.result; };
        tx.oncomplete = () => resolve(result);
        tx.onerror = () => reject(tx.error);
        tx.onabort = () => reject(tx.error || new Error('Device storage is unavailable.'));
      });
    } finally { db.close(); }
  }
  async function derive(passphrase, savedSalt) {
    const material = await crypto.subtle.importKey('raw', encoder.encode(passphrase), 'PBKDF2', false, ['deriveKey']);
    return crypto.subtle.deriveKey({name: 'PBKDF2', salt: new Uint8Array(savedSalt), iterations: 250000, hash: 'SHA-256'}, material, {name: 'AES-GCM', length: 256}, false, ['encrypt', 'decrypt']);
  }
  function sanitise(state) {
    const result = clone(state);
    result.records.payroll = []; result.records.commissions = []; result.audit = []; result.attachments = [];
    result.records.employees = result.records.employees.map(x => ({id:x.id, name:x.name, role:x.role, active:x.active, version:x.version, type:x.type}));
    result.permissions.read = result.permissions.read.filter(x => !['payroll', 'commissions'].includes(x));
    result.permissions.write = result.permissions.write.filter(x => draftKinds.has(x));
    return result;
  }
  async function persist() {
    // sessionStorage survives a refresh in this tab, so uncertain online writes
    // keep their original retry IDs even when an offline vault is not enabled.
    sessionStorage.setItem(bucket(), JSON.stringify(pending));
    if (!key || !snapshot) return;
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const body = encoder.encode(JSON.stringify({user:S.user, state:sanitise(snapshot), pending, lastOnline}));
    const ciphertext = await crypto.subtle.encrypt({name:'AES-GCM', iv}, key, body);
    await vault('put', {id:userId, name:S.user.username, salt:Array.from(salt), iv:Array.from(iv), ciphertext});
  }
  function setUser(user) {
    if (userId !== user.id) {
      if (pending.length) throw new Error('Sign in with the account that owns the pending changes first.');
      if (releaseWriter) releaseWriter(); releaseWriter = null; writerPromise = null;
      userId = user.id; key = null; salt = null; snapshot = null;
      try { pending = JSON.parse(sessionStorage.getItem(bucket()) || '[]'); } catch { pending = []; }
    }
  }
  function overlay(state) {
    const result = clone(state);
    pending.filter(x => x.endpoint === 'record' && x.payload.business_id === state.business.id).forEach(op => {
      const p = op.payload;
      if (!draftKinds.has(p.kind)) return;
      const list = result.records[p.kind];
      const index = list.findIndex(x => x.id === p.id);
      const row = {...(index < 0 ? {} : list[index]), ...p.data, id:p.id, type:p.kind, version:p.version || 0, _pending:true};
      if (['quotes'].includes(p.kind)) row._totals = estimate(row);
      if (index < 0) list.unshift(row); else list[index] = row;
    });
    return result;
  }
  async function state() {
    let result;
    try {
      result = await rawApi('state?business=' + encodeURIComponent(S.bid));
    } catch (error) {
      if (error.status || !snapshot || snapshot.business.id !== S.bid) throw error;
      if (Date.now()-lastOnline > 86400000) throw new Error('Connect and sign in to refresh this expired offline workspace.');
      S.offline = true;
      return overlay(sanitise(snapshot));
    }
    snapshot = result; lastOnline = Date.now(); S.offline = false;
    try { await persist(); } catch { toast('The current records loaded, but this device could not save its offline copy.',true); }
    return overlay(result);
  }
  async function request(path, data) {
    if (path === 'calculate' && S.offline) return estimate(data.data);
    if (!commandPaths.has(path) || data === undefined) return rawApi(path, data);
    if (!await writer()) throw new Error('Another tab is editing this workspace. Close that tab, then refresh this one. Other staff can use their own devices.');
    if (pending.some(x => x.payload.business_id === S.bid && x.endpoint !== 'record' || x.payload.business_id === S.bid && !draftKinds.has(x.payload.kind))) {
      throw new Error('Resolve the pending server operation in Sync before recording another transaction.');
    }
    const payload = clone(data);
    if (path === 'record') payload.id = payload.id || uuid();
    if (pending.some(x => x.payload.id === payload.id)) throw new Error('This record already has a pending change. Sync or resolve it before editing again.');
    const offlineAllowed = path === 'record' && draftKinds.has(payload.kind) && (payload.kind !== 'quotes' || (payload.data.status || 'draft') === 'draft');
    if ((S.offline || !navigator.onLine) && (!key || !offlineAllowed)) {
      throw new Error(!key ? 'Enable offline drafts on this device while online first.' : 'This action needs the server. You can save enquiries, customers, follow-ups, attendance and draft quotes offline.');
    }
    if ((S.offline || !navigator.onLine) && Date.now()-lastOnline > 86400000) throw new Error('Connect and sign in to refresh this expired offline workspace.');
    const operation = {operation_id:uuid(), endpoint:path, payload, data_epoch:S.state.data_epoch, status:'pending', created_at:new Date().toISOString()};
    pending.push(operation);
    try { await persist(); } catch (error) { pending.pop(); throw new Error('Device storage failed. The operation was not sent.'); }
    if (!S.offline && navigator.onLine) {
      try {
        const result = await rawApi('command', operation);
        pending = pending.filter(x => x !== operation);
        try { await persist(); } catch { toast('Saved on the server. The device cache needs to be refreshed.',true); }
        return result;
      } catch (error) {
        if (error.status && error.status < 500) {
          pending = pending.filter(x => x !== operation); await persist(); throw error;
        }
        operation.status = 'uncertain'; operation.error = 'The server may have saved this. Retry with the same operation ID.';
        await persist();
        if (!offlineAllowed) { updateIndicator(); throw new Error('Connection interrupted. This operation is saved for a safe retry in Sync. Check Sync before entering it again.'); }
      }
    }
    S.offline = true;
    updateIndicator();
    return {...payload.data, id:payload.id, type:payload.kind, version:payload.version || 0, _pending:true};
  }
  async function sync() {
    if (syncing) return;
    syncing = true;
    try {
      if (!await writer()) throw new Error('Close the other editing tab and refresh before syncing here.');
      const health = await rawApi('health');
      if (!health.user || health.user.id !== userId) {
        renderAuth(false);
        throw new Error('Sign in with the same account before syncing these changes.');
      }
      S.csrf = health.csrf; S.user = health.user;
      for (const operation of [...pending]) {
        if (operation.status === 'conflict') break;
        try {
          await rawApi('command', operation);
          pending = pending.filter(x => x !== operation);
          await persist();
        } catch (error) {
          if (error.status === 401) break;
          operation.status = error.status && error.status < 500 ? 'conflict' : 'uncertain';
          operation.error = error.message;
          await persist();
          break; // Dependencies may reference a new customer in this operation.
        }
      }
      S.offline = false;
      await reload();
      toast(pending.length ? 'Some changes need review in Sync.' : 'All changes are confirmed by the server.');
    } finally { syncing = false; updateIndicator(); }
  }
  function updateIndicator() {
    const node = document.querySelector('#sync-indicator');
    if (node) {
      node.textContent = pending.length ? `${pending.length} pending · Sync` : S.offline ? 'Offline drafts' : 'Synced';
      node.classList.toggle('pending', !!pending.length || !!S.offline);
    }
  }
  function dialog() {
    showDialog('Device sync', `<p class="help-text">Drafts can wait for a connection. Bills, receipts, inventory changes and reservations are confirmed by the server. A conflicting edit is never overwritten automatically.</p><div class="sync-list">${pending.length ? pending.map(op => `<article class="sync-item"><b>${e(models[op.payload.kind]?.singular || op.endpoint)} · ${e(op.status)}</b><p>${e(op.payload.data?.name || op.payload.data?.subject || op.payload.id || '')}</p><small>${e(op.error || 'Waiting for the server')}</small><div class="actions">${op.status === 'conflict' ? `<button class="btn small" data-sync-review="${e(op.operation_id)}">Review saved change</button>` : ''}</div></article>`).join('') : '<p class="empty">No pending changes.</p>'}</div>`, '<button class="btn" data-action="close">Close</button><button id="sync-now" class="btn primary">Sync now</button>');
    document.querySelector('#sync-now').onclick = async event => {
      event.target.disabled = true;
      try { await sync(); dialog(); } catch (error) { toast(error.message, true); event.target.disabled = false; }
    };
    document.querySelectorAll('[data-sync-review]').forEach(button => button.onclick = () => review(button.dataset.syncReview));
  }
  function review(id) {
    const op = pending.find(x => x.operation_id === id);
    if (!op) return;
    const current = snapshot?.records?.[op.payload.kind]?.find(x=>x.id===op.payload.id);
    showDialog('Resolve a saved change', `<p class="notice warning">${e(op.error)} Copy any details you need, then discard this queued change and edit the current server record. Dependent queued records remain blocked until you resolve them. An uncertain operation must be retried; it cannot be discarded here.</p><div class="form-grid"><div class="field"><label>Your saved change</label><textarea readonly rows="12">${e(JSON.stringify(op.payload.data || op.payload, null, 2))}</textarea></div><div class="field"><label>Current view (refresh after discard)</label><textarea readonly rows="12">${e(JSON.stringify(current || {}, null, 2))}</textarea></div></div>`, '<button class="btn" data-action="close">Keep for review</button><button id="discard-sync" class="btn danger">Discard this rejected change</button>', true);
    document.querySelector('#discard-sync').onclick = async () => {
      pending = pending.filter(x => x.operation_id !== id); await persist();
      document.querySelector('#editor').close(); await reload(); toast('Rejected change discarded. Open the current record to apply a reviewed edit.');
    };
  }
  async function enable(passphrase) {
    if (passphrase.length < 10) throw new Error('Use at least 10 characters for the offline passphrase.');
    if (!navigator.locks || !await writer()) throw new Error('Use one editing tab in a current browser that supports Web Locks.');
    const old = (await vault('getAll')).find(x => x.id === userId);
    if (old && !key) {
      const candidate = await derive(passphrase, old.salt);
      let saved;
      try { saved = JSON.parse(decoder.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:new Uint8Array(old.iv)}, candidate, old.ciphertext))); }
      catch { throw new Error('Enter the existing offline passphrase to unlock this device copy.'); }
      const merged = new Map(saved.pending.map(x=>[x.operation_id,x])); pending.forEach(x=>merged.set(x.operation_id,x)); pending=[...merged.values()];
      salt = new Uint8Array(old.salt); key = candidate;
    } else if (!key) {
      salt = crypto.getRandomValues(new Uint8Array(16)); key = await derive(passphrase, salt);
    }
    await persist();
  }
  async function unlock(id, passphrase) {
    const entry = (await vault('getAll')).find(x => x.id === id);
    if (!entry) throw new Error('No offline workspace is saved for that account.');
    const candidate = await derive(passphrase, entry.salt);
    let data;
    try { data = JSON.parse(decoder.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:new Uint8Array(entry.iv)}, candidate, entry.ciphertext))); }
    catch { throw new Error('Offline passphrase is incorrect.'); }
    if (Date.now() - data.lastOnline > 24 * 60 * 60 * 1000) throw new Error('Connect and sign in to refresh this workspace. Offline access expires after 24 hours.');
    userId = data.user.id;
    if (!await writer()) throw new Error('Close the other editing tab and refresh before unlocking here.');
    key = candidate; salt = new Uint8Array(entry.salt); snapshot = data.state;
    // A tab's newer uncertain operations take precedence over an older vault.
    const saved = JSON.parse(sessionStorage.getItem(bucket()) || '[]');
    const operations = new Map(data.pending.map(x => [x.operation_id, x]));
    saved.forEach(x => operations.set(x.operation_id, x)); pending = [...operations.values()];
    lastOnline = data.lastOnline; S.user = data.user; S.csrf = ''; S.offline = true;
    S.bid = snapshot.business.id; S.businesses = [snapshot.business]; S.state = overlay(snapshot);
    renderShell();
  }
  async function forget() {
    if (pending.length) throw new Error('Sync or resolve pending changes before removing this device workspace.');
    await vault('delete', userId); key = null; salt = null;
  }
  async function logout() {
    if (pending.length) throw new Error('Sync or resolve pending changes before signing out.');
    sessionStorage.removeItem(bucket());
    Object.keys(sessionStorage).filter(x=>x.startsWith('bd_draft_'+userId+'_')).forEach(x=>sessionStorage.removeItem(x));
    if(releaseWriter)releaseWriter(); releaseWriter=null;writerPromise=null;
    key = null; salt = null; snapshot = null; userId = '';
  }
  function estimate(data) {
    let net=0, tax=0, total=0, cost=0, discount=0;
    const round = x => Math.round((x + Number.EPSILON) * 100) / 100;
    const lines = (data.items || []).filter(x => x.description || Number(x.rate)).map(x => {
      const raw=round(Number(x.qty || 1) * Number(x.rate || 0));
      const amount=round(raw * (1-Number(x.discount || 0)/100) * (1-Number(data.discount_percent || 0)/100));
      const rate=data.vat_mode === 'none' ? 0 : Number(x.tax_rate ?? data.vat_rate ?? 13);
      const n=data.vat_mode === 'included' ? round(amount/(1+rate/100)) : amount;
      const t=data.vat_mode === 'included' ? round(amount-n) : round(n*rate/100);
      const c=round(Number(x.unit_cost || 0)*Number(x.qty || 1));
      net+=n;tax+=t;total+=round(n+t);cost+=c;discount+=raw-amount;
      return {...x,net:n,tax:t,total:round(n+t),discount_amount:round(raw-amount),cost:c};
    });
    return {lines,net:round(net),tax:round(tax),total:round(total),estimated_cost:round(cost),estimated_contribution:round(net-cost),discount:round(discount),words:'Offline estimate — totals are verified by the server on sync.'};
  }
  return {setUser, state, request, sync, dialog, enable, forget, logout, unlock, updateIndicator,
          accounts:() => vault('getAll'), pending:() => pending, enabled:() => !!key};
})();

window.addEventListener('online', () => { if (typeof S !== 'undefined' && S.user) DeskSync.sync().catch(error => toast(error.message, true)); });
window.addEventListener('offline', () => { if (typeof S !== 'undefined') { S.offline = true; DeskSync.updateIndicator(); } });
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
