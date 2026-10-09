import { createContext, useContext } from "react";
import type { BenchSessionSnapshot } from "./api.ts";

/**
 * C4 — contrato da sessão do operador no nível do cockpit (branch + workCenter).
 * Contexto/hook separados dos componentes para fast-refresh limpo.
 */

export type OperatorSessionStatus = "restoring" | "anonymous" | "identified";

export type OperatorSessionContextValue = {
  session: BenchSessionSnapshot | null;
  status: OperatorSessionStatus;
  /** Matrícula → sessão oficial. Lança ApiError com status do backend. */
  identify: (registration: string) => Promise<BenchSessionSnapshot>;
  logout: () => Promise<void>;
  /** 401 em qualquer operação → descarta a sessão local. */
  invalidate: () => void;
  openIdentify: () => void;
  /** Modal «Identificar operador» aberto — overlays suspendem o próprio close. */
  identifyOpen: boolean;
};

const defaultValue: OperatorSessionContextValue = {
  session: null,
  status: "anonymous",
  identify: () => Promise.reject(new Error("OperatorSessionProvider ausente.")),
  logout: () => Promise.resolve(),
  invalidate: () => undefined,
  openIdentify: () => undefined,
  identifyOpen: false,
};

export const OperatorSessionContext =
  createContext<OperatorSessionContextValue>(defaultValue);

export function useOperatorSession(): OperatorSessionContextValue {
  return useContext(OperatorSessionContext);
}
