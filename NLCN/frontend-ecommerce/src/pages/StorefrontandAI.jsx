import { ArrowRight, Crown, Leaf, Scissors, ShieldCheck, Sparkles, Truck } from 'lucide-react';
import { Link, navigate } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { CATEGORIES, LOOKS, PRODUCTS, getProduct } from '../data/products';
import ProductCard from '../components/ProductCard';
import ProductImage from '../components/ProductImage';
import { SectionHead } from '../components/ui';

const SERVICES = [
  [Truck, 'Complimentary white-glove delivery', 'Private evening courier in Paris, insured worldwide.'],
  [Scissors, 'Bespoke alterations', 'Master-tailor finishing on every acquisition.'],
  [Leaf, 'Carbon-neutral logistics', 'Net-zero shipping from our Paris atelier.'],
  [ShieldCheck, 'NFC authenticity seal', 'Verify fibre origin and the tailor’s signature.'],
];

const TILES = [
  { cat: 'blazers', title: 'Tailoring', tone: 'double-breasted-blazer', note: 'Structured shoulders, hand-canvassed.' },
  { cat: 'cashmere', title: 'Vicuña & Cashmere', tone: 'sculpted-cashmere-turtleneck', note: 'Seven-gauge Mongolian cashmere.' },
  { cat: 'bags', title: 'Leather Goods', tone: 'minimalist-leather-tote', note: 'Vegetable-tanned Tuscan calf.' },
];

const PROMPTS = ['Suggest an evening coat', 'Analyze fabric drape', 'Color match my shoes'];

