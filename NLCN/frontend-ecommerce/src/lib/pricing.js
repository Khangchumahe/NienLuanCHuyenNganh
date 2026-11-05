import { getProduct } from '../data/products';

export const VAT_RATE = 0.08;

export const PROMOS = {
  ATELIER10: { rate: 0.1, label: 'ATELIER10 • 10% invitation credit' },
};

export const DELIVERY = [
  { id: 'courier', label: 'White-Glove Evening Courier', note: 'Paris intra-muros • Today 19:30 – 21:00', fee: 0 },
  { id: 'express', label: 'Express Global Courier', note: '2–3 business days • fully insured', fee: 45, freeFromTier: 2 },
  { id: 'salon', label: 'Collect at Salon Cambon', note: '8 Rue Cambon • private fitting included', fee: 0 },
];

export const PAYMENTS = [
  { id: 'apple', label: 'Apple Pay', note: 'Ending in 8841' },
  { id: 'card', label: 'Atelier Visa Infinite', note: 'Ending in 0412' },
  { id: 'transfer', label: 'Private Bank Transfer', note: 'Invoice issued by the salon' },
];

const round2 = (n) => Math.round(n * 100) / 100;

export function money(n, { cents = false } = {}) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: cents ? 2 : 0,
    maximumFractionDigits: cents ? 2 : 0,
  }).format(n);
}

/** Gắn thông tin sản phẩm + thành tiền cho từng dòng giỏ hàng */
export function detail(lines) {
  return lines
    .map((l) => {
      const product = getProduct(l.id);
      return product ? { ...l, product, lineTotal: product.price * l.qty } : null;
    })
    .filter(Boolean);
}

/** Một hàm duy nhất tính toàn bộ tiền → Cart và Order luôn khớp nhau */
export function priceOrder(lines, { rate = 0, tier = 0, promo = null, deliveryId = 'courier' } = {}) {
  const items = detail(lines);
  const subtotal = items.reduce((s, i) => s + i.lineTotal, 0);
  const privilege = round2(subtotal * rate);
  const promoRate = promo && PROMOS[promo] ? PROMOS[promo].rate : 0;
  const promoOff = round2((subtotal - privilege) * promoRate);
  const d = DELIVERY.find((x) => x.id === deliveryId) ?? DELIVERY[0];
  const delivery = d.freeFromTier && tier >= d.freeFromTier ? 0 : d.fee;
  const taxable = subtotal - privilege - promoOff;
  const vat = round2(taxable * VAT_RATE);
  const total = round2(taxable + vat + delivery);
  return { items, count: items.reduce((s, i) => s + i.qty, 0), subtotal, privilege, promoOff, delivery, vat, total };
}
