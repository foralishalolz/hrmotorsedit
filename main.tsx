import { useState, useEffect, useCallback, useRef, type KeyboardEvent } from 'react';
import { QuotePrint, type QuoteItem, type VatMode } from './components/QuotePrint';
import { numberToWords } from './utils/numberToWords';

const DRAFT_KEY = 'qg_draft_v9';
const SAVED_KEY = 'qg_saved_v9';

function uid(): string { return Math.random().toString(36).substring(2, 11); }
function emptyItem(): QuoteItem { return { id: uid(), description: '', qty: 1, unit: 'pc', rate: 0 }; }

interface FontSizes { zain: number; ragee: number; moonstar: number; }

interface CustomText {
  zainNameVat: string;
  zainNameNoVat: string;
  zainAddress: string;
  zainPhone: string;
  zainEmail: string;
  zainVatNo: string;
  zainThankYou: string;
  rageeName: string;
  rageeAddress: string;
  rageePhone: string;
  rageePan: string;
  rageeThankYou: string;
  moonName: string;
  moonAddress: string;
  moonPhone: string;
  moonReg: string;
}

const DEFAULT_ZAIN_TERMS = [
  'Quotation valid for 1 month.',
  'Payment terms as agreed.',
];
const DEFAULT_RAGEE_TERMS = [
  'Rates valid for 15 days from quotation date.',
  'Delivery time as per availability of parts.',
  'Warranty as per spare part manufacturer policy.',
  'Goods once sold will not be taken back or exchanged.',
];
const DEFAULT_MOONSTAR_TERMS = [
  'Rates valid for 7 working days from quotation date.',
  'Service execution subject to workshop schedule.',
  'Transportation and handling charges extra.',
  'Warranty as per manufacturer terms only.',
];

interface QuotationData {
  id: string; name: string; savedAt: number;
  items: QuoteItem[]; vatMode: VatMode;
  quotationNumber: string; quotationDate: string;
  clientName: string; clientAddress: string; subject: string;
  vehicleModel: string; vehicleRegNo: string;
  chassisNumber: string; showChassis: boolean;
  fontSizes: FontSizes;
  rageeItems: QuoteItem[] | null; moonstarItems: QuoteItem[] | null;
  zainTerms: string[]; rageeTerms: string[];   moonstarTerms: string[];
  customText: CustomText;
}

function defaultData(): QuotationData {
  return {
    id: uid(), name: 'New Quote', savedAt: Date.now(),
    items: [emptyItem(), emptyItem(), emptyItem()],
    vatMode: 'added', quotationNumber: '', quotationDate: '',
    clientName: '', clientAddress: '', subject: '',
    vehicleModel: '', vehicleRegNo: '',
    chassisNumber: '', showChassis: false,
    fontSizes: { zain: 10, ragee: 10, moonstar: 10 },
    rageeItems: null, moonstarItems: null,
    zainTerms: [...DEFAULT_ZAIN_TERMS],
    rageeTerms: [...DEFAULT_RAGEE_TERMS],
    moonstarTerms: [...DEFAULT_MOONSTAR_TERMS],
    customText: {
      zainNameVat: 'ZAIN MOTORS WORKSHOP',
      zainNameNoVat: 'ZAIN MOTORS',
      zainAddress: 'Garud Marg, Hetauda',
      zainPhone: '9802951839',
      zainEmail: 'ZAINMOTORSWORKSHOP@proton.me',
      zainVatNo: '607216794',
      zainThankYou: 'Thank you for choosing {{name}}. We value your trust and look forward to serving you.',
      rageeName: 'RAGEE AUTOMOTIVES',
      rageeAddress: 'Main Road, Hetauda-4',
      rageePhone: '9845025901',
      rageePan: '301492753',
      rageeThankYou: 'We appreciate your enquiry and assure you of the best quality spare parts at competitive pricing.',
      moonName: 'MOON STAR ENGINEERING WORKSHOP',
      moonAddress: 'Hetauda-4, Main Road Makawanpur',
      moonPhone: '057-521517',
      moonReg: '7835/136/2069/2070',
    },
  };
}

function loadDraft(): QuotationData {
  try {
    const s = localStorage.getItem(DRAFT_KEY);
          if (s) {
        const p = JSON.parse(s) as QuotationData;
        if (p.items?.length) {
          return { ...defaultData(), ...p,
            zainTerms: p.zainTerms ?? [...DEFAULT_ZAIN_TERMS],
            rageeTerms: p.rageeTerms ?? [...DEFAULT_RAGEE_TERMS],
            moonstarTerms: p.moonstarTerms ?? [...DEFAULT_MOONSTAR_TERMS],
            customText: { ...defaultData().customText, ...(p.customText ?? {}) },
          };
        }
      }
  } catch { /* ignore */ }
  return defaultData();
}

function loadSaved(): QuotationData[] {
  try {
    const s = localStorage.getItem(SAVED_KEY);
    if (s) return JSON.parse(s) as QuotationData[];
  } catch { /* ignore */ }
  return [];
}

function saveDraft(data: QuotationData) { localStorage.setItem(DRAFT_KEY, JSON.stringify(data)); }
function saveSavedList(list: QuotationData[]) { localStorage.setItem(SAVED_KEY, JSON.stringify(list)); }

/* ═══════════════════════════════════════════════════════════════
   COMPETITOR RATE CALCULATION
   - Dynamic markup: fewer items = higher increase
   - Silicone: max 3%, rounded to nearest 5
   - ltr: keep exactly same
   - job: increase then round to nearest 500 or 1000
   ═══════════════════════════════════════════════════════════════ */
function roundNear500or1000(n: number): number {
  if (n > 5000) return Math.round(n / 1000) * 1000;
  return Math.round(n / 500) * 500;
}

