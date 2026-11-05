/**
 * Cache em memória das consultas do Portal Controladoria & Finanças.
 *
 * O cliente é singleton de módulo: desmontar o React não apaga o cache.
 * A publicação de um resultado só ocorre se a geração capturada no
 * início da consulta ainda for a geração ativa.
 */
import {
  QueryClient,
  type Query,
  type QueryKey,
} from "@tanstack/react-query";

import { ApiError } from "../api/httpClient";
import {
  REPORT_GC_TIME_MS,
  type ReportCacheScope,
} from "./reportQueryKeys";

export type GuardedResult<T> =
  | { kind: "ready"; data: T; fetchedAt: number }
  | { kind: "not_opened" }
  | { kind: "forbidden" }
  | { kind: "unauthorized" };

type ScopeListener = () => void;

let client: QueryClient | null = null;
let generation = 0;
/**
 * Barreira de publicação. 403 incrementa esta barreira sem selar a
 * sessão e sem trocar a chave: consultas já iniciadas não gravam
 * payload financeiro depois da negativa.
 */
let publicationEpoch = 0;
let active: ReportCacheScope | null = null;
let sealed = false;
let sealedSubject: string | null = null;
const listeners = new Set<ScopeListener>();

function isProtectedDenial(data: unknown): boolean {
  if (!data || typeof data !== "object") return false;
  const kind = (data as { kind?: string }).kind;
  return kind === "forbidden" || kind === "unauthorized";
}

/** Erro técnico volta a ser buscado só depois do frescor da própria fonte. */
function retryTechnicalErrorOnMount(query: Query): boolean {
  if (query.state.status !== "error") return true;
  const staleTime = (query.options as { staleTime?: unknown }).staleTime;
  const windowMs = typeof staleTime === "number" ? staleTime : 0;
  return Date.now() - query.state.errorUpdatedAt >= windowMs;
}

/** 401/403 já gravados não disparam novo GET automático. */
function refetchUnlessDenied(query: Query): boolean {
  return !isProtectedDenial(query.state.data);
}

export function getReportQueryClient(): QueryClient {
  if (!client) client = createReportQueryClient();
  return client;
}

export function createReportQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        retryOnMount: retryTechnicalErrorOnMount,
        refetchOnMount: refetchUnlessDenied,
        refetchOnWindowFocus: refetchUnlessDenied,
        refetchOnReconnect: refetchUnlessDenied,
        gcTime: REPORT_GC_TIME_MS,
        structuralSharing: true,
      },
    },
  });
}

export function getReportCacheGeneration(): number {
  return generation;
}

export function getActiveReportCacheScope(): ReportCacheScope | null {
  return active;
}

export function isReportSessionSealed(): boolean {
  return sealed;
}

export function subscribeReportCacheScope(listener: ScopeListener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function emit(): void {
  for (const listener of listeners) listener();
}

function replaceClientEmpty(): void {
  const current = client;
  if (!current) return;
  current.cancelQueries();
  current.clear();
}

/** Lê `sub` do access token só como discriminador. Não valida assinatura. */
export function readTokenSubject(token: string | undefined): string | null {
  if (!token) return null;
  const parts = token.split(".");
  if (parts.length < 2 || !parts[1]) return null;
  try {
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), "=");
    const payload = JSON.parse(atob(padded)) as { sub?: unknown };
    return typeof payload.sub === "string" && payload.sub.length > 0
      ? payload.sub
      : null;
  } catch {
    return null;
  }
}

export function authzFingerprint(
  permissions: readonly string[] | undefined,
  isSuperadmin: boolean | undefined,
): string {
  const codes = [...(permissions ?? [])].map((code) => code.trim()).filter(Boolean).sort();
  return `${isSuperadmin ? "1" : "0"}:${codes.join("\n")}`;
}

/**
 * Adota o contexto observável antes dos filhos consultarem.
 * Mesmo `sub` e mesmo fingerprint preservam a geração e o cache.
 */
