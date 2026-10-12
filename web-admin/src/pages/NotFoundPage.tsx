import { Link } from 'react-router-dom';
import { usePageTitle } from '../lib/usePageTitle';

export function NotFoundPage() {
  usePageTitle('Page not found');
  return (
    <div className="state-page">
      <div>
        <div className="code">404</div>
        <h2>We couldn’t find that page</h2>
        <p>The link may be old or mistyped. Head back to the dashboard to keep going.</p>
        <Link className="btn btn-primary" to="/">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
