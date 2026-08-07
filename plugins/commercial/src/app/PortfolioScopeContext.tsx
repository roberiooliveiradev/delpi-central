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
  canViewAnalytics: boolean;
  canViewProposals: boolean;
  canExportProposals: boolean;
  canUseTeamScope: boolean;
  canViewWorklistTeam: boolean;
  /** Id do usuário autenticado (JWT), mesmo sem carteira própria. */
  currentUserId: string | null;
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
  analytics_view: false,
  proposals_view: false,
  proposals_export: false,
  accounts_team_view: false,
  worklist_team_view: false,
  team_scope: false,
};

function resolveCapabilities(
  raw: SellerPortfolioMeCapabilities | undefined,
  admin: boolean,
): CommercialCapabilities {
  // manage implica team_scope na prática (G4); analytics/proposals NÃO herdam de admin.
  const teamScope = Boolean(raw?.team_scope ?? admin);
  return {
    worklist_view: Boolean(raw?.worklist_view),
    followups_manage: Boolean(raw?.followups_manage),
    seller_portfolios_manage: Boolean(raw?.seller_portfolios_manage ?? admin),
    analytics_view: Boolean(raw?.analytics_view),
    proposals_view: Boolean(raw?.proposals_view),
    proposals_export: Boolean(raw?.proposals_export ?? raw?.proposals_view),
    accounts_team_view: Boolean(raw?.accounts_team_view ?? teamScope),
    worklist_team_view: Boolean(raw?.worklist_team_view),
    team_scope: teamScope,
  };
}

type SellerPortfolioMeCapabilities = CommercialCapabilities;

export function PortfolioScopeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [capabilities, setCapabilities] = useState<CommercialCapabilities>(EMPTY_CAPABILITIES);
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
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
        const fromMe = (response.user_id || "").trim();
        const fromPortfolio = (response.portfolio?.user_id || "").trim();
        setCurrentUserId(fromMe || fromPortfolio || null);
        setMyPortfolio(response.portfolio);
        const nextCapabilities = resolveCapabilities(response.capabilities, admin);
        setCapabilities(nextCapabilities);

        if (nextCapabilities.team_scope || admin) {
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
        setCurrentUserId(null);
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
      canViewAnalytics: capabilities.analytics_view,
      canViewProposals: capabilities.proposals_view,
      canExportProposals: capabilities.proposals_export,
      canUseTeamScope: capabilities.team_scope,
      canViewWorklistTeam: capabilities.worklist_team_view,
      currentUserId,
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
      currentUserId,
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
