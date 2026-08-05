import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getMySellerPortfolio } from "../api/commercialPortfolioApi";
import type { SellerPortfolio } from "../types/portfolio";

type PortfolioScopeValue = {
  loading: boolean;
  error: string | null;
  isAdmin: boolean;
  myPortfolio: SellerPortfolio | null;
  reload: () => void;
};

const PortfolioScopeContext = createContext<PortfolioScopeValue | null>(null);

export function PortfolioScopeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [myPortfolio, setMyPortfolio] = useState<SellerPortfolio | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMySellerPortfolio(controller.signal)
      .then((response) => {
        setIsAdmin(Boolean(response.is_admin));
        setMyPortfolio(response.portfolio);
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Erro ao carregar carteira.");
        setIsAdmin(false);
        setMyPortfolio(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [reloadToken]);

  const value = useMemo(
    () => ({
      loading,
      error,
      isAdmin,
      myPortfolio,
      reload,
    }),
    [loading, error, isAdmin, myPortfolio, reload],
  );

  return (
    <PortfolioScopeContext.Provider value={value}>{children}</PortfolioScopeContext.Provider>
  );
}

export function usePortfolioScope(): PortfolioScopeValue {
  const context = useContext(PortfolioScopeContext);
  if (!context) {
    throw new Error("usePortfolioScope deve ser usado dentro de PortfolioScopeProvider.");
  }
  return context;
}
