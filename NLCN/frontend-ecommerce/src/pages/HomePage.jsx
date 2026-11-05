import { useEffect, useMemo, useState } from 'react';
import { Check, ChevronDown, ChevronLeft, ChevronRight, Columns3, LayoutGrid, Rows3, Search, Sparkles } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { CATEGORIES, COLORS, CRAFTS, NEUTRALS, OCCASIONS, PRICE_MAX, PRICE_MIN, PRODUCTS, SIZES } from '../data/products';
import { money } from '../lib/pricing';
import ProductCard from '../components/ProductCard';
import ProductImage from '../components/ProductImage';
import { Breadcrumb, EmptyState, SizeGuide, Switch } from '../components/ui';

const PAGE_SIZE = 6;

const SORTS = [
  { id: 'ai', label: 'Curated by AI Match (98% ↓)', fn: (a, b) => b.ai - a.ai },
  { id: 'new', label: 'Newest arrivals', fn: (a, b) => b.added - a.added },
  { id: 'price-asc', label: 'Price: low to high', fn: (a, b) => a.price - b.price },
  { id: 'price-desc', label: 'Price: high to low', fn: (a, b) => b.price - a.price },
];

const VIEWS = [
  { id: '3', label: '3-Col', icon: LayoutGrid, grid: 'grid-cols-2 xl:grid-cols-3' },
  { id: '4', label: '4-Col', icon: Columns3, grid: 'grid-cols-3 xl:grid-cols-4' },
  { id: 'ed', label: 'Editorial', icon: Rows3, grid: 'grid-cols-2' },
];

const toggle = (arr, v) => (arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v]);

