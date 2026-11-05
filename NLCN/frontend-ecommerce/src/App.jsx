import { RouterProvider, Redirect, useMatch, useRoute } from './lib/router';
import { StoreProvider, useStore } from './context/StoreContext';
import Layout from './components/Layout';

import StorefrontandAI from './pages/StorefrontandAI';
import HomePage from './pages/HomePage';
import ProductDetailPage from './pages/ProductDetailPage';
import CartPage from './pages/CartPage';
import WishlistPage from './pages/WishlistPage';
import RunwayPage from './pages/RunwayPage';
import ChatbotWidget from './pages/ChabotWidget';
import LoginPage from './pages/LoginPage';
import AccountPage from './pages/AccountPage';
import ProfilePage from './pages/ProfilePage';
import OrderPage from './pages/OrderPage';
import NotFoundPage from './pages/NotFoundPage';

/**
 * Bảng route của toàn site.
 *   auth: true → cần đăng nhập (chưa đăng nhập sẽ chuyển sang /login rồi quay lại)
 *   bare: true → không dùng header/footer (màn hình đăng nhập)
 * Thêm trang mới = thêm một dòng ở đây.
 */
const ROUTES = [
  { path: '/', component: StorefrontandAI },
  { path: '/catalog', component: HomePage },
  { path: '/product/:id', component: ProductDetailPage },
  { path: '/cart', component: CartPage },
  { path: '/wishlist', component: WishlistPage },
  { path: '/runway', component: RunwayPage },
  { path: '/stylist', component: ChatbotWidget },
  { path: '/login', component: LoginPage, bare: true },
  { path: '/account', component: AccountPage, auth: true },
  { path: '/profile', component: ProfilePage, auth: true },
  { path: '/order', component: OrderPage },
  { path: '/order/:id', component: OrderPage },
];

function Routes() {
  const match = useMatch(ROUTES);
  const { path, query } = useRoute();
  const { user } = useStore();

  if (!match) return <Layout><NotFoundPage /></Layout>;

  const { route, params } = match;
  if (route.auth && !user) return <Redirect to={`/login?next=${encodeURIComponent(path)}`} />;

  const Page = route.component;
  return (
    <Layout bare={route.bare}>
      <Page params={params} query={query} />
    </Layout>
  );
}

export default function App() {
  return (
    <StoreProvider>
      <RouterProvider>
        <Routes />
      </RouterProvider>
    </StoreProvider>
  );
}
