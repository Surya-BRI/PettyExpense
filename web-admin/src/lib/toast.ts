import { createContext, useContext } from 'react';

export type ToastTone = 'success' | 'error' | 'info';

export interface ToastApi {
  show: (message: string, tone?: ToastTone) => void;
}

export const ToastContext = createContext<ToastApi>({ show: () => {} });

/** `toast.show('Claim approved')` -- brief confirmation in the bottom-right corner. */
export const useToast = () => useContext(ToastContext);
