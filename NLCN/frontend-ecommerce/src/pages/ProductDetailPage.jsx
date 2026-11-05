import { useEffect, useMemo, useState } from 'react';
import { Heart, Minus, Plus, RotateCcw, ShieldCheck, ShoppingBag, Sparkles, Truck, ChevronDown, SearchX } from 'lucide-react';
import { Link, navigate } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { COLORS, LOOKS, PRODUCTS, categoryLabel, getProduct, sizeLabel } from '../data/products';
import { money } from '../lib/pricing';
import ProductCard from '../components/ProductCard';
import ProductImage from '../components/ProductImage';
import { Breadcrumb, EmptyState, SizeGuide } from '../components/ui';

export default function ProductDetailPage({ params }) {
  const product = getProduct(params.id);
  if (!product) {
    return (
      <div className="shell pt-10">
        <EmptyState icon={SearchX} title="Piece not found" text="This piece is no longer part of the capsule, or the link is incorrect.">
          <Link to="/catalog" className="btn-primary">Back to catalog</Link>
        </EmptyState>
      </div>
    );
  }
  // key = id → đổi sản phẩm thì reset toàn bộ state chọn size/màu
  return <Detail key={product.id} p={product} />;
}

function Detail({ p }) {
  const { addToCart, toggleWish, wishlist } = useStore();
  const [color, setColor] = useState(p.colors[0]);
  const [size, setSize] = useState(null);
  const [qty, setQty] = useState(1);
  const [view, setView] = useState(0);
  const [error, setError] = useState('');
  const [guide, setGuide] = useState(false);
  const [open, setOpen] = useState('details');

  const saved = wishlist.includes(p.id);
  const needsSize = p.sizes.length > 0;

  useEffect(() => {
    document.title = `${p.name} — Atelier Studio`;
    return () => { document.title = 'Atelier Studio — Haute Couture'; };
  }, [p.name]);

  const related = useMemo(() => {
    const look = LOOKS.find((l) => l.items.includes(p.id));
    const ids = look ? look.items.filter((i) => i !== p.id) : [];
    const fill = PRODUCTS.filter((x) => x.id !== p.id && !ids.includes(x.id)).sort((a, b) => Number(b.category === p.category) - Number(a.category === p.category) || b.ai - a.ai).map((x) => x.id);
    return [...ids, ...fill].slice(0, 4).map(getProduct);
  }, [p]);

  const validate = () => {
    if (needsSize && size == null) {
      setError(`Please select a size${p.sizesLabel ? ' (EU)' : ' (FR)'} to continue.`);
      return false;
    }
    setError('');
    return true;
  };
  const add = () => validate() && addToCart(p.id, { size, color, qty });
  const buyNow = () => {
    if (!validate()) return;
    addToCart(p.id, { size, color, qty });
    navigate('/cart');
  };

  const sections = [
    { id: 'details', title: 'Description', body: p.description },
    { id: 'composition', title: 'Composition & care', body: `${p.composition}. ${p.care}` },
    { id: 'delivery', title: 'Delivery & returns', body: 'Complimentary white-glove delivery and carbon-neutral logistics. Returns accommodated at courier handover inspection or within 30 days via private collection.' },
    { id: 'craft', title: 'Craftsmanship & traceability', body: 'Each piece carries an NFC authenticity seal verifying fibre origin, certification and the signature of the tailor who finished it. Lifetime maintenance is included.' },
  ];

  return (
    <div className="shell pb-8 pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Catalog', to: '/catalog' }, { label: categoryLabel(p.category), to: `/catalog?cat=${p.category}` }, { label: p.name }]} />

      <div className="mt-6 grid grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] items-start gap-12">
        {/* gallery */}
        <div className="grid grid-cols-[5rem_minmax(0,1fr)] gap-4">
          <div className="flex flex-col gap-3" role="tablist" aria-label="Product views">
            {[0, 1, 2, 3].map((v) => (
              <button key={v} type="button" role="tab" aria-selected={view === v} onClick={() => setView(v)} className={`aspect-[3/4] overflow-hidden rounded-lg transition ${view === v ? 'ring-2 ring-stone-900 ring-offset-2 ring-offset-stone-50' : 'opacity-70 hover:opacity-100'}`}>
                <ProductImage product={p} color={color} variant={v} label={false} />
              </button>
            ))}
          </div>
          <div className="relative aspect-[4/5] overflow-hidden rounded-xl bg-stone-200 shadow-soft">
            <ProductImage product={p} color={color} variant={view} />
            <span className="chip absolute left-4 top-4 bg-white/90 !text-stone-900 backdrop-blur-md"><span className="size-1.5 rounded-full bg-stone-600" /> AI Match: {p.ai}%</span>
            {p.limited && <span className="absolute right-4 top-4 bg-black px-2.5 py-1 text-xs font-semibold uppercase tracking-wide text-white">Limited edition</span>}
          </div>
        </div>

        {/* info */}
        <div className="sticky top-32">
          <p className="eyebrow">{p.kind} • {p.material}</p>
          <h1 className="display mt-2 text-5xl leading-[1.1]">{p.name}</h1>
          <div className="mt-4 flex items-baseline gap-4">
            <span className="display text-3xl">{money(p.price)}</span>
            <span className={`text-xs font-semibold uppercase tracking-wider ${/only|1 pair/i.test(p.status) ? 'text-red-800' : 'text-stone-600'}`}>{p.status}</span>
          </div>
          <p className="mt-5 text-sm leading-6 text-zinc-700">{p.short}</p>

          {/* màu */}
          <div className="mt-7">
            <p className="eyebrow-ink mb-3">Palette — <span className="font-medium text-zinc-700">{COLORS[color].label}</span></p>
            <div className="flex gap-3">
              {p.colors.map((c) => (
                <button key={c} type="button" onClick={() => setColor(c)} aria-label={COLORS[c].label} aria-pressed={color === c} title={COLORS[c].label} className={`size-9 rounded-full ring-1 ring-black/10 transition ${color === c ? 'ring-2 !ring-stone-900 ring-offset-2 ring-offset-stone-50' : 'hover:scale-110'}`} style={{ background: COLORS[c].hex }} />
              ))}
            </div>
          </div>

          {/* size */}
          {needsSize && (
            <div className="mt-6">
              <div className="mb-3 flex items-center justify-between">
                <p className="eyebrow-ink">{p.sizesLabel ? 'European sizing (EU)' : 'French sizing (FR)'}</p>
                <button type="button" onClick={() => setGuide(true)} className="text-xs font-semibold uppercase tracking-wide text-zinc-700 underline underline-offset-4 hover:text-stone-900">Size guide</button>
              </div>
              <div className="grid grid-cols-6 gap-2" role="radiogroup" aria-label="Size">
                {p.sizes.map((s) => (
                  <button key={s} type="button" role="radio" aria-checked={size === s} onClick={() => { setSize(s); setError(''); }} className={`rounded-lg py-2.5 text-xs font-semibold transition ${size === s ? 'bg-stone-900 text-stone-50' : 'bg-stone-100 text-stone-900 hover:bg-stone-200'} ${error ? 'ring-1 ring-red-700/50' : ''}`}>
                    {sizeLabel(p, s)}
                  </button>
                ))}
              </div>
              {error && <p className="mt-2 text-xs font-medium text-red-800" role="alert">{error}</p>}
            </div>
          )}

          {/* số lượng + CTA */}
          <div className="mt-7 flex items-stretch gap-3">
            <div className="flex items-center rounded-lg bg-stone-100">
              <button type="button" onClick={() => setQty((q) => Math.max(1, q - 1))} disabled={qty <= 1} className="flex size-12 items-center justify-center disabled:opacity-30" aria-label="Decrease quantity"><Minus className="size-4" /></button>
              <span className="w-8 text-center text-sm font-semibold" aria-live="polite">{qty}</span>
              <button type="button" onClick={() => setQty((q) => Math.min(9, q + 1))} disabled={qty >= 9} className="flex size-12 items-center justify-center disabled:opacity-30" aria-label="Increase quantity"><Plus className="size-4" /></button>
            </div>
            <button type="button" onClick={add} className="btn-primary flex-1 !py-4"><ShoppingBag className="size-4" /> Add to bag — {money(p.price * qty)}</button>
            <button type="button" onClick={() => toggleWish(p.id)} aria-pressed={saved} aria-label={saved ? 'Remove from saved' : 'Save piece'} className="flex size-12 items-center justify-center rounded-lg border border-stone-300 transition hover:bg-stone-100">
              <Heart className={`size-5 ${saved ? 'fill-stone-900' : ''}`} strokeWidth={1.6} />
            </button>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-3">
            <button type="button" onClick={buyNow} className="btn-outline">Acquire now</button>
            <Link to="/stylist" className="btn-outline"><Sparkles className="size-4" /> Ask Elena about this piece</Link>
          </div>

          <ul className="mt-7 grid grid-cols-3 gap-3 text-center">
            {[[Truck, 'Complimentary white-glove delivery'], [RotateCcw, '30-day private returns'], [ShieldCheck, 'NFC authenticity seal']].map(([Icon, t]) => (
              <li key={t} className="rounded-lg bg-stone-100/70 px-3 py-4">
                <Icon className="mx-auto mb-2 size-5 text-stone-600" strokeWidth={1.4} />
                <span className="text-[11px] font-medium leading-4 text-zinc-700">{t}</span>
              </li>
            ))}
          </ul>

          <div className="mt-7 divide-y divide-stone-200 border-y border-stone-200">
            {sections.map((s) => (
              <div key={s.id}>
                <button type="button" onClick={() => setOpen(open === s.id ? '' : s.id)} aria-expanded={open === s.id} className="flex w-full items-center justify-between py-4 text-left">
                  <span className="eyebrow-ink">{s.title}</span>
                  <ChevronDown className={`size-4 text-zinc-700 transition-transform ${open === s.id ? 'rotate-180' : ''}`} />
                </button>
                {open === s.id && <p className="animate-fade-in pb-5 text-sm leading-6 text-zinc-700">{s.body}</p>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* complete the look */}
      <section className="mt-20">
        <div className="mb-8 flex items-end justify-between">
          <div>
            <p className="eyebrow mb-2">Elena • AI styling</p>
            <h2 className="display text-4xl">Complete the look</h2>
          </div>
          <Link to="/runway" className="btn-outline">View runway looks</Link>
        </div>
        <div className="grid grid-cols-4 gap-6">
          {related.map((r) => <ProductCard key={r.id} product={r} compact />)}
        </div>
      </section>

      <SizeGuide open={guide} onClose={() => setGuide(false)} />
    </div>
  );
}
