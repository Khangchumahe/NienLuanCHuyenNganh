/** Hạng thành viên – nội dung lấy từ trang Account (Figma) */
export const TIERS = [
  {
    id: 1, no: 'TIER I', name: 'Privilege', range: '0 - 4,999 PTS', min: 0, max: 4999, rate: 0.05,
    tagline: 'Foundation of Luxury Ready-to-Wear',
    perks: ['Seasonal digital lookbook preview', 'Standard private salon access', 'Annual atelier anniversary greeting'],
  },
  {
    id: 2, no: 'TIER II', name: 'Luminary', range: '5,000 - 9,999 PTS', min: 5000, max: 9999, rate: 0.1,
    tagline: 'Ascension to Private Salons',
    perks: ['All Privilege tier allocations', 'Complimentary express global courier', 'Private fitting room advance booking'],
  },
  {
    id: 3, no: 'TIER III', name: 'Nocturne Elite', range: '10,000 - 19,999 PTS', min: 10000, max: 19999, rate: 0.15,
    tagline: 'Couture & Archival Mastery',
    perks: [
      'Dedicated Stylist (Elena AI & Concierge Laurent M.)',
      'Complimentary bespoke alterations & monograms',
      'Invitation to Paris Fashion Week presentation',
      'Priority waitlist for limited capsule drops',
    ],
  },
  {
    id: 4, no: 'TIER IV', name: 'Archival Salon', range: '20,000+ PTS', min: 20000, max: Infinity, rate: 0.2,
    tagline: 'The Highest Order of Patronage',
    perks: [
      'First-look runway allocations & pre-orders',
      'In-suite tailor handover & worldwide white-glove courier',
      'Custom-tailored seasonal gifts from creative directorship',
    ],
  },
];

export const tierFor = (pts) => [...TIERS].reverse().find((t) => pts >= t.min) ?? TIERS[0];
export const nextTier = (pts) => TIERS.find((t) => t.min > pts) ?? null;

export const REWARDS = [
  { id: 'r-pocket', name: 'Silk Twill Pocket Square', cost: 1500, desc: 'Hand-rolled edge, printed in the Paris atelier.' },
  { id: 'r-care', name: 'Cedar Garment Care Kit', cost: 2500, desc: 'Cedar hanger, linen envelope and restorative steam voucher.' },
  { id: 'r-fitting', name: 'Private Fitting Session', cost: 3000, desc: 'One hour with a master tailor, in-suite or at Rue Cambon.' },
  { id: 'r-monogram', name: 'Bespoke Monogram Service', cost: 4000, desc: 'Hand-embroidered initials on any garment you own.' },
  { id: 'r-credit', name: '€100 Atelier Credit', cost: 10000, desc: 'Applied at checkout on atelierstudio.com or in any salon.' },
  { id: 'r-runway', name: 'Runway Front-Row Invitation', cost: 15000, desc: 'Two seats at the next Paris presentation, with salon after-party.' },
];

export const DEMO_EMAIL = 'vivienne.laurent@archival-atelier.com';

export const DEMO_USER = {
  honorific: 'Mrs.',
  name: 'Vivienne Laurent',
  moniker: 'Vivienne',
  email: DEMO_EMAIL,
  phone: '+1 (212) 555-0198',
  birth: '1992-10-14',
  pronouns: 'She / Her',
  memberSince: 2021,
  clientNo: 'ATL-9042-PARIS',
  points: 14850,
  communication: 'Concierge Direct Messaging & Private Email',
  language: 'English (Primary)',
  emergency: { name: 'Marc Laurent', role: 'Authorized Salon Representative & Escort', phone: '+33 1 42 68 55 00' },
  addresses: [
    { id: 'a1', label: 'Paris Residence', line: '14 Avenue Montaigne, Suite 4B', city: '75008 Paris, France', isDefault: true },
    { id: 'a2', label: 'Milan Pied-à-terre', line: 'Via Monte Napoleone 12', city: '20121 Milano, Italy', isDefault: false },
  ],
  measurements: { unit: 'cm', height: 178, bust: 92, waist: 68, hips: 96, shoulder: 42, sleeve: 61, inseam: 81, fit: 'Architectural' },
  prefs: { newsletter: true, sms: false, runwayInvites: true, aiMemory: true },
  twoFactor: true,
  passkeys: [
    { id: 'pk1', name: 'MacBook Pro • Touch ID', added: '12 Mar 2025' },
    { id: 'pk2', name: 'iPhone 15 • Face ID', added: '02 Jun 2025' },
  ],
  redeemed: [],
  ledger: [
    { id: 'l1', date: '18 Nov 2025', label: 'Acquisition ATL-849204 — Wool Blazer & Silk Pant', pts: 2170 },
    { id: 'l2', date: '14 Oct 2025', label: 'Birthday privilege accrual', pts: 500 },
    { id: 'l3', date: '02 Oct 2025', label: 'Acquisition ATL-771203 — Cashmere Capsule', pts: 1240 },
    { id: 'l4', date: '21 Aug 2025', label: 'Redeemed — Silk Twill Pocket Square', pts: -1500 },
    { id: 'l5', date: '09 Jun 2025', label: 'Acquisition ATL-690118 — Tuscan Leather Tote', pts: 1450 },
    { id: 'l6', date: '15 Mar 2025', label: 'Private salon appointment bonus', pts: 300 },
  ],
};

/** Tạo hồ sơ mới khi đăng ký */
export function newUser({ name, email }) {
  const clean = (name || email.split('@')[0] || 'Guest').trim();
  const first = clean.split(/\s+/)[0];
  return {
    ...DEMO_USER,
    honorific: '',
    name: clean,
    moniker: first,
    email,
    phone: '',
    birth: '',
    pronouns: '',
    memberSince: new Date().getFullYear(),
    clientNo: `ATL-${Math.floor(1000 + Math.random() * 9000)}-PARIS`,
    points: 500,
    emergency: { name: '', role: '', phone: '' },
    addresses: [],
    measurements: { unit: 'cm', height: '', bust: '', waist: '', hips: '', shoulder: '', sleeve: '', inseam: '', fit: 'Tailored' },
    passkeys: [],
    twoFactor: false,
    redeemed: [],
    ledger: [{ id: 'l0', date: new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }), label: 'Welcome to the Maison', pts: 500 }],
  };
}
