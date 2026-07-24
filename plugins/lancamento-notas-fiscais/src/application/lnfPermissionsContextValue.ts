import { createContext } from "react";
import type { LnfPermissionFlags } from "../domain/permissions";

export type LnfPermissionsState = LnfPermissionFlags & {
  loading: boolean;
  error: string | null;
  userId: string | null;
  userName: string | null;
  refresh: () => void;
};

export const LnfPermissionsContext = createContext<LnfPermissionsState | null>(
  null,
);
