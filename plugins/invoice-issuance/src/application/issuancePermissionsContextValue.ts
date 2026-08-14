import { createContext } from "react";
import type { IssuancePermissionFlags } from "../domain/permissions";

export type IssuancePermissionsState = IssuancePermissionFlags & {
  loading: boolean;
  error: string | null;
  userId: string | null;
  userName: string | null;
  refresh: () => void;
};

export const IssuancePermissionsContext =
  createContext<IssuancePermissionsState | null>(null);
