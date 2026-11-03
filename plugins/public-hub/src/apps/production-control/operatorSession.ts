import { ApiError, type BenchSessionSnapshot } from "./api.ts";

/**
 * C4 — sessão do operador por posto (branch + workCenter).
 * Módulo puro/testável: storage, validação de matrícula e mapeamento de erro.
 * O token da sessão fica em sessionStorage (escopo da aba) — nunca localStorage.
 */

const SESSION_STORAGE_PREFIX = "delpi.pcp.cockpit.bench-session";
const MAX_REGISTRATION_LENGTH = 30;

export function sessionStorageKey(branch: string, workCenter: string): string {
  return `${SESSION_STORAGE_PREFIX}.${branch}.${workCenter}`;
}

export function readStoredSession(
  branch: string,
  workCenter: string,
): BenchSessionSnapshot | null {
  try {
    const raw = window.sessionStorage.getItem(sessionStorageKey(branch, workCenter));
    if (!raw) return null;
    return JSON.parse(raw) as BenchSessionSnapshot;
  } catch {
    return null;
  }
}

export function storeSession(
  branch: string,
  workCenter: string,
  session: BenchSessionSnapshot | null,
): void {
  try {
    const key = sessionStorageKey(branch, workCenter);
    if (session) window.sessionStorage.setItem(key, JSON.stringify(session));
    else window.sessionStorage.removeItem(key);
  } catch {
    /* modo privado sem storage */
  }
}

/**
 * Matrícula é texto: trim externo, não vazia, máx. 30 chars.
 * "001" permanece "001" — nunca conversão numérica.
 */
export function normalizeRegistration(input: string): string | null {
  const value = input.trim();
  if (!value || value.length > MAX_REGISTRATION_LENGTH) return null;
  return value;
}

/** Mensagem pública por status do backend (sem expor detalhes de S2S). */
export function identifyErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 404) return "Matrícula não encontrada.";
    if (err.status === 403) {
      return "Esta matrícula não está ativa no cadastro de colaboradores.";
    }
    if (err.status === 503) {
      return "Não foi possível validar a matrícula no momento. Tente novamente.";
    }
    if (err.status === 422) {
      return err.message || "Matrícula inválida.";
    }
  }
  return "Não foi possível validar a matrícula no momento. Tente novamente.";
}
