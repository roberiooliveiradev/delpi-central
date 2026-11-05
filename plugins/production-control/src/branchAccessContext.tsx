import { createContext, useContext, type ReactNode } from "react";

import type { PpcBranch } from "./types";
import { ALL_PPC_BRANCHES } from "./utils/branchAccess";

const PpcAllowedBranchesContext = createContext<readonly PpcBranch[]>(ALL_PPC_BRANCHES);

export function PpcAllowedBranchesProvider({
  allowedBranches,
  children,
}: {
  allowedBranches: readonly PpcBranch[];
  children: ReactNode;
}) {
  return (
    <PpcAllowedBranchesContext.Provider value={allowedBranches}>
      {children}
    </PpcAllowedBranchesContext.Provider>
  );
}

/** Filiais exibíveis no seletor — nunca inventar filial fora do RBAC. */
export function useAllowedPpcBranches(): readonly PpcBranch[] {
  return useContext(PpcAllowedBranchesContext);
}
