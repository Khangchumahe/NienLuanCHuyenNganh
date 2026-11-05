/**
 * Hình minh hoạ trang phục (SVG, viewBox 200x260), tô theo màu sản phẩm.
 * Thêm kiểu mới: viết một hàm trả về <g> rồi đăng ký vào GARMENTS.
 */

function mix(hex, to, amt) {
  const n = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
  const [a, b] = [n(hex), n(to)];
  return `#${a.map((v, i) => Math.round(v + (b[i] - v) * amt).toString(16).padStart(2, '0')).join('')}`;
}

export function tones(hex) {
  const isDark = parseInt(hex.slice(1, 3), 16) + parseInt(hex.slice(3, 5), 16) + parseInt(hex.slice(5, 7), 16) < 260;
  return {
    base: hex,
    dark: isDark ? mix(hex, '#ffffff', 0.12) : mix(hex, '#000000', 0.18),
    light: isDark ? mix(hex, '#ffffff', 0.28) : mix(hex, '#ffffff', 0.3),
    line: isDark ? mix(hex, '#ffffff', 0.35) : mix(hex, '#000000', 0.28),
    shirt: '#f4f0e8',
  };
}

const sw = { fill: 'none', strokeLinecap: 'round', strokeLinejoin: 'round' };

function Blazer({ t, field }) {
  return (
    <g>
      <path d="M52 62 L30 74 L20 198 L46 202 L56 118 Z" fill={t.base} />
      <path d="M148 62 L170 74 L180 198 L154 202 L144 118 Z" fill={t.base} />
      <path d="M30 74 L20 198 L46 202" {...sw} stroke={t.line} strokeWidth="1.2" />
      <path d="M170 74 L180 198 L154 202" {...sw} stroke={t.line} strokeWidth="1.2" />
      <path d="M64 46 Q100 32 136 46 L152 62 L158 240 L42 240 L48 62 Z" fill={t.base} />
      <path d="M84 40 Q100 62 116 40 L110 34 Q100 44 90 34 Z" fill={t.shirt} />
      {field ? (
        <>
          <path d="M84 38 L100 70 L116 38 L128 44 L100 86 L72 44 Z" fill={t.dark} />
          <path d="M100 70 V240" {...sw} stroke={t.line} strokeWidth="1.4" />
          {[[60, 150], [112, 150], [60, 190], [112, 190]].map(([x, y]) => (
            <g key={x + y}><rect x={x} y={y} width="28" height="26" rx="2" fill={t.dark} /><path d={`M${x} ${y + 8}H${x + 28}`} {...sw} stroke={t.line} strokeWidth="1" /></g>
          ))}
          <path d="M48 138 Q100 150 152 138" {...sw} stroke={t.line} strokeWidth="1.2" />
        </>
      ) : (
        <>
          <path d="M80 42 L100 126 L62 104 L68 62 Z" fill={t.dark} />
          <path d="M120 42 L100 126 L138 104 L132 62 Z" fill={t.dark} />
          <path d="M100 126 L122 238" {...sw} stroke={t.line} strokeWidth="1.4" />
          <path d="M62 104 L100 126" {...sw} stroke={t.line} strokeWidth="1" />
          {[[86, 150], [114, 150], [86, 188], [114, 188]].map(([x, y]) => <circle key={x + y} cx={x} cy={y} r="3.4" fill={t.light} stroke={t.line} strokeWidth=".8" />)}
          <path d="M54 214 H82 M118 214 H146" {...sw} stroke={t.line} strokeWidth="1.4" />
        </>
      )}
    </g>
  );
}

function Pant({ t }) {
  return (
    <g>
      <path d="M58 42 H142 L148 64 L160 242 L108 242 L100 112 L92 242 L40 242 L52 64 Z" fill={t.base} />
      <path d="M58 42 H142 V54 H58 Z" fill={t.dark} />
      <path d="M100 54 V112" {...sw} stroke={t.line} strokeWidth="1.2" />
      {[[74, 54, 70, 130], [88, 54, 82, 150], [112, 54, 118, 150], [126, 54, 130, 130]].map(([a, b, c, d]) => <path key={a} d={`M${a} ${b} L${c} ${d}`} {...sw} stroke={t.line} strokeWidth="1" />)}
      <path d="M66 140 L58 238 M134 140 L142 238" {...sw} stroke={t.line} strokeWidth=".9" opacity=".7" />
      <rect x="96" y="40" width="8" height="14" fill={t.light} />
    </g>
  );
}

