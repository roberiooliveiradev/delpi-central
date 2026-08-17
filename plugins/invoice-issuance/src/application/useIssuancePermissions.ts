import { useContext } from "react";
import {
  IssuancePermissionsContext,
  type IssuancePermissionsState,
} from "./issuancePermissionsContextValue";

export function useIssuancePermissions(): IssuancePermissionsState {
  const ctx = useContext(IssuancePermissionsContext);
  if (!ctx) {
    throw new Error(
      "useIssuancePermissions deve ser usado dentro de IssuancePermissionsProvider.",
    );
  }
  return ctx;
}
