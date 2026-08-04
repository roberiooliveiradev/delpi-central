import { useContext } from "react";

import {
  PortfolioScopeContext,
  type PortfolioScopeContextValue,
} from "./portfolioScopeContextValue";

export function usePortfolioScope(): PortfolioScopeContextValue {
  const ctx = useContext(PortfolioScopeContext);
  if (!ctx) {
    throw new Error("usePortfolioScope deve ser usado dentro de PortfolioScopeProvider.");
  }
  return ctx;
}
