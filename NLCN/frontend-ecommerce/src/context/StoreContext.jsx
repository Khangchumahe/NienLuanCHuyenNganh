import { createContext, useCallback, useContext, useEffect, useMemo, useReducer, useState } from 'react';
import { getProduct } from '../data/products';
import { DEMO_EMAIL, DEMO_USER, newUser, tierFor } from '../data/user';
import { priceOrder } from '../lib/pricing';

const STORAGE_KEY = 'atelier-studio:v1';

const initialState = {
  cart: [],        // [{ key, id, size, color, qty }]
  wishlist: [],    // [productId]
  user: null,      // null = khách
  orders: [],      // đơn đã đặt trong phiên demo
  promo: null,
  delivery: 'courier',
};

function load() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? { ...initialState, ...JSON.parse(raw) } : initialState;
  } catch {
    return initialState;
  }
}

const lineKey = (id, size, color) => `${id}|${size ?? '-'}|${color ?? '-'}`;
const today = () => new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });

function reducer(state, a) {
  switch (a.type) {
    case 'CART_ADD': {
      const key = lineKey(a.id, a.size, a.color);
      const existing = state.cart.find((l) => l.key === key);
      const cart = existing
        ? state.cart.map((l) => (l.key === key ? { ...l, qty: Math.min(9, l.qty + a.qty) } : l))
        : [...state.cart, { key, id: a.id, size: a.size, color: a.color, qty: a.qty }];
      return { ...state, cart };
    }
    case 'CART_QTY':
      return { ...state, cart: state.cart.map((l) => (l.key === a.key ? { ...l, qty: Math.max(1, Math.min(9, a.qty)) } : l)) };
    case 'CART_REMOVE':
      return { ...state, cart: state.cart.filter((l) => l.key !== a.key) };
    case 'CART_CLEAR':
      return { ...state, cart: [], promo: null };
    case 'PROMO':
      return { ...state, promo: a.code };
    case 'DELIVERY':
      return { ...state, delivery: a.id };
    case 'WISH':
      return { ...state, wishlist: state.wishlist.includes(a.id) ? state.wishlist.filter((x) => x !== a.id) : [...state.wishlist, a.id] };
    case 'LOGIN':
      return { ...state, user: a.user };
    case 'LOGOUT':
      return { ...state, user: null };
    case 'USER_PATCH':
      return state.user ? { ...state, user: { ...state.user, ...a.patch } } : state;
    case 'REDEEM': {
      const u = state.user;
      if (!u || u.points < a.reward.cost) return state;
      return {
        ...state,
        user: {
          ...u,
          points: u.points - a.reward.cost,
          redeemed: [...u.redeemed, a.reward.id],
          ledger: [{ id: `l${Date.now()}`, date: today(), label: `Redeemed — ${a.reward.name}`, pts: -a.reward.cost }, ...u.ledger],
        },
      };
    }
    case 'ORDER': {
      const u = state.user;
      const user = u
        ? {
            ...u,
            points: u.points + a.order.earned,
            ledger: [{ id: `l${Date.now()}`, date: today(), label: `Acquisition ${a.order.id}`, pts: a.order.earned }, ...u.ledger],
          }
        : u;
      return { ...state, orders: [a.order, ...state.orders], cart: [], promo: null, user };
    }
    default:
      return state;
  }
}

const StoreContext = createContext(null);

export function StoreProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, undefined, load);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch {
      /* private mode / quota → bỏ qua, ứng dụng vẫn chạy trong bộ nhớ */
    }
  }, [state]);

  const toast = useCallback((message) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((t) => [...t.slice(-2), { id, message }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 3200);
  }, []);

  const user = state.user;
  const tier = user ? tierFor(user.points) : null;

  const pricing = useMemo(
    () => priceOrder(state.cart, { rate: tier?.rate ?? 0, tier: tier?.id ?? 0, promo: state.promo, deliveryId: state.delivery }),
    [state.cart, state.promo, state.delivery, tier],
  );

  const actions = useMemo(
    () => ({
      addToCart: (id, { size = null, color = null, qty = 1 } = {}) => {
        dispatch({ type: 'CART_ADD', id, size, color, qty });
        const p = getProduct(id);
        toast(`${p?.name ?? 'Piece'} added to your bag`);
      },
      setQty: (key, qty) => dispatch({ type: 'CART_QTY', key, qty }),
      removeFromCart: (key) => dispatch({ type: 'CART_REMOVE', key }),
      clearCart: () => dispatch({ type: 'CART_CLEAR' }),
      setPromo: (code) => dispatch({ type: 'PROMO', code }),
      setDelivery: (id) => dispatch({ type: 'DELIVERY', id }),
      toggleWish: (id) => {
        const had = state.wishlist.includes(id);
        dispatch({ type: 'WISH', id });
        toast(had ? 'Removed from your saved pieces' : 'Saved to your private selection');
      },
      /** Đăng nhập demo: email demo → hồ sơ đầy đủ; email khác → hồ sơ mới */
      login: ({ email, name }) => {
        const isDemo = email.trim().toLowerCase() === DEMO_EMAIL;
        dispatch({ type: 'LOGIN', user: isDemo ? DEMO_USER : newUser({ name, email: email.trim() }) });
      },
      logout: () => {
        dispatch({ type: 'LOGOUT' });
        toast('You have been signed out');
      },
      updateUser: (patch) => dispatch({ type: 'USER_PATCH', patch }),
      redeem: (reward) => {
        if (!user || user.points < reward.cost) {
          toast('Not enough points for this reward yet');
          return false;
        }
        dispatch({ type: 'REDEEM', reward });
        toast(`${reward.name} added to your vault`);
        return true;
      },
      placeOrder: ({ paymentId, address }) => {
        const id = `ATL-${Math.floor(100000 + Math.random() * 899999)}-PARIS`;
        const order = {
          id,
          placedAt: new Date().toISOString(),
          lines: state.cart,
          rate: tier?.rate ?? 0,
          tier: tier?.id ?? 0,
          promo: state.promo,
          deliveryId: state.delivery,
          paymentId,
          address,
          total: pricing.total,
          earned: Math.round(pricing.total - pricing.vat),
          clientName: user?.name ?? 'Guest',
        };
        dispatch({ type: 'ORDER', order });
        return order;
      },
    }),
    [state.cart, state.wishlist, state.promo, state.delivery, tier, pricing.total, pricing.vat, user, toast],
  );

  const value = useMemo(
    () => ({ ...state, tier, pricing, cartCount: pricing.count, toasts, toast, ...actions }),
    [state, tier, pricing, toasts, toast, actions],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error('useStore phải được dùng bên trong <StoreProvider>');
  return ctx;
}
