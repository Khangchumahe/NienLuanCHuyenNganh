/**
 * Dữ liệu mẫu cho catalog. Khi có backend, chỉ cần thay các hàm ở cuối file
 * (getProduct / listProducts) bằng lời gọi API — các trang không cần sửa.
 *
 * `shape` chọn hình minh hoạ (xem components/garments.jsx).
 * Có ảnh thật thì thêm `image: '/img/ten.jpg'` (hoặc mảng `gallery`) → tự dùng ảnh thật,
 * ảnh lỗi/không tải được thì tự quay về hình minh hoạ.
 */

export const COLORS = {
  noir: { label: 'Noir', hex: '#171717', tint: '#d6d3d1' },
  ecru: { label: 'Ecru', hex: '#c9bfa7', tint: '#ece7dc' },
  camel: { label: 'Camel', hex: '#b48a5a', tint: '#e6d3b8' },
  olive: { label: 'Olive', hex: '#6b6f45', tint: '#d9dbc2' },
  espresso: { label: 'Espresso', hex: '#3b2a20', tint: '#dccdc2' },
};

/** Bảng màu "trung tính" dùng cho AI Palette Sync */
export const NEUTRALS = ['noir', 'ecru', 'camel', 'espresso'];

export const SIZES = [34, 36, 38, 40, 42, 44];

export const CATEGORIES = [
  { id: 'blazers', label: 'Tailored Blazers' },
  { id: 'trousers', label: 'Pleated Trousers' },
  { id: 'cashmere', label: 'Vicuña & Cashmere' },
  { id: 'footwear', label: 'Atelier Footwear' },
  { id: 'bags', label: 'Structured Leather Bags' },
  { id: 'evening', label: 'Outerwear & Evening' },
  { id: 'accessories', label: 'Atelier Accessories' },
];

export const CRAFTS = [
  { id: 'gots', label: 'GOTS Certified Virgin Wool' },
  { id: 'cashmere', label: 'Fair-Trade Mongolian Cashmere' },
  { id: 'tuscan', label: 'Vegetable-Tanned Tuscan Calf' },
];

export const OCCASIONS = [
  { id: 'salon', label: 'Atelier Salon' },
  { id: 'travel', label: 'Metropolitan Travel' },
  { id: 'vernissage', label: 'Evening Vernissage' },
];

export const PRICE_MIN = 300;
export const PRICE_MAX = 3500;

const care = 'Dry clean only by a certified atelier. Store on the supplied cedar hanger inside the linen garment envelope.';