export default function HomePage({ query }) {
  const { toast } = useStore();

  const [q, setQ] = useState('');
  const [sort, setSort] = useState('ai');
  const [view, setView] = useState('3');
  const [sync, setSync] = useState(true);
  const [cats, setCats] = useState(query?.cat ? [query.cat] : []);
  const [colors, setColors] = useState([]);
  const [sizes, setSizes] = useState([]);
  const [crafts, setCrafts] = useState([]);
  const [occ, setOcc] = useState([]);
  const [min, setMin] = useState(PRICE_MIN);
  const [max, setMax] = useState(PRICE_MAX);
  const [page, setPage] = useState(1);
  const [guide, setGuide] = useState(false);

  // Vào từ Storefront với /catalog?cat=blazers → lọc sẵn danh mục
  useEffect(() => {
    if (query?.cat) setCats([query.cat]);
  }, [query?.cat]);

  const filtered = useMemo(() => {
    const s = q.trim().toLowerCase();
    const fn = SORTS.find((x) => x.id === sort).fn;
    return PRODUCTS.filter((p) => {
      if (s && !`${p.name} ${p.kind} ${p.material} ${p.short}`.toLowerCase().includes(s)) return false;
      if (cats.length && !cats.includes(p.category)) return false;
      if (colors.length && !p.colors.some((c) => colors.includes(c))) return false;
      if (sizes.length && !p.sizes.some((x) => sizes.includes(x))) return false;
      if (crafts.length && !p.craft.some((c) => crafts.includes(c))) return false;
      if (occ.length && !p.occasions.some((o) => occ.includes(o))) return false;
      if (p.price < min || p.price > max) return false;
      if (sync && !p.colors.some((c) => NEUTRALS.includes(c))) return false;
      return true;
    }).sort(fn);
  }, [q, sort, cats, colors, sizes, crafts, occ, min, max, sync]);

  // Mỗi lần đổi bộ lọc → về trang 1
  useEffect(() => setPage(1), [q, sort, cats, colors, sizes, crafts, occ, min, max, sync]);

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const shown = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const from = filtered.length ? (page - 1) * PAGE_SIZE + 1 : 0;
  const to = Math.min(page * PAGE_SIZE, filtered.length);

  const active = cats.length + colors.length + sizes.length + crafts.length + occ.length + (min !== PRICE_MIN || max !== PRICE_MAX ? 1 : 0) + (q ? 1 : 0);
  const clearAll = () => {
    setQ(''); setCats([]); setColors([]); setSizes([]); setCrafts([]); setOcc([]); setMin(PRICE_MIN); setMax(PRICE_MAX);
  };

  const grid = VIEWS.find((v) => v.id === view).grid;
  const catCount = (id) => PRODUCTS.filter((p) => p.category === id).length;

  return (
    <div className="shell pb-4 pt-7">
      {/* breadcrumb + live curator */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
        <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Women', to: '/catalog' }, { label: 'Autumn-Winter Capsule' }]} />
        <span className="chip"><span className="size-2 rounded-full bg-stone-600" /> Live curator active: 14 stylists in atelier</span>
      </div>

      {/* hero */}
      <section className="relative overflow-hidden rounded-xl bg-stone-200 px-12 pb-14 pt-12">
        <svg className="pointer-events-none absolute right-10 top-0 h-64 w-96 opacity-25" viewBox="0 0 384 256" aria-hidden="true">
          <rect x="88" y="26" width="208" height="208" fill="none" stroke="#52525b" />
          <line x1="88" y1="133" x2="296" y2="133" stroke="#52525b" strokeWidth=".7" />
          <line x1="194" y1="26" x2="194" y2="234" stroke="#52525b" strokeWidth=".7" />
          <rect x="190" y="129" width="8" height="8" fill="#52525b" />
        </svg>
        <div className="relative max-w-2xl">
          <span className="inline-block bg-black px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white">Capsule N° 04 — AW25</span>
          <h1 className="display mt-3 text-6xl leading-[72px]">Architectural Solitude</h1>
          <p className="mt-2 max-w-xl text-lg leading-7 text-zinc-700">
            Structured outerwear, double-faced vicuña cashmere, and calibrated monochrome tailoring conceived for the metropolitan wardrobe.
          </p>
        </div>
      </section>

      {/* toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 py-5">
        <p className="flex items-center gap-2">
          <span className="text-sm font-medium tracking-tight">{filtered.length} Garments</span>
          <span className="eyebrow !font-medium">• All limited editions</span>
        </p>
        <div className="flex flex-wrap items-center gap-4">
          <label className="relative block w-64">
            <Search className="absolute left-3 top-1/2 size-3.5 -translate-y-1/2 text-zinc-700" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter by piece, fabric, style..." className="field !py-2 !pl-9 text-sm font-medium tracking-tight shadow-soft" aria-label="Filter catalog" />
          </label>

          <label className="relative flex items-center rounded-lg bg-stone-100 py-1.5 pl-3 shadow-soft">
            <span className="eyebrow pr-2">Sort:</span>
            <select value={sort} onChange={(e) => setSort(e.target.value)} className="cursor-pointer appearance-none bg-transparent py-0.5 pl-1 pr-8 text-sm font-medium tracking-tight outline-none">
              {SORTS.map((s) => <option key={s.id} value={s.id}>{s.label}</option>)}
            </select>
            <ChevronDown className="pointer-events-none absolute right-3 size-3.5 text-zinc-700" />
          </label>

          <div className="flex items-center gap-1 rounded-lg bg-stone-100 p-1 shadow-soft" role="group" aria-label="Grid layout">
            {VIEWS.map((v) => (
              <button
                key={v.id}
                type="button"
                onClick={() => setView(v.id)}
                aria-pressed={view === v.id}
                className={`flex items-center gap-1.5 rounded-sm px-2.5 py-1 text-xs font-semibold uppercase tracking-wider transition ${view === v.id ? 'bg-black text-white' : 'text-zinc-700 hover:bg-stone-200'}`}
              >
                <v.icon className="size-3.5" /> {v.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-[17rem_minmax(0,1fr)] items-start gap-8 pb-16 xl:grid-cols-[18rem_minmax(0,1fr)]">
        {/* sidebar */}
        <aside className="sticky top-32 max-h-[calc(100vh-9rem)] space-y-4 overflow-y-auto rounded-xl bg-stone-100/70 p-4 shadow-soft backdrop-blur-md" aria-label="Filters">
          <div className="card p-4">
            <div className="flex items-center justify-between pb-1">
              <p className="eyebrow-ink flex items-center gap-2"><Sparkles className="size-4 text-stone-600" strokeWidth={1.6} /> AI Palette Sync</p>
              <Switch checked={sync} onChange={(v) => { setSync(v); toast(v ? 'Palette sync on — neutral wardrobe capsule' : 'Showing the full catalogue'); }} label="AI Palette Sync" />
            </div>
            <p className="text-xs leading-5 tracking-tight text-zinc-700">
              {sync ? 'Filtering catalogue to complement your uploaded neutral-tone wardrobe capsule.' : 'Palette sync is off — showing every piece in the capsule.'}
            </p>
            <div className="flex items-center gap-1.5 pt-3">
              {['#18181b', '#e7e5e4', '#78716c', '#404040'].map((c) => <span key={c} className="size-4 rounded-full shadow-soft" style={{ background: c }} />)}
              <span className="pl-1 text-[10px] uppercase leading-6 text-zinc-700">{sync ? 'Calibrated' : 'Off'}</span>
            </div>
          </div>

          <Filter title="Garment category">
            <div className="space-y-1">
              {CATEGORIES.map((c) => {
                const on = cats.includes(c.id);
                return (
                  <button key={c.id} type="button" onClick={() => setCats(toggle(cats, c.id))} aria-pressed={on} className={`flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-xs tracking-tight transition ${on ? 'bg-stone-900 text-stone-50' : 'hover:bg-stone-100'}`}>
                    {c.label}
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${on ? 'bg-white/20' : 'bg-gray-200 text-zinc-700'}`}>{catCount(c.id)}</span>
                  </button>
                );
              })}
            </div>
          </Filter>

          <Filter title="Palette shades">
            <div className="flex flex-wrap gap-2">
              {Object.entries(COLORS).map(([id, c]) => {
                const on = colors.includes(id);
                return (
                  <button key={id} type="button" onClick={() => setColors(toggle(colors, id))} aria-pressed={on} className={`flex items-center gap-1.5 rounded-full py-1 pl-1 pr-2.5 text-[11px] font-semibold uppercase tracking-wide transition ${on ? 'bg-stone-900 text-stone-50' : 'bg-stone-100 text-zinc-700 hover:bg-stone-200'}`}>
                    <span className="size-4 rounded-full ring-1 ring-black/10" style={{ background: c.hex }} /> {c.label}
                  </button>
                );
              })}
            </div>
          </Filter>

          <Filter title="French sizing (FR)" action={<button type="button" onClick={() => setGuide(true)} className="text-[11px] font-semibold uppercase tracking-wide text-zinc-700 underline underline-offset-2 hover:text-stone-900">Size guide</button>}>
            <div className="grid grid-cols-3 gap-2">
              {SIZES.map((s) => {
                const on = sizes.includes(s);
                return (
                  <button key={s} type="button" onClick={() => setSizes(toggle(sizes, s))} aria-pressed={on} className={`rounded-md py-1.5 text-xs font-medium transition ${on ? 'bg-stone-900 text-stone-50' : 'bg-stone-100 text-stone-900 hover:bg-stone-200'}`}>FR {s}</button>
                );
              })}
            </div>
          </Filter>

          <Filter title="Investment range">
            <p className="display mb-3 text-xl">{money(min)} — {money(max)}{max === PRICE_MAX ? '+' : ''}</p>
            <label className="eyebrow block !text-[10px]">From
              <input type="range" min={PRICE_MIN} max={PRICE_MAX} step={10} value={min} onChange={(e) => setMin(Math.min(+e.target.value, max))} className="mt-1 h-1 w-full accent-stone-900" aria-label="Minimum price" />
            </label>
            <label className="eyebrow mt-3 block !text-[10px]">To
              <input type="range" min={PRICE_MIN} max={PRICE_MAX} step={10} value={max} onChange={(e) => setMax(Math.max(+e.target.value, min))} className="mt-1 h-1 w-full accent-stone-900" aria-label="Maximum price" />
            </label>
          </Filter>

          <Filter title="Craftsmanship & traceability">
            <Checks items={CRAFTS} value={crafts} onChange={setCrafts} />
          </Filter>

          <Filter title="Atmosphere / occasion">
            <Checks items={OCCASIONS} value={occ} onChange={setOcc} />
          </Filter>

          <button type="button" onClick={clearAll} disabled={!active} className="w-full py-1 text-center text-xs font-semibold uppercase tracking-wide text-zinc-700 underline underline-offset-4 transition hover:text-stone-900 disabled:no-underline disabled:opacity-40">
            Clear all preferences ({active} active)
          </button>
        </aside>

        {/* grid */}
        <section aria-label="Products" className="min-w-0">
          {shown.length ? (
            <div className={`grid gap-6 ${grid}`}>
              {shown.map((p) => <ProductCard key={p.id} product={p} showAi={sync || sort === 'ai'} compact={view === '4'} />)}
            </div>
          ) : (
            <EmptyState icon={Search} title="No garment matches" text="Try loosening a filter, or ask Elena, our AI stylist, to curate something for you.">
              <button type="button" onClick={clearAll} className="btn-primary">Clear preferences</button>
              <Link to="/stylist" className="btn-outline">Ask Elena</Link>
            </EmptyState>
          )}

          {/* pagination */}
          {filtered.length > 0 && (
            <div className="mt-8 flex items-center justify-between rounded-xl bg-stone-100/50 p-4">
              <p className="text-xs tracking-tight text-zinc-700">
                Displaying <b className="text-stone-900">{from} — {to}</b> of <b className="text-stone-900">{filtered.length}</b> haute couture garments
              </p>
              <div className="flex items-center gap-1.5">
                <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="flex size-9 items-center justify-center rounded-lg bg-white shadow-soft transition hover:bg-stone-200 disabled:opacity-40" aria-label="Previous page"><ChevronLeft className="size-4" /></button>
                {Array.from({ length: pages }, (_, i) => i + 1).map((n) => (
                  <button key={n} type="button" onClick={() => setPage(n)} aria-current={n === page ? 'page' : undefined} className={`size-9 rounded-lg text-xs font-semibold shadow-soft transition ${n === page ? 'bg-black text-white' : 'bg-white hover:bg-stone-200'}`}>{n}</button>
                ))}
                <button type="button" onClick={() => setPage((p) => Math.min(pages, p + 1))} disabled={page === pages} className="flex size-9 items-center justify-center rounded-lg bg-white shadow-soft transition hover:bg-stone-200 disabled:opacity-40" aria-label="Next page"><ChevronRight className="size-4" /></button>
              </div>
              <span className="eyebrow">Atelier speed: instant</span>
            </div>
          )}
        </section>
      </div>

      {/* CTA: runway archive */}
      <section className="mb-4 grid grid-cols-[1fr_auto] items-center gap-12 rounded-xl bg-gray-200 p-12 shadow-soft">
        <div className="max-w-2xl">
          <p className="eyebrow mb-3">Runway archive synchronicity</p>
          <h2 className="display text-4xl leading-tight">Complete the Look with AI Salon Styling</h2>
          <p className="mt-4 text-sm leading-6 text-zinc-700">Connect your existing digital wardrobe or schedule a private 1-on-1 video consultation with our Paris Flagship head tailor.</p>
          <div className="mt-7 flex flex-wrap gap-3">
            <Link to="/runway" className="btn-primary">Explore 3-piece capsule edits</Link>
            <button type="button" onClick={() => toast('Request received — your concierge will confirm within two hours')} className="btn-outline bg-white/40">Book private appointment</button>
          </div>
        </div>
        <div className="flex gap-4">
          {[PRODUCTS[0], PRODUCTS[4]].map((p, i) => (
            <Link key={p.id} to={`/product/${p.id}`} className={`block h-64 w-52 overflow-hidden rounded-lg shadow-float transition hover:-translate-y-1 ${i ? 'mt-8' : ''}`} aria-label={p.name}>
              <ProductImage product={p} label={false} />
            </Link>
          ))}
        </div>
      </section>

      <SizeGuide open={guide} onClose={() => setGuide(false)} />
    </div>
  );
}

function Filter({ title, action, children }) {
  const [open, setOpen] = useState(true);
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between">
        <button type="button" onClick={() => setOpen((o) => !o)} aria-expanded={open} className="eyebrow-ink flex flex-1 items-center justify-between pr-2 text-left">
          {title}
          <ChevronDown className={`size-3.5 text-zinc-700 transition-transform ${open ? '' : '-rotate-90'}`} />
        </button>
        {action}
      </div>
      {open && <div className="pt-3">{children}</div>}
    </div>
  );
}

function Checks({ items, value, onChange }) {
  return (
    <div className="space-y-2">
      {items.map((it) => {
        const on = value.includes(it.id);
        return (
          <label key={it.id} className="flex cursor-pointer items-start gap-2.5 text-xs leading-5 tracking-tight text-stone-900">
            <input type="checkbox" checked={on} onChange={() => onChange(toggle(value, it.id))} className="peer sr-only" />
            <span className={`mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-sm border transition peer-focus-visible:outline peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 ${on ? 'border-stone-900 bg-stone-900 text-white' : 'border-stone-400 bg-white'}`}>
              {on && <Check className="size-3" strokeWidth={3} />}
            </span>
            {it.label}
          </label>
        );
      })}
    </div>
  );
}
