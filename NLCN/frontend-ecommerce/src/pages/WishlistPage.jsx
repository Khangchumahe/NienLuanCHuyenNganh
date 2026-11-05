import { Heart } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { getProduct } from '../data/products';
import ProductCard from '../components/ProductCard';
import { Breadcrumb, EmptyState } from '../components/ui';

export default function WishlistPage() {
  const { wishlist } = useStore();
  const items = wishlist.map(getProduct).filter(Boolean);

  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Saved pieces' }]} />
      <h1 className="display mb-8 mt-4 text-5xl">Private Selection <span className="text-2xl text-zinc-700">({items.length})</span></h1>
      {items.length ? (
        <div className="grid grid-cols-3 gap-6 xl:grid-cols-4">{items.map((p) => <ProductCard key={p.id} product={p} compact />)}</div>
      ) : (
        <EmptyState icon={Heart} title="Nothing saved yet" text="Tap the heart on any piece to keep it here for later.">
          <Link to="/catalog" className="btn-primary">Explore the catalog</Link>
        </EmptyState>
      )}
    </div>
  );
}