export default function StorefrontandAI() {
  const { user } = useStore();
  const top = [...PRODUCTS].sort((a, b) => b.ai - a.ai).slice(0, 4);
  const hero = ['double-breasted-blazer', 'cocoon-wool-coat', 'sculpted-cashmere-turtleneck'].map(getProduct);

  return (
    <div>
      {/* HERO */}
      <section className="shell grid grid-cols-[1.05fr_1fr] items-center gap-14 pb-16 pt-12">
        <div>
          <span className="chip"><span className="size-2 rounded-full bg-stone-600" /> Live curator active: 14 stylists in atelier</span>
          <p className="eyebrow mt-8">Capsule N° 04 — AW25</p>
          <h1 className="display mt-3 text-[4.5rem] leading-[1.05] xl:text-[5.25rem]">Tailoring for the metropolitan wardrobe</h1>
          <p className="mt-6 max-w-xl text-lg leading-7 text-zinc-700">
            Structured outerwear, double-faced vicuña cashmere and calibrated monochrome pieces, composed by master tailors and your personal AI stylist.
          </p>
          <div className="mt-9 flex flex-wrap gap-3">
            <Link to="/catalog" className="btn-primary !px-7 !py-4">Explore the capsule <ArrowRight className="size-4" /></Link>
            <Link to="/stylist" className="btn-outline !px-7 !py-4"><Sparkles className="size-4" /> Consult Elena, AI stylist</Link>
          </div>
          <dl className="mt-12 flex gap-12">
            {[[String(PRODUCTS.length), 'Limited-edition pieces'], ['4', 'Global salons'], ['98%', 'AI style match']].map(([n, l]) => (
              <div key={l}><dt className="display text-4xl">{n}</dt><dd className="eyebrow mt-1">{l}</dd></div>
            ))}
          </dl>
        </div>

        <div className="relative grid h-[34rem] grid-cols-6 grid-rows-6 gap-4">
          <Link to={`/product/${hero[0].id}`} className="col-span-4 row-span-4 overflow-hidden rounded-xl shadow-float transition hover:-translate-y-1" aria-label={hero[0].name}><ProductImage product={hero[0]} /></Link>
          <Link to={`/product/${hero[1].id}`} className="col-span-2 col-start-5 row-span-3 row-start-2 overflow-hidden rounded-xl shadow-float transition hover:-translate-y-1" aria-label={hero[1].name}><ProductImage product={hero[1]} label={false} /></Link>
          <Link to={`/product/${hero[2].id}`} className="col-span-3 col-start-3 row-span-2 row-start-5 overflow-hidden rounded-xl shadow-float transition hover:-translate-y-1" aria-label={hero[2].name}><ProductImage product={hero[2]} label={false} /></Link>
          <div className="col-span-2 col-start-1 row-span-2 row-start-5 flex flex-col justify-end rounded-xl bg-stone-900 p-5 text-stone-50">
            <Sparkles className="mb-auto size-5" strokeWidth={1.4} />
            <p className="display text-3xl !text-stone-50">98%</p>
            <p className="text-[11px] uppercase tracking-wider text-stone-400">Curated AI match</p>
          </div>
        </div>
      </section>

      {/* SERVICES */}
      <section className="border-y border-stone-200 bg-stone-100/60" aria-label="Services">
        <ul className="shell grid grid-cols-4 gap-8 py-8">
          {SERVICES.map(([Icon, t, d]) => (
            <li key={t} className="flex gap-4">
              <Icon className="mt-0.5 size-6 shrink-0 text-stone-600" strokeWidth={1.3} />
              <div><p className="text-sm font-semibold">{t}</p><p className="mt-1 text-xs leading-5 text-zinc-700">{d}</p></div>
            </li>
          ))}
        </ul>
      </section>

      {/* COLLECTIONS */}
      <section className="shell pt-20">
        <SectionHead eyebrow="Collections" title="Shop by garment" action={<Link to="/catalog" className="btn-outline">View all {PRODUCTS.length} pieces</Link>} />
        <div className="grid grid-cols-3 gap-6">
          {TILES.map((t) => {
            const p = getProduct(t.tone);
            const n = PRODUCTS.filter((x) => x.category === t.cat).length;
            return (
              <Link key={t.cat} to={`/catalog?cat=${t.cat}`} className="group relative block aspect-[4/5] overflow-hidden rounded-xl shadow-soft">
                <div className="h-full w-full transition duration-700 group-hover:scale-105"><ProductImage product={p} label={false} /></div>
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-stone-900/70 to-transparent p-6 pt-24 text-stone-50">
                  <p className="text-[11px] font-semibold uppercase tracking-wider opacity-80">{n} pieces</p>
                  <h3 className="display mt-1 text-3xl !text-stone-50">{t.title}</h3>
                  <p className="mt-1 flex items-center justify-between text-xs opacity-90">{t.note}<ArrowRight className="size-4 transition group-hover:translate-x-1" /></p>
                </div>
              </Link>
            );
          })}
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <Link key={c.id} to={`/catalog?cat=${c.id}`} className="rounded-full bg-stone-100 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-700 shadow-soft transition hover:bg-stone-900 hover:text-stone-50">{c.label}</Link>
          ))}
        </div>
      </section>

      {/* FEATURED */}
      <section className="shell pt-24">
        <SectionHead eyebrow="Elena’s selection" title="Highest AI matches this week" action={<Link to="/catalog" className="btn-outline">Open the catalog</Link>} />
        <div className="grid grid-cols-4 gap-6">{top.map((p) => <ProductCard key={p.id} product={p} compact />)}</div>
      </section>

      {/* AI STYLIST */}
      <section className="shell pt-24">
        <div className="grid grid-cols-[1fr_1.1fr] items-center gap-16 overflow-hidden rounded-2xl bg-stone-900 p-14 text-stone-50">
          <div>
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-stone-400"><Sparkles className="size-4" /> Elena • AI luxury stylist</p>
            <h2 className="display mt-4 text-5xl leading-[1.1] !text-stone-50">A stylist who knows your wardrobe</h2>
            <p className="mt-5 max-w-md text-sm leading-6 text-stone-300">Describe an occasion, a fabric or a silhouette. Elena composes looks from the capsule, calibrated to your measurements and your existing pieces.</p>
            <div className="mt-8 flex flex-wrap gap-2">
              {PROMPTS.map((q) => (
                <button key={q} type="button" onClick={() => navigate(`/stylist?q=${encodeURIComponent(q)}`)} className="rounded-full border border-stone-600 px-4 py-2 text-xs font-medium text-stone-200 transition hover:border-stone-50 hover:bg-stone-50 hover:text-stone-900">“{q}”</button>
              ))}
            </div>
            <Link to="/stylist" className="btn-light mt-9">Start a consultation <ArrowRight className="size-4" /></Link>
          </div>
          <div className="space-y-4" aria-hidden="true">
            <div className="ml-auto max-w-sm rounded-2xl rounded-tr-sm bg-stone-700/60 p-4 text-sm leading-6">I’m attending the Palais Garnier Gala in late November. I need an architectural silhouette in midnight wool.</div>
            <div className="max-w-md rounded-2xl rounded-tl-sm bg-stone-50 p-4 text-sm leading-6 text-stone-900">
              For the Garnier’s neoclassicism, lean into crisp structural volume rather than embellishment. I’ve pulled two silhouettes from our Nocturne capsule.
              <div className="mt-3 grid grid-cols-2 gap-3">
                {['cape-back-column', 'asymmetric-faille-sheath'].map((id) => (
                  <div key={id} className="overflow-hidden rounded-lg"><div className="h-28"><ProductImage product={getProduct(id)} label={false} /></div></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* RUNWAY */}
      <section className="shell pt-24">
        <SectionHead eyebrow="Paris • Runway archive" title="From the runway" action={<Link to="/runway" className="btn-outline">See every look</Link>} />
        <div className="grid grid-cols-3 gap-6">
          {LOOKS.slice(0, 3).map((l) => {
            const p = getProduct(l.items[0]);
            return (
              <Link key={l.id} to="/runway" className="group card flex items-center gap-5 p-4 transition hover:shadow-float">
                <div className="h-28 w-24 shrink-0 overflow-hidden rounded-lg"><ProductImage product={p} label={false} /></div>
                <div><p className="eyebrow">{l.no} • {l.collection}</p><p className="display mt-1 text-xl">{l.title}</p><p className="mt-1 flex items-center gap-1 text-xs text-zinc-700">{l.items.length} pieces <ArrowRight className="size-3 transition group-hover:translate-x-1" /></p></div>
              </Link>
            );
          })}
        </div>
      </section>

      {/* PRIVILEGE */}
      <section className="shell pt-24">
        <div className="flex items-center justify-between gap-10 rounded-2xl bg-stone-200 px-14 py-12">
          <div className="max-w-2xl">
            <p className="eyebrow mb-3 flex items-center gap-2"><Crown className="size-4" /> Atelier Privilege</p>
            <h2 className="display text-4xl leading-tight">Up to 20% privilege rate, bespoke alterations and private salons.</h2>
            <p className="mt-3 text-sm leading-6 text-zinc-700">Every acquisition earns points towards four tiers of patronage.</p>
          </div>
          <Link to={user ? '/account' : '/login'} className="btn-primary !px-8 !py-4">{user ? 'View my privileges' : 'Join the Maison'}</Link>
        </div>
      </section>
    </div>
  );
}
