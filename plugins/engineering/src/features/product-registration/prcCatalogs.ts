/** Catálogos oficiais da ficha técnica — máquina de estados explícita
 * por campo: `idle → loading → success | empty | error` (+ retry).
 *
 * Regras do contrato de UI:
 * - array vazio é estado `empty` legítimo, nunca erro de integração;
 * - `error` expõe retry e preserva o valor já selecionado;
 * - request obsoleta (retry/unmount/troca de etapa) é abortada e seu
 *   resultado nunca sobrescreve uma carga mais nova (guard por epoch);
 * - códigos são strings — zeros à esquerda preservados.
 *
 * Módulo framework-agnostic para ser testável sem DOM; o componente
 * assina via `useSyncExternalStore`. */

import {
  fetchPrcCatalog,
} from "./api/productRegistrationApi";

/* PRC-REF-023-F03 — helpers puros de catálogo migraram para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada com Minhas Solicitações; o store com fetch injetável
 * permanece local. */
import {
  catalogOptions,
  enumOptions,
  PRC_CATALOG_KINDS,
  withSelectedOption,
  type PrcCatalogOption,
} from "@delpi/plugin-ui/index";

export { catalogOptions, enumOptions, PRC_CATALOG_KINDS, withSelectedOption };
export type { PrcCatalogOption };

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
  /** `kind` do HomeApiError (unauthorized/forbidden/unavailable/…). */
  errorKind?: string;
};

export const PRC_CATALOG_PAGE_LIMIT = 500;

const IDLE_VIEW: PrcCatalogView = {
  status: "idle",
  options: [],
  hasMore: false,
};

type FetchCatalog = typeof fetchPrcCatalog;
type Listener = () => void;

export class PrcCatalogStore {
  private views = new Map<string, PrcCatalogView>();
  private snapshot = new Map<string, PrcCatalogView>();
  private seq = new Map<string, number>();
  private controllers = new Map<string, AbortController>();
  private listeners = new Set<Listener>();

  constructor(
    private readonly fetchCatalog: FetchCatalog = fetchPrcCatalog,
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
        const options = catalogOptions(env?.data?.items ?? []);
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
