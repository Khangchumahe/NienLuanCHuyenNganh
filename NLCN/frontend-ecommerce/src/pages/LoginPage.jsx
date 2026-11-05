import { useState } from 'react';
import { ArrowLeft, Apple, Eye, EyeOff, Fingerprint, Scissors, Sparkles, Ticket } from 'lucide-react';
import { Link, Redirect } from '../lib/router';
import { useStore } from '../context/StoreContext';
import { DEMO_EMAIL } from '../data/user';

const PRIVILEGES = [
  [Ticket, 'Private Trunk Shows', 'Priority access to numbered runway editions and pre-orders.'],
  [Sparkles, 'Atelier AI Stylist', 'Algorithmic silhouette composition and customized wardrobing.'],
  [Scissors, 'Concierge Tailoring', 'Global in-suite fitting appointments and bespoke alterations.'],
];

/** Chỉ cho phép quay lại đường dẫn nội bộ (chống open-redirect) */
const safeNext = (n) => (n && n.startsWith('/') && !n.startsWith('//') ? n : '/account');

export default function LoginPage({ query }) {
  const { user, login, toast } = useStore();
  const next = safeNext(query?.next);

  const [mode, setMode] = useState('signin'); // 'signin' | 'register'
  const [name, setName] = useState('');
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState('atelier2025');
  const [show, setShow] = useState(false);
  const [remember, setRemember] = useState(true);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  // Đã đăng nhập (kể cả vừa đăng nhập xong) → chuyển về trang trước đó
  if (user) return <Redirect to={next} />;

  const register = mode === 'register';

  const switchMode = (m) => {
    setMode(m);
    setErrors({});
    if (m === 'register') { setEmail(''); setPassword(''); }
    else { setEmail(DEMO_EMAIL); setPassword('atelier2025'); }
  };

  const validate = () => {
    const e = {};
    if (register && name.trim().length < 2) e.name = 'Please tell us your name.';
    if (!/^\S+@\S+\.\S+$/.test(email)) e.email = 'Enter a valid email address.';
    if (password.length < (register ? 8 : 6)) e.password = `Passphrase must be at least ${register ? 8 : 6} characters.`;
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const submit = (ev) => {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    // Giả lập độ trễ mạng; khi có API thật: await api.login(...) rồi gọi login(user)
    setTimeout(() => {
      login({ email, name });
      toast(register ? 'Welcome to the Maison — 500 points have been credited' : 'Welcome back to the Atelier');
    }, 600);
  };

  const quick = (label) => {
    toast(`${label} sign-in (demo)`);
    login({ email: DEMO_EMAIL });
  };

  const forgot = () => {
    if (!/^\S+@\S+\.\S+$/.test(email)) return setErrors({ email: 'Enter your email first, then request a reset.' });
    setErrors({});
    toast(`A reset link has been sent to ${email}`);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-stone-50 p-8">
      <div className="grid w-full max-w-[1120px] grid-cols-[1fr_1.05fr] overflow-hidden rounded-2xl bg-white shadow-2xl">
        {/* manifeste */}
        <aside className="relative flex min-h-[760px] flex-col justify-between overflow-hidden bg-black p-12 text-stone-50">
          <svg className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.07]" aria-hidden="true">
            <defs><pattern id="lg" width="56" height="56" patternUnits="userSpaceOnUse"><path d="M56 0H0V56" fill="none" stroke="#fff" strokeWidth="0.6" /></pattern></defs>
            <rect width="100%" height="100%" fill="url(#lg)" />
          </svg>
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-black/80 via-black/60 to-black/95" />

          <div className="relative">
            <Link to="/" className="mb-10 inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-stone-400 transition hover:text-stone-50"><ArrowLeft className="size-3.5" /> Back to the store</Link>
            <div className="flex items-center">
              <span className="flex h-10 w-6 items-center justify-center rounded-full bg-white/10 font-display text-base font-semibold backdrop-blur-md">M</span>
              <div className="pl-3">
                <p className="font-display text-xl font-medium uppercase leading-6 tracking-widest">Maison<br />Vesper</p>
                <p className="mt-1 text-[10px] font-semibold uppercase tracking-widest text-orange-200">Haute Couture • Paris</p>
              </div>
            </div>
          </div>

          <div className="relative">
            <p className="text-[10px] font-semibold uppercase tracking-[0.25em] text-orange-200">Manifeste</p>
            <blockquote className="mt-4 font-display text-3xl leading-[1.3] text-stone-50">“Style is a deeply personal expression of inner architecture.”</blockquote>
            <p className="mt-4 text-xs uppercase tracking-wider text-stone-300">— Julien Delacroix, Directeur de Création</p>
          </div>

          <div className="relative">
            <p className="mb-4 text-[10px] font-semibold uppercase tracking-[0.25em] text-orange-200">Privilèges Membre</p>
            <ul className="space-y-4">
              {PRIVILEGES.map(([Icon, t, d]) => (
                <li key={t} className="flex gap-4 rounded-lg bg-white/5 p-4">
                  <Icon className="mt-0.5 size-5 shrink-0 text-orange-200" strokeWidth={1.4} />
                  <div><p className="text-sm font-semibold">{t}</p><p className="mt-0.5 text-xs leading-5 text-stone-300">{d}</p></div>
                </li>
              ))}
            </ul>
          </div>
        </aside>

        {/* form */}
        <section className="flex flex-col justify-center p-14">
          <div className="mb-8 flex rounded-lg bg-stone-100 p-1" role="tablist">
            {[['signin', 'Accéder', 'Sign in'], ['register', 'Créer compte', 'Register']].map(([id, fr, en]) => (
              <button key={id} type="button" role="tab" aria-selected={mode === id} onClick={() => switchMode(id)} className={`flex-1 rounded-md py-2.5 text-center text-xs font-semibold uppercase tracking-wider transition ${mode === id ? 'bg-white text-stone-900 shadow-soft' : 'text-zinc-700 hover:text-stone-900'}`}>
                {fr} <span className="font-normal text-zinc-700">• {en}</span>
              </button>
            ))}
          </div>

          <h1 className="display text-4xl">{register ? 'Join the Maison' : 'Welcome to the Maison'}</h1>
          <p className="mt-2 text-sm leading-6 text-zinc-700">{register ? 'Request your Atelier account and receive 500 welcome points.' : 'Authenticate your client identity to consult your private selections.'}</p>

          <div className="mt-7 grid grid-cols-3 gap-3">
            <button type="button" onClick={() => quick('Apple')} className="btn-outline !normal-case !tracking-normal !text-sm !font-medium"><Apple className="size-4" /> Apple</button>
            <button type="button" onClick={() => quick('Google')} className="btn-outline !normal-case !tracking-normal !text-sm !font-medium"><span className="font-semibold">G</span> Google</button>
            <button type="button" onClick={() => quick('Passkey')} className="btn-outline !normal-case !tracking-normal !text-sm !font-medium"><Fingerprint className="size-4" /> Passkey</button>
          </div>

          <div className="my-6 flex items-center gap-4"><span className="h-px flex-1 bg-stone-200" /><span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-700">Ou par identifiant</span><span className="h-px flex-1 bg-stone-200" /></div>

          <form onSubmit={submit} noValidate className="space-y-5">
            {register && (
              <Field label="Nom complet" error={errors.name}>
                <input className="field" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" placeholder="Vivienne Laurent" aria-invalid={!!errors.name} />
              </Field>
            )}
            <Field label="Adresse email professionnelle ou personnelle" error={errors.email}>
              <input className="field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" placeholder="name@maison.com" aria-invalid={!!errors.email} />
            </Field>
            <Field label="Mot de passe" error={errors.password}>
              <div className="relative">
                <input className="field pr-11" type={show ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={register ? 'new-password' : 'current-password'} placeholder="••••••••" aria-invalid={!!errors.password} />
                <button type="button" onClick={() => setShow((s) => !s)} className="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-2 text-zinc-700 hover:text-stone-900" aria-label={show ? 'Hide passphrase' : 'Show passphrase'}>
                  {show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </Field>

            {!register && (
              <div className="flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-2 text-xs text-zinc-700">
                  <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="size-4 accent-stone-900" /> Remember this device
                </label>
                <button type="button" onClick={forgot} className="text-xs font-medium text-zinc-700 underline underline-offset-4 hover:text-stone-900">Forgot passphrase?</button>
              </div>
            )}

            <button type="submit" disabled={loading} className="btn-primary w-full !py-4">
              {loading ? 'Authenticating…' : register ? 'Request an Atelier account' : 'Enter the Atelier'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-700">
            {register ? 'Already a collector?' : 'Unregistered collector?'}{' '}
            <button type="button" onClick={() => switchMode(register ? 'signin' : 'register')} className="font-semibold text-stone-900 underline underline-offset-4">
              {register ? 'Sign in' : 'Request an Atelier Account'}
            </button>
          </p>
          {!register && <p className="mt-4 text-center text-[11px] text-zinc-700/70">Demo access is pre-filled — just press “Enter the Atelier”.</p>}
        </section>
      </div>
    </div>
  );
}

function Field({ label, error, children }) {
  return (
    <label className="block">
      <span className="eyebrow mb-2 block !text-[11px]">{label}</span>
      {children}
      {error && <span className="mt-1.5 block text-xs font-medium text-red-800" role="alert">{error}</span>}
    </label>
  );
}