function Knit({ t }) {
  return (
    <g>
      <path d="M52 68 L26 88 L20 222 L44 224 L52 116 Z" fill={t.base} />
      <path d="M148 68 L174 88 L180 222 L156 224 L148 116 Z" fill={t.base} />
      <path d="M60 64 H140 L152 80 L156 218 H44 L48 80 Z" fill={t.base} />
      <path d="M80 26 H120 L124 66 H76 Z" fill={t.dark} />
      {[34, 42, 50, 58].map((y) => <path key={y} d={`M79 ${y}H121`} {...sw} stroke={t.line} strokeWidth=".9" />)}
      <path d="M44 208 H156 V222 H44 Z" fill={t.dark} />
      <path d="M20 212 H44 M156 212 H180" {...sw} stroke={t.line} strokeWidth="2.5" />
      {Array.from({ length: 14 }, (_, i) => <path key={i} d={`M${54 + i * 7} 90 V200`} {...sw} stroke={t.line} strokeWidth=".6" opacity=".45" />)}
    </g>
  );
}

function Tote({ t }) {
  return (
    <g>
      <path d="M68 108 C66 40 134 40 132 108" {...sw} stroke={t.dark} strokeWidth="9" />
      <path d="M34 104 H166 L178 224 Q178 232 170 232 H30 Q22 232 22 224 Z" fill={t.base} />
      <path d="M34 104 H166 L168 122 H32 Z" fill={t.dark} />
      <path d="M34 128 L28 222 M166 128 L172 222" {...sw} stroke={t.line} strokeWidth="1.2" strokeDasharray="3 3" />
      <rect x="88" y="150" width="24" height="16" rx="2" fill={t.light} stroke={t.line} strokeWidth=".8" />
      <circle cx="100" cy="158" r="2.5" fill={t.line} />
    </g>
  );
}

function Coat({ t }) {
  return (
    <g>
      <path d="M62 46 Q100 32 138 46 L160 64 C182 120 178 200 172 248 L28 248 C22 200 18 120 40 64 Z" fill={t.base} />
      <path d="M40 64 C26 120 30 200 34 242 L54 244 C50 180 52 124 62 72 Z" fill={t.dark} />
      <path d="M160 64 C174 120 170 200 166 242 L146 244 C150 180 148 124 138 72 Z" fill={t.dark} />
      <path d="M82 40 Q100 62 118 40 L110 32 Q100 42 90 32 Z" fill={t.shirt} />
      <path d="M78 40 L100 92 L122 40 L134 46 L100 112 L66 46 Z" fill={t.light} opacity=".9" />
      <path d="M100 92 V246" {...sw} stroke={t.line} strokeWidth="1.4" />
      {[120, 156, 192].map((y) => <circle key={y} cx="108" cy={y} r="3.4" fill={t.light} stroke={t.line} strokeWidth=".8" />)}
      <path d="M62 150 H84 M116 150 H138" {...sw} stroke={t.line} strokeWidth="1.4" />
    </g>
  );
}

function Boot({ t }) {
  return (
    <g>
      <path d="M62 38 H120 L126 150 C128 168 150 170 168 182 C184 192 186 214 182 226 H62 Z" fill={t.base} />
      <path d="M62 38 H120 V52 H62 Z" fill={t.dark} />
      <path d="M62 218 H184 V228 H62 Z" fill={t.dark} />
      <rect x="62" y="228" width="30" height="16" fill={t.dark} />
      <path d="M126 150 C132 166 150 170 168 182" {...sw} stroke={t.line} strokeWidth="1.2" />
      <path d="M70 60 V200" {...sw} stroke={t.light} strokeWidth="1.4" opacity=".6" />
      <path d="M174 190 L184 200 V226" {...sw} stroke={t.line} strokeWidth="1.2" />
    </g>
  );
}