export function reconcileReportCacheScope(
  subject: string | null,
  fingerprint: string,
): ReportCacheScope | null {
  if (sealed) {
    if (subject && subject !== sealedSubject) {
      sealed = false;
      sealedSubject = null;
      generation += 1;
      replaceClientEmpty();
      active = { subject, authzFingerprint: fingerprint, generation };
      return active;
    }
    return null;
  }

  if (!subject) {
    if (active) {
      generation += 1;
      replaceClientEmpty();
      active = null;
    }
    return null;
  }

  if (
    active &&
    active.subject === subject &&
    active.authzFingerprint === fingerprint &&
    active.generation === generation
  ) {
    return active;
  }

  generation += 1;
  replaceClientEmpty();
  active = { subject, authzFingerprint: fingerprint, generation };
  return active;
}

export function sealReportSession(subject: string | null = active?.subject ?? null): void {
  if (sealed && sealedSubject === subject) return;
  sealed = true;
  sealedSubject = subject;
  generation += 1;
  active = null;
  replaceClientEmpty();
  emit();
}

export function resetReportQueryCacheForTests(): void {
  client?.cancelQueries();
  client?.clear();
  client = null;
  generation = 0;
  publicationEpoch = 0;
  active = null;
  sealed = false;
  sealedSubject = null;
  emit();
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function isReadyFinancial(data: unknown): boolean {
  return Boolean(
    data &&
      typeof data === "object" &&
      (data as { kind?: string }).kind === "ready",
  );
}

function discardOtherFinancialQueries(currentKey: QueryKey): void {
  getReportQueryClient().removeQueries({
    predicate: (query: Query) =>
      JSON.stringify(query.queryKey) !== JSON.stringify(currentKey) &&
      isReadyFinancial(query.state.data),
  });
}

function abortStalePublication(): never {
  throw new DOMException("Aborted", "AbortError");
}

/**
 * Executa a leitura e só devolve payload financeiro se a geração
 * e a barreira de publicação capturadas ainda forem as ativas.
 * 401 sela a sessão. 403 preserva a sessão, descarta financeiros
 * já gravados e impede que uma leitura anterior publique depois.
 */
export async function guardReportQuery<T>(
  scope: ReportCacheScope,
  queryKey: QueryKey,
  signal: AbortSignal,
  read: (signal: AbortSignal) => Promise<T>,
  options?: { notOpened?: (error: ApiError) => boolean; emptyIsNotOpened?: boolean },
): Promise<GuardedResult<T>> {
  const started = scope.generation;
  const startedEpoch = publicationEpoch;
  if (sealed || started !== generation) abortStalePublication();
  try {
    const data = await read(signal);
    if (sealed || started !== generation) abortStalePublication();
    if (startedEpoch !== publicationEpoch) return { kind: "forbidden" };
    if (signal.aborted) abortStalePublication();
    if (options?.emptyIsNotOpened && (data === null || data === undefined)) {
      return { kind: "not_opened" };
    }
    return { kind: "ready", data, fetchedAt: Date.now() };
  } catch (error) {
    if (isAbortError(error)) throw error;
    if (sealed || started !== generation) abortStalePublication();
    if (error instanceof ApiError && error.status === 401) {
      sealReportSession(scope.subject);
      return { kind: "unauthorized" };
    }
    if (error instanceof ApiError && error.status === 403) {
      if (startedEpoch === publicationEpoch) {
        publicationEpoch += 1;
        discardOtherFinancialQueries(queryKey);
      }
      return { kind: "forbidden" };
    }
    if (startedEpoch !== publicationEpoch) return { kind: "forbidden" };
    if (signal.aborted) abortStalePublication();
    if (
      error instanceof ApiError &&
      options?.notOpened?.(error)
    ) {
      return { kind: "not_opened" };
    }
    throw error;
  }
}
