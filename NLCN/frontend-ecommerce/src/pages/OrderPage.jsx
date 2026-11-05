import { Check, Truck } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { VAT_RATE, money, priceOrder } from '../lib/pricing';
import ProductImage from '../components/ProductImage';
import { Breadcrumb } from '../components/ui';

// Đơn mẫu để xem giao diện khi chưa đặt đơn nào
const DEMO = {
  id: 'ATL-849204-PARIS',
  lines: [
    { key: 'a', id: 'double-breasted-blazer', size: 38, color: 'camel', qty: 1 },
    { key: 'b', id: 'pleated-silk-pant', size: 38, color: 'ecru', qty: 1 },
  ],
  rate: 0.15, tier: 3, promo: null, deliveryId: 'courier',
};

const STEPS = [
  ['01 / Registration', 'Certified & monogrammed'],
  ['02 / Salon quality', 'Inspected in Paris atelier'],
  ['03 / Active en route', 'Private evening courier'],
  ['04 / Reception', 'In-suite handover & try-on'],
];

export default function OrderPage({ params }) {
  const { orders } = useStore();
  const order = orders.find((o) => o.id === params.id) ?? (params.id ? null : orders[0]) ?? DEMO;
  if (!order) return <div className="shell py-24 text-center"><p className="display text-4xl">Order not found</p><Link to="/catalog" className="btn-primary mt-8">Back to catalog</Link></div>;

  const p = priceOrder(order.lines, order);
  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Order tracking' }]} />
      <header className="mb-8 mt-4">
        <p className="eyebrow">Atelier acquisition certified • Receipt #{order.id}</p>
        <h1 className="display mt-2 text-5xl leading-tight">Merci. Your bespoke consignment is consecrated.</h1>
      </header>

      <section className="card mb-6 p-8">
        <p className="eyebrow mb-6 flex items-center gap-2"><Truck className="size-4" /> Stage III of IV active • Private white-glove transit</p>
        <ol className="grid grid-cols-4 gap-4">
          {STEPS.map(([t, d], i) => (
            <li key={t} className={`rounded-lg p-4 ${i < 3 ? 'bg-stone-900 text-stone-50' : 'bg-stone-100'}`}>
              <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">{i < 2 && <Check className="size-3.5" />}{t}</p>
              <p className="mt-2 text-sm">{d}</p>
            </li>
          ))}
        </ol>
      </section>

      <div className="grid grid-cols-[1fr_22rem] items-start gap-6">
        <section className="card divide-y divide-stone-100">
          {p.items.map((it) => (
            <article key={it.key} className="flex gap-5 p-5">
              <Link to={`/product/${it.id}`} className="h-28 w-24 shrink-0 overflow-hidden rounded-lg"><ProductImage product={it.product} color={it.color} label={false} /></Link>
              <div className="flex-1"><p className="text-lg">{it.product.name}</p><p className="mt-1 text-xs text-zinc-700">Qty {it.qty}</p></div>
              <p className="display text-xl">{money(it.lineTotal)}</p>
            </article>
          ))}
        </section>
        <aside className="card p-6">
          <h2 className="eyebrow-ink mb-4">Acquisition ledger</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt>Subtotal</dt><dd>{money(p.subtotal, { cents: true })}</dd></div>
            {p.privilege > 0 && <div className="flex justify-between"><dt>Privilege</dt><dd>− {money(p.privilege, { cents: true })}</dd></div>}
            <div className="flex justify-between"><dt>TVA {VAT_RATE * 100}%</dt><dd>{money(p.vat, { cents: true })}</dd></div>
            <div className="flex justify-between border-t border-stone-200 pt-3 text-base font-semibold"><dt>Total</dt><dd>{money(p.total, { cents: true })}</dd></div>
          </dl>
          <Link to="/stylist" className="btn-outline mt-6 w-full">Message salon</Link>
        </aside>
      </div>
    </div>
  );
}
