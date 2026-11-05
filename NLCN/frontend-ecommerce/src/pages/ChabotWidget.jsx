import { useEffect, useRef, useState } from 'react';
import { Bookmark, Lock, MessageSquare, Plus, Send, Sparkles } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { getProduct } from '../data/products';
import { money } from '../lib/pricing';
import ProductImage from '../components/ProductImage';

const PROMPTS = ['Suggest an evening coat', 'Analyze fabric drape', 'Color match my shoes', 'Request bespoke hem fitting'];

const GREETING = { from: 'elena', text: 'Welcome. I am Elena, your confidential AI stylist. Tell me about an occasion, a fabric or a silhouette, and I will compose it for you.' };

const GALA = [
  { from: 'me', time: '15:42', text: 'I am attending the Palais Garnier Gala in late November. I need an architectural silhouette in midnight wool or washed silk that flatters broad shoulders and pairs effortlessly with minimalist gold cuff jewelry.' },
  {
    from: 'elena',
    text: 'Welcome, Mrs. Laurent. For the Garnier Gala’s vaulted neoclassicism, we recommend leaning into crisp structural volume rather than conventional embellishment. I have pulled two complementary runway silhouettes from our Fall Nocturne capsule, both with razor-sharp shoulder construction calibrated to balance posture while leaving collarbones open for severe metal cuffs.',
    metric: { value: '97.8%', label: 'Geometric drape concordance', sub: 'Calibrated against your 178cm height profile', tag: 'Optimal' },
    picks: ['cape-back-column', 'asymmetric-faille-sheath'],
    looks: ['LOOK 18 • NOCTURNE', 'LOOK 07 • ALABASTER'],
  },
];

const THREADS = {
  gala: { title: 'Paris Gala Ensemble', msgs: GALA },
  cashmere: { title: 'Winter Cashmere Selection', msgs: [{ from: 'me', time: '09:10', text: 'Which cashmere pieces suit a neutral wardrobe?' }, { from: 'elena', text: 'The roll neck and the fringe scarf in camel anchor a neutral capsule beautifully.', picks: ['sculpted-cashmere-turtleneck', 'cashmere-fringe-scarf'] }] },
  suiting: { title: 'Bespoke Suiting Inquiry', msgs: [{ from: 'me', time: 'Mon', text: 'I would like a double-breasted jacket made to measure.' }, { from: 'elena', text: 'Our oversized blazer is the starting point. A master tailor can recut it to your measurements in 6–8 weeks.', picks: ['double-breasted-blazer'] }] },
  silk: { title: 'Silk Evening Drape & Hem', msgs: [{ from: 'me', time: 'Sun', text: 'How should the silk pant be hemmed for heels?' }, { from: 'elena', text: 'Hem it to graze the floor with a 65mm heel — about 1cm above the ground at the back.', picks: ['pleated-silk-pant'] }] },
  aw25: { title: 'Autumn / Winter 2025', saved: true, msgs: [{ from: 'elena', text: 'Your saved Autumn / Winter dossier: a tonal capsule built around the cocoon coat.', picks: ['cocoon-wool-coat', 'sculpted-cashmere-turtleneck'] }] },
  opera: { title: 'Opera Nocturne Trunks', saved: true, msgs: [{ from: 'elena', text: 'Your saved Opera Nocturne selection, ready to be reserved at Rue Cambon.', picks: ['cape-back-column', 'brass-torc-collar'] }] },
};

/** Trả lời mẫu theo từ khoá. Khi có AI thật, chỉ cần thay hàm này bằng lời gọi API. */
function reply(text) {
  const t = text.toLowerCase();
  if (/coat|evening|gala/.test(t)) return { text: 'For an evening of crisp structural volume, I pulled two silhouettes from our Nocturne capsule.', picks: ['cape-back-column', 'cocoon-wool-coat'] };
  if (/shoe|boot|colou?r/.test(t)) return { text: 'Espresso and noir calfskin ground a fluid silhouette beautifully.', picks: ['sculpted-heel-boots', 'square-toe-ankle-boot'] };
  if (/drape|fabric/.test(t)) return { text: 'Mulberry silk crepe and double-faced wool give the best drape for your profile.', metric: { value: '97.8%', label: 'Geometric drape concordance', sub: 'Calibrated against your 178cm height profile', tag: 'Optimal' }, picks: ['pleated-silk-pant'] };
  if (/hem|fitting|tailor/.test(t)) return { text: 'I have requested a bespoke hem fitting at Rue Cambon. Your concierge will confirm within two hours.', picks: [] };
  return { text: 'Here are the pieces with the highest AI match for you right now.', picks: ['sculpted-cashmere-turtleneck', 'double-breasted-blazer'] };
}

