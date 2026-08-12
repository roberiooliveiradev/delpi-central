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
  canViewWorklist: boolean;
  canManageFollowups: boolean;
  canViewAnalytics: boolean;
  canViewProposals: boolean;
  canExportProposals: boolean;
  canUseTeamScope: boolean;
  canViewAccountsTeam: boolean;
  canViewWorklistTeam: boolean;
  /** Minha Carteira: membership, team.view ou manage. */
  canAccessMyPortfolio: boolean;
  /** Id do usuário autenticado (JWT), mesmo sem carteira própria. */
  currentUserId: string | null;
  /** Compat single-portfolio: primeira carteira de `myPortfolios`. */
  myPortfolio: SellerPortfolio | null;
  /** Todas as carteiras em que o usuário é owner ou member. */
  myPortfolios: SellerPortfolio[];
  sellers: SellerPortfolio[];
  /**
   * Pode escolher carteira: team/manage (universo equipe) ou
   * mais de uma carteira própria.
   */
  canFilterPortfolios: boolean;
  /** Universo do seletor de carteira: equipe → todas; senão → carteiras próprias. */
  filterablePortfolios: SellerPortfolio[];
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

/** Confia no payload da API — não inventa team.view a partir de admin. */
function resolveCapabilities(
  raw: SellerPortfolioMeCapabilities | undefined,
): CommercialCapabilities {
  return {
    worklist_view: Boolean(raw?.worklist_view),
    followups_manage: Boolean(raw?.followups_manage),
    seller_portfolios_manage: Boolean(raw?.seller_portfolios_manage),
    analytics_view: Boolean(raw?.analytics_view),
    proposals_view: Boolean(raw?.proposals_view),
    proposals_export: Boolean(raw?.proposals_export ?? raw?.proposals_view),
    accounts_team_view: Boolean(raw?.accounts_team_view),
    worklist_team_view: Boolean(raw?.worklist_team_view),
    team_scope: Boolean(raw?.team_scope),
  };
}

type SellerPortfolioMeCapabilities = CommercialCapabilities;

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

        const canListAll =
          nextCapabilities.team_scope ||
          nextCapabilities.seller_portfolios_manage ||
          admin;
        if (canListAll) {
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
        setMyPortfolios([]);
        setSellers([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [reloadToken]);

  const value = useMemo(() => {
    const canManagePortfolios =
      capabilities.seller_portfolios_manage || isAdmin;
    const canUseTeamScope = Boolean(capabilities.team_scope);
    const canViewAccountsTeam = Boolean(capabilities.accounts_team_view);
    const filterablePortfolios = canUseTeamScope ? sellers : myPortfolios;
    const canAccessMyPortfolio =
      myPortfolios.length > 0 || canUseTeamScope || canManagePortfolios;
    return {
      loading,
      error,
      isAdmin: canManagePortfolios,
      canManagePortfolios,
      canViewWorklist: capabilities.worklist_view,
      canManageFollowups: capabilities.followups_manage,
      canViewAnalytics: capabilities.analytics_view,
      canViewProposals: capabilities.proposals_view,
      canExportProposals: capabilities.proposals_export,
      canUseTeamScope,
      canViewAccountsTeam,
      canViewWorklistTeam: capabilities.worklist_team_view,
      canAccessMyPortfolio,
      currentUserId,
      myPortfolio: myPortfolios[0] ?? null,
      myPortfolios,
      sellers,
      canFilterPortfolios: canUseTeamScope || myPortfolios.length > 1,
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
