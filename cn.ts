@import "tailwindcss";

/* ════════════════════════════════════════════════════════════════
   VARIABLES & RESET
   ════════════════════════════════════════════════════════════════ */
:root {
  --pri: #2563eb; --pri-d: #1d4ed8;
  --grn: #16a34a; --grn-d: #15803d;
  --red: #dc2626;
  --g50: #f9fafb; --g100: #f3f4f6; --g200: #e5e7eb; --g300: #d1d5db;
  --g400: #9ca3af; --g500: #6b7280; --g600: #4b5563; --g700: #374151;
  --g800: #1f2937; --g900: #111827;
  --rad: 10px;
}
*,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #eef1f5; color: var(--g800); line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
.bn { font-weight: 700 !important; }
.c { text-align: center; }
.r { text-align: right; }
.print-only { display: none; }

/* ═══════ HEADER ═══════ */
.app-header {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1e40af 100%);
  color: white; padding: 10px 20px;
  position: sticky; top: 0; z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,0.3);
}
.hdr-inner { max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
.hdr-left { display: flex; align-items: center; gap: 10px; }
.hdr-logo {
  width: 36px; height: 36px; background: rgba(255,255,255,0.15); border-radius: 8px; border: 1px solid rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  font-weight: 900; font-size: 0.9rem; letter-spacing: -1px; color: #60a5fa;
}
.hdr-title { font-size: 1.05rem; font-weight: 800; letter-spacing: -0.02em; }
.hdr-sub { font-size: 0.66rem; opacity: 0.5; margin-top: 1px; }
.hdr-actions { display: flex; align-items: center; gap: 6px; }
.save-flash {
  font-size: 0.72rem; font-weight: 700; color: #4ade80;
  background: rgba(74,222,128,0.15); padding: 3px 12px; border-radius: 20px;
  animation: flashIn 0.3s ease;
}
@keyframes flashIn { 0% { opacity: 0; transform: scale(0.85); } 100% { opacity: 1; transform: scale(1); } }

/* ═══════ TAB BAR ═══════ */
.tab-bar {
  max-width: 1400px; margin: 0 auto; padding: 5px 20px 0;
  display: flex; gap: 2px; overflow-x: auto;
  background: #dde3eb; border-bottom: 2px solid var(--g300); scrollbar-width: thin;
}
.tab-btn {
  padding: 6px 14px; border: none; border-radius: 7px 7px 0 0;
  background: rgba(255,255,255,0.45); font-size: 0.76rem; font-weight: 600;
  color: var(--g600); cursor: pointer; white-space: nowrap; transition: all 0.1s;
  border: 1px solid transparent; border-bottom: none;
  display: flex; align-items: center; gap: 5px;
}
.tab-btn:hover { background: rgba(255,255,255,0.8); color: var(--g800); }
.tab-active {
  background: #fff !important; color: var(--pri) !important;
  border-color: var(--g300) !important; box-shadow: 0 -2px 6px rgba(0,0,0,0.04); position: relative;
}
.tab-active::after { content: ''; position: absolute; bottom: -2px; left: 0; right: 0; height: 3px; background: #fff; }
.tab-saved { max-width: 200px; }
.tab-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 130px; display: inline-block; }
.tab-divider { width: 1px; background: var(--g300); margin: 4px 4px; flex-shrink: 0; }

/* ═══════ MAIN LAYOUT ═══════ */
.app-main { max-width: 1400px; margin: 0 auto; padding: 12px 20px 50px; display: flex; flex-direction: column; gap: 10px; }

/* ═══════ CARD ═══════ */
.card {
  background: white; border-radius: var(--rad);
  box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  border: 1px solid var(--g200); overflow: hidden;
}
.card-hdr { padding: 9px 16px; border-bottom: 1px solid var(--g100); display: flex; align-items: center; gap: 10px; }
.card-hdr h2 { font-size: 0.88rem; font-weight: 600; display: flex; align-items: center; gap: 6px; }
.comp-card { border-left: 3px solid var(--g300); }
.comp-ragee { border-left-color: #8b7355; }
.comp-moonstar { border-left-color: #555; }
.comp-sub { font-weight: 400; color: var(--g400); font-size: 0.68rem; }

/* ═══════ SAVED VIEW ═══════ */
.saved-card { border: 2px solid var(--g200); }
.saved-actions { display: flex; gap: 6px; }
.saved-preview {
  padding: 12px 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 6px;
  background: var(--g50); border-bottom: 1px solid var(--g100);
}
.sp-item { display: flex; gap: 6px; font-size: 0.82rem; }
.sp-l { font-weight: 600; color: var(--g500); min-width: 55px; }
.sp-v { color: var(--g800); }
.sp-total { background: #f0f4ff; padding: 4px 8px; border-radius: 6px; }
.saved-items-wrap { padding: 0; }
.saved-items-wrap .grid-table tbody td { padding: 5px 8px; }

/* ═══════ SETTINGS GRID ═══════ */
.settings-grid { padding: 10px 16px; display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 8px; }
.fg label { display: block; font-size: 0.67rem; font-weight: 600; color: var(--g500); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 2px; }
.fg input {
  width: 100%; padding: 6px 9px; border: 1px solid var(--g200); border-radius: 6px;
  font-size: 0.84rem; background: var(--g50); transition: all 0.1s;
}
.fg input:focus { outline: none; border-color: var(--pri); box-shadow: 0 0 0 2px rgba(37,99,235,0.08); background: #fff; }
.wide { grid-column: 1 / -1; }

/* ═══════ CHASSIS ═══════ */
.chassis-row { padding: 6px 16px 10px; display: flex; align-items: center; gap: 14px; border-top: 1px dashed var(--g200); }
.chassis-toggle {
  display: flex; align-items: center; gap: 8px; cursor: pointer;
  font-size: 0.78rem; font-weight: 500; color: var(--g600); user-select: none; white-space: nowrap;
}
.chassis-toggle input { display: none; }
.cht-slider {
  width: 32px; height: 17px; background: var(--g300); border-radius: 10px;
  position: relative; transition: background 0.2s; flex-shrink: 0;
}
.cht-slider::after {
  content: ''; position: absolute; left: 2px; top: 2px;
  width: 13px; height: 13px; background: #fff; border-radius: 50%; transition: transform 0.2s;
}
.chassis-toggle input:checked + .cht-slider { background: var(--pri); }
.chassis-toggle input:checked + .cht-slider::after { transform: translateX(15px); }
.chassis-input {
  padding: 5px 9px; border: 1px solid var(--g200); border-radius: 6px;
  font-size: 0.82rem; background: var(--g50); width: 240px; transition: all 0.1s;
}
.chassis-input:focus { outline: none; border-color: var(--pri); box-shadow: 0 0 0 2px rgba(37,99,235,0.08); background: #fff; }

/* ═══════ VAT ═══════ */
.badge-name { font-size: 0.74rem; font-weight: 700; color: var(--pri); background: rgba(37,99,235,0.06); padding: 3px 10px; border-radius: 20px; }
.vat-grid { padding: 10px 16px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; }
.vat-btn {
  display: flex; align-items: center; gap: 8px; padding: 8px 10px;
  border: 2px solid var(--g200); border-radius: 8px; background: #fff;
  cursor: pointer; text-align: left; transition: all 0.1s;
}
.vat-btn:hover { border-color: var(--pri); }
.vat-active { border-color: var(--pri) !important; background: rgba(37,99,235,0.03) !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.07); }
.vat-icon {
  width: 30px; height: 30px; border-radius: 6px; background: var(--g100);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.9rem; font-weight: 700; color: var(--g500); flex-shrink: 0;
}
.vi-on { background: var(--pri); color: #fff; }
.vat-btn strong { display: block; font-size: 0.78rem; color: var(--g800); }
.vat-btn small { display: block; font-size: 0.66rem; color: var(--g400); margin-top: 1px; }

/* ═══════ TERMS EDITOR ═══════ */
.terms-container { padding: 12px 16px; display: grid; grid-template-columns: 1fr; gap: 14px; }
.terms-editor { border: 1px solid var(--g200); border-radius: 8px; padding: 10px; background: var(--g50); }
.terms-hdr { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.terms-label { font-size: 0.76rem; font-weight: 700; color: var(--g700); }
.terms-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.terms-num { font-size: 0.72rem; font-weight: 600; color: var(--g400); min-width: 18px; text-align: right; }
.terms-input {
  flex: 1; padding: 4px 8px; border: 1px solid var(--g200); border-radius: 5px;
  font-size: 0.78rem; background: #fff; transition: border-color 0.1s;
}
.terms-input:focus { outline: none; border-color: var(--pri); }
.terms-del {
  width: 22px; height: 22px; border: none; background: transparent; color: var(--g400);
  border-radius: 4px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.1s;
}
.terms-del:hover { background: #fef2f2; color: var(--red); }
.terms-empty { font-size: 0.72rem; color: var(--g400); font-style: italic; text-align: center; padding: 6px; }

/* ═══════ FONT SIZES ═══════ */
.kbd-hint {
  font-size: 0.64rem; color: var(--g400); font-weight: 500;
  background: var(--g50); padding: 2px 7px; border-radius: 4px;
  border: 1px solid var(--g200); font-family: 'SF Mono', 'Fira Code', monospace;
}
.font-size-row { padding: 10px 16px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.fs-control label { display: block; font-size: 0.68rem; font-weight: 600; color: var(--g600); margin-bottom: 4px; }
.fs-btns { display: flex; align-items: center; border: 1px solid var(--g200); border-radius: 7px; overflow: hidden; }
.fs-btns button {
  width: 32px; height: 30px; border: none; background: var(--g50);
  font-size: 1rem; font-weight: 700; cursor: pointer; color: var(--g700);
  display: flex; align-items: center; justify-content: center; transition: background 0.1s;
}
.fs-btns button:hover { background: var(--g200); }
.fs-btns button:first-child { border-right: 1px solid var(--g200); }
.fs-btns button:last-child { border-left: 1px solid var(--g200); }
.fs-val { flex: 1; text-align: center; font-size: 0.78rem; font-weight: 700; color: var(--pri); min-width: 42px; }

/* ═══════ GRID TABLE (SCREEN) ═══════ */
.tbl-wrap { overflow-x: auto; }
.grid-table { width: 100%; border-collapse: collapse; font-size: 0.84rem; }
.grid-table thead th {
  padding: 7px 6px; background: var(--g50); border-bottom: 2px solid var(--g200);
  text-align: left; font-weight: 600; font-size: 0.68rem;
  text-transform: uppercase; letter-spacing: 0.04em; color: var(--g500); white-space: nowrap;
}
.grid-table tbody td { padding: 2px 3px; border-bottom: 1px solid var(--g100); vertical-align: middle; }
.grid-table tbody tr:hover { background: #f0f4ff; }
.grid-table tbody tr:focus-within { background: #eef2ff; box-shadow: inset 3px 0 0 var(--pri); }
.w-sn { width: 36px; text-align: center; }
.w-desc { min-width: 180px; }
.w-qty { width: 62px; }
.w-unit { width: 58px; }
.w-rate { width: 90px; }
.w-amt { width: 100px; text-align: right; }
.w-act { width: 34px; }
.ci {
  width: 100%; padding: 5px 6px; border: 1px solid transparent; border-radius: 4px;
  font-size: 0.84rem; background: transparent; transition: all 0.1s; font-family: inherit;
}
.ci:hover { background: var(--g50); border-color: var(--g200); }
.ci:focus { outline: none; background: #fff; border-color: var(--pri); box-shadow: 0 0 0 2px rgba(37,99,235,0.1); }
.ni { text-align: right; font-variant-numeric: tabular-nums; }
.si { cursor: pointer; text-align: center; }
.di { min-width: 150px; }
.amt-cell { padding-right: 6px !important; font-variant-numeric: tabular-nums; font-size: 0.84rem; color: var(--g700); }
.ci[type="number"]::-webkit-inner-spin-button,
.ci[type="number"]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
.ci[type="number"] { -moz-appearance: textfield; }
.del-btn {
  width: 26px; height: 26px; border: none; background: transparent;
  border-radius: 5px; cursor: pointer; color: var(--g400);
  display: flex; align-items: center; justify-content: center; transition: all 0.1s;
}
.del-btn:hover:not(:disabled) { background: #fef2f2; color: var(--red); }
.del-btn:disabled { opacity: 0.15; cursor: default; }
.row-act { display: inline-flex; align-items: center; gap: 3px; }
.mv-btn {
  width: 22px;
  height: 22px;
  border: 1px solid var(--g200);
  background: #fff;
  color: var(--g600);
  border-radius: 4px;
  line-height: 1;
  font-weight: 700;
  cursor: pointer;
}
.mv-btn:hover:not(:disabled) { border-color: var(--pri); color: var(--pri); }
.mv-btn:disabled { opacity: 0.35; cursor: default; }

/* ═══════ TOTALS BAR ═══════ */
.totals-bar {
  padding: 10px 16px; border-top: 2px solid var(--g200);
  display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; flex-wrap: wrap;
}
.words-box { flex: 1; min-width: 200px; padding: 7px 10px; background: #f0f4ff; border-radius: 7px; border: 1px solid #dbe4ff; }
.wlabel { font-size: 0.66rem; font-weight: 600; color: var(--pri); text-transform: uppercase; letter-spacing: 0.04em; }
.wtext { font-size: 0.82rem; color: var(--g700); margin-top: 2px; line-height: 1.3; font-weight: 600; }
.nums-box { min-width: 220px; }
.trow {
  display: flex; justify-content: space-between; padding: 5px 10px;
  font-size: 0.84rem; color: var(--g600); border-bottom: 1px solid var(--g100);
}
.vrow { color: var(--g500); }
.vinc { font-size: 0.74rem; color: var(--pri); font-weight: 600; }
.gtrow {
  background: linear-gradient(135deg, #0f172a, #1e40af); color: #fff;
  border-radius: 7px; font-size: 0.94rem; font-weight: 700; margin-top: 3px; border: none;
}
.comp-total-bar {
  padding: 6px 16px; border-top: 1px solid var(--g100);
  display: flex; gap: 18px; justify-content: flex-end; font-size: 0.82rem; color: var(--g600);
}

/* ═══════ BUTTONS ═══════ */
.btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 6px 12px; border: none; border-radius: 7px;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.1s; white-space: nowrap;
}
.btn:disabled { opacity: 0.35; cursor: default; }
.btn-xs { padding: 2px 7px; font-size: 0.66rem; border-radius: 5px; }
.btn-sm { padding: 4px 9px; font-size: 0.72rem; }
.btn-lg { padding: 9px 18px; font-size: 0.86rem; }
.btn-primary { background: var(--pri); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--pri-d); }
.btn-sec { background: var(--g100); color: var(--g700); border: 1px solid var(--g200); }
.btn-sec:hover:not(:disabled) { background: var(--g200); }
.btn-green { background: var(--grn); color: #fff; }
.btn-green:hover:not(:disabled) { background: var(--grn-d); }
.btn-dark { background: var(--g800); color: #fff; }
.btn-dark:hover:not(:disabled) { background: var(--g900); }
.btn-danger { background: #fee2e2; color: var(--red); border: 1px solid #fecaca; }
.btn-danger:hover:not(:disabled) { background: #fecaca; }
.btn-outline-w { background: transparent; color: #fff; border: 1px solid rgba(255,255,255,0.25); }
.btn-outline-w:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.45); }

/* ═══════ ACTIONS ═══════ */
.actions-card { padding: 10px 16px; }
.act-row { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.act-left { display: flex; align-items: center; gap: 8px; }
.act-right { display: flex; align-items: center; gap: 5px; flex-wrap: wrap; }
.gen-ok { font-size: 0.72rem; font-weight: 700; color: var(--grn); background: #f0fdf4; padding: 2px 8px; border-radius: 20px; border: 1px solid #bbf7d0; }

/* ═══════ RESPONSIVE ═══════ */
@media (max-width: 768px) {
  .vat-grid { grid-template-columns: 1fr; }
  .font-size-row { grid-template-columns: 1fr; }
  .act-row { flex-direction: column; align-items: stretch; }
  .act-right { justify-content: center; }
  .settings-grid { grid-template-columns: 1fr; }
  .hdr-sub { display: none; }
  .totals-bar { flex-direction: column; }
  .chassis-row { flex-direction: column; align-items: flex-start; }
  .chassis-input { width: 100%; }
  .tab-bar { padding: 4px 10px 0; }
}


/* ════════════════════════════════════════════════════════════════════════
   ████████  PRINT STYLES  ████████
   ALL BLACK & WHITE — BOLD & CLEAR FOR PRINT
   ════════════════════════════════════════════════════════════════════════ */
@media print {
  @page {
    size: A4;
    margin: 10mm 10mm 15mm 10mm;
  }

  html, body {
    margin: 0 !important; padding: 0 !important;
    background: white !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .app-screen { display: none !important; }
  .print-only { display: block !important; }

  /* Global print overrides for clarity */
  .bn { font-weight: 800 !important; }
  .c { text-align: center !important; }
  .r { text-align: right !important; }

  .quote-page {
    page-break-after: always;
    padding: 0; color: #000; background: #fff;
  }
  .quote-page:last-child { page-break-after: auto; }

  .print-entity { position: relative; }
  .page-num {
    position: absolute;
    right: 6px;
    font-size: 7pt;
    color: #444;
    pointer-events: none;
  }

  .tight-footer .z-footer,
  .tight-footer .r-footer,
  .tight-footer .m-footer {
    margin-top: 2px;
  }
  .tight-footer .z-inwords,
  .tight-footer .r-inwords,
  .tight-footer .m-inwords {
    padding: 4px 8px;
    font-size: calc(var(--fs, 10pt) + 0.3pt);
  }
  .tight-footer .z-btm,
  .tight-footer .r-btm,
  .tight-footer .m-btm {
    margin-top: 4px;
  }
  .tight-footer .z-terms,
  .tight-footer .r-terms,
  .tight-footer .m-terms {
    line-height: 1.3;
  }
  .tight-footer .z-thanks,
  .tight-footer .r-thanks {
    margin: 4px 0;
  }
  .no-terms .z-terms,
  .no-terms .r-terms,
  .no-terms .m-terms {
    display: none !important;
  }


  /* ══════════════════════════════════════════════════════════════
     ENTITY A: ZAIN MOTORS / ZAIN MOTORS WORKSHOP
     Sans-Serif | Professional | Clean | Dark header
     ══════════════════════════════════════════════════════════════ */
  .zain-page {
    font-family: 'Arial', 'Helvetica Neue', 'Helvetica', sans-serif;
    color: #000;
    padding: 8px 4px;
    position: relative;
  }
  .zain-page.show-page-num { counter-reset: page 1; }
  .zain-page.show-page-num::after {
    content: "Page " counter(page) " of " var(--page-total);
    position: absolute;
    right: 6px;
    bottom: -10mm;
    font-size: 7pt;
    color: #555;
  }

  .z-header { margin-bottom: 2px; }
  .z-name {
    font-weight: 900; letter-spacing: 3px; margin: 0; line-height: 1.05; color: #000;
    font-family: 'Helvetica Neue', 'Arial Black', sans-serif;
  }
  .z-contact { color: #111; margin-top: 4px; font-weight: 700; }
  .z-dot { margin: 0 6px; color: #333; }
  .z-vatno { color: #000; margin-top: 3px; font-weight: 800; letter-spacing: 0.6px; }

  .z-quot-row {
    display: flex; justify-content: space-between; align-items: center;
    margin-top: 8px; padding: 6px 0 2px;
    border-top: 1px solid #000;
  }
  .z-quot-lbl {
    font-weight: 900; letter-spacing: 3px; text-transform: uppercase; color: #000;
    border-bottom: 2px solid #000; padding-bottom: 2px; display: inline-block;
  }
  .z-quot-meta { display: flex; gap: 14px; align-items: center; font-weight: 700; color: #111; }
  .z-ml { font-weight: 900; color: #000; }

  .z-hdr-line {
    height: 1px; background: #000; margin: 6px 0 8px;
  }

  .z-subject { margin: 4px 0 8px; font-weight: 600; }

  /* Client details — no boxes */
  .z-client {
    display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
    padding: 6px 0 10px; border-bottom: 1px solid #000; margin-bottom: 10px;
  }
  .z-client-title { font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }

  /* Table — black header bar, no vertical lines */
  .z-tbl { width: 100%; border-collapse: collapse; }
  .z-tbl thead { display: table-header-group; }
  .z-tbl thead tr { background: #000 !important; }
  .z-tbl thead th {
    padding: 6px 7px; color: #fff !important; font-weight: 900;
    text-align: left; border: none; text-transform: uppercase; letter-spacing: 0.6px;
  }
  .z-desc-head { text-align: center; }
  .z-tbl tbody tr { page-break-inside: avoid; }
  .z-tbl tbody td { padding: 4px 6px; border: none; border-bottom: 1px solid #222; color: #000; font-weight: 700; }
  .z-tbl tbody tr:nth-child(even) {
    background: #f4f4f4 !important;
    -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;
  }

  /* Footer — stays together */
  .z-footer { page-break-inside: avoid; margin-top: 6px; }
  .z-totals { max-width: 320px; margin-left: auto; }
  .z-trow, .z-grand { display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid #000; }
  .z-grand { border-top: 3px solid #000; border-bottom: 3px solid #000; margin-top: 6px; padding: 6px 0; }
  .z-tl { font-weight: 900; color: #000; }
  .z-tv { min-width: 120px; text-align: right; }
  .z-vatinc-note { font-weight: 800; font-style: italic; text-align: right; color: #000; margin-top: 4px; }

  /* In Words — BIGGER & BOLDER */
  .z-inwords {
    padding: 8px 14px; border: 2px solid #000;
    margin-top: 10px; line-height: 1.5;
  }
  .z-iw-lbl { font-weight: 900; text-transform: uppercase; letter-spacing: 1px; color: #000; }
  .z-iw-txt { font-weight: 800; font-style: italic; color: #000; }
  .z-thanks { text-align: center; font-style: italic; color: #111; margin: 10px 0; font-weight: 700; }

  .z-btm { display: flex; justify-content: space-between; margin-top: 12px; align-items: flex-end; }
  .z-terms { flex: 1; color: #000; line-height: 1.65; font-weight: 700; }
  .z-sig { text-align: center; min-width: 190px; flex-shrink: 0; }
  .z-sig-ln { width: 170px; border-bottom: 2px solid #000; margin: 0 auto 5px; }


  /* ══════════════════════════════════════════════════════════════
     ENTITY B: RAGEE AUTOMOTIVES
     Serif | Traditional | Old School | Bottom borders only
     PAN only: 301492753
     ══════════════════════════════════════════════════════════════ */
  .ragee-page {
    font-family: 'Times New Roman', 'Georgia', 'Garamond', serif;
    color: #000;
    position: relative;
  }
  .ragee-page.show-page-num { counter-reset: page 1; }
  .ragee-page.show-page-num::after {
    content: "Page " counter(page) " of " var(--page-total);
    position: absolute;
    right: 6px;
    bottom: -10mm;
    font-size: 7pt;
    color: #555;
  }

  .r-hdr { text-align: center; padding-bottom: 6px; }
  .r-name {
    font-weight: 800; margin: 0; letter-spacing: 3px;
    font-family: 'Times New Roman', 'Georgia', serif; color: #000;
  }
  .r-desc { font-style: italic; color: #222; margin: 2px 0 0; font-weight: 600; }
  .r-addr { color: #333; margin: 2px 0 0; font-weight: 600; }
  .r-pan { color: #222; margin: 1px 0 0; font-weight: 700; }
  .r-line1 { height: 2.5px; background: #000; margin-bottom: 2px; }
  .r-line2 { height: 1px; background: #666; margin-bottom: 10px; }

  .r-title {
    text-align: center; margin: 6px 0 12px;
    font-weight: 800; font-style: italic; letter-spacing: 8px;
    text-decoration: underline; text-underline-offset: 5px; color: #000;
  }

  .r-meta {
    display: flex; justify-content: space-between; margin-bottom: 12px;
    gap: 12px; line-height: 1.9; color: #000;
  }
  .r-meta-l { flex: 1; }
  .r-meta-r { text-align: right; white-space: nowrap; }
  .r-lb { font-weight: 800; color: #000; }

  /* Table — horizontal lines only */
  .r-tbl { width: 100%; border-collapse: collapse; }
  .r-tbl thead { display: table-header-group; }
  .r-tbl thead tr { border-bottom: 2.5px solid #000; }
  .r-tbl thead th {
    padding: 5px 7px; font-weight: 800; font-style: italic;
    text-align: left; border: none;
    border-bottom: 2.5px solid #000; border-top: 2px solid #000;
    letter-spacing: 0.5px; color: #000;
  }
  .r-tbl tbody tr { page-break-inside: avoid; }
  .r-tbl tbody td { padding: 4px 6px; border: none; border-bottom: 1px solid #aaa; color: #000; font-weight: 600; }

  /* Totals */
  .r-footer { page-break-inside: avoid; }
  .r-tot { width: 100%; border-collapse: collapse; }
  .r-tot td { padding: 5px 8px; border: none; }
  .r-tl { text-align: right; padding-right: 10px; color: #000; font-weight: 700; }
  .r-tv { width: 110px; text-align: right; }
  .r-row-sub td { border-top: 2px solid #000; }
  .r-row-vat td { font-style: italic; }
  .r-row-grand td { border-top: 3px double #000; border-bottom: 3px double #000; }
  .r-vatinc { font-style: italic; font-weight: 800; text-align: right; margin: 4px 0; color: #000; }

  /* In Words — serif italic with dash */
  .r-inwords {
    margin: 12px 0; padding: 8px 0;
    border-top: 2px solid #000; border-bottom: 2px solid #000;
    font-style: italic; line-height: 1.5;
  }
  .r-iw-lbl { font-weight: 900; color: #000; font-style: italic; }
  .r-iw-txt { font-weight: 800; color: #000; font-style: italic; }

  .r-thanks { font-style: italic; margin: 10px 0; color: #222; text-align: center; font-weight: 600; }

  .r-btm { display: flex; justify-content: space-between; margin-top: 14px; align-items: flex-end; }
  .r-terms { flex: 1; color: #000; line-height: 1.65; font-weight: 600; }
  .r-sig { text-align: center; min-width: 190px; }
  .r-sig-ln { width: 170px; border-bottom: 2px solid #000; margin: 0 auto 5px; }


  /* ══════════════════════════════════════════════════════════════
     ENTITY C: MOON STAR ENGINEERING WORKSHOP
     Monospace | Simple borders | Clean industrial
     Reg: 7835/136/2069/2070
     ══════════════════════════════════════════════════════════════ */
  .moon-page {
    font-family: 'Arial', 'Helvetica Neue', sans-serif;
    color: #000;
    position: relative;
  }
  .moon-page.show-page-num { counter-reset: page 1; }
  .moon-page.show-page-num::after {
    content: "Page " counter(page) " of " var(--page-total);
    position: absolute;
    right: 6px;
    bottom: -10mm;
    font-size: 7pt;
    color: #555;
  }

  .m-hdr {
    border-top: 4px solid #000; border-bottom: 3px solid #000;
    padding: 6px 0; text-align: center; margin-bottom: 8px;
  }
  .m-name {
    font-weight: 900; letter-spacing: 2px; margin: 0;
    font-family: 'Arial', 'Helvetica Neue', sans-serif; color: #000;
  }
  .m-addr { color: #111; margin: 3px 0 0; font-weight: 700; }
  .m-reg { color: #222; margin: 1px 0 0; font-weight: 800; }

  .m-title {
    text-align: center; margin: 6px 0 10px;
    font-weight: 900; letter-spacing: 4px; color: #000;
    text-decoration: underline; text-underline-offset: 4px;
    font-family: 'Arial', 'Helvetica Neue', sans-serif;
  }

  /* Meta — simple text lines */
  .m-meta {
    display: flex; justify-content: space-between; margin-bottom: 10px;
    line-height: 1.9; color: #000; font-weight: 700;
    border-bottom: 1px solid #999; padding-bottom: 6px;
  }
  .m-meta-l { flex: 1; }
  .m-meta-r { text-align: right; }

  /* Table — borders on every cell */
  .m-tbl { width: 100%; border-collapse: collapse; }
  .m-tbl thead { display: table-header-group; }
  .m-tbl thead tr {
    background: #ddd !important;
    -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;
  }
  .m-tbl thead th {
    padding: 5px 6px; font-weight: 900; color: #000;
    text-align: left; border: 1.5px solid #000;
    letter-spacing: 1px;
  }
  .m-tbl tbody tr { page-break-inside: avoid; }
  .m-tbl tbody td { padding: 3px 5px; border: 1.5px solid #000; color: #000; font-weight: 700; }

  /* Totals */
  .m-footer { page-break-inside: avoid; }
  .m-tot { width: 100%; border-collapse: collapse; }
  .m-tot td { padding: 4px 6px; border: 1.5px solid #000; color: #000; }
  .m-tl { text-align: right; padding-right: 6px; font-weight: 800; }
  .m-tv { width: 100px; text-align: right; }
  .m-row-sub td { border-top: 3px solid #000; }
  .m-row-vat td { font-weight: 800; }
  .m-row-grand td {
    border-top: 3px double #000;
    background: #ddd !important;
    -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important;
  }
  .m-vatinc { font-weight: 900; text-align: right; margin: 4px 0; color: #000; }

  /* In Words — simple underlined */
  .m-inwords {
    margin: 10px 0; padding: 6px 10px;
    border: 2px solid #000; line-height: 1.5;
  }

  .m-btm { display: flex; justify-content: space-between; margin-top: 14px; align-items: flex-end; }
  .m-terms { flex: 1; line-height: 1.65; color: #000; font-weight: 700; }
  .m-sig { text-align: center; min-width: 170px; }
  .m-sig-ln { width: 160px; border-bottom: 3px solid #000; margin: 0 auto 4px; }
}
