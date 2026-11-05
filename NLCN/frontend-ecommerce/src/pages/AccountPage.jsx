import { useState } from 'react';
import { Check, Crown, Gift, Lock, MapPin, Pencil, Ruler, ScrollText, UserRound } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { REWARDS, TIERS, nextTier } from '../data/user';
import { Breadcrumb, Switch } from '../components/ui';

const TABS = [
  { id: 'dossier', label: 'Client Profile & Dossier', icon: UserRound },
  { id: 'tiers', label: 'Privilege Tiers & Matrix', icon: Crown },
  { id: 'ledger', label: 'Points Ledger & Accrual', icon: ScrollText },
  { id: 'vault', label: 'Reward Redemption Vault', icon: Gift },
  { id: 'measurements', label: 'Bespoke Measurements', icon: Ruler },
  { id: 'sanctuaries', label: 'Sanctuaries & Preferences', icon: MapPin },
];

const fmt = (n) => n.toLocaleString('en-US');

export default function AccountPage() {
  const { user, tier } = useStore();
  const [tab, setTab] = useState('tiers');
  const next = nextTier(user.points);
  const progress = next ? Math.min(100, Math.round((user.points / next.min) * 100)) : 100;
  const display = `${user.honorific ? 'Madame ' : ''}${user.name}`;
  const initials = user.name.split(/\s+/).map((w) => w[0]).slice(0, 2).join('').toUpperCase();

  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Privilege & points' }]} />

      {/* heading */}
      <header className="mt-6 flex items-start justify-between gap-10">
        <div className="max-w-3xl">
          <p className="eyebrow flex items-center gap-2">Client dossier <span>•</span> N° {user.clientNo} <span>•</span> Member since {user.memberSince}</p>
          <h1 className="display mt-3 text-6xl leading-[1.1]">{display}</h1>
          <p className="mt-4 text-sm leading-6 text-zinc-700">Welcome to your private sanctuary. Your personal allocation benefits, bespoke alterations privileges, and tiered rewards are synchronized across all global salons.</p>
        </div>
        <div className="card flex shrink-0 items-center gap-4 p-4 pr-6">
          <span className="flex size-12 items-center justify-center rounded-lg bg-stone-900 font-display text-lg text-stone-50">LM</span>
          <div>
            <p className="eyebrow !text-[10px]">Senior salon concierge</p>
            <p className="text-sm font-semibold">Laurent M.</p>
            <p className="text-xs text-zinc-700">Paris Salon • 8 Rue Cambon</p>
          </div>
        </div>
      </header>

      {/* stat cards */}
      <section className="mt-9 grid grid-cols-4 gap-5" aria-label="Status">
        <div className="card bg-stone-900 p-6 !text-stone-50">
          <p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Current standing</p>
          <p className="mt-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-widest"><Crown className="size-4 text-orange-200" /> {tier.no}</p>
          <p className="display mt-1 text-3xl !text-stone-50">{tier.name}</p>
          <p className="mt-2 text-xs text-stone-400">Global salon full privileges</p>
        </div>
        <div className="card p-6">
          <p className="eyebrow">Atelier privilege rate</p>
          <p className="display mt-4 text-5xl">{Math.round(tier.rate * 100)}%</p>
          <p className="mt-1 text-xs font-semibold uppercase tracking-wide">Bespoke</p>
          <p className="mt-2 text-xs text-zinc-700">Applied automatically at salon checkout.</p>
        </div>
        <div className="card p-6">
          <p className="eyebrow">Accumulated points</p>
          <p className="mt-4 flex items-baseline gap-2"><span className="display text-5xl">{fmt(user.points)}</span><span className="eyebrow">pts</span></p>
          <div className="mt-2 flex items-center justify-between">
            <p className="text-xs text-zinc-700">Credit value: <b className="text-stone-900">€{(user.points / 100).toFixed(2)}</b></p>
            <button type="button" onClick={() => setTab('vault')} className="rounded-md bg-stone-900 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-wider text-stone-50 hover:bg-black">Redeem</button>
          </div>
        </div>
        <div className="card p-6">
          <p className="eyebrow">{next ? `${next.name} goal` : 'Highest order reached'}</p>
          <p className="display mt-4 text-5xl">{progress}%</p>
          <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-stone-200" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div className="h-full rounded-full bg-stone-900 transition-all duration-700" style={{ width: `${progress}%` }} />
          </div>
          <p className="mt-2 text-xs text-zinc-700">{next ? <><b className="text-stone-900">{fmt(next.min - user.points)}</b> to {next.no.replace('TIER', 'Tier')} • next level: {next.name} ({fmt(next.min / 1000)}K pts)</> : 'You hold the highest order of patronage.'}</p>
        </div>
      </section>

      {/* tabs */}
      <div className="mt-10 grid grid-cols-[17rem_minmax(0,1fr)] items-start gap-8">
        <nav className="card sticky top-32 p-2" aria-label="Account sections" role="tablist" aria-orientation="vertical">
          {TABS.map((t) => (
            <button key={t.id} type="button" role="tab" aria-selected={tab === t.id} onClick={() => setTab(t.id)} className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-xs font-semibold uppercase leading-4 tracking-wide transition ${tab === t.id ? 'bg-stone-900 text-stone-50' : 'text-zinc-700 hover:bg-stone-100 hover:text-stone-900'}`}>
              <t.icon className="size-4 shrink-0" strokeWidth={1.6} /> {t.label}
            </button>
          ))}
        </nav>

        <div key={tab} className="min-w-0 animate-fade-up" role="tabpanel">
          {tab === 'dossier' && <Dossier />}
          {tab === 'tiers' && <Tiers onVault={() => setTab('vault')} />}
          {tab === 'ledger' && <Ledger />}
          {tab === 'vault' && <Vault />}
          {tab === 'measurements' && <Measurements />}
          {tab === 'sanctuaries' && <Sanctuaries />}
        </div>
      </div>
    </div>
  );
}

function Panel({ eyebrow, title, intro, action, children }) {
  return (
    <section>
      <div className="mb-6 flex items-end justify-between gap-6">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">{eyebrow}</p>
          <h2 className="display text-4xl">{title}</h2>
          {intro && <p className="mt-3 text-sm leading-6 text-zinc-700">{intro}</p>}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

/* ---------- 1. Dossier ---------- */
function Dossier() {
  const { user } = useStore();
  const rows = [
    ['Legal name', `${user.honorific} ${user.name}`.trim()],
    ['Email', user.email],
    ['Private direct line', user.phone || '—'],
    ['Client reference', user.clientNo],
    ['Language protocol', user.language],
    ['Communication', user.communication],
  ];
  return (
    <Panel eyebrow="Client profile & dossier" title="Your private record" action={<Link to="/profile" className="btn-primary"><Pencil className="size-3.5" /> Edit full profile</Link>}>
      <dl className="card grid grid-cols-2 gap-x-10 gap-y-6 p-8">
        {rows.map(([k, v]) => (
          <div key={k}><dt className="eyebrow">{k}</dt><dd className="mt-1.5 text-sm">{v}</dd></div>
        ))}
      </dl>
      <div className="mt-5 grid grid-cols-3 gap-5">
        {[['Active garments in atelier', '4 creations'], ['Archived purchases', '28 pieces'], ['Global salon priority', 'Instant reservation']].map(([k, v]) => (
          <div key={k} className="card p-6"><p className="eyebrow">{k}</p><p className="display mt-3 text-2xl">{v}</p></div>
        ))}
      </div>
    </Panel>
  );
}

/* ---------- 2. Tiers ---------- */
function Tiers({ onVault }) {
  const { tier, user } = useStore();
  return (
    <Panel eyebrow="The architecture of exclusivity" title="Privilege Tiers & Matrix" intro="Privilege status at Atelier Studio is renewed annually and confers perpetual private salon consultations, bespoke runway piece reservations, and tiered purchasing allowances." action={<span className="chip">Cycle 2025</span>}>
      <div className="grid grid-cols-2 gap-5 xl:grid-cols-4">
        {TIERS.map((t) => {
          const state = t.id < tier.id ? 'done' : t.id === tier.id ? 'current' : 'locked';
          return (
            <article key={t.id} className={`relative flex flex-col rounded-xl p-6 shadow-soft transition ${state === 'current' ? 'bg-stone-900 text-stone-50 ring-1 ring-stone-900' : 'bg-white'} ${state === 'locked' ? 'opacity-80' : ''}`}>
              <div className="flex items-center justify-between">
                <p className={`text-xs font-semibold uppercase tracking-widest ${state === 'current' ? 'text-orange-200' : 'text-zinc-700'}`}>{t.no}</p>
                {state === 'done' && <span className="flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-stone-600"><Check className="size-3" /> Completed</span>}
                {state === 'locked' && <Lock className="size-3.5 text-zinc-700" />}
              </div>
              <p className={`mt-1 text-[11px] ${state === 'current' ? 'text-stone-400' : 'text-zinc-700'}`}>{t.range}</p>
              <h3 className={`display mt-4 text-2xl ${state === 'current' ? '!text-stone-50' : ''}`}>{t.name}</h3>
              <p className={`mt-1 text-xs ${state === 'current' ? 'text-stone-300' : 'text-zinc-700'}`}>{t.tagline}</p>
              <p className="display mt-5 text-4xl ">{Math.round(t.rate * 100)}%<span className={`ml-2 align-middle text-[10px] font-semibold uppercase tracking-wider ${state === 'current' ? 'text-stone-400' : 'text-zinc-700'}`}>Privilege checkout discount</span></p>
              <ul className="mt-5 flex-1 space-y-2.5 border-t border-current/10 pt-5">
                {t.perks.map((p) => (
                  <li key={p} className="flex gap-2 text-xs leading-5"><Check className={`mt-0.5 size-3.5 shrink-0 ${state === 'current' ? 'text-orange-200' : 'text-stone-600'}`} />{p}</li>
                ))}
              </ul>
              <p className={`mt-5 text-[10px] font-semibold uppercase tracking-widest ${state === 'current' ? 'text-orange-200' : 'text-zinc-700'}`}>
                {state === 'current' ? 'Current privilege level • Active status' : state === 'locked' ? `${fmt(Math.max(0, t.min - user.points))} pts remaining` : 'Achieved'}
              </p>
            </article>
          );
        })}
      </div>

      <div className="mt-6 flex items-center justify-between gap-10 rounded-xl bg-stone-200 p-8">
        <div className="max-w-2xl">
          <p className="eyebrow mb-2">Automatic privilege protocol</p>
          <h3 className="display text-2xl">Seamless checkout integration</h3>
          <p className="mt-2 text-sm leading-6 text-zinc-700">Your {Math.round(tier.rate * 100)}% {tier.name} discount is automatically recognized at cart inspection across atelierstudio.com and during in-person atelier appointments in Paris, Milan, New York, and Tokyo.</p>
        </div>
        <button type="button" onClick={onVault} className="btn-primary shrink-0">View reward vault</button>
      </div>
    </Panel>
  );
}

/* ---------- 3. Ledger ---------- */
function Ledger() {
  const { user } = useStore();
  const [filter, setFilter] = useState('all');
  // Số dư chạy: lùi từ số điểm hiện tại
  let bal = user.points;
  const rows = user.ledger.map((l) => { const r = { ...l, balance: bal }; bal -= l.pts; return r; });
  const shown = rows.filter((r) => filter === 'all' || (filter === 'earned' ? r.pts > 0 : r.pts < 0));
  return (
    <Panel eyebrow="Points ledger & accrual" title="Every point, accounted for" action={
      <div className="flex gap-1 rounded-lg bg-stone-100 p-1">
        {['all', 'earned', 'redeemed'].map((f) => (
          <button key={f} type="button" onClick={() => setFilter(f)} aria-pressed={filter === f} className={`rounded-md px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition ${filter === f ? 'bg-stone-900 text-stone-50' : 'text-zinc-700 hover:bg-stone-200'}`}>{f}</button>
        ))}
      </div>
    }>
      <div className="card overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead><tr className="eyebrow border-b border-stone-200 bg-stone-50"><th className="px-6 py-3">Date</th><th>Description</th><th className="text-right">Points</th><th className="px-6 text-right">Balance</th></tr></thead>
          <tbody>
            {shown.map((r) => (
              <tr key={r.id} className="border-b border-stone-100 last:border-0">
                <td className="whitespace-nowrap px-6 py-4 text-zinc-700">{r.date}</td>
                <td className="py-4 pr-4">{r.label}</td>
                <td className={`py-4 text-right font-semibold ${r.pts > 0 ? 'text-emerald-800' : 'text-red-800'}`}>{r.pts > 0 ? '+' : '−'}{fmt(Math.abs(r.pts))}</td>
                <td className="px-6 py-4 text-right text-zinc-700">{fmt(r.balance)}</td>
              </tr>
            ))}
            {!shown.length && <tr><td colSpan={4} className="px-6 py-12 text-center text-zinc-700">No entries for this filter.</td></tr>}
          </tbody>
        </table>
      </div>
    </Panel>
  );
}

/* ---------- 4. Vault ---------- */
function Vault() {
  const { user, redeem } = useStore();
  return (
    <Panel eyebrow="Reward redemption vault" title="Redeem your points" intro={`You currently hold ${fmt(user.points)} points (€${(user.points / 100).toFixed(2)} credit value).`}>
      <div className="grid grid-cols-2 gap-5 xl:grid-cols-3">
        {REWARDS.map((r) => {
          const owned = user.redeemed.includes(r.id);
          const short = r.cost - user.points;
          return (
            <article key={r.id} className="card flex flex-col p-6">
              <Gift className="size-6 text-stone-600" strokeWidth={1.3} />
              <h3 className="mt-4 text-base font-semibold">{r.name}</h3>
              <p className="mt-1 flex-1 text-xs leading-5 text-zinc-700">{r.desc}</p>
              <p className="display mt-5 text-3xl">{fmt(r.cost)} <span className="eyebrow">pts</span></p>
              <button type="button" disabled={owned || short > 0} onClick={() => redeem(r)} className={`mt-4 ${owned ? 'btn-outline' : 'btn-primary'}`}>
                {owned ? <><Check className="size-3.5" /> In your vault</> : short > 0 ? `${fmt(short)} pts to go` : 'Redeem'}
              </button>
            </article>
          );
        })}
      </div>
    </Panel>
  );
}

/* ---------- 5. Measurements ---------- */
function Measurements() {
  const { user } = useStore();
  const m = user.measurements;
  const keys = ['height', 'bust', 'waist', 'hips', 'shoulder', 'sleeve', 'inseam'];
  return (
    <Panel eyebrow="Bespoke measurements" title="Your measurements" intro="Used by Elena and your tailor to calibrate every recommendation and alteration." action={<Link to="/profile" className="btn-primary"><Pencil className="size-3.5" /> Update in profile</Link>}>
      <div className="grid grid-cols-4 gap-5">
        {keys.map((k) => (
          <div key={k} className="card p-6"><p className="eyebrow capitalize">{k}</p><p className="display mt-3 text-4xl">{m[k] || '—'}{m[k] ? <span className="ml-1 text-sm text-zinc-700">{m.unit}</span> : null}</p></div>
        ))}
        <div className="card bg-stone-900 p-6 !text-stone-50"><p className="text-xs font-semibold uppercase tracking-wide text-stone-400">Fit preference</p><p className="display mt-3 text-2xl !text-stone-50">{m.fit}</p></div>
      </div>
    </Panel>
  );
}

/* ---------- 6. Sanctuaries ---------- */
function Sanctuaries() {
  const { user, updateUser, toast } = useStore();
  const prefs = [
    ['newsletter', 'Private salon newsletter', 'Haute couture invitations and seasonal runway edits.'],
    ['runwayInvites', 'Runway & presentation invitations', 'Priority invitations from Paris, Milan, New York and Tokyo.'],
    ['sms', 'Courier updates by SMS', 'Live notifications while a parcel is in transit.'],
    ['aiMemory', 'Let Elena remember my style', 'Personalises recommendations using your wardrobe vault.'],
  ];
  return (
    <Panel eyebrow="Sanctuaries & preferences" title="Where and how we reach you" action={<Link to="/profile" className="btn-outline">Manage addresses</Link>}>
      <div className="grid grid-cols-2 gap-5">
        <div className="card p-6">
          <p className="eyebrow mb-4">Registered sanctuaries</p>
          {user.addresses.length ? user.addresses.map((a) => (
            <div key={a.id} className="mb-4 flex gap-3 last:mb-0"><MapPin className="mt-0.5 size-4 shrink-0 text-stone-600" strokeWidth={1.5} /><div><p className="text-sm font-semibold">{a.label} {a.isDefault && <span className="ml-1 rounded-full bg-stone-100 px-2 py-0.5 text-[10px] uppercase text-zinc-700">Default</span>}</p><p className="text-xs text-zinc-700">{a.line}, {a.city}</p></div></div>
          )) : <p className="text-sm text-zinc-700">No sanctuary yet. Add one in your profile.</p>}
        </div>
        <div className="card divide-y divide-stone-100 p-2">
          {prefs.map(([k, t, d]) => (
            <div key={k} className="flex items-center justify-between gap-6 p-4">
              <div><p className="text-sm font-medium">{t}</p><p className="mt-0.5 text-xs text-zinc-700">{d}</p></div>
              <Switch label={t} checked={!!user.prefs[k]} onChange={(v) => { updateUser({ prefs: { ...user.prefs, [k]: v } }); toast('Preference saved'); }} />
            </div>
          ))}
        </div>
      </div>
    </Panel>
  );
}
