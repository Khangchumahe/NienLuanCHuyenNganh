import { useState } from 'react';
import { Crown, Minus, Plus, ShoppingBag, Tag, Trash2, Lock, Heart } from 'lucide-react';
import { Link, navigate } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { COLORS, sizeLabel } from '../data/products';
import { DELIVERY, PAYMENTS, PROMOS, VAT_RATE, money } from '../lib/pricing';
import ProductImage from '../components/ProductImage';
import { Breadcrumb, EmptyState } from '../components/ui';

export default function CartPage() {
  const { cart, pricing, user, tier, promo, setPromo, delivery, setDelivery, setQty, removeFromCart, toggleWish, wishlist, placeOrder, toast } = useStore();
  const [code, setCode] = useState('');
  const [codeError, setCodeError] = useState('');
  const [payment, setPayment] = useState('apple');
  const [addressId, setAddressId] = useState(user?.addresses.find((a) => a.isDefault)?.id ?? user?.addresses[0]?.id ?? 'new');
  const [newAddr, setNewAddr] = useState({ line: '', city: '' });
  const [error, setError] = useState('');

  if (cart.length === 0) {
    return (
      <div className="shell pt-10">
        <EmptyState icon={ShoppingBag} title="Your bag is empty" text="Discover the Autumn-Winter capsule, or let Elena compose a look for you.">
          <Link to="/catalog" className="btn-primary">Explore the catalog</Link>
          <Link to="/stylist" className="btn-outline">Ask Elena</Link>
        </EmptyState>
      </div>
    );
  }

  const applyCode = (e) => {
    e.preventDefault();
    const c = code.trim().toUpperCase();
    if (!c) return;
    if (!PROMOS[c]) return setCodeError('This invitation code is not recognised.');
    setCodeError('');
    setPromo(c);
    setCode('');
    toast(`${PROMOS[c].label} applied`);
  };

  const needsAddress = delivery !== 'salon';
  const submit = () => {
    if (!user) {
      toast('Please sign in to complete your acquisition');
      return navigate('/login?next=%2Fcart');
    }
    let address = null;
    if (needsAddress) {
      if (addressId === 'new' || !user.addresses.length) {
        if (!newAddr.line.trim() || !newAddr.city.trim()) return setError('Please enter a delivery sanctuary (street and city).');
        address = { label: 'Delivery', ...newAddr };
      } else {
        address = user.addresses.find((a) => a.id === addressId);
      }
    } else {
      address = { label: 'Salon Cambon', line: '8 Rue Cambon', city: '75001 Paris, France' };
    }
    setError('');
    const order = placeOrder({ paymentId: payment, address });
    navigate(`/order/${order.id}`);
  };

  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Catalog', to: '/catalog' }, { label: 'Shopping bag' }]} />
      <div className="mb-8 mt-4 flex items-end justify-between">
        <h1 className="display text-5xl">Your Bag <span className="text-2xl text-zinc-700">({pricing.count})</span></h1>
        <Link to="/catalog" className="text-xs font-semibold uppercase tracking-wider text-zinc-700 underline underline-offset-4 hover:text-stone-900">Continue browsing</Link>
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)_24rem] items-start gap-10 xl:grid-cols-[minmax(0,1fr)_26rem]">
        <div className="space-y-6">
          {/* 1. items */}
          <section className="card divide-y divide-stone-100">
            {pricing.items.map((it) => (
              <article key={it.key} className="flex gap-5 p-5">
                <Link to={`/product/${it.id}`} className="h-36 w-28 shrink-0 overflow-hidden rounded-lg" aria-label={it.product.name}>
                  <ProductImage product={it.product} color={it.color} label={false} />
                </Link>
                <div className="flex flex-1 flex-col">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="eyebrow">{it.product.kind} • {it.product.material}</p>
                      <Link to={`/product/${it.id}`} className="mt-1 block text-lg leading-6 hover:underline">{it.product.name}</Link>
                      <p className="mt-2 text-xs text-zinc-700">
                        <span className="mr-1 inline-block size-2.5 translate-y-px rounded-full ring-1 ring-black/10" style={{ background: COLORS[it.color]?.hex }} />
                        {COLORS[it.color]?.label}{it.size != null && <> • {sizeLabel(it.product, it.size)}</>}
                      </p>
                    </div>
                    <p className="display text-xl">{money(it.lineTotal)}</p>
                  </div>
                  <div className="mt-auto flex items-center justify-between pt-4">
                    <div className="flex items-center rounded-lg bg-stone-100">
                      <button type="button" onClick={() => setQty(it.key, it.qty - 1)} disabled={it.qty <= 1} className="flex size-9 items-center justify-center disabled:opacity-30" aria-label="Decrease quantity"><Minus className="size-3.5" /></button>
                      <span className="w-7 text-center text-sm font-semibold">{it.qty}</span>
                      <button type="button" onClick={() => setQty(it.key, it.qty + 1)} disabled={it.qty >= 9} className="flex size-9 items-center justify-center disabled:opacity-30" aria-label="Increase quantity"><Plus className="size-3.5" /></button>
                    </div>
                    <div className="flex items-center gap-5 text-xs font-semibold uppercase tracking-wider text-zinc-700">
                      <button type="button" onClick={() => toggleWish(it.id)} className="flex items-center gap-1.5 hover:text-stone-900"><Heart className={`size-3.5 ${wishlist.includes(it.id) ? 'fill-stone-900' : ''}`} /> Save</button>
                      <button type="button" onClick={() => { removeFromCart(it.key); toast('Piece removed from your bag'); }} className="flex items-center gap-1.5 hover:text-red-800"><Trash2 className="size-3.5" /> Remove</button>
                    </div>
                  </div>
                </div>
              </article>
            ))}
          </section>

          {/* 2. delivery */}
          <section className="card p-6">
            <h2 className="eyebrow-ink mb-4">Delivery</h2>
            <div className="space-y-2" role="radiogroup" aria-label="Delivery method">
              {DELIVERY.map((d) => {
                const fee = d.freeFromTier && (tier?.id ?? 0) >= d.freeFromTier ? 0 : d.fee;
                return (
                  <Option key={d.id} on={delivery === d.id} onClick={() => setDelivery(d.id)} title={d.label} note={d.note} right={fee ? money(fee) : 'Complimentary'} />
                );
              })}
            </div>

            {needsAddress && (
              <div className="mt-5 border-t border-stone-100 pt-5">
                <h3 className="eyebrow mb-3">Delivery sanctuary</h3>
                {user?.addresses.length ? (
                  <div className="space-y-2">
                    {user.addresses.map((a) => (
                      <Option key={a.id} on={addressId === a.id} onClick={() => setAddressId(a.id)} title={a.label} note={`${a.line}, ${a.city}`} />
                    ))}
                    <Option on={addressId === 'new'} onClick={() => setAddressId('new')} title="Another address" note="Enter a new sanctuary" />
                  </div>
                ) : null}
                {(!user?.addresses.length || addressId === 'new') && (
                  <div className="mt-3 grid grid-cols-2 gap-3">
                    <input className="field" placeholder="Street & suite" aria-label="Street" value={newAddr.line} onChange={(e) => setNewAddr({ ...newAddr, line: e.target.value })} />
                    <input className="field" placeholder="Postcode, city, country" aria-label="City" value={newAddr.city} onChange={(e) => setNewAddr({ ...newAddr, city: e.target.value })} />
                  </div>
                )}
              </div>
            )}
          </section>

          {/* 3. payment */}
          <section className="card p-6">
            <h2 className="eyebrow-ink mb-4">Payment</h2>
            <div className="space-y-2" role="radiogroup" aria-label="Payment method">
              {PAYMENTS.map((p) => <Option key={p.id} on={payment === p.id} onClick={() => setPayment(p.id)} title={p.label} note={p.note} />)}
            </div>
          </section>
        </div>

        {/* summary */}
        <aside className="card sticky top-32 p-6" aria-label="Order summary">
          <h2 className="display text-2xl">Acquisition summary</h2>

          {user && tier ? (
            <p className="mt-4 flex items-center gap-2 rounded-lg bg-stone-100 px-3 py-2.5 text-xs text-zinc-700">
              <Crown className="size-4 shrink-0 text-stone-600" /> {tier.name} privilege rate of {tier.rate * 100}% applied automatically.
            </p>
          ) : (
            <p className="mt-4 rounded-lg bg-stone-100 px-3 py-2.5 text-xs leading-5 text-zinc-700">
              <Link to="/login?next=%2Fcart" className="font-semibold text-stone-900 underline underline-offset-2">Sign in</Link> to apply your privilege rate (up to 20%) and earn points.
            </p>
          )}

          <form onSubmit={applyCode} className="mt-5">
            {promo ? (
              <p className="flex items-center justify-between rounded-lg bg-stone-900 px-3 py-2.5 text-xs text-stone-50">
                <span className="flex items-center gap-2"><Tag className="size-3.5" /> {PROMOS[promo].label}</span>
                <button type="button" onClick={() => setPromo(null)} className="underline underline-offset-2">Remove</button>
              </p>
            ) : (
              <div className="relative">
                <input value={code} onChange={(e) => { setCode(e.target.value); setCodeError(''); }} placeholder="Invitation code (try ATELIER10)" aria-label="Invitation code" className="field pr-20" />
                <button type="submit" className="absolute right-1.5 top-1.5 rounded-md bg-stone-900 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-stone-50 hover:bg-black">Apply</button>
              </div>
            )}
            {codeError && <p className="mt-2 text-xs text-red-800" role="alert">{codeError}</p>}
          </form>

          <dl className="mt-6 space-y-3 text-sm">
            <Row label={`Garments subtotal (${pricing.count} item${pricing.count > 1 ? 's' : ''})`} value={money(pricing.subtotal, { cents: true })} />
            {pricing.privilege > 0 && <Row label={`Privilege rate (${tier.rate * 100}%)`} value={`− ${money(pricing.privilege, { cents: true })}`} />}
            {pricing.promoOff > 0 && <Row label="Invitation credit" value={`− ${money(pricing.promoOff, { cents: true })}`} />}
            <Row label="Delivery" value={pricing.delivery ? money(pricing.delivery, { cents: true }) : 'Complimentary'} />
            <Row label={`Taxe sur la valeur ajoutée (TVA ${VAT_RATE * 100}%)`} value={money(pricing.vat, { cents: true })} />
          </dl>
          <div className="mt-5 flex items-baseline justify-between border-t border-stone-200 pt-5">
            <span className="eyebrow-ink">Total investment</span>
            <span className="display text-3xl">{money(pricing.total, { cents: true })}</span>
          </div>

          {error && <p className="mt-4 text-xs font-medium text-red-800" role="alert">{error}</p>}
          <button type="button" onClick={submit} className="btn-primary mt-6 w-full !py-4"><Lock className="size-4" /> {user ? 'Place acquisition' : 'Sign in to acquire'}</button>
          <p className="mt-3 text-center text-[11px] leading-4 text-zinc-700">Secured by 256-bit SSL. You will earn {Math.round(pricing.total - pricing.vat).toLocaleString()} points.</p>
        </aside>
      </div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <dt className="text-zinc-700">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

function Option({ on, onClick, title, note, right }) {
  return (
    <button type="button" role="radio" aria-checked={on} onClick={onClick} className={`flex w-full items-center gap-4 rounded-lg px-4 py-3.5 text-left transition ${on ? 'bg-stone-900 text-stone-50' : 'bg-stone-100 hover:bg-stone-200/70'}`}>
      <span className={`flex size-4 shrink-0 items-center justify-center rounded-full border ${on ? 'border-stone-50' : 'border-stone-400'}`}>{on && <span className="size-2 rounded-full bg-stone-50" />}</span>
      <span className="flex-1">
        <span className="block text-sm font-medium">{title}</span>
        {note && <span className={`block text-xs ${on ? 'text-stone-300' : 'text-zinc-700'}`}>{note}</span>}
      </span>
      {right && <span className="text-xs font-semibold uppercase tracking-wider">{right}</span>}
    </button>
  );
}
