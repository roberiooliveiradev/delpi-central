import { useContext } from "react";
import {
  LnfPermissionsContext,
  type LnfPermissionsState,
} from "./lnfPermissionsContextValue";

export function useLnfPermissions(): LnfPermissionsState {
  const ctx = useContext(LnfPermissionsContext);
  if (!ctx) {
    throw new Error(
      "useLnfPermissions deve ser usado dentro de LnfPermissionsProvider.",
    );
  }
  return ctx;
}
