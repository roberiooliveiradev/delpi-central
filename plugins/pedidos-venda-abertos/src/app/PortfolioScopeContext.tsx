import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { getMySellerPortfolio, listSellerPortfolios } from "../api/sellerPortfolioApi";
import type { SellerPortfolio } from "../types/sellerPortfolio";
import {
  PortfolioScopeContext,
  type PortfolioScopeContextValue,
} from "./portfolioScopeContextValue";

export function PortfolioScopeProvider({ children }: { children: ReactNode }) {
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [myPortfolio, setMyPortfolio] = useState<SellerPortfolio | null>(null);
  const [sellers, setSellers] = useState<SellerPortfolio[]>([]);
  const [sellerIdFilter, setSellerIdFilter] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reloadScope = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function run() {
      setLoading(true);
      try {
        const me = await getMySellerPortfolio(controller.signal);
        if (controller.signal.aborted) return;
        setIsAdmin(Boolean(me.is_admin));
        setMyPortfolio(me.portfolio);
        if (me.is_admin) {
          const items = await listSellerPortfolios({
            activeOnly: true,
            signal: controller.signal,
          });
          if (!controller.signal.aborted) {
            setSellers(items);
          }
        } else {
          setSellers([]);
          setSellerIdFilter(null);
        }
      } catch {
        if (!controller.signal.aborted) {
          setIsAdmin(false);
          setMyPortfolio(null);
          setSellers([]);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }
    void run();
    return () => controller.abort();
  }, [reloadKey]);

  const value = useMemo<PortfolioScopeContextValue>(
    () => ({
      loading,
      isAdmin,
      myPortfolio,
      sellers,
      sellerIdFilter,
      setSellerIdFilter,
      reloadScope,
    }),
    [loading, isAdmin, myPortfolio, sellers, sellerIdFilter, reloadScope],
  );

  return (
    <PortfolioScopeContext.Provider value={value}>{children}</PortfolioScopeContext.Provider>
  );
}
