/** PRC-REF-023-UX-PARITY-FIX-02 — store neutro de catálogos da ficha
 * técnica, fonte única para Portal Engenharia e Minhas Solicitações.
 * Máquina de estados por campo: idle → loading → success | empty | error
 * (+ retry). Fetch injetado — cada MFE passa seu client da
 * Engineering API; request obsoleta é abortada via guard por epoch.
 * Códigos são strings — zeros à esquerda preservados. */

import {
  catalogOptions,
  PRC_CATALOG_KINDS,
} from "./prcProductRegistration";
import type {
  PrcCatalogOption,
  PrcCatalogOptionItem,
} from "./prcProductRegistration";

export type PrcCatalogStatus =
  | "idle"
  | "loading"
  | "success"
  | "empty"
  | "error";

export type PrcCatalogView = {
  status: PrcCatalogStatus;
  options: PrcCatalogOption[];
  /** `true` quando a fonte paginou além do limite carregado. */
  hasMore: boolean;
  /** `kind` do erro HTTP (unauthorized/forbidden/unavailable/…). */
  errorKind?: string;
};

export const PRC_CATALOG_PAGE_LIMIT = 500;

const IDLE_VIEW: PrcCatalogView = {
  status: "idle",
  options: [],
  hasMore: false,
};

/** Contrato do fetcher injetado: envelope `{ data: { items, hasMore? } }`
 * como os clients PRC dos MFEs retornam. */
export type PrcCatalogFetcher = (
  kind: string,
  query: string | undefined,
  signal: AbortSignal | undefined,
  limit: number,
) => Promise<{
  data?: { items?: unknown[]; hasMore?: boolean };
}>;

type Listener = () => void;

export class PrcCatalogStore {
  private views = new Map<string, PrcCatalogView>();
  private snapshot = new Map<string, PrcCatalogView>();
  private seq = new Map<string, number>();
  private controllers = new Map<string, AbortController>();
  private listeners = new Set<Listener>();

  constructor(
    private readonly fetchCatalog: PrcCatalogFetcher,
    private readonly limit: number = PRC_CATALOG_PAGE_LIMIT,
  ) {}

  view(path: string): PrcCatalogView {
    return this.views.get(path) ?? IDLE_VIEW;
  }

  getSnapshot = (): Map<string, PrcCatalogView> => this.snapshot;

  subscribe = (listener: Listener): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  /** Dispara (ou recomeça) a carga de um catálogo — aborta a anterior. */
  load(path: string, signal?: AbortSignal): void {
    const kind = PRC_CATALOG_KINDS[path];
    if (!kind) return;

    this.controllers.get(path)?.abort();
    const controller = new AbortController();
    this.controllers.set(path, controller);
    const epoch = (this.seq.get(path) ?? 0) + 1;
    this.seq.set(path, epoch);
    const abortOnOuter = () => controller.abort();
    signal?.addEventListener("abort", abortOnOuter, { once: true });

    this.set(path, {
      ...this.view(path),
      status: "loading",
      errorKind: undefined,
    });

    void this.fetchCatalog(
      kind,
      undefined,
      controller.signal,
      this.limit,
    )
      .then((env) => {
        if (!this.isCurrent(path, epoch, controller)) return;
        const options = catalogOptions(
          (env?.data?.items ?? []) as PrcCatalogOptionItem[],
        );
        this.set(
          path,
          options.length
            ? {
                status: "success",
                options,
                hasMore: Boolean(env?.data?.hasMore),
              }
            : { status: "empty", options: [], hasMore: false },
        );
      })
      .catch((err: { kind?: string }) => {
        if (!this.isCurrent(path, epoch, controller)) return;
        this.set(path, {
          ...this.view(path),
          status: "error",
          errorKind: err?.kind,
        });
      })
      .finally(() => {
        signal?.removeEventListener("abort", abortOnOuter);
      });
  }

  loadAll(paths: Iterable<string>, signal?: AbortSignal): void {
    for (const path of paths) this.load(path, signal);
  }

  retry(path: string): void {
    this.load(path);
  }

  abortAll(): void {
    for (const controller of this.controllers.values()) controller.abort();
  }

  private isCurrent(
    path: string,
    epoch: number,
    controller: AbortController,
  ): boolean {
    return (
      this.seq.get(path) === epoch && !controller.signal.aborted
    );
  }

  private set(path: string, view: PrcCatalogView): void {
    this.views.set(path, view);
    this.snapshot = new Map(this.views);
    for (const listener of this.listeners) listener();
  }
}
