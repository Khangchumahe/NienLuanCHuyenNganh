import { useEffect, useMemo, useRef, useState } from 'react';
import { CornerDownLeft, FileText, Search, Shirt } from 'lucide-react';
import { navigate } from '../lib/router';
import { PRODUCTS } from '../data/products';
import { money } from '../lib/pricing';

const PAGES = [
  { label: 'Collections — Storefront', to: '/' },
  { label: 'Catalog — Autumn-Winter Capsule', to: '/catalog' },
  { label: 'Runway — Paris Archive', to: '/runway' },
  { label: 'AI Stylist — Elena', to: '/stylist' },
  { label: 'Shopping Bag', to: '/cart' },
  { label: 'Saved Pieces', to: '/wishlist' },
  { label: 'Privilege & Points', to: '/account' },
  { label: 'Client Profile', to: '/profile' },
  { label: 'Order Tracking', to: '/order' },
];

/** Command palette: ⌘K / Ctrl+K mở, ↑↓ chọn, Enter đi, Esc đóng */
export default function SearchModal({ open, onClose }) {
  const [q, setQ] = useState('');
  const [idx, setIdx] = useState(0);
  const input = useRef(null);

  const results = useMemo(() => {
    const s = q.trim().toLowerCase();
    const prods = PRODUCTS.filter((p) => !s || `${p.name} ${p.kind} ${p.material}`.toLowerCase().includes(s)).slice(0, s ? 6 : 4).map((p) => ({ type: 'product', p, to: `/product/${p.id}` }));
    const pages = PAGES.filter((pg) => !s || pg.label.toLowerCase().includes(s)).slice(0, s ? 4 : 5).map((pg) => ({ type: 'page', pg, to: pg.to }));
    return [...prods, ...pages];
  }, [q]);

  useEffect(() => {
    if (open) {
      setQ('');
      setIdx(0);
      setTimeout(() => input.current?.focus(), 30);
    }
  }, [open]);
  useEffect(() => setIdx(0), [q]);

  const go = (r) => {
    if (!r) return;
    onClose();
    navigate(r.to);
  };

  const onKey = (e) => {
    if (e.key === 'Escape') onClose();
    else if (e.key === 'ArrowDown') { e.preventDefault(); setIdx((i) => Math.min(results.length - 1, i + 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setIdx((i) => Math.max(0, i - 1)); }
    else if (e.key === 'Enter') go(results[idx]);
  };

  if (!open) return null;
  return (
    <div className="no-print fixed inset-0 z-[60] flex items-start justify-center bg-stone-900/40 px-6 pt-[14vh] backdrop-blur-sm animate-fade-in" onMouseDown={onClose} role="dialog" aria-modal="true" aria-label="Search">
      <div className="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-float" onMouseDown={(e) => e.stopPropagation()}>
        <div className="flex items-center gap-3 border-b border-stone-100 px-5">
          <Search className="size-4 text-zinc-700" />
          <input ref={input} value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={onKey} placeholder="Search pieces, fabrics, pages…" className="h-14 flex-1 bg-transparent text-sm outline-none placeholder:text-zinc-700/60" />
          <kbd className="rounded-sm bg-stone-100 px-1.5 py-0.5 text-[10px] text-zinc-700">ESC</kbd>
        </div>
        <ul className="max-h-[50vh] overflow-y-auto p-2">
          {results.length === 0 && <li className="px-4 py-10 text-center text-sm text-zinc-700">No result for “{q}”.</li>}
          {results.map((r, i) => (
            <li key={r.to + i}>
              <button
                type="button"
                onMouseEnter={() => setIdx(i)}
                onClick={() => go(r)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition ${i === idx ? 'bg-stone-100' : ''}`}
              >
                {r.type === 'product' ? <Shirt className="size-4 shrink-0 text-zinc-700" strokeWidth={1.5} /> : <FileText className="size-4 shrink-0 text-zinc-700" strokeWidth={1.5} />}
                <span className="flex-1 truncate text-sm">{r.type === 'product' ? r.p.name : r.pg.label}</span>
                <span className="text-xs text-zinc-700">{r.type === 'product' ? money(r.p.price) : 'Page'}</span>
                {i === idx && <CornerDownLeft className="size-3.5 text-zinc-700" />}
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
