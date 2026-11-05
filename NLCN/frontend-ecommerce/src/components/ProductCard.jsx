import { Heart, Plus } from 'lucide-react';
import { Link } from '../lib/router';
import { money } from '../lib/pricing';
import { COLORS } from '../data/products';
import { useStore } from '../context/StoreContext';
import ProductImage from './ProductImage';

/** Thẻ sản phẩm dùng ở Catalog, Storefront, Wishlist, trang chi tiết */
export default function ProductCard({ product: p, showAi = true, compact = false }) {
  const { wishlist, toggleWish, addToCart } = useStore();
  const saved = wishlist.includes(p.id);
  const low = /only|1 pair/i.test(p.status);

  return (
    <article className="group card flex flex-col overflow-hidden transition duration-300 hover:-translate-y-0.5 hover:shadow-float">
      <div className={`relative bg-stone-200 ${compact ? 'aspect-[4/5]' : 'aspect-[3/4]'}`}>
        <Link to={`/product/${p.id}`} className="block h-full" aria-label={`View ${p.name}`}>
          <ProductImage product={p} />
        </Link>
        {showAi && (
          <span className="chip absolute left-3 top-3 bg-white/90 !text-stone-900 backdrop-blur-md">
            <span className="size-1.5 rounded-full bg-stone-600" />
            AI Match: {p.ai}%
          </span>
        )}
        <button
          type="button"
          onClick={() => toggleWish(p.id)}
          aria-pressed={saved}
          aria-label={saved ? 'Remove from saved' : 'Save piece'}
          className="absolute right-3 top-3 flex size-8 items-center justify-center rounded-full bg-white/80 shadow-soft backdrop-blur-md transition hover:bg-white"
        >
          <Heart className={`size-4 ${saved ? 'fill-stone-900 text-stone-900' : 'text-stone-900'}`} strokeWidth={1.6} />
        </button>
        <button
          type="button"
          onClick={() => addToCart(p.id, { size: p.sizes[Math.min(2, p.sizes.length - 1)] ?? null, color: p.colors[0] })}
          className="btn-primary absolute inset-x-3 bottom-3 translate-y-2 !py-2.5 opacity-0 transition duration-300 group-hover:translate-y-0 group-hover:opacity-100 focus-visible:translate-y-0 focus-visible:opacity-100"
        >
          <Plus className="size-3.5" /> Quick add to bag
        </button>
      </div>

      <div className="flex flex-1 flex-col gap-2 p-4">
        <div className="flex items-center justify-between gap-2">
          <span className="eyebrow truncate">{p.kind} • {p.material}</span>
          <span className="flex shrink-0 gap-1">
            {p.colors.map((c) => (
              <span key={c} title={COLORS[c].label} className="size-3 rounded-full shadow-soft ring-1 ring-black/5" style={{ background: COLORS[c].hex }} />
            ))}
          </span>
        </div>
        <Link to={`/product/${p.id}`} className="text-lg leading-6 text-stone-900 hover:underline decoration-stone-400 underline-offset-4">
          {p.name}
        </Link>
        {!compact && <p className="line-clamp-2 text-xs leading-5 tracking-tight text-zinc-700">{p.short}</p>}
        <div className="mt-auto flex items-baseline justify-between pt-2">
          <span className="display text-xl">{money(p.price)}</span>
          <span className={`text-xs font-semibold uppercase tracking-wider ${low ? 'text-red-800' : 'text-stone-600'}`}>{p.status}</span>
        </div>
      </div>
    </article>
  );
}
