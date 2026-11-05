import { useState } from 'react';
import { ArrowRight } from 'lucide-react';
import { Link } from '../lib/router';
import { useStore } from '../context/StoreContext';

const COLUMNS = [
  { title: 'Boutique Concierge', items: [['Flagship Locations', 'flagships'], ['Private Salon Appointments', 'appointments'], ['Virtual Atelier Styling', 'styling'], ['Bespoke Tailoring', 'bespoke']] },
  { title: 'Client Services', items: [['Order Tracking', 'tracking'], ['White-Glove Returns', 'returns'], ['Garment Preservation', 'preservation'], ['Direct Concierge Hotline', 'hotline']] },
  { title: 'Sustainability & Ethics', items: [['Circularity Manifesto', 'circularity'], ['Fibre Origin & Traceability', 'traceability'], ['Artisanal Preservation', 'artisanal'], ['Net-Zero Milestone', 'netzero']] },
];

export default function Footer({ onInfo }) {
  const { toast } = useStore();
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');

  const subscribe = (e) => {
    e.preventDefault();
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError('Please enter a valid correspondence address.');
    setError('');
    setEmail('');
    toast('Welcome to the Private Salon — your first edit arrives shortly');
  };

  return (
    <footer className="no-print mt-24 border-t border-stone-200 bg-stone-100/60">
      <div className="shell py-16">
        <div className="grid grid-cols-[1.3fr_1fr_1fr_1fr] gap-12">
          <form onSubmit={subscribe} noValidate>
            <p className="eyebrow-ink">Private Salon Newsletter</p>
            <p className="mt-3 max-w-xs text-xs leading-5 tracking-tight text-zinc-700">Receive haute couture invitations and seasonal runway edits.</p>
            <div className="relative mt-5 max-w-xs">
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Atelier correspondence address" aria-label="Email" aria-invalid={!!error} className="field !rounded-lg !bg-white pr-12" />
              <button type="submit" className="absolute right-1.5 top-1.5 flex size-8 items-center justify-center rounded-md bg-stone-900 text-stone-50 transition hover:bg-black" aria-label="Subscribe">
                <ArrowRight className="size-4" />
              </button>
            </div>
            {error && <p className="mt-2 text-xs text-red-800" role="alert">{error}</p>}
          </form>

          {COLUMNS.map((c) => (
            <div key={c.title}>
              <p className="eyebrow-ink">{c.title}</p>
              <ul className="mt-4 space-y-2.5">
                {c.items.map(([label, key]) => (
                  <li key={key}>
                    <button type="button" onClick={() => onInfo(key)} className="text-left text-xs tracking-tight text-zinc-700 transition hover:text-stone-900 hover:underline">{label}</button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-14 flex items-center justify-between border-t border-stone-200 pt-7">
          <p className="eyebrow">© 2025 Atelier Studio. All rights reserved.</p>
          <div className="flex items-center gap-7">
            <button type="button" onClick={() => onInfo('legal')} className="eyebrow hover:text-stone-900">Legal &amp; Privacy</button>
            <button type="button" onClick={() => onInfo('terms')} className="eyebrow hover:text-stone-900">Terms of Atelier</button>
            <button type="button" onClick={() => onInfo('accessibility')} className="eyebrow hover:text-stone-900">Accessibility Standards</button>
            <Link to="/stylist" className="eyebrow hover:text-stone-900">AI Stylist</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
