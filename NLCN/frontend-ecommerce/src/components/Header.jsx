import { useEffect, useRef, useState } from 'react';
import { ChevronDown, Heart, LogOut, Search, ShoppingBag, User, UserRound, Package, Crown } from 'lucide-react';
import { Link, navigate, useRoute } from '../lib/router';
import { useStore } from '../context/StoreContext';

const NAV = [
  { label: 'Collections', to: '/', match: (p) => p === '/' },
  { label: 'Catalog', to: '/catalog', match: (p) => p.startsWith('/catalog') || p.startsWith('/product') },
  { label: 'Runway', to: '/runway', match: (p) => p.startsWith('/runway') },
  { label: 'AI Stylist', to: '/stylist', match: (p) => p.startsWith('/stylist') },
];

export default function Header({ onSearch }) {
  const { path } = useRoute();
  const { cartCount, wishlist, user, tier, logout } = useStore();
  const [menu, setMenu] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => ref.current && !ref.current.contains(e.target) && setMenu(false);
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);
  useEffect(() => setMenu(false), [path]);

  const linkCls = (active) =>
    `rounded-sm px-3 py-2 text-xs font-semibold uppercase tracking-wider transition ${active ? 'bg-stone-900 text-stone-50' : 'text-zinc-700 hover:bg-stone-200/70 hover:text-stone-900'}`;

  return (
    <header className="no-print sticky top-0 z-40 bg-stone-50/85 shadow-[0px_1px_8px_0px_rgba(0,0,0,0.04)] backdrop-blur-xl">
      <div className="bg-stone-200 py-1">
        <p className="eyebrow text-center">Complimentary private atelier delivery &amp; carbon-neutral global logistics</p>
      </div>

      <div className="shell flex h-20 items-center justify-between gap-6">
        <Link to="/" className="display text-xl font-medium uppercase leading-6 tracking-wide" aria-label="Atelier Studio — home">
          ATELIER<br />STUDIO
        </Link>

        <nav className="flex items-center gap-2 xl:gap-5" aria-label="Main">
          {NAV.map((n) => (
            <Link key={n.to} to={n.to} className={linkCls(n.match(path))} aria-current={n.match(path) ? 'page' : undefined}>
              {n.label}
            </Link>
          ))}
          <Link to="/cart" className={linkCls(path.startsWith('/cart'))}>
            Bag ({cartCount})
          </Link>
        </nav>

        <div className="flex items-center gap-2 xl:gap-4">
          <button
            type="button"
            onClick={onSearch}
            className="relative hidden h-10 w-56 items-center rounded-full bg-stone-100 pl-10 pr-12 text-left text-xs text-zinc-700/70 transition hover:bg-stone-200/80 lg:flex xl:w-64"
          >
            <Search className="absolute left-3.5 size-3.5 text-zinc-700" />
            Search editorial archive...
            <kbd className="absolute right-2 rounded-sm bg-white px-1.5 py-0.5 text-[10px] text-zinc-700/70 outline outline-1 -outline-offset-1 outline-stone-300/40">⌘K</kbd>
          </button>
          <button type="button" onClick={onSearch} className="rounded-full p-2 text-zinc-700 hover:bg-stone-200/70 lg:hidden" aria-label="Search">
            <Search className="size-5" strokeWidth={1.6} />
          </button>

          <Link to="/wishlist" className="relative rounded-full p-2 text-zinc-700 transition hover:bg-stone-200/70" aria-label="Saved pieces">
            <Heart className="size-5" strokeWidth={1.6} />
            {wishlist.length > 0 && <Badge n={wishlist.length} />}
          </Link>

          <Link to="/cart" className="relative rounded-full p-2 text-zinc-700 transition hover:bg-stone-200/70" aria-label={`Shopping bag, ${cartCount} items`}>
            <ShoppingBag className="size-5" strokeWidth={1.6} />
            {cartCount > 0 && <Badge n={cartCount} />}
          </Link>

          <div ref={ref} className="relative">
            {user ? (
              <button
                type="button"
                onClick={() => setMenu((v) => !v)}
                aria-expanded={menu}
                className="flex items-center gap-2 rounded-full bg-stone-900 py-1 pl-1 pr-3 text-stone-50 transition hover:bg-black"
              >
                <span className="flex size-7 items-center justify-center rounded-full bg-stone-50 text-[11px] font-semibold text-stone-900">
                  {user.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase()}
                </span>
                <ChevronDown className="size-3.5" />
              </button>
            ) : (
              <Link to="/login" className="flex items-center gap-2 rounded-full p-2 text-zinc-700 transition hover:bg-stone-200/70" aria-label="Sign in">
                <User className="size-5" strokeWidth={1.6} />
              </Link>
            )}

            {menu && user && (
              <div className="absolute right-0 top-12 z-50 w-72 animate-fade-in overflow-hidden rounded-xl bg-white shadow-float ring-1 ring-black/5">
                <div className="border-b border-stone-100 p-4">
                  <p className="text-sm font-medium">{user.name}</p>
                  <p className="mt-0.5 flex items-center gap-1.5 text-xs text-zinc-700"><Crown className="size-3" /> {tier?.no} • {tier?.name}</p>
                </div>
                <MenuItem to="/account" icon={Crown}>Privilege &amp; points</MenuItem>
                <MenuItem to="/profile" icon={UserRound}>Client profile</MenuItem>
                <MenuItem to="/order" icon={Package}>Order tracking</MenuItem>
                <button
                  type="button"
                  onClick={() => { logout(); navigate('/'); }}
                  className="flex w-full items-center gap-3 border-t border-stone-100 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-zinc-700 hover:bg-stone-50"
                >
                  <LogOut className="size-4" /> Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

function Badge({ n }) {
  return <span className="absolute -right-0.5 -top-0.5 flex size-4 items-center justify-center rounded-full bg-black text-[9px] text-white">{n}</span>;
}

function MenuItem({ to, icon: Icon, children }) {
  return (
    <Link to={to} className="flex items-center gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wider text-zinc-700 transition hover:bg-stone-50 hover:text-stone-900">
      <Icon className="size-4" strokeWidth={1.6} /> {children}
    </Link>
  );
}
