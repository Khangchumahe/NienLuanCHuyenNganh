import { useState } from 'react';
import { COLORS } from '../data/products';
import { Garment } from './garments';

/**
 * Ảnh sản phẩm.
 * - product.image / product.gallery có → dùng ảnh thật (lỗi tải thì rơi về hình minh hoạ).
 * - Không có → hình minh hoạ trang phục theo màu đang chọn.
 * `variant` 0-3 dùng cho thư viện ảnh ở trang chi tiết.
 */
export default function ProductImage({ product, color, variant = 0, className = '', label = true }) {
  const [broken, setBroken] = useState(false);
  const real = product.gallery?.[variant] ?? (variant === 0 ? product.image : null);
  if (real && !broken) {
    return <img src={real} alt={product.name} onError={() => setBroken(true)} className={`h-full w-full object-cover ${className}`} />;
  }

  const c = COLORS[color ?? product.colors[0]] ?? COLORS.noir;
  const grid = `linear-gradient(${c.hex}1f 1px, transparent 1px), linear-gradient(90deg, ${c.hex}1f 1px, transparent 1px)`;
  const swatch = `repeating-linear-gradient(45deg, ${c.hex}55 0 1.5px, transparent 1.5px 10px)`;

  return (
    <div
      className={`relative h-full w-full overflow-hidden transition-colors duration-500 ${className}`}
      style={{ background: `radial-gradient(120% 90% at 50% 25%, #ffffff66, transparent 60%), ${c.tint}` }}
      role="img"
      aria-label={product.name}
    >
      <div className="absolute inset-0 opacity-60" style={{ backgroundImage: variant === 2 ? swatch : grid, backgroundSize: variant === 2 ? 'auto' : '40px 40px' }} />

      {variant === 2 ? (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="display bg-white/80 px-4 py-2 text-center text-lg text-stone-900">{product.material}</span>
        </div>
      ) : (
        <>
          {/* bóng đổ sàn */}
          {variant !== 1 && <div className="absolute bottom-[6%] left-1/2 h-[4%] w-[55%] -translate-x-1/2 rounded-[50%] bg-black/15 blur-md" />}
          <svg
            viewBox="0 0 200 260"
            preserveAspectRatio="xMidYMid meet"
            className="absolute inset-0 h-full w-full transition-transform duration-500"
            style={{
              padding: variant === 1 ? 0 : '7% 8% 9%',
              transform: variant === 1 ? 'scale(2) translateY(22%)' : variant === 3 ? 'rotate(-10deg) scale(.9)' : undefined,
              transformOrigin: variant === 1 ? '50% 0%' : 'center',
              filter: 'drop-shadow(0 6px 8px rgba(0,0,0,.12))',
            }}
            aria-hidden="true"
          >
            <Garment shape={product.shape} hex={c.hex} />
          </svg>
        </>
      )}

      {label && (
        <span className="eyebrow absolute bottom-3 left-4 z-10 !text-[10px] opacity-70" style={{ color: c.hex }}>
          {variant === 0 ? `Ref. ${product.id.slice(0, 3).toUpperCase()}-${product.price}` : `View 0${variant + 1}`}
        </span>
      )}
    </div>
  );
}
