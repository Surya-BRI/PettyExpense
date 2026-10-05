import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react';
import { ToastContext, type ToastTone } from '../lib/toast';
import { Icon } from './Icon';

interface ToastItem {
  id: number;
  message: string;
  tone: ToastTone;
}

const DISMISS_MS = 4500;

export function Toaster({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(1);

  const dismiss = useCallback((id: number) => setItems((xs) => xs.filter((t) => t.id !== id)), []);
  const show = useCallback(
    (message: string, tone: ToastTone = 'success') => {
      const id = nextId.current++;
      // Keep at most 3 on screen; newest at the bottom.
      setItems((xs) => [...xs.slice(-2), { id, message, tone }]);
      setTimeout(() => dismiss(id), DISMISS_MS);
    },
    [dismiss],
  );
  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toasts" aria-live="polite" aria-atomic="false">
        {items.map((t) => (
          <div key={t.id} className={`toast ${t.tone}`} role={t.tone === 'error' ? 'alert' : 'status'}>
            <div className="toast-body">{t.message}</div>
            <button className="toast-close" onClick={() => dismiss(t.id)} aria-label="Dismiss">
              <Icon name="close" size={16} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
