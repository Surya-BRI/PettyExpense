import { Component, type ErrorInfo, type ReactNode } from 'react';

/** Last-resort catch for a render crash: shows a recovery screen instead of a blank page. */
export class ErrorBoundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state: { error: Error | null } = { error: null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="state-page">
        <div>
          <div className="code">Oops</div>
          <h2>Something went wrong on this page</h2>
          <p>The error has been logged in the browser console. Reloading usually fixes it; your data is safe on the server.</p>
          <div className="row" style={{ justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={() => window.location.reload()}>
              Reload page
            </button>
            <a className="btn" href="/">
              Go to dashboard
            </a>
          </div>
        </div>
      </div>
    );
  }
}
