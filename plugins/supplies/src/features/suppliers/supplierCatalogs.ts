/**
 * Catálogos TOTVS do cadastro de fornecedores — acesso à BFF com cache
 * de rótulos por catálogo. A BFF é authority das opções; o MFE apenas
 * exibe descrições e envia os códigos previstos no contrato.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { httpGet, suppliesApiUrl } from "../../api/httpClient";
import type { SupplierCatalogKind } from "./types";

export type SupplierCatalogOption = {
  code: string;
  label: string;
  disabled: boolean;
};

type CatalogEnvelope = {
  catalog: string;
  items: SupplierCatalogOption[];
  has_more: boolean;
  total: number;
};

/**
 * Catálogos carregados por completo em uma única chamada (listas
 * pequenas/médias) — usados com filtro local no `SuppliesSelectField`.
 */
export const PRELOAD_CATALOG_LIMIT = 500;
export const REMOTE_CATALOG_LIMIT = 50;
export const REMOTE_SEARCH_MIN_CHARS = 0;

const PRELOAD_KINDS = new Set<SupplierCatalogKind>([
  "states",
  "countries",
  "bacen-countries",
  "payment-conditions",
  "payment-methods",
  "financial-natures",
]);

export function isPreloadCatalog(kind: SupplierCatalogKind): boolean {
  return PRELOAD_KINDS.has(kind);
}

function catalogUrl(
  kind: SupplierCatalogKind,
  opts: { query?: string; state?: string; limit?: number },
): string {
  const params = new URLSearchParams();
  if (opts.query?.trim()) params.set("query", opts.query.trim());
  if (opts.state?.trim()) params.set("state", opts.state.trim().toUpperCase());
  params.set("limit", String(opts.limit ?? PRELOAD_CATALOG_LIMIT));
  return suppliesApiUrl(
    `/suppliers/catalogs/${kind}?${params.toString()}`,
  );
}

/** Cache de rótulos resolvidos: kind → code → label (alimenta VIEW/REVIEW). */
const _labelCache = new Map<string, Map<string, string>>();

export function catalogLabelOf(
  kind: SupplierCatalogKind,
  code: string,
): string | null {
  const labels = _labelCache.get(kind);
  if (!labels) return null;
  const hit = labels.get(code.trim());
  return hit ?? null;
}

function rememberLabels(
  kind: SupplierCatalogKind,
  items: SupplierCatalogOption[],
): void {
  let labels = _labelCache.get(kind);
  if (!labels) {
    labels = new Map();
    _labelCache.set(kind, labels);
  }
  for (const item of items) {
    if (!labels.has(item.code)) labels.set(item.code, item.label);
  }
}

export function fetchCatalogItems(
  kind: SupplierCatalogKind,
  opts: { query?: string; state?: string; limit?: number },
  signal?: AbortSignal,
): Promise<CatalogEnvelope> {
  return httpGet<CatalogEnvelope>(catalogUrl(kind, opts), { signal }).then(
    (env) => {
      rememberLabels(kind, env.items ?? []);
      return env;
    },
  );
}

const _preloadCache = new Map<string, Promise<SupplierCatalogOption[]>>();

function preloadKey(kind: SupplierCatalogKind, state?: string): string {
  return `${kind}|${(state ?? "").trim().toUpperCase()}`;
}

/** Catálogo pequeno/médio — uma chamada cacheada por kind (+UF quando há). */
export function loadCatalogOptions(
  kind: SupplierCatalogKind,
  opts: { state?: string; limit?: number } = {},
): Promise<SupplierCatalogOption[]> {
  const key = preloadKey(kind, opts.state);
  let pending = _preloadCache.get(key);
  if (!pending) {
    pending = fetchCatalogItems(kind, {
      state: opts.state,
      limit: opts.limit ?? PRELOAD_CATALOG_LIMIT,
    })
      .then((env) => env.items)
      .catch((err) => {
        _preloadCache.delete(key);
        throw err;
      });
    _preloadCache.set(key, pending);
  }
  return pending;
}

type CatalogOptionsState = {
  options: SupplierCatalogOption[];
  loading: boolean;
  error: boolean;
};

/**
 * Opções de um catálogo preload (lista completa, filtrada no cliente pelo
 * `SuppliesSelectField`). `state` vale para catálogos dependentes de UF.
 */
