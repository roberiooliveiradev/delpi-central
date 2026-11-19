import { createContext, useContext, type ReactNode } from "react";

import type { PpcBranch } from "./types";
import { ALL_PPC_BRANCHES } from "./utils/branchAccess";

const PpcAllowedBranchesContext = createContext<readonly PpcBranch[]>(ALL_PPC_BRANCHES);

type FeatureAccess = { canViewLineFeeder: boolean; canViewMyWeg: boolean };
const PpcFeatureAccessContext = createContext<FeatureAccess>({
  canViewLineFeeder: false,
  canViewMyWeg: false,
});

export function usePpcFeatureAccess(): FeatureAccess {
  return useContext(PpcFeatureAccessContext);
}

export function PpcAllowedBranchesProvider({
  allowedBranches,
  children,
  featureAccess = { canViewLineFeeder: false, canViewMyWeg: false },
}: {
  allowedBranches: readonly PpcBranch[];
  featureAccess?: FeatureAccess;
  children: ReactNode;
}) {
  return (
    <PpcAllowedBranchesContext.Provider value={allowedBranches}>
      <PpcFeatureAccessContext.Provider value={featureAccess}>
        {children}
      </PpcFeatureAccessContext.Provider>
    </PpcAllowedBranchesContext.Provider>
  );
}

/** Filiais exibíveis no seletor — nunca inventar filial fora do RBAC. */
export function useAllowedPpcBranches(): readonly PpcBranch[] {
  return useContext(PpcAllowedBranchesContext);
}
