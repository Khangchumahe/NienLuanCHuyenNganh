import { createContext, useContext, useEffect, useLayoutEffect, useMemo, useState } from 'react';

/**
 * Hash router tối giản (URL dạng  /#/catalog?cat=blazers ).
 * Không cần cài react-router; chạy được cả khi mở file tĩnh / deploy không cấu hình server.
 */

function readLocation() {
  const raw = window.location.hash.replace(/^#/, '') || '/';
  const [pathPart, queryPart = ''] = raw.split('?');
  const path = pathPart.startsWith('/') ? pathPart : `/${pathPart}`;
  return { path: path.length > 1 ? path.replace(/\/+$/, '') : path, query: Object.fromEntries(new URLSearchParams(queryPart)) };
}

const RouterContext = createContext({ path: '/', query: {} });

export function RouterProvider({ children }) {
  const [loc, setLoc] = useState(readLocation);

  useEffect(() => {
    const onChange = () => setLoc(readLocation());
    window.addEventListener('hashchange', onChange);
    return () => window.removeEventListener('hashchange', onChange);
  }, []);

  // Mỗi lần đổi trang → cuộn lên đầu
  useLayoutEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
  }, [loc.path]);

  return <RouterContext.Provider value={loc}>{children}</RouterContext.Provider>;
}

export const useRoute = () => useContext(RouterContext);

/** Điều hướng bằng code: navigate('/cart') hoặc navigate('/login', { replace: true }) */
export function navigate(to, { replace = false } = {}) {
  const target = `#${to.startsWith('/') ? to : `/${to}`}`;
  if (replace) window.location.replace(target);
  else window.location.hash = target;
}

export function Link({ to, children, className, onClick, ...rest }) {
  return (
    <a
      href={`#${to}`}
      className={className}
      onClick={(e) => {
        // Cùng URL thì hashchange không bắn → tự cuộn lên đầu cho cảm giác "bấm là có phản hồi"
        if (window.location.hash === `#${to}`) window.scrollTo({ top: 0, behavior: 'smooth' });
        onClick?.(e);
      }}
      {...rest}
    >
      {children}
    </a>
  );
}

export function Redirect({ to }) {
  useEffect(() => navigate(to, { replace: true }), [to]);
  return null;
}

function compile(pattern) {
  const keys = [];
  const source = pattern
    .replace(/\/+$/, '')
    .replace(/:([A-Za-z0-9_]+)/g, (_, k) => {
      keys.push(k);
      return '([^/]+)';
    });
  return { regex: new RegExp(`^${source || ''}/?$`), keys };
}

/** Tìm route khớp path → { route, params } */
export function matchRoute(routes, path) {
  for (const route of routes) {
    const { regex, keys } = compile(route.path);
    const m = path.match(regex);
    if (m) {
      const params = {};
      keys.forEach((k, i) => (params[k] = decodeURIComponent(m[i + 1])));
      return { route, params };
    }
  }
  return null;
}

export function useMatch(routes) {
  const { path } = useRoute();
  return useMemo(() => matchRoute(routes, path), [routes, path]);
}
