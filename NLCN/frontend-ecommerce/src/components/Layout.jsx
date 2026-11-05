import { useEffect, useState } from 'react';
import { Sparkles } from 'lucide-react';
import { Link, useRoute } from '../lib/router';
import Header from './Header';
import Footer from './Footer';
import SearchModal from './SearchModal';
import InfoModal from './InfoModal';
import Toasts from './Toasts';

/** Khung chung cho mọi trang: Header + nội dung + Footer + nút AI Stylist nổi */
export default function Layout({ children, bare = false }) {
  const { path } = useRoute();
  const [searchOpen, setSearchOpen] = useState(false);
  const [info, setInfo] = useState(null);

  useEffect(() => {
    const onKey = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setSearchOpen((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const showFab = !path.startsWith('/stylist');

  // Màn hình đăng nhập: toàn khung, không header/footer
  if (bare) {
    return (
      <>
        {children}
        <Toasts />
      </>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header onSearch={() => setSearchOpen(true)} />
      <main className="flex-1 animate-fade-in" key={path}>{children}</main>
      <Footer onInfo={setInfo} />

      {showFab && (
        <Link
          to="/stylist"
          className="no-print fixed bottom-6 right-6 z-30 flex items-center gap-3 rounded-full bg-white/85 px-5 py-3 shadow-float backdrop-blur-xl transition hover:-translate-y-0.5 hover:bg-white"
        >
          <span className="relative flex size-2.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-stone-600 opacity-75" />
            <span className="relative inline-flex size-2.5 rounded-full bg-stone-600" />
          </span>
          <span className="eyebrow-ink">AI Stylist Concierge</span>
          <Sparkles className="size-4 text-stone-600" strokeWidth={1.6} />
        </Link>
      )}

      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
      <InfoModal id={info} onClose={() => setInfo(null)} />
      <Toasts />
    </div>
  );
}
