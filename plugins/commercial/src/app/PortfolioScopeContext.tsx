import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getMySellerPortfolio, listSellerPortfolios } from "../api/commercialPortfolioApi";
import type { CommercialCapabilities, SellerPortfolio } from "../types/portfolio";

type PortfolioScopeValue = {
  loading: boolean;
  error: string | null;
  isAdmin: boolean;
  canViewWorklist: boolean;
  canManageFollowups: boolean;
  myPortfolio: SellerPortfolio | null;
  sellers: SellerPortfolio[];
  sellerIdFilter: string | null;
  setSellerIdFilter: (sellerId: string | null) => void;
  reload: () => void;
  reloadScope: () => void;
};

const PortfolioScopeContext = createContext<PortfolioScopeValue | null>(null);

const EMPTY_CAPABILITIES: CommercialCapabilities = {
  worklist_view: false,
  followups_manage: false,
  seller_portfolios_manage: false,
};

export function PortfolioScopeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [capabilities, setCapabilities] = useState<CommercialCapabilities>(EMPTY_CAPABILITIES);
  const [myPortfolio, setMyPortfolio] = useState<SellerPortfolio | null>(null);
  const [sellers, setSellers] = useState<SellerPortfolio[]>([]);
  const [sellerIdFilter, setSellerIdFilterState] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => {
    setReloadToken((value) => value + 1);
  }, []);

  const setSellerIdFilter = useCallback((sellerId: string | null) => {
    setSellerIdFilterState(sellerId && sellerId.trim() ? sellerId : null);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    getMySellerPortfolio(controller.signal)
      .then(async (response) => {
        const admin = Boolean(response.is_admin);
        setIsAdmin(admin);
        setMyPortfolio(response.portfolio);
        setCapabilities({
          worklist_view: Boolean(response.capabilities?.worklist_view),
          followups_manage: Boolean(response.capabilities?.followups_manage),
          seller_portfolios_manage: Boolean(
            response.capabilities?.seller_portfolios_manage ?? admin,
          ),
        });

        if (admin) {
          const portfolios = await listSellerPortfolios({
            activeOnly: true,
            signal: controller.signal,
          });
          setSellers(portfolios);
        } else {
          setSellers([]);
          setSellerIdFilterState(null);
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar carteira.");
        setIsAdmin(false);
        setCapabilities(EMPTY_CAPABILITIES);
        setMyPortfolio(null);
        setSellers([]);
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
      canViewWorklist: capabilities.worklist_view,
      canManageFollowups: capabilities.followups_manage,
      myPortfolio,
      sellers,
      sellerIdFilter,
      setSellerIdFilter,
      reload,
      reloadScope: reload,
    }),
    [
      loading,
      error,
      isAdmin,
      capabilities,
      myPortfolio,
      sellers,
      sellerIdFilter,
      setSellerIdFilter,
      reload,
    ],
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