function compRate(rate: number, unit: string, description: string, itemCount: number): number {
  if (unit === 'ltr') return rate;

  // Silicone: max 3% increase, always rounded to nearest 5
  if (description.toLowerCase().includes('silicone')) {
    const pct = Math.random() * 3;
    const inc = rate * (1 + pct / 100);
    return Math.round(inc / 5) * 5;
  }

  // Dynamic markup based on item count
  let minPct: number, maxPct: number;
  if (itemCount <= 2) { minPct = 16; maxPct = 28; }
  else if (itemCount <= 4) { minPct = 12; maxPct = 22; }
  else if (itemCount <= 7) { minPct = 8; maxPct = 16; }
  else if (itemCount <= 12) { minPct = 5; maxPct = 13; }
  else { minPct = 4; maxPct = 10; }

  const pct = minPct + Math.random() * (maxPct - minPct);
  const inc = rate * (1 + pct / 100);

  if (unit === 'job') return roundNear500or1000(inc);
  return Math.round(inc * 100) / 100;
}

function fmt(n: number): string {
  if (n === 0) return '0.00';
  return n.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/* KEYBOARD NAVIGATION */
function handleGridKey(
  e: KeyboardEvent<HTMLInputElement | HTMLSelectElement>,
  rowIdx: number, colIdx: number, totalRows: number, addRow: () => void,
) {
  const parent = (e.target as HTMLElement).closest('table');
  if (!parent) return;
  const moveTo = (r: number, c: number) => {
    const rows = parent.querySelectorAll('tbody tr');
    if (r < 0 || r >= rows.length) return;
    const cells = rows[r].querySelectorAll<HTMLInputElement | HTMLSelectElement>('input, select');
    const target = cells[c];
    if (target) { target.focus(); if (target instanceof HTMLInputElement) target.select(); }
  };
  const skipQty = (idx: number, dir: 1 | -1, max: number) => {
    let next = idx + dir;
    if (next === 1) next += dir; // skip Qty column
    if (next < 0) next = 0;
    if (next >= max) next = max - 1;
    return next;
  };
  if (e.key === 'Enter') {
    e.preventDefault();
    if (rowIdx === totalRows - 1) { addRow(); setTimeout(() => moveTo(rowIdx + 1, colIdx), 30); }
    else moveTo(rowIdx + 1, colIdx);
  } else if (e.key === 'Tab') {
    const cells = (e.target as HTMLElement).closest('tr')?.querySelectorAll<HTMLInputElement | HTMLSelectElement>('input, select');
    if (!cells) return;
    const idx = Array.from(cells).indexOf(e.target as HTMLInputElement | HTMLSelectElement);
    if (e.shiftKey) {
      e.preventDefault();
      const next = skipQty(idx, -1, cells.length);
      if (idx === 0) moveTo(rowIdx - 1, cells.length - 1);
      else moveTo(rowIdx, next);
    } else {
      e.preventDefault();
      if (idx === cells.length - 1) {
        if (rowIdx === totalRows - 1) { addRow(); setTimeout(() => moveTo(rowIdx + 1, 0), 30); }
        else moveTo(rowIdx + 1, 0);
      } else {
        const next = skipQty(idx, 1, cells.length);
        moveTo(rowIdx, next);
      }
    }
  } else if (e.key === 'ArrowDown') { e.preventDefault(); moveTo(rowIdx + 1, colIdx); }
  else if (e.key === 'ArrowUp') { e.preventDefault(); moveTo(rowIdx - 1, colIdx); }
  else if (e.key === 'ArrowRight') {
    e.preventDefault();
    let next = colIdx + 1;
    if (next === 1) next = 2; // skip Qty column
    moveTo(rowIdx, next);
  }
  else if (e.key === 'ArrowLeft') {
    e.preventDefault();
    let next = colIdx - 1;
    if (next === 1) next = 0; // skip Qty column
    moveTo(rowIdx, next);
  }
}

type PastedRow = {
  description: string;
  qty?: number;
  unit?: QuoteItem['unit'];
  rate?: number;
};

function parsePastedRows(text: string): PastedRow[] {
  const lines = text
    .split(/\r?\n/)
    .map(line => line.trim())
    .filter(Boolean);

  return lines.map((line) => {
    const cols = line.split('\t').map(c => c.trim());
    const row: PastedRow = { description: cols[0] ?? '' };

    if (cols[1]) {
      const qty = Number(cols[1]);
      if (!Number.isNaN(qty)) row.qty = qty;
    }
    if (cols[2]) {
      const unit = cols[2].toLowerCase();
      if (unit === 'pc' || unit === 'job' || unit === 'set' || unit === 'ltr') row.unit = unit;
    }
    if (cols[3]) {
      const rate = Number(cols[3].replace(/,/g, ''));
      if (!Number.isNaN(rate)) row.rate = rate;
    }
    return row;
  });
}

/* ICONS */
const IconSave = () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>;
const IconPlus = () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const IconTrash = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>;
const IconX = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>;
const IconPrint = () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>;
const IconGen = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" /><polyline points="3.27 6.96 12 12.01 20.73 6.96" /><line x1="12" y1="22.08" x2="12" y2="12" /></svg>;
const IconFolder = () => <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>;
const IconEdit = () => <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>;

/* TERMS EDITOR */
function TermsEditor({ label, terms, onChange }: { label: string; terms: string[]; onChange: (t: string[]) => void }) {
  return (
    <div className="terms-editor">
      <div className="terms-hdr">
        <span className="terms-label">{label}</span>
        <button className="btn btn-xs btn-sec" onClick={() => onChange([...terms, ''])}><IconPlus /> Add</button>
      </div>
      {terms.map((t, i) => (
        <div key={i} className="terms-row">
          <span className="terms-num">{i + 1}.</span>
          <input className="terms-input" type="text" value={t}
            onChange={e => { const u = [...terms]; u[i] = e.target.value; onChange(u); }}
            placeholder="Enter term..." />
          <button className="terms-del" onClick={() => onChange(terms.filter((_, idx) => idx !== i))} title="Remove"><IconX /></button>
        </div>
      ))}
      {terms.length === 0 && <div className="terms-empty">No terms added</div>}
    </div>
  );
}


/* ═══════════════════════════════════════════════════════════════
   MAIN APP
   ═══════════════════════════════════════════════════════════════ */
export function App() {
  const [data, setData] = useState<QuotationData>(loadDraft);
  const [savedList, setSavedList] = useState<QuotationData[]>(loadSaved);
  const [activeTab, setActiveTab] = useState<'editor' | string>('editor');
  const [printEntity, setPrintEntity] = useState<'zain' | 'ragee' | 'moonstar' | null>(null);
  const [showAllPrint, setShowAllPrint] = useState(false);
  const [saveMsg, setSaveMsg] = useState('');
  const [termsOpen, setTermsOpen] = useState(false);

  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => saveDraft(data), 250);
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current); };
  }, [data]);

  const preparePrint = useCallback(() => {
    const pageHeight = 1045;
    document.body.classList.add('force-print');
    document.querySelectorAll('.page-num').forEach(n => n.remove());
    document.querySelectorAll<HTMLElement>('.print-entity').forEach(section => {
      section.classList.remove('tight-footer', 'no-terms');
      const height = section.scrollHeight;
      let pages = Math.max(1, Math.ceil(height / pageHeight));
      if (pages > 1) {
        const lastPageContent = height - (pages - 1) * pageHeight;
        if (lastPageContent < 260) section.classList.add('tight-footer');
        if (lastPageContent < 190) section.classList.add('no-terms');
      }
      const adjHeight = section.scrollHeight;
      pages = Math.max(1, Math.ceil(adjHeight / pageHeight));
      if (pages <= 1) return;
      for (let i = 1; i <= pages; i += 1) {
        const el = document.createElement('div');
        el.className = 'page-num';
        el.textContent = `Page ${i} of ${pages}`;
        el.style.top = `${(i - 1) * pageHeight + pageHeight - 18}px`;
        section.appendChild(el);
      }
    });
  }, []);

  useEffect(() => {
    const beforePrint = () => preparePrint();
    const afterPrint = () => {
      document.querySelectorAll('.page-num').forEach(n => n.remove());
      document.querySelectorAll<HTMLElement>('.print-entity').forEach(section => {
        section.classList.remove('tight-footer', 'no-terms');
      });
      document.body.classList.remove('force-print');
    };
    window.addEventListener('beforeprint', beforePrint);
    window.addEventListener('afterprint', afterPrint);
    return () => {
      window.removeEventListener('beforeprint', beforePrint);
      window.removeEventListener('afterprint', afterPrint);
    };
  }, [preparePrint]);

  useEffect(() => { saveSavedList(savedList); }, [savedList]);

  const set = useCallback(<K extends keyof QuotationData>(k: K, v: QuotationData[K]) => {
    setData(prev => ({ ...prev, [k]: v }));
  }, []);

  const setFS = useCallback((entity: keyof FontSizes, val: number) => {
    setData(prev => ({ ...prev, fontSizes: { ...prev.fontSizes, [entity]: val } }));
  }, []);

  const updateItem = useCallback((id: string, field: keyof QuoteItem, value: string | number) => {
    setData(prev => ({ ...prev, items: prev.items.map(it => it.id === id ? { ...it, [field]: value } : it) }));
  }, []);

  const pasteMainRows = useCallback((startIndex: number, text: string) => {
    const rows = parsePastedRows(text);
    if (!rows.length) return;

    setData((prev) => {
      const next = [...prev.items];
      const needed = startIndex + rows.length;
      while (next.length < needed) next.push(emptyItem());

      rows.forEach((row, idx) => {
        const targetIndex = startIndex + idx;
        const target = next[targetIndex];
        next[targetIndex] = {
          ...target,
          description: row.description || target.description,
          qty: row.qty ?? target.qty,
          unit: row.unit ?? target.unit,
          rate: row.rate ?? target.rate,
        };
      });

      return { ...prev, items: next };
    });
  }, []);

  const addRow = useCallback(() => {
    setData(prev => ({ ...prev, items: [...prev.items, emptyItem()] }));
  }, []);

  const delRow = useCallback((id: string) => {
    setData(prev => ({ ...prev, items: prev.items.length > 1 ? prev.items.filter(i => i.id !== id) : prev.items }));
  }, []);

  const moveRow = useCallback((from: number, to: number) => {
    setData(prev => {
      if (to < 0 || to >= prev.items.length) return prev;
      const next = [...prev.items];
      const [picked] = next.splice(from, 1);
      next.splice(to, 0, picked);
      return { ...prev, items: next };
    });
  }, []);

  const updateCompItem = useCallback((which: 'ragee' | 'moonstar', id: string, field: keyof QuoteItem, value: string | number) => {
    const key = which === 'ragee' ? 'rageeItems' : 'moonstarItems';
    setData(prev => ({ ...prev, [key]: prev[key] ? prev[key]!.map(it => it.id === id ? { ...it, [field]: value } : it) : prev[key] }));
  }, []);

  const pasteCompRows = useCallback((which: 'ragee' | 'moonstar', startIndex: number, text: string) => {
    const rows = parsePastedRows(text);
    if (!rows.length) return;

    const key = which === 'ragee' ? 'rageeItems' : 'moonstarItems';
    setData((prev) => {
      const current = prev[key] ? [...prev[key]!] : [];
      const needed = startIndex + rows.length;
      while (current.length < needed) current.push(emptyItem());

      rows.forEach((row, idx) => {
        const targetIndex = startIndex + idx;
        const target = current[targetIndex];
        current[targetIndex] = {
          ...target,
          description: row.description || target.description,
          qty: row.qty ?? target.qty,
          rate: row.rate ?? target.rate,
        };
      });

      return { ...prev, [key]: current };
    });
  }, []);

  const addCompRow = useCallback((which: 'ragee' | 'moonstar') => {
    const key = which === 'ragee' ? 'rageeItems' : 'moonstarItems';
    setData(prev => ({ ...prev, [key]: prev[key] ? [...prev[key]!, emptyItem()] : [emptyItem()] }));
  }, []);

  const delCompRow = useCallback((which: 'ragee' | 'moonstar', id: string) => {
    const key = which === 'ragee' ? 'rageeItems' : 'moonstarItems';
    setData(prev => ({ ...prev, [key]: prev[key] && prev[key]!.length > 1 ? prev[key]!.filter(i => i.id !== id) : prev[key] }));
  }, []);

  const moveCompRow = useCallback((which: 'ragee' | 'moonstar', from: number, to: number) => {
    const key = which === 'ragee' ? 'rageeItems' : 'moonstarItems';
    setData(prev => {
      const list = prev[key];
      if (!list || to < 0 || to >= list.length) return prev;
      const next = [...list];
      const [picked] = next.splice(from, 1);
      next.splice(to, 0, picked);
      return { ...prev, [key]: next };
    });
  }, []);

  const generate = useCallback(() => {
    const valid = data.items.filter(i => i.description.trim() && i.rate > 0);
    if (valid.length === 0) { alert('Add at least one item with description and rate.'); return; }
    const count = valid.length;
    const hasJob = valid.some(i => i.unit === 'job');
    const jobItems = valid.filter(i => i.unit === 'job');
    const nonJobItems = valid.filter(i => i.unit !== 'job');

    const randSeed = `${data.quotationNumber}-${data.quotationDate}-${count}`;
    const rand = (seedText: string) => {
      let h = 2166136261;
      for (let i = 0; i < seedText.length; i += 1) {
        h ^= seedText.charCodeAt(i);
        h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
      }
      let x = h >>> 0;
      return () => {
        x ^= x << 13; x ^= x >> 17; x ^= x << 5;
        return ((x < 0 ? ~x + 1 : x) % 1000) / 1000;
      };
    };
    const makeShuffled = (source: QuoteItem[], seed: string) => {
      const rnd = rand(seed);
      const arr = [...source];
      for (let i = arr.length - 1; i > 0; i -= 1) {
        const j = Math.floor(rnd() * (i + 1));
        [arr[i], arr[j]] = [arr[j], arr[i]];
      }
      if (hasJob && jobItems.length) {
        const jobs = arr.filter(i => i.unit === 'job');
        const nonJobs = arr.filter(i => i.unit !== 'job');
        return [...nonJobs, ...jobs];
      }
      return arr;
    };

    const rageeBase = makeShuffled([...nonJobItems, ...jobItems], `${randSeed}-r`);
    const moonBase = makeShuffled([...nonJobItems, ...jobItems], `${randSeed}-m`);

    setData(prev => ({
      ...prev,
      rageeItems: rageeBase.map(i => ({ ...i, id: uid(), rate: compRate(i.rate, i.unit, i.description, count) })),
      moonstarItems: moonBase.map(i => ({ ...i, id: uid(), rate: compRate(i.rate, i.unit, i.description, count) })),
    }));
  }, [data.items, data.quotationNumber, data.quotationDate]);

  const saveQuotation = useCallback(() => {
    const label = data.clientName || data.vehicleRegNo || 'Untitled';
    const qLabel = data.quotationNumber ? `Q#${data.quotationNumber}` : '';
    const autoName = [label, qLabel].filter(Boolean).join(' — ');
    const toSave: QuotationData = { ...data, name: autoName, savedAt: Date.now() };
    setSavedList(prev => {
      const idx = prev.findIndex(s => s.id === toSave.id);
      if (idx >= 0) { const u = [...prev]; u[idx] = toSave; return u; }
      return [toSave, ...prev];
    });
    setSaveMsg('✓ Saved!');
    setTimeout(() => setSaveMsg(''), 2000);
  }, [data]);

  const loadQuotation = useCallback((saved: QuotationData) => {
    setData({ ...defaultData(), ...saved,
      zainTerms: saved.zainTerms ?? [...DEFAULT_ZAIN_TERMS],
      rageeTerms: saved.rageeTerms ?? [...DEFAULT_RAGEE_TERMS],
      moonstarTerms: saved.moonstarTerms ?? [...DEFAULT_MOONSTAR_TERMS],
    });
    setActiveTab('editor');
  }, []);

  const newQuotation = useCallback(() => { setData(defaultData()); setActiveTab('editor'); }, []);

  const deleteQuotation = useCallback((id: string) => {
    if (!window.confirm('Delete this saved quotation permanently?')) return;
    setSavedList(prev => prev.filter(s => s.id !== id));
    if (activeTab === id) setActiveTab('editor');
  }, [activeTab]);

  const clearCurrent = useCallback(() => { if (window.confirm('Clear all data?')) setData(defaultData()); }, []);

  const doPrint = useCallback((entity: 'zain' | 'ragee' | 'moonstar') => {
    setPrintEntity(entity); setShowAllPrint(false);
    setTimeout(() => window.print(), 200);
  }, []);

  const doPrintAll = useCallback(() => {
    if (validItems.length === 0) { alert('Add at least one item.'); return; }
    if (!data.rageeItems || !data.moonstarItems) { alert('Generate competitor quotes first.'); return; }
    setPrintEntity(null); setShowAllPrint(true);
    setTimeout(() => window.print(), 300);
  }, [data]);

  useEffect(() => {
    const ap = () => { setPrintEntity(null); setShowAllPrint(false); };
    window.addEventListener('afterprint', ap);
    return () => window.removeEventListener('afterprint', ap);
  }, []);

  const { items, vatMode, quotationNumber, quotationDate, clientName, clientAddress, subject, vehicleModel, vehicleRegNo, chassisNumber, showChassis, fontSizes, rageeItems, moonstarItems, zainTerms, rageeTerms, moonstarTerms, customText } = data;
  const subtotal = items.reduce((s, i) => s + i.qty * i.rate, 0);
  const vatAmt = vatMode === 'added' ? subtotal * 0.13 : 0;
  const displayTotal = vatMode === 'added' ? subtotal + vatAmt : subtotal;
  const validItems = items.filter(i => i.description.trim() && i.rate > 0);
  const zainName = vatMode === 'none' ? customText.zainNameNoVat : customText.zainNameVat;
  const rageeTotal = rageeItems ? rageeItems.reduce((s, i) => s + i.qty * i.rate, 0) : 0;
  const moonstarTotal = moonstarItems ? moonstarItems.reduce((s, i) => s + i.qty * i.rate, 0) : 0;
  const compTotal = (total: number) => vatMode === 'added' ? total * 1.13 : total;

  const printProps = { quotationNumber, quotationDate, clientName, clientAddress, subject, vehicleModel, vehicleRegNo, chassisNumber, showChassis, vatMode, zainTerms, rageeTerms, moonstarTerms, customText };

  return (
    <>
      <div
        className="app-screen"
        onFocusCapture={(e) => {
          const t = e.target as HTMLInputElement;
          if (t && t.tagName === 'INPUT' && (t.type === 'text' || t.type === 'number' || t.type === 'search' || t.type === 'tel' || t.type === 'email')) {
            t.select();
          }
        }}
      >
        <header className="app-header">
          <div className="hdr-inner">
            <div className="hdr-left">
              <div className="hdr-logo">ZM</div>
              <div>
                <h1 className="hdr-title">ZMW Quotations</h1>
                <p className="hdr-sub">Zain Motors • Ragee • Moon Star</p>
              </div>
            </div>
            <div className="hdr-actions">
              <button className="btn btn-green btn-sm" onClick={saveQuotation}><IconSave /> Save</button>
              {saveMsg && <span className="save-flash">{saveMsg}</span>}
              <button className="btn btn-outline-w btn-sm" onClick={newQuotation}><IconPlus /> New</button>
              <button className="btn btn-outline-w btn-sm" onClick={clearCurrent}><IconTrash /> Reset</button>
            </div>
          </div>
        </header>

        <div className="tab-bar">
          <button className={`tab-btn ${activeTab === 'editor' ? 'tab-active' : ''}`} onClick={() => setActiveTab('editor')}>✎ Editor</button>
          {savedList.length > 0 && <span className="tab-divider" />}
          {savedList.map(s => (
            <button key={s.id} className={`tab-btn tab-saved ${activeTab === s.id ? 'tab-active' : ''}`} onClick={() => setActiveTab(s.id)}>
              <IconFolder /><span className="tab-name">{s.name}</span>
            </button>
          ))}
        </div>

        {/* SAVED VIEW */}
        {activeTab !== 'editor' && (() => {
          const saved = savedList.find(s => s.id === activeTab);
          if (!saved) return null;
          const sTotal = saved.items.reduce((s, i) => s + i.qty * i.rate, 0);
          const sFinal = saved.vatMode === 'added' ? sTotal * 1.13 : sTotal;
          return (
            <main className="app-main">
              <section className="card saved-card">
                <div className="card-hdr" style={{ justifyContent: 'space-between' }}>
                  <h2><IconFolder /> {saved.name}</h2>
                  <div className="saved-actions">
                    <button className="btn btn-sm btn-primary" onClick={() => loadQuotation(saved)}><IconEdit /> Edit</button>
                    <button className="btn btn-sm btn-danger" onClick={() => deleteQuotation(saved.id)}><IconTrash /> Delete</button>
                  </div>
                </div>
                <div className="saved-preview">
                  <div className="sp-item"><span className="sp-l">Client</span><span className="sp-v">{saved.clientName || saved.vehicleRegNo || '—'}</span></div>
                  <div className="sp-item"><span className="sp-l">Q#</span><span className="sp-v">{saved.quotationNumber || '—'}</span></div>
                  <div className="sp-item"><span className="sp-l">Date</span><span className="sp-v">{saved.quotationDate}</span></div>
                  <div className="sp-item"><span className="sp-l">Vehicle</span><span className="sp-v">{saved.vehicleModel} {saved.vehicleRegNo}</span></div>
                  <div className="sp-item"><span className="sp-l">VAT</span><span className="sp-v">{saved.vatMode === 'added' ? 'Added 13%' : saved.vatMode === 'none' ? 'No VAT' : 'Included'}</span></div>
                  <div className="sp-item"><span className="sp-l">Items</span><span className="sp-v">{saved.items.filter(i => i.description.trim()).length}</span></div>
                  <div className="sp-item sp-total"><span className="sp-l">Total</span><span className="sp-v bn">{fmt(sFinal)}</span></div>
                </div>
                <div className="saved-items-wrap">
                  <table className="grid-table">
                    <thead><tr>
                      <th className="w-sn">SN</th><th className="w-desc">Description</th>
                      <th className="w-qty">Qty</th><th className="w-unit">Unit</th>
                      <th className="w-rate">Rate</th><th className="w-amt">Amount</th>
                    </tr></thead>
                    <tbody>
                      {saved.items.filter(i => i.description.trim()).map((item, idx) => (
                        <tr key={item.id}>
                          <td className="c bn">{idx + 1}</td><td>{item.description}</td>
                          <td className="c bn">{item.qty}</td><td className="c">{item.unit}</td>
                          <td className="r bn">{fmt(item.rate)}</td><td className="r bn amt-cell">{fmt(item.qty * item.rate)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </main>
          );
        })()}

        {/* EDITOR VIEW */}
        {activeTab === 'editor' && (
          <main className="app-main">
            {/* Details */}
            <section className="card">
              <div className="card-hdr"><h2>📋 Quotation Details</h2></div>
              <div className="settings-grid">
                <div className="fg"><label>Customer Name</label><input type="text" value={clientName} onChange={e => set('clientName', e.target.value)} placeholder="Leave blank → Reg No used" /></div>
                <div className="fg"><label>Address</label><input type="text" value={clientAddress} onChange={e => set('clientAddress', e.target.value)} placeholder="Customer address" /></div>
                <div className="fg"><label>Q# (Quotation No)</label><input type="text" value={quotationNumber} onChange={e => set('quotationNumber', e.target.value)} placeholder="e.g. 001" /></div>
                <div className="fg"><label>Date (BS) — YYYY-MM-DD</label><input type="text" value={quotationDate} onChange={e => set('quotationDate', e.target.value)} placeholder="YYYY-MM-DD" /></div>
                <div className="fg"><label>Vehicle Model</label><input type="text" value={vehicleModel} onChange={e => set('vehicleModel', e.target.value)} placeholder="e.g. Toyota Hilux" /></div>
                <div className="fg"><label>Vehicle Reg. No</label><input type="text" value={vehicleRegNo} onChange={e => set('vehicleRegNo', e.target.value)} placeholder="e.g. Ba 1 Ja 1234" /></div>
                <div className="fg wide"><label>Subject</label><input type="text" value={subject} onChange={e => set('subject', e.target.value)} placeholder="e.g. Quotation for vehicle repair work" /></div>
              </div>
              <div className="chassis-row">
                <label className="chassis-toggle">
                  <input type="checkbox" checked={showChassis} onChange={e => set('showChassis', e.target.checked)} />
                  <span className="cht-slider" /><span className="cht-label">Add Chassis Number</span>
                </label>
                {showChassis && <input type="text" className="chassis-input" value={chassisNumber} onChange={e => set('chassisNumber', e.target.value)} placeholder="Enter chassis number" />}
              </div>
            </section>

            {/* VAT */}
            <section className="card">
              <div className="card-hdr" style={{ justifyContent: 'space-between' }}>
                <h2>💰 VAT Mode</h2><span className="badge-name">{zainName}</span>
              </div>
              <div className="vat-grid">
                {(['added', 'none', 'included'] as VatMode[]).map(mode => (
                  <button key={mode} className={`vat-btn ${vatMode === mode ? 'vat-active' : ''}`} onClick={() => set('vatMode', mode)}>
                    <span className={`vat-icon ${vatMode === mode ? 'vi-on' : ''}`}>
                      {mode === 'added' ? '＋' : mode === 'none' ? '✕' : '✓'}
                    </span>
                    <span>
                      <strong>{mode === 'added' ? 'VAT Added 13%' : mode === 'none' ? 'No VAT' : 'VAT Included'}</strong>
                      <small>{mode === 'added' ? 'Subtotal + 13% = Total' : mode === 'none' ? 'Subtotal = Total' : 'Prices inclusive of VAT'}</small>
                    </span>
                  </button>
                ))}
              </div>
            </section>

            {/* Line Items */}
            <section className="card">
              <div className="card-hdr" style={{ justifyContent: 'space-between' }}>
                <h2>📝 Line Items — {zainName}</h2>
                <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                  <span className="kbd-hint">Enter↵ Tab→ ↑↓</span>
                  <button className="btn btn-sm btn-primary" onClick={addRow}><IconPlus /> Row</button>
                </div>
              </div>
              <div className="tbl-wrap">
                <table className="grid-table" id="zain-grid">
                  <thead><tr>
                    <th className="w-sn">SN</th><th className="w-desc">Description</th>
                    <th className="w-qty">Qty</th><th className="w-unit">Unit</th>
                    <th className="w-rate">Rate</th><th className="w-amt">Amount</th><th className="w-act" />
                  </tr></thead>
                  <tbody>
                    {items.map((item, idx) => (
                      <tr key={item.id}>
                        <td className="c bn">{idx + 1}</td>
                                <td><input className="ci di" type="text" value={item.description} onChange={e => updateItem(item.id, 'description', e.target.value)} onKeyDown={e => handleGridKey(e, idx, 0, items.length, addRow)} onPaste={e => { const txt = e.clipboardData.getData('text'); if (txt.includes('\n') || txt.includes('\t')) { e.preventDefault(); pasteMainRows(idx, txt); } }} onFocus={e => e.currentTarget.select()} placeholder="Description..." /></td>
        <td><input className="ci ni bn" type="number" value={item.qty || ''} onChange={e => updateItem(item.id, 'qty', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 1, items.length, addRow)} onFocus={e => e.currentTarget.select()} min="0" step="1" /></td>
        <td><select className="ci si" value={item.unit} onChange={e => updateItem(item.id, 'unit', e.target.value)} onKeyDown={e => handleGridKey(e, idx, 2, items.length, addRow)}>
          <option value="pc">pc</option><option value="job">job</option><option value="set">set</option><option value="ltr">ltr</option>
        </select></td>
        <td><input className="ci ni bn" type="number" value={item.rate || ''} onChange={e => updateItem(item.id, 'rate', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 3, items.length, addRow)} onFocus={e => e.currentTarget.select()} min="0" step="0.01" /></td>
                        <td className="r bn amt-cell">{fmt(item.qty * item.rate)}</td>
                        <td className="c">
                          <div className="row-act">
                            <button className="mv-btn" onClick={() => moveRow(idx, idx - 1)} disabled={idx === 0} title="Move up">↑</button>
                            <button className="mv-btn" onClick={() => moveRow(idx, idx + 1)} disabled={idx === items.length - 1} title="Move down">↓</button>
                            <button className="del-btn" onClick={() => delRow(item.id)} disabled={items.length <= 1} title="Delete row"><IconX /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="totals-bar">
                <div className="words-box">
                  <div className="wlabel">In Words:</div>
                  <div className="wtext">{numberToWords(displayTotal)}</div>
                </div>
                <div className="nums-box">
                  <div className="trow"><span>Subtotal</span><span className="bn">{fmt(subtotal)}</span></div>
                  {vatMode === 'added' && <div className="trow vrow"><span>VAT (13%)</span><span className="bn">{fmt(vatAmt)}</span></div>}
                  {vatMode === 'included' && <div className="trow"><span className="vinc">VAT (13% Included): {fmt(subtotal - subtotal / 1.13)}</span></div>}
                  <div className="trow gtrow"><span>Grand Total</span><span className="bn">{fmt(displayTotal)}</span></div>
                </div>
              </div>
            </section>

            {/* Terms */}
            <section className="card">
              <div className="card-hdr" style={{ justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => setTermsOpen(!termsOpen)}>
                <h2>📜 Terms &amp; Conditions (editable)</h2>
                <span style={{ fontSize: '0.78rem', color: '#9ca3af' }}>{termsOpen ? '▲ Collapse' : '▼ Expand'}</span>
              </div>
              {termsOpen && (
                <div className="terms-container">
                  <TermsEditor label="Zain Motors" terms={zainTerms} onChange={t => set('zainTerms', t)} />
                  <TermsEditor label="Ragee Automotives" terms={rageeTerms} onChange={t => set('rageeTerms', t)} />
                  <TermsEditor label="Moon Star Engineering" terms={moonstarTerms} onChange={t => set('moonstarTerms', t)} />
                </div>
              )}
            </section>

            {/* Actions */}
            <section className="card actions-card">
              <div className="act-row">
                <div className="act-left">
                  <button className="btn btn-lg btn-green" onClick={generate}><IconGen /> Generate Competitors</button>
                  {rageeItems && <span className="gen-ok">✓ Ready</span>}
                </div>
                <div className="act-right">
                  <button className="btn btn-primary" onClick={() => doPrint('zain')} disabled={validItems.length === 0}><IconPrint /> Zain</button>
                  <button className="btn btn-sec" onClick={() => doPrint('ragee')} disabled={!rageeItems}><IconPrint /> Ragee</button>
                  <button className="btn btn-sec" onClick={() => doPrint('moonstar')} disabled={!moonstarItems}><IconPrint /> Moon Star</button>
                  <button className="btn btn-dark" onClick={doPrintAll} disabled={validItems.length === 0 || !rageeItems}><IconPrint /> All 3</button>
                </div>
              </div>
            </section>

            {/* Font Sizes */}
            <section className="card">
              <div className="card-hdr"><h2>🔤 Print Font Sizes</h2></div>
              <div className="font-size-row">
                {(['zain', 'ragee', 'moonstar'] as const).map(ent => (
                  <div key={ent} className="fs-control">
                    <label>{ent === 'zain' ? 'Zain Motors' : ent === 'ragee' ? 'Ragee Automotives' : 'Moon Star Engg.'}</label>
                    <div className="fs-btns">
                      <button onClick={() => setFS(ent, Math.max(6, fontSizes[ent] - 0.5))}>−</button>
                      <span className="fs-val">{fontSizes[ent]}pt</span>
                      <button onClick={() => setFS(ent, Math.min(16, fontSizes[ent] + 0.5))}>+</button>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Custom print text removed to keep workflow faster and cleaner. */}

            {/* RAGEE EDITABLE */}
            {rageeItems && (
              <section className="card comp-card comp-ragee">
                <div className="card-hdr" style={{ justifyContent: 'space-between' }}>
                  <h2>Ragee Automotives <small className="comp-sub">• editable</small></h2>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button className="btn btn-sm btn-sec" onClick={generate}>↻ Regen</button>
                    <button className="btn btn-sm btn-primary" onClick={() => addCompRow('ragee')}><IconPlus /> Row</button>
                  </div>
                </div>
                <div className="tbl-wrap">
                  <table className="grid-table comp-tbl">
                    <thead><tr>
                      <th className="w-sn">SN</th><th className="w-desc">Particulars</th>
                      <th className="w-qty">Qty</th><th className="w-rate">Rate</th><th className="w-amt">Amount</th><th className="w-act" />
                    </tr></thead>
                    <tbody>
                      {rageeItems.map((item, idx) => (
                        <tr key={item.id}>
                          <td className="c bn">{idx + 1}</td>
                                    <td><input className="ci di" type="text" value={item.description} onChange={e => updateCompItem('ragee', item.id, 'description', e.target.value)} onKeyDown={e => handleGridKey(e, idx, 0, rageeItems.length, () => addCompRow('ragee'))} onPaste={e => { const txt = e.clipboardData.getData('text'); if (txt.includes('\n') || txt.includes('\t')) { e.preventDefault(); pasteCompRows('ragee', idx, txt); } }} onFocus={e => e.currentTarget.select()} /></td>
          <td><input className="ci ni bn" type="number" value={item.qty || ''} onChange={e => updateCompItem('ragee', item.id, 'qty', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 1, rageeItems.length, () => addCompRow('ragee'))} onFocus={e => e.currentTarget.select()} min="0" /></td>
          <td><input className="ci ni bn" type="number" value={item.rate || ''} onChange={e => updateCompItem('ragee', item.id, 'rate', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 2, rageeItems.length, () => addCompRow('ragee'))} onFocus={e => e.currentTarget.select()} min="0" step="0.01" /></td>
                          <td className="r bn amt-cell">{fmt(item.qty * item.rate)}</td>
                          <td className="c">
                            <div className="row-act">
                              <button className="mv-btn" onClick={() => moveCompRow('ragee', idx, idx - 1)} disabled={idx === 0} title="Move up">↑</button>
                              <button className="mv-btn" onClick={() => moveCompRow('ragee', idx, idx + 1)} disabled={idx === rageeItems.length - 1} title="Move down">↓</button>
                              <button className="del-btn" onClick={() => delCompRow('ragee', item.id)} disabled={rageeItems.length <= 1}><IconX /></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="comp-total-bar">
                  <span>Sub: <strong className="bn">{fmt(rageeTotal)}</strong></span>
                  {vatMode === 'added' && <span>VAT: <strong className="bn">{fmt(rageeTotal * 0.13)}</strong></span>}
                  <span>Total: <strong className="bn">{fmt(compTotal(rageeTotal))}</strong></span>
                </div>
              </section>
            )}

            {/* MOON STAR EDITABLE */}
            {moonstarItems && (
              <section className="card comp-card comp-moonstar">
                <div className="card-hdr" style={{ justifyContent: 'space-between' }}>
                  <h2>Moon Star Engineering <small className="comp-sub">• editable</small></h2>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button className="btn btn-sm btn-sec" onClick={generate}>↻ Regen</button>
                    <button className="btn btn-sm btn-primary" onClick={() => addCompRow('moonstar')}><IconPlus /> Row</button>
                  </div>
                </div>
                <div className="tbl-wrap">
                  <table className="grid-table comp-tbl">
                    <thead><tr>
                      <th className="w-sn">SN</th><th className="w-desc">Description</th>
                      <th className="w-qty">Qty</th><th className="w-rate">Rate</th><th className="w-amt">Amount</th><th className="w-act" />
                    </tr></thead>
                    <tbody>
                      {moonstarItems.map((item, idx) => (
                        <tr key={item.id}>
                          <td className="c bn">{idx + 1}</td>
                          <td><input className="ci di" type="text" value={item.description} onChange={e => updateCompItem('moonstar', item.id, 'description', e.target.value)} onKeyDown={e => handleGridKey(e, idx, 0, moonstarItems.length, () => addCompRow('moonstar'))} onPaste={e => { const txt = e.clipboardData.getData('text'); if (txt.includes('\n') || txt.includes('\t')) { e.preventDefault(); pasteCompRows('moonstar', idx, txt); } }} onFocus={e => e.currentTarget.select()} /></td>
                          <td><input className="ci ni bn" type="number" value={item.qty || ''} onChange={e => updateCompItem('moonstar', item.id, 'qty', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 1, moonstarItems.length, () => addCompRow('moonstar'))} onFocus={e => e.currentTarget.select()} min="0" /></td>
                          <td><input className="ci ni bn" type="number" value={item.rate || ''} onChange={e => updateCompItem('moonstar', item.id, 'rate', parseFloat(e.target.value) || 0)} onKeyDown={e => handleGridKey(e, idx, 2, moonstarItems.length, () => addCompRow('moonstar'))} onFocus={e => e.currentTarget.select()} min="0" step="0.01" /></td>
                          <td className="r bn amt-cell">{fmt(item.qty * item.rate)}</td>
                          <td className="c">
                            <div className="row-act">
                              <button className="mv-btn" onClick={() => moveCompRow('moonstar', idx, idx - 1)} disabled={idx === 0} title="Move up">↑</button>
                              <button className="mv-btn" onClick={() => moveCompRow('moonstar', idx, idx + 1)} disabled={idx === moonstarItems.length - 1} title="Move down">↓</button>
                              <button className="del-btn" onClick={() => delCompRow('moonstar', item.id)} disabled={moonstarItems.length <= 1}><IconX /></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="comp-total-bar">
                  <span>Sub: <strong className="bn">{fmt(moonstarTotal)}</strong></span>
                  {vatMode === 'added' && <span>VAT: <strong className="bn">{fmt(moonstarTotal * 0.13)}</strong></span>}
                  <span>Total: <strong className="bn">{fmt(compTotal(moonstarTotal))}</strong></span>
                </div>
              </section>
            )}
          </main>
        )}
      </div>

      {/* PRINT VIEWS */}
      <div className="print-only">
        {printEntity === 'zain' && <QuotePrint entity="zain" items={validItems} {...printProps} fontSize={fontSizes.zain} />}
        {printEntity === 'ragee' && rageeItems && <QuotePrint entity="ragee" items={rageeItems} {...printProps} fontSize={fontSizes.ragee} />}
        {printEntity === 'moonstar' && moonstarItems && <QuotePrint entity="moonstar" items={moonstarItems} {...printProps} fontSize={fontSizes.moonstar} />}
        {showAllPrint && (
          <>
            <QuotePrint entity="zain" items={validItems} {...printProps} fontSize={fontSizes.zain} />
            {rageeItems && <QuotePrint entity="ragee" items={rageeItems} {...printProps} fontSize={fontSizes.ragee} />}
            {moonstarItems && <QuotePrint entity="moonstar" items={moonstarItems} {...printProps} fontSize={fontSizes.moonstar} />}
          </>
        )}
      </div>
    </>
  );
}
