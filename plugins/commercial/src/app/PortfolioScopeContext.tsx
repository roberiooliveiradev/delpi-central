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
  canManagePortfolios: boolean;
  /** Derivado de commercial.access — produto (tarefas, analytics, propostas). */
  canViewWorklist: boolean;
  canManageFollowups: boolean;
  canViewAnalytics: boolean;
  canViewProposals: boolean;
  canExportProposals: boolean;
  /** Derivado de commercial.manage — todas as carteiras. */
  canUseTeamScope: boolean;
  canViewAccountsTeam: boolean;
  canViewWorklistTeam: boolean;
  /** Minha Carteira: membership ou manage. */
  canAccessMyPortfolio: boolean;
  canBillingNotify: boolean;
  /** Id do usuário autenticado (JWT), mesmo sem carteira própria. */
  currentUserId: string | null;
  /** Compat single-portfolio: primeira carteira de `myPortfolios`. */
  myPortfolio: SellerPortfolio | null;
  /** Todas as carteiras em que o usuário é owner ou member. */
  myPortfolios: SellerPortfolio[];
  sellers: SellerPortfolio[];
  /**
   * Pode escolher carteira: manage (universo equipe) ou
   * mais de uma carteira própria.
   */
  canFilterPortfolios: boolean;
  /** Universo do seletor de carteira: manage → todas; senão → carteiras próprias. */
  filterablePortfolios: SellerPortfolio[];
  sellerIdFilter: string | null;
  setSellerIdFilter: (sellerId: string | null) => void;
  reload: () => void;
  reloadScope: () => void;
};

const PortfolioScopeContext = createContext<PortfolioScopeValue | null>(null);

const EMPTY_CAPABILITIES: CommercialCapabilities = {
  access: false,
  manage: false,
  billing_notify: false,
};

function resolveCapabilities(
  raw: CommercialCapabilities | undefined,
): CommercialCapabilities {
  return {
    access: Boolean(raw?.access),
    manage: Boolean(raw?.manage),
    billing_notify: Boolean(raw?.billing_notify),
  };
}

export function PortfolioScopeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [capabilities, setCapabilities] = useState<CommercialCapabilities>(EMPTY_CAPABILITIES);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [myPortfolios, setMyPortfolios] = useState<SellerPortfolio[]>([]);
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
        const fromMe = (response.user_id || "").trim();
        const fromPortfolio = (response.portfolio?.user_id || "").trim();
        setCurrentUserId(fromMe || fromPortfolio || null);
        setMyPortfolios(
          response.portfolios?.length
            ? response.portfolios
            : response.portfolio
              ? [response.portfolio]
              : [],
        );
        const nextCapabilities = resolveCapabilities(response.capabilities);
        setCapabilities(nextCapabilities);

        const canListAll = nextCapabilities.manage || admin;
        if (canListAll) {
          const portfolios = await listSellerPortfolios({
            activeOnly: true,
            signal: controller.signal,
          });
          setSellers(portfolios);
        } else {
          setSellers([]);
          const mineIds = new Set(
            (
              response.portfolios?.length
                ? response.portfolios
                : response.portfolio
                  ? [response.portfolio]
                  : []
            )
              .map((portfolio) => portfolio.id)
              .filter(Boolean),
          );
          setSellerIdFilterState((current) =>
            current && mineIds.has(current) ? current : null,
          );
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar carteira.");
        setIsAdmin(false);
        setCapabilities(EMPTY_CAPABILITIES);
        setCurrentUserId(null);
        setMyPortfolios([]);
        setSellers([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [reloadToken]);

  const value = useMemo(() => {
    const canManagePortfolios = capabilities.manage || isAdmin;
    const hasAccess = Boolean(capabilities.access);
    const filterablePortfolios = canManagePortfolios ? sellers : myPortfolios;
    const canAccessMyPortfolio =
      myPortfolios.length > 0 || canManagePortfolios;
    return {
      loading,
      error,
      isAdmin: canManagePortfolios,
      canManagePortfolios,
      canViewWorklist: hasAccess,
      canManageFollowups: hasAccess,
      canViewAnalytics: hasAccess,
      canViewProposals: hasAccess,
      canExportProposals: hasAccess,
      canUseTeamScope: canManagePortfolios,
      canViewAccountsTeam: canManagePortfolios,
      canViewWorklistTeam: canManagePortfolios,
      canAccessMyPortfolio,
      canBillingNotify: Boolean(capabilities.billing_notify),
      currentUserId,
      myPortfolio: myPortfolios[0] ?? null,
      myPortfolios,
      sellers,
      canFilterPortfolios: canManagePortfolios || myPortfolios.length > 1,
      filterablePortfolios,
      sellerIdFilter,
      setSellerIdFilter,
      reload,
      reloadScope: reload,
    };
  }, [
    loading,
    error,
    isAdmin,
    capabilities,
    currentUserId,
    myPortfolios,
    sellers,
    sellerIdFilter,
    setSellerIdFilter,
    reload,
  ]);

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
