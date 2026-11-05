import { useEffect } from 'react';
import { X } from 'lucide-react';
import { INFO } from '../data/info';
import { navigate } from '../lib/router';
import { useStore } from '../context/StoreContext';

export default function InfoModal({ id, onClose }) {
  const { toast } = useStore();
  const info = id ? INFO[id] : null;

  useEffect(() => {
    if (!info) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [info, onClose]);

  if (!info) return null;
  return (
    <div className="no-print fixed inset-0 z-[60] flex items-center justify-center bg-stone-900/40 px-6 backdrop-blur-sm animate-fade-in" onMouseDown={onClose} role="dialog" aria-modal="true" aria-label={info.title}>
      <div className="relative w-full max-w-lg animate-fade-up rounded-2xl bg-white p-8 shadow-float" onMouseDown={(e) => e.stopPropagation()}>
        <button type="button" onClick={onClose} className="absolute right-4 top-4 rounded-full p-2 text-zinc-700 hover:bg-stone-100" aria-label="Close"><X className="size-4" /></button>
        <p className="eyebrow mb-2">Atelier Studio</p>
        <h2 className="display text-3xl">{info.title}</h2>
        <div className="mt-5 space-y-2 text-sm leading-6 text-zinc-700">{info.body.map((l) => <p key={l}>{l}</p>)}</div>
        {info.cta && (
          <button
            type="button"
            className="btn-primary mt-7"
            onClick={() => {
              onClose();
              if (info.to) navigate(info.to);
              else toast('Request received — your concierge will confirm within two hours');
            }}
          >
            {info.cta}
          </button>
        )}
      </div>
    </div>
  );
}