function Scarf({ t }) {
  return (
    <g>
      <path d="M66 28 C50 42 52 66 72 74 L62 222 H114 L112 126 C138 116 148 88 136 58 C126 34 92 20 66 28 Z" fill={t.base} />
      <path d="M112 126 C130 126 146 140 144 168 L138 222 H112 Z" fill={t.dark} />
      <path d="M72 74 C90 84 112 92 124 80" {...sw} stroke={t.line} strokeWidth="1.2" />
      {Array.from({ length: 13 }, (_, i) => <path key={i} d={`M${62 + i * 4.2} 222 V240`} {...sw} stroke={t.dark} strokeWidth="1.6" />)}
      {Array.from({ length: 7 }, (_, i) => <path key={`b${i}`} d={`M${112 + i * 4.3} 222 V240`} {...sw} stroke={t.line} strokeWidth="1.6" />)}
      {[60, 100, 140, 180].map((y) => <path key={y} d={`M${66} ${y}H${112}`} {...sw} stroke={t.line} strokeWidth=".6" opacity=".4" />)}
    </g>
  );
}

function Collar({ t }) {
  return (
    <g>
      <path d="M52 96 A52 66 0 1 0 148 96" {...sw} stroke={t.base} strokeWidth="12" />
      <path d="M52 96 A52 66 0 1 0 148 96" {...sw} stroke={t.light} strokeWidth="3" opacity=".7" transform="translate(0 -2)" />
      <circle cx="50" cy="94" r="11" fill={t.base} stroke={t.line} strokeWidth="1" />
      <circle cx="150" cy="94" r="11" fill={t.base} stroke={t.line} strokeWidth="1" />
      <circle cx="47" cy="90" r="3.5" fill={t.light} />
      <circle cx="147" cy="90" r="3.5" fill={t.light} />
    </g>
  );
}

function Column({ t }) {
  return (
    <g>
      <path d="M62 54 L28 132 L44 232 L76 150 Z" fill={t.dark} />
      <path d="M138 54 L172 132 L156 232 L124 150 Z" fill={t.dark} />
      <path d="M72 36 Q100 50 128 36 L138 74 L130 126 L146 246 H54 L70 126 L62 74 Z" fill={t.base} />
      <path d="M84 40 Q100 62 116 40" {...sw} stroke={t.line} strokeWidth="1.2" />
      <path d="M100 62 V246" {...sw} stroke={t.line} strokeWidth="1" opacity=".5" />
      <path d="M70 126 H130" {...sw} stroke={t.line} strokeWidth="1.2" />
    </g>
  );
}

function Sheath({ t }) {
  return (
    <g>
      <path d="M70 34 L112 44 L134 36 L140 84 L130 132 L148 248 H56 L70 132 L62 80 Z" fill={t.base} />
      <path d="M70 34 L134 36 L112 44 Z" fill={t.dark} />
      <path d="M62 80 L140 84 M70 132 H130" {...sw} stroke={t.line} strokeWidth="1.1" />
      <path d="M112 44 L90 120 L110 246" {...sw} stroke={t.line} strokeWidth="1.2" />
      <path d="M62 80 C50 120 56 190 56 248 L84 248 C80 190 78 130 90 100 Z" fill={t.dark} opacity=".6" />
    </g>
  );
}

const GARMENTS = {
  blazer: (t) => <Blazer t={t} />,
  field: (t) => <Blazer t={t} field />,
  pant: (t) => <Pant t={t} />,
  knit: (t) => <Knit t={t} />,
  tote: (t) => <Tote t={t} />,
  coat: (t) => <Coat t={t} />,
  boot: (t) => <Boot t={t} />,
  scarf: (t) => <Scarf t={t} />,
  collar: (t) => <Collar t={t} />,
  column: (t) => <Column t={t} />,
  sheath: (t) => <Sheath t={t} />,
};

export function Garment({ shape, hex }) {
  const draw = GARMENTS[shape] ?? GARMENTS.blazer;
  return draw(tones(hex));
}
