import { ShoppingBag } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { LOOKS, getProduct } from '../data/products';
import { money } from '../lib/pricing';
import ProductImage from '../components/ProductImage';
import { Breadcrumb } from '../components/ui';

export default function RunwayPage() {
  const { addToCart, toast } = useStore();

  /** Thêm cả bộ: mỗi món lấy màu đầu tiên và size phổ biến (FR 38 / EU 38) nếu có */
  const addLook = (look) => {
    look.items.forEach((id) => {
      const p = getProduct(id);
      addToCart(id, { color: p.colors[0], size: p.sizes.includes(38) ? 38 : p.sizes[0] ?? null });
    });
    toast(`${look.no} — ${look.items.length} pieces added to your bag`);
  };

  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Runway' }]} />
      <header className="mb-10 mt-4 max-w-3xl">
        <p className="eyebrow mb-3">Paris • Autumn-Winter 2025</p>
        <h1 className="display text-6xl leading-[1.1]">The Runway Archive</h1>
        <p className="mt-4 text-lg leading-7 text-zinc-700">Every look from the Paris presentation, composed piece by piece. Add the full silhouette to your bag, or take only what speaks to you.</p>
      </header>

      <div className="grid grid-cols-2 gap-8 xl:grid-cols-3">
        {LOOKS.map((look) => {
          const products = look.items.map(getProduct);
          const total = products.reduce((s, p) => s + p.price, 0);
          return (
            <article key={look.id} className="card overflow-hidden">
              <div className="grid h-72 grid-cols-3 gap-px bg-stone-200">
                {products.map((p, i) => (
                  <Link key={p.id} to={`/product/${p.id}`} className={`block overflow-hidden ${products.length === 2 && i === 0 ? 'col-span-2' : ''}`} aria-label={p.name}>
                    <ProductImage product={p} label={false} />
                  </Link>
                ))}
              </div>
              <div className="p-6">
                <p className="eyebrow">{look.no} • {look.collection}</p>
                <h2 className="display mt-1 text-2xl">{look.title}</h2>
                <p className="mt-2 text-sm leading-6 text-zinc-700">{look.note}</p>
                <ul className="mt-4 space-y-1.5 border-t border-stone-100 pt-4">
                  {products.map((p) => (
                    <li key={p.id} className="flex items-center justify-between gap-4 text-xs">
                      <Link to={`/product/${p.id}`} className="truncate text-stone-900 hover:underline">{p.name}</Link>
                      <span className="shrink-0 text-zinc-700">{money(p.price)}</span>
                    </li>
                  ))}
                </ul>
                <button type="button" onClick={() => addLook(look)} className="btn-primary mt-5 w-full"><ShoppingBag className="size-4" /> Add the look — {money(total)}</button>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