export const PRODUCTS = [
  {
    id: 'double-breasted-blazer',
    name: 'Double-Breasted Wool Oversized Blazer',
    kind: 'Tailoring', material: 'Virgin Wool', category: 'blazers', shape: 'blazer',
    price: 1280, ai: 98, status: 'Atelier in-stock', added: 9,
    colors: ['noir', 'camel'], sizes: [34, 36, 38, 40, 42, 44],
    craft: ['gots'], occasions: ['salon', 'travel'],
    short: 'Structured architectural shoulder with a sculpted double-breasted closure.',
    description:
      'A masterwork of proportion: a structured architectural shoulder, deep double-breasted closure and a hand-canvassed chest that holds its line from salon to street. Cut oversized through the body, finished with hand-stitched pick-seams.',
    composition: '100% GOTS certified virgin wool twill, silk-cupro lining', care,
  },
  {
    id: 'pleated-silk-pant',
    name: 'Pleated Silk Wide-Leg Pant',
    kind: 'Trousers', material: 'Mulberry Silk', category: 'trousers', shape: 'pant',
    price: 890, ai: 95, status: 'Only 4 remaining', added: 7,
    colors: ['ecru', 'noir'], sizes: [34, 36, 38, 40, 42],
    craft: [], occasions: ['salon', 'vernissage'],
    short: 'High-rise waistband with inverted pleats and a fluid, floor-grazing leg.',
    description:
      'High-rise waistband, inverted pleats and a fluid wide leg that moves like a drape. Cut from heavyweight mulberry silk crepe with a hidden grosgrain waist stay for an architectural, effortless fall.',
    composition: 'Heavyweight mulberry silk crepe, 100% silk lining', care,
  },
  {
    id: 'sculpted-cashmere-turtleneck',
    name: 'Sculpted Cashmere Turtleneck',
    kind: 'Knitwear', material: '100% Cashmere', category: 'cashmere', shape: 'knit',
    price: 760, ai: 99, status: 'Atelier in-stock', added: 8,
    colors: ['camel', 'ecru', 'espresso'], sizes: [34, 36, 38, 40, 42, 44],
    craft: ['cashmere'], occasions: ['travel', 'salon'],
    short: 'Heavyweight 7-gauge pure Inner Mongolian cashmere with a sculpted roll neck.',
    description:
      'Heavyweight 7-gauge pure Inner Mongolian cashmere, fully fashioned for a sculpted roll neck that stands on its own. Dense, soft and made to be worn for decades.',
    composition: '100% Fair-Trade Mongolian cashmere (7-gauge)', care: 'Hand wash cold or restorative steam at any Atelier salon. Dry flat.',
  },
  {
    id: 'minimalist-leather-tote',
    name: 'Structured Minimalist Leather Tote',
    kind: 'Leather Goods', material: 'Hand-Stitched', category: 'bags', shape: 'tote',
    price: 1450, ai: 91, status: 'Limited edition', added: 6, limited: true,
    colors: ['espresso', 'noir', 'camel'], sizes: [],
    craft: ['tuscan'], occasions: ['travel', 'salon'],
    short: 'Vegetable-tanned full-grain leather, stitched by hand in a single sitting.',
    description:
      'Vegetable-tanned full-grain Tuscan calf, cut as a single architectural volume and stitched by one artisan in a single sitting. Unlined, numbered and designed to take on a patina that is yours alone.',
    composition: 'Vegetable-tanned Tuscan calf, brass hardware, linen thread', care: 'Condition twice a year with the atelier balm. Keep away from prolonged moisture.',
  },
  {
    id: 'cocoon-wool-coat',
    name: 'Cocoon Double-Faced Wool Coat',
    kind: 'Outerwear', material: 'Double-Faced', category: 'evening', shape: 'coat',
    price: 1390, ai: 96, status: 'Atelier in-stock', added: 10,
    colors: ['camel', 'noir', 'olive'], sizes: [34, 36, 38, 40, 42, 44],
    craft: ['gots'], occasions: ['travel', 'vernissage'],
    short: 'Hand-finished perimeter seams, drop shoulder and a cocoon silhouette.',
    description:
      'Double-faced virgin wool with hand-finished perimeter seams and no lining to hide behind. A drop shoulder and cocoon volume wrap the body in calm, architectural warmth.',
    composition: '100% double-faced GOTS virgin wool', care,
  },
  {
    id: 'square-toe-ankle-boot',
    name: 'Chiseled Square-Toe Ankle Boot',
    kind: 'Footwear', material: 'Made in Marche', category: 'footwear', shape: 'boot',
    price: 690, ai: 94, status: 'Atelier in-stock', added: 5,
    colors: ['noir', 'espresso'], sizes: [36, 37, 38, 39, 40, 41], sizesLabel: 'EU',
    craft: ['tuscan'], occasions: ['salon', 'travel'],
    short: '50mm stacked architectural wooden heel, hand-lasted in Marche.',
    description:
      'Lasted by hand in the Marche region, with a chiseled square toe and a 50mm stacked architectural wooden heel. Goodyear-welted, resoleable and polished to a deep, quiet shine.',
    composition: 'Vegetable-tanned calf upper, leather lining, hand-stacked wooden heel', care: 'Polish with neutral cream. Resoling available at all salons.',
  },
  {
    id: 'cashmere-fringe-scarf',
    name: 'Cashmere Fringe Scarf',
    kind: 'Accessories', material: 'Raw Edge', category: 'cashmere', shape: 'scarf',
    price: 320, ai: 93, status: 'In stock at Cambon', added: 4,
    colors: ['camel', 'ecru'], sizes: [],
    craft: ['cashmere'], occasions: ['travel', 'salon'],
    short: '100% Mongolian combed cashmere with a raw, hand-knotted edge.',
    description: 'Mongolian combed cashmere, loomed wide and finished with a raw, hand-knotted fringe. Balances the collar of a wool coat with tonal depth.',
    composition: '100% Fair-Trade Mongolian combed cashmere', care: 'Hand wash cold or restorative steam at any Atelier salon.',
  },
  {
    id: 'sculpted-heel-boots',
    name: 'Sculpted Heel Calfskin Boots',
    kind: 'Footwear', material: 'Hand-Polished', category: 'footwear', shape: 'boot',
    price: 690, ai: 92, status: '1 pair in FR 38', added: 3,
    colors: ['espresso', 'noir'], sizes: [36, 37, 38, 39, 40, 41], sizesLabel: 'EU',
    craft: ['tuscan'], occasions: ['vernissage', 'salon'],
    short: 'Hand-polished espresso calfskin on a sculpted 65mm heel.',
    description: 'A sculpted 65mm heel in hand-polished espresso calfskin. Grounds a fluid silhouette with architectural poise.',
    composition: 'Vegetable-tanned Tuscan calfskin, leather sole', care: 'Polish with neutral cream.',
  },
  {
    id: 'brass-torc-collar',
    name: 'Cast Brass Torc Collar',
    kind: 'Accessories', material: 'Lost-Wax Bronze', category: 'accessories', shape: 'collar',
    price: 380, ai: 90, status: 'Atelier edition', added: 2,
    colors: ['camel'], sizes: [],
    craft: [], occasions: ['vernissage', 'salon'],
    short: 'Hand-cast sculptural collar in satin-lustre lost-wax bronze.',
    description: 'A handmade sculptural accent cast by the lost-wax method and finished to a satin lustre. Sits at the collar break of a tailored overcoat.',
    composition: 'Lost-wax cast bronze, satin finish', care: 'Wipe with a dry cloth.',
  },
  {
    id: 'cape-back-column',
    name: 'Cape-Back Sculpted Column',
    kind: 'Evening', material: 'Italian Barathéa', category: 'evening', shape: 'column',
    price: 2850, ai: 97, status: 'Look 18 • Nocturne', added: 11, limited: true,
    colors: ['noir', 'espresso'], sizes: [34, 36, 38, 40, 42],
    craft: ['gots'], occasions: ['vernissage'],
    short: 'Virgin Italian wool barathéa with bonded silk faille facing.',
    description: 'Razor-sharp shoulder construction and a cape back in virgin Italian wool barathéa with bonded silk faille facing. Crisp structural volume instead of embellishment.',
    composition: 'Virgin Italian wool barathéa, bonded silk faille facing', care,
  },
  {
    id: 'asymmetric-faille-sheath',
    name: 'Asymmetric Faille Sheath',
    kind: 'Evening', material: 'French Silk Crepe', category: 'evening', shape: 'sheath',
    price: 3200, ai: 90, status: 'Look 07 • Alabaster', added: 12, limited: true,
    colors: ['ecru'], sizes: [34, 36, 38, 40, 42],
    craft: [], occasions: ['vernissage'],
    short: 'Heavy French silk crepe with a concealed shoulder armature.',
    description: 'Heavy French silk crepe cut on an asymmetric line, with a concealed shoulder armature that holds the silhouette without a single visible seam.',
    composition: 'Heavy French silk crepe, concealed boned armature', care,
  },
  {
    id: 'olive-field-jacket',
    name: 'Olive Gabardine Field Jacket',
    kind: 'Outerwear', material: 'Cotton Gabardine', category: 'evening', shape: 'field',
    price: 980, ai: 88, status: 'Atelier in-stock', added: 1,
    colors: ['olive'], sizes: [36, 38, 40, 42, 44],
    craft: [], occasions: ['travel'],
    short: 'Dense Japanese gabardine cut as a tailored field jacket.',
    description: 'Dense Japanese cotton gabardine, cut as a tailored field jacket with a cinched waist and horn buttons.',
    composition: '100% Japanese cotton gabardine, horn buttons', care,
  },
];

