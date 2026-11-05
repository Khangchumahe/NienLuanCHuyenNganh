import { useEffect } from 'react';
import { ChevronRight, X } from 'lucide-react';
import { Link } from '../lib/router';

/** Công tắc bật/tắt (role=switch) */
export function Switch({ checked, onChange, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={`relative h-5 w-9 shrink-0 rounded-full transition-colors duration-200 ${checked ? 'bg-black' : 'bg-stone-300'}`}
    >
      <span className={`absolute left-0.5 top-0.5 size-4 rounded-full bg-white shadow-soft transition-transform duration-200 ${checked ? 'translate-x-4' : ''}`} />
    </button>
  );
}

/** COLLECTIONS / WOMEN / ... (mục cuối là trang hiện tại) */
export function Breadcrumb({ items }) {
  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap items-center gap-2">
      {items.map((it, i) => {
        const last = i === items.length - 1;
        return (
          <span key={it.label} className="flex items-center gap-2">
            {it.to && !last ? (
              <Link to={it.to} className="eyebrow transition hover:text-stone-900">{it.label}</Link>
            ) : (
              <span className={`eyebrow ${last ? '!text-black' : ''}`} aria-current={last ? 'page' : undefined}>{it.label}</span>
            )}
            {!last && <ChevronRight className="size-3 text-zinc-700" />}
          </span>
        );
      })}
    </nav>
  );
}

export function Modal({ open, onClose, title, children, width = 'max-w-lg' }) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="no-print fixed inset-0 z-[60] flex items-center justify-center bg-stone-900/40 px-6 backdrop-blur-sm animate-fade-in" onMouseDown={onClose} role="dialog" aria-modal="true" aria-label={title}>
      <div className={`relative w-full ${width} animate-fade-up rounded-2xl bg-white p-8 shadow-float`} onMouseDown={(e) => e.stopPropagation()}>
        <button type="button" onClick={onClose} className="absolute right-4 top-4 rounded-full p-2 text-zinc-700 hover:bg-stone-100" aria-label="Close"><X className="size-4" /></button>
        <h2 className="display mb-5 text-3xl">{title}</h2>
        {children}
      </div>
    </div>
  );
}

const SIZE_ROWS = [
  ['FR 34', 80, 62, 88], ['FR 36', 84, 66, 92], ['FR 38', 88, 70, 96],
  ['FR 40', 92, 74, 100], ['FR 42', 96, 78, 104], ['FR 44', 100, 82, 108],
];

export function SizeGuide({ open, onClose }) {
  return (
    <Modal open={open} onClose={onClose} title="French Sizing Guide" width="max-w-xl">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="eyebrow border-b border-stone-200">
            <th className="py-2">Size</th><th>Bust (cm)</th><th>Waist (cm)</th><th>Hips (cm)</th>
          </tr>
        </thead>
        <tbody>
          {SIZE_ROWS.map(([s, ...v]) => (
            <tr key={s} className="border-b border-stone-100">
              <td className="py-2.5 font-medium">{s}</td>{v.map((n, i) => <td key={i} className="text-zinc-700">{n}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-4 text-xs leading-5 text-zinc-700">Between two sizes? Choose the larger for an oversized, architectural line. Your saved measurements are available in your client profile.</p>
    </Modal>
  );
}

/** Tiêu đề section: nhãn nhỏ + tiêu đề serif + (tuỳ chọn) action bên phải */
export function SectionHead({ eyebrow, title, action }) {
  return (
    <div className="mb-8 flex items-end justify-between gap-6">
      <div>
        {eyebrow && <p className="eyebrow mb-2">{eyebrow}</p>}
        <h2 className="display text-4xl leading-tight">{title}</h2>
      </div>
      {action}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, text, children }) {
  return (
    <div className="card flex flex-col items-center px-10 py-20 text-center">
      {Icon && <Icon className="mb-5 size-10 text-stone-400" strokeWidth={1} />}
      <h2 className="display text-3xl">{title}</h2>
      <p className="mt-3 max-w-md text-sm leading-6 text-zinc-700">{text}</p>
      <div className="mt-8 flex gap-3">{children}</div>
    </div>
  );
}
