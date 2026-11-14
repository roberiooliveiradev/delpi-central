/** Contexto das bandeiras de produto acompanhado — separado dos
 * componentes para manter o módulo de UI exportando só componentes
 * (fast refresh). */

import { createContext, useContext } from "react";

import type { PrcRecordFlag } from "../api/productRegistrationApi";
import type { FlagTargetContext } from "./PrcFlagModal";

export type ProductFlagsCtx = {
  recordId: string;
  flags: PrcRecordFlag[];
  /** Ações permitidas pelo backend no corte atual (vazio em revisão
   * histórica — snapshots são imutáveis). */
  allowedActions: string[];
  isCurrentRevision: boolean;
  reload: () => void;
  openTarget: (
    target: FlagTargetContext,
    flag?: PrcRecordFlag | null,
  ) => void;
};

export const PrcProductFlagsCtx =
  createContext<ProductFlagsCtx | null>(null);

export function usePrcProductFlags(): ProductFlagsCtx {
  const ctx = useContext(PrcProductFlagsCtx);
  if (!ctx) {
    throw new Error(
      "usePrcProductFlags fora de PrcProductFlagsProvider",
    );
  }
  return ctx;
}