export default function ChatbotWidget({ query }) {
  const { user } = useStore();
  const [active, setActive] = useState('gala');
  const [extra, setExtra] = useState({}); // tin nhắn mới theo từng cuộc trò chuyện
  const [fresh, setFresh] = useState(false); // đang ở "New consultation"
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const end = useRef(null);
  const sentQuery = useRef(false);

  const key = fresh ? 'new' : active;
  const base = fresh ? [GREETING] : THREADS[active].msgs;
  const msgs = [...base, ...(extra[key] ?? [])];

  const send = (text, k = key) => {
    if (!text.trim()) return;
    setExtra((e) => ({ ...e, [k]: [...(e[k] ?? []), { from: 'me', text, time: 'Now' }] }));
    setInput('');
    setTyping(true);
    setTimeout(() => {
      setExtra((e) => ({ ...e, [k]: [...(e[k] ?? []), { from: 'elena', ...reply(text) }] }));
      setTyping(false);
    }, 800);
  };

  // Vào từ Storefront với /stylist?q=... → mở cuộc trò chuyện mới và tự gửi câu hỏi
  useEffect(() => {
    if (query?.q && !sentQuery.current) {
      sentQuery.current = true;
      setFresh(true);
      send(query.q, 'new');
    }
  }, [query?.q]);

  useEffect(() => {
    end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [msgs.length, typing, key]);

  const open = (id) => { setFresh(false); setActive(id); };
  const initials = (user?.name ?? 'Guest').split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();
  const recent = Object.entries(THREADS).filter(([, t]) => !t.saved);
  const saved = Object.entries(THREADS).filter(([, t]) => t.saved);

  return (
    <div className="shell py-6">
      <div className="card grid h-[calc(100vh-9.5rem)] min-h-[34rem] grid-cols-[18rem_minmax(0,1fr)] overflow-hidden">
        {/* sidebar */}
        <aside className="flex flex-col border-r border-stone-100 bg-stone-50/70">
          <div className="p-4">
            <button type="button" onClick={() => { setFresh(true); setExtra((e) => ({ ...e, new: [] })); }} className="btn-primary w-full"><Plus className="size-4" /> New consultation</button>
          </div>
          <div className="flex-1 overflow-y-auto px-3 pb-4">
            <p className="eyebrow px-2 pb-2 pt-2">Recent consultations</p>
            {recent.map(([id, t]) => <Item key={id} on={!fresh && active === id} onClick={() => open(id)} icon={MessageSquare}>{t.title}</Item>)}
            <p className="eyebrow px-2 pb-2 pt-6">Saved dossiers</p>
            {saved.map(([id, t]) => <Item key={id} on={!fresh && active === id} onClick={() => open(id)} icon={Bookmark}>{t.title}</Item>)}
          </div>
          <div className="flex items-center gap-3 border-t border-stone-100 p-4">
            <Avatar>E</Avatar>
            <div className="min-w-0 flex-1"><p className="text-sm font-semibold">Elena AI</p><p className="eyebrow !text-[10px]">Neural stylist active</p></div>
          </div>
          <p className="flex items-center gap-1.5 px-4 pb-4 text-[11px] text-zinc-700"><Lock className="size-3" /> Preferences encrypted</p>
        </aside>

        {/* conversation */}
        <section className="flex min-h-0 flex-col">
          <header className="flex items-center justify-between border-b border-stone-100 px-8 py-4">
            <div>
              <p className="font-semibold">Elena Stylist Concierge</p>
              <p className="eyebrow !text-[10px]">Atelier Cambon • Session synchronized • Paris 15:42 CET</p>
            </div>
            <span className="chip"><span className="size-2 rounded-full bg-emerald-700" /> Online</span>
          </header>

          <div className="flex-1 space-y-7 overflow-y-auto bg-stone-50/40 px-8 py-7">
            {msgs.map((m, i) => (m.from === 'me' ? <Me key={i} m={m} initials={initials} /> : <Elena key={i} m={m} />))}
            {typing && <div className="flex items-center gap-3"><Avatar>E</Avatar><span className="flex gap-1 rounded-2xl bg-white px-4 py-3 shadow-soft">{[0, 1, 2].map((d) => <span key={d} className="size-1.5 animate-bounce rounded-full bg-stone-400" style={{ animationDelay: `${d * 120}ms` }} />)}</span></div>}
            <div ref={end} />
          </div>

          <footer className="border-t border-stone-100 px-8 py-4">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <span className="eyebrow pr-1">Try:</span>
              {PROMPTS.map((p) => <button key={p} type="button" onClick={() => send(p)} className="rounded-full bg-stone-100 px-3 py-1.5 text-xs text-zinc-700 transition hover:bg-stone-900 hover:text-stone-50">“{p}”</button>)}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="relative">
              <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask Elena anything about styling, fabrics, or gala attire..." className="field !py-3.5 pr-14" />
              <button type="submit" className="absolute right-1.5 top-1.5 flex size-10 items-center justify-center rounded-lg bg-stone-900 text-stone-50 hover:bg-black" aria-label="Send"><Send className="size-4" /></button>
            </form>
            <p className="mt-2.5 text-center text-[11px] text-zinc-700">Elena is your confidential AI luxury fashion stylist • Responses may be reviewed by Paris master tailors upon request.</p>
          </footer>
        </section>
      </div>
    </div>
  );
}

function Avatar({ children, dark = true }) {
  return <span className={`flex size-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${dark ? 'bg-stone-900 text-stone-50' : 'bg-stone-200 text-stone-900'}`}>{children}</span>;
}

function Item({ on, onClick, icon: Icon, children }) {
  return (
    <button type="button" onClick={onClick} className={`mb-1 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left text-sm transition ${on ? 'bg-stone-900 text-stone-50' : 'text-stone-900 hover:bg-stone-200/60'}`}>
      <Icon className="size-4 shrink-0 opacity-70" strokeWidth={1.6} /> <span className="truncate">{children}</span>
    </button>
  );
}

function Me({ m, initials }) {
  return (
    <div className="flex flex-row-reverse items-start gap-3">
      <Avatar dark={false}>{initials}</Avatar>
      <div className="max-w-xl">
        <div className="rounded-2xl rounded-tr-sm bg-stone-900 px-5 py-4 text-sm leading-6 text-stone-50">{m.text}</div>
        <p className="eyebrow mt-1.5 text-right !text-[10px]">You • {m.time}</p>
      </div>
    </div>
  );
}

function Elena({ m }) {
  return (
    <div className="flex items-start gap-3">
      <Avatar><Sparkles className="size-3.5" /></Avatar>
      <div className="max-w-2xl">
        <div className="rounded-2xl rounded-tl-sm bg-white px-5 py-4 text-sm leading-6 shadow-soft">
          {m.text}
          {m.metric && (
            <div className="mt-4 flex items-center justify-between rounded-lg bg-stone-100 p-4">
              <div><p className="display text-3xl">{m.metric.value}</p><p className="eyebrow mt-0.5">{m.metric.label}</p><p className="mt-1 text-xs text-zinc-700">{m.metric.sub}</p></div>
              <span className="rounded-full bg-stone-900 px-3 py-1 text-[10px] font-semibold uppercase tracking-widest text-stone-50">{m.metric.tag}</span>
            </div>
          )}
          {m.picks?.length > 0 && (
            <div className="mt-4 grid grid-cols-2 gap-4">
              {m.picks.map((id, i) => {
                const p = getProduct(id);
                return (
                  <article key={id} className="overflow-hidden rounded-xl bg-stone-50 ring-1 ring-stone-200/70">
                    <div className="h-48"><ProductImage product={p} label={false} /></div>
                    <div className="p-4">
                      <p className="eyebrow !text-[10px]">{m.looks?.[i] ?? `${p.kind} • AI match ${p.ai}%`}</p>
                      <p className="display mt-1 text-lg leading-6">{p.name}</p>
                      <p className="mt-1 text-sm">{money(p.price)}</p>
                      <p className="mt-1 line-clamp-2 text-xs leading-5 text-zinc-700">{p.short}</p>
                      <Link to={`/product/${id}`} className="btn-outline mt-3 w-full !py-2">Inspect silhouette</Link>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </div>
        <p className="eyebrow mt-1.5 !text-[10px]">Elena • AI atelier stylist</p>
      </div>
    </div>
  );
}
