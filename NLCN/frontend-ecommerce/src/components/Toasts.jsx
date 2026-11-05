import { Check } from 'lucide-react';
import { useStore } from '../context/StoreContext';

export default function Toasts() {
  const { toasts } = useStore();
  return (
    <div className="no-print pointer-events-none fixed bottom-6 left-1/2 z-[70] flex -translate-x-1/2 flex-col items-center gap-2" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto flex animate-fade-up items-center gap-2.5 rounded-full bg-stone-900 py-2.5 pl-3 pr-5 text-xs font-medium tracking-wide text-stone-50 shadow-float">
          <span className="flex size-5 items-center justify-center rounded-full bg-stone-50 text-stone-900"><Check className="size-3" strokeWidth={3} /></span>
          {t.message}
        </div>
      ))}
    </div>
  );
}
