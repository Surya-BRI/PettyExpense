import { useEffect } from 'react';

/** Browser tab title, e.g. "All claims · Expense Tracker". */
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} · Expense Tracker` : 'Expense Tracker · Blue Rhine';
  }, [title]);
}