export function useCatalogOptions(
  kind: SupplierCatalogKind,
  opts: { state?: string; enabled?: boolean } = {},
): CatalogOptionsState {
  const enabled = opts.enabled !== false;
  const stateKey = (opts.state ?? "").trim().toUpperCase();
  const key = preloadKey(kind, stateKey);
  const [result, setResult] = useState<{
    key: string;
    options: SupplierCatalogOption[];
    error: boolean;
  } | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    loadCatalogOptions(kind, { state: stateKey })
      .then((options) => {
        if (alive) setResult({ key, options, error: false });
      })
      .catch(() => {
        if (alive) setResult({ key, options: [], error: true });
      });
    return () => {
      alive = false;
    };
  }, [kind, stateKey, enabled, key]);

  const mine = result && result.key === key ? result : null;
  return {
    options: mine?.options ?? [],
    loading: enabled && !mine,
    error: mine?.error ?? false,
  };
}

/**
 * Pesquisa remota com debounce — catálogos grandes (conta contábil,
 * municípios). Resultados limitados pelo backend (`REMOTE_CATALOG_LIMIT`).
 */
export function useCatalogSearch(
  kind: SupplierCatalogKind,
  opts: { state?: string; enabled?: boolean } = {},
): {
  options: SupplierCatalogOption[];
  hasMore: boolean;
  loading: boolean;
  error: boolean;
  search: (query: string) => void;
} {
  const enabled = opts.enabled !== false;
  const stateKey = (opts.state ?? "").trim().toUpperCase();
  const key = preloadKey(kind, stateKey);
  const [result, setResult] = useState<{
    key: string;
    options: SupplierCatalogOption[];
    hasMore: boolean;
    error: boolean;
    phase: "loading" | "done";
  } | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const seqRef = useRef(0);

  const run = useCallback(
    (query: string) => {
      if (!enabled) return;
      const seq = ++seqRef.current;
      setResult({
        key,
        options: [],
        hasMore: false,
        error: false,
        phase: "loading",
      });
      fetchCatalogItems(kind, {
        query,
        state: stateKey,
        limit: REMOTE_CATALOG_LIMIT,
      })
        .then((env) => {
          if (seq !== seqRef.current) return;
          setResult({
            key,
            options: env.items,
            hasMore: Boolean(env.has_more),
            error: false,
            phase: "done",
          });
        })
        .catch(() => {
          if (seq !== seqRef.current) return;
          setResult({
            key,
            options: [],
            hasMore: false,
            error: true,
            phase: "done",
          });
        });
    },
    [kind, stateKey, enabled, key],
  );

  const search = useCallback(
    (query: string) => {
      if (timerRef.current) clearTimeout(timerRef.current);
      setResult((current) =>
        current && current.key === key
          ? { ...current, phase: "loading" }
          : { key, options: [], hasMore: false, error: false, phase: "loading" },
      );
      timerRef.current = setTimeout(() => run(query.trim()), 250);
    },
    [key, run],
  );

  useEffect(() => {
    if (!enabled) return;
    const id = setTimeout(() => run(""), 0);
    return () => {
      clearTimeout(id);
      if (timerRef.current) clearTimeout(timerRef.current);
      seqRef.current += 1;
    };
  }, [enabled, run]);

  const mine = result && result.key === key ? result : null;
  return {
    options: mine?.options ?? [],
    hasMore: mine?.hasMore ?? false,
    loading: enabled && (!mine || mine.phase === "loading"),
    error: mine?.error ?? false,
    search,
  };
}

/**
 * Resolve o rótulo de um código já salvo — usado no modo consulta.
 * Preload: consulta o mapa local; remoto: busca `?query=<code>` e casa exato.
 */
export function useCatalogLabel(
  kind: SupplierCatalogKind,
  code: string,
  opts: { state?: string } = {},
): string | null {
  const trimmed = code.trim();
  const stateKey = (opts.state ?? "").trim().toUpperCase();
  const known = catalogLabelOf(kind, trimmed);
  const key = `${kind}|${stateKey}|${trimmed}`;
  const [remote, setRemote] = useState<{
    key: string;
    label: string | null;
  } | null>(null);

  useEffect(() => {
    if (!trimmed || known) return;
    let alive = true;
    const pending = isPreloadCatalog(kind)
      ? loadCatalogOptions(kind, { state: stateKey }).then(
          (items) => items.find((o) => o.code === trimmed)?.label ?? null,
        )
      : fetchCatalogItems(kind, {
          query: trimmed,
          state: stateKey,
          limit: REMOTE_CATALOG_LIMIT,
        }).then(
          (env) => env.items.find((o) => o.code === trimmed)?.label ?? null,
        );
    pending
      .then((label) => {
        if (alive) setRemote({ key, label });
      })
      .catch(() => {
        if (alive) setRemote({ key, label: null });
      });
    return () => {
      alive = false;
    };
  }, [kind, trimmed, stateKey, known, key]);

  if (!trimmed) return null;
  return known ?? (remote && remote.key === key ? remote.label : null);
}
