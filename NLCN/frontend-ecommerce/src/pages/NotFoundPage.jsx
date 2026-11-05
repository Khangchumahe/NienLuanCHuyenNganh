import { Link } from '../lib/router';

export default function NotFoundPage() {
  return (
    <div className="shell flex flex-col items-center py-32 text-center">
      <p className="eyebrow mb-3">Error 404</p>
      <h1 className="display text-6xl">This salon does not exist</h1>
      <p className="mt-4 max-w-md text-sm leading-6 text-zinc-700">The page you are looking for has moved, or never was. Let us return you to the collection.</p>
      <div className="mt-8 flex gap-3">
        <Link to="/" className="btn-primary">Back to the storefront</Link>
        <Link to="/catalog" className="btn-outline">Explore the catalog</Link>
      </div>
    </div>
  );
}
