import React, { Component, ErrorInfo, ReactNode, StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.tsx';
import './index.css';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('React ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-tg-bg text-tg-text flex flex-col items-center justify-center p-6 text-center">
          <div className="max-w-sm w-full bg-tg-section border border-tg-secondary p-6 rounded-3xl space-y-4 shadow-lg">
            <div className="w-12 h-12 rounded-2xl bg-blue-500/15 text-blue-600 flex items-center justify-center mx-auto text-xl font-bold">
              🔄
            </div>
            <h2 className="text-base font-bold text-tg-text">Ilova yangilandi</h2>
            <p className="text-xs text-tg-hint">
              Eng so'nggi versiyani ochish uchun quyidagi tugmani bosing:
            </p>
            {this.state.error?.message && (
              <p className="text-[10px] text-rose-400 bg-rose-500/10 p-2 rounded-xl font-mono text-left overflow-auto max-h-24">
                {this.state.error.message}
              </p>
            )}
            <button
              onClick={() => {
                try {
                  localStorage.clear();
                  sessionStorage.clear();
                } catch {}
                window.location.reload();
              }}
              className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-md"
            >
              Qayta yuklash
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
