import { useState } from 'react';
import { Download, MapPin, Fingerprint, Ruler, UserRound } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { Breadcrumb } from '../components/ui';

const TABS = [
  { id: 'personal', label: '1. Personal & Contact', icon: UserRound },
  { id: 'addresses', label: '2. Sanctuaries & Residences', icon: MapPin },
  { id: 'measure', label: '3. Bespoke Measurements', icon: Ruler },
  { id: 'security', label: '4. Security & Passkeys', icon: Fingerprint },
];

export default function ProfilePage() {
  const { user, tier, updateUser, toast } = useStore();
  const [tab, setTab] = useState('personal');
  const [form, setForm] = useState({ name: user.name, moniker: user.moniker, email: user.email, phone: user.phone });
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const save = () => {
    updateUser(form);
    toast('Dossier saved');
  };

  return (
    <div className="shell pt-7">
      <Breadcrumb items={[{ label: 'Collections', to: '/' }, { label: 'Privilege', to: '/account' }, { label: 'Client profile' }]} />
      <header className="mb-8 mt-4 flex items-end justify-between">
        <div>
          <p className="eyebrow">Confidential record • REF: {user.clientNo}</p>
          <h1 className="display mt-2 text-5xl">Client Profile & Personal Dossier</h1>
        </div>
        <div className="flex gap-3">
          <button type="button" onClick={() => window.print()} className="btn-outline"><Download className="size-4" /> Download dossier (PDF)</button>
          <button type="button" onClick={save} className="btn-primary">Save changes</button>
        </div>
      </header>

      <div className="grid grid-cols-[18rem_minmax(0,1fr)] items-start gap-8">
        <aside className="space-y-4">
          <div className="card p-6 text-center">
            <span className="mx-auto flex size-24 items-center justify-center rounded-full bg-stone-900 font-display text-3xl text-stone-50">{user.name.split(' ').map((w) => w[0]).slice(0, 2).join('')}</span>
            <p className="mt-4 font-semibold">{user.honorific} {user.name}</p>
            <p className="eyebrow mt-1">{tier.no} {tier.name}</p>
          </div>
          <nav className="card p-2">
            {TABS.map((t) => (
              <button key={t.id} type="button" onClick={() => setTab(t.id)} className={`flex w-full items-center gap-3 rounded-lg px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide transition ${tab === t.id ? 'bg-stone-900 text-stone-50' : 'text-zinc-700 hover:bg-stone-100'}`}>
                <t.icon className="size-4" /> {t.label}
              </button>
            ))}
          </nav>
        </aside>

        <section className="card min-h-[24rem] animate-fade-up p-8" key={tab}>
          {tab === 'personal' && (
            <div className="grid grid-cols-2 gap-6">
              {[['name', 'Legal honorific & name'], ['moniker', 'Preferred moniker'], ['email', 'Primary email'], ['phone', 'Private direct line']].map(([k, l]) => (
                <label key={k}><span className="eyebrow mb-2 block">{l}</span><input className="field" value={form[k]} onChange={set(k)} /></label>
              ))}
            </div>
          )}
          {tab === 'addresses' && (user.addresses.length ? user.addresses.map((a) => (
            <div key={a.id} className="mb-4 rounded-lg bg-stone-100 p-4"><p className="font-semibold">{a.label}</p><p className="text-sm text-zinc-700">{a.line}, {a.city}</p></div>
          )) : <p className="text-sm text-zinc-700">No address saved yet.</p>)}
          {tab === 'measure' && (
            <div className="grid grid-cols-4 gap-4">
              {['height', 'bust', 'waist', 'hips', 'shoulder', 'sleeve', 'inseam'].map((k) => (
                <div key={k} className="rounded-lg bg-stone-100 p-4"><p className="eyebrow capitalize">{k}</p><p className="display mt-2 text-2xl">{user.measurements[k] || '—'} {user.measurements.unit}</p></div>
              ))}
            </div>
          )}
          {tab === 'security' && (
            <ul className="space-y-3">
              {user.passkeys.map((p) => <li key={p.id} className="flex justify-between rounded-lg bg-stone-100 p-4 text-sm"><span>{p.name}</span><span className="text-zinc-700">Added {p.added}</span></li>)}
              {!user.passkeys.length && <li className="text-sm text-zinc-700">No passkey registered.</li>}
            </ul>
          )}
        </section>
      </div>
      <p className="mt-6 text-xs text-zinc-700">Need to see your points? <Link to="/account" className="underline">Go to Privilege</Link></p>
    </div>
  );
}