/* ------------------------------------------------------------------ */
/* Truy xuất dữ liệu – nơi duy nhất cần đổi khi nối backend            */
/* ------------------------------------------------------------------ */
export const getProduct = (id) => PRODUCTS.find((p) => p.id === id);
export const listProducts = () => PRODUCTS;
export const categoryLabel = (id) => CATEGORIES.find((c) => c.id === id)?.label ?? id;

/** Chuẩn hoá cỡ: giày dùng EU, còn lại dùng FR */
export const sizeLabel = (p, s) => (p.sizesLabel ? `EU ${s}` : `FR ${s}`);

export const LOOKS = [
  { id: 'look-18', no: 'LOOK 18', collection: 'Nocturne', title: 'The Garnier Column', note: 'Cape-back volume, collarbones open for a severe metal cuff.', items: ['cape-back-column', 'brass-torc-collar', 'sculpted-heel-boots'] },
  { id: 'look-07', no: 'LOOK 07', collection: 'Alabaster', title: 'Faille in Motion', note: 'An asymmetric sheath that photographs like sculpture.', items: ['asymmetric-faille-sheath', 'sculpted-heel-boots'] },
  { id: 'look-03', no: 'LOOK 03', collection: 'Solitude', title: 'Architectural Solitude', note: 'Double-breasted tailoring over liquid silk.', items: ['double-breasted-blazer', 'pleated-silk-pant', 'square-toe-ankle-boot'] },
  { id: 'look-11', no: 'LOOK 11', collection: 'Metropolitan', title: 'Cocoon & Cashmere', note: 'A cocoon coat layered with a sculpted roll neck.', items: ['cocoon-wool-coat', 'sculpted-cashmere-turtleneck', 'cashmere-fringe-scarf'] },
  { id: 'look-14', no: 'LOOK 14', collection: 'Travel', title: 'The Tuscan Carry', note: 'Field jacket, cashmere and a tote that ages beautifully.', items: ['olive-field-jacket', 'sculpted-cashmere-turtleneck', 'minimalist-leather-tote'] },
  { id: 'look-21', no: 'LOOK 21', collection: 'Vernissage', title: 'Brass & Noir', note: 'Noir tailoring finished with a cast bronze collar.', items: ['double-breasted-blazer', 'brass-torc-collar', 'square-toe-ankle-boot'] },
];
