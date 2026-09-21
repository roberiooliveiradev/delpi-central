import { ensurePortalFederationShareScope } from "../utils/federationShareScope";
import type { FederatedAppRouteProp } from "./appHostEntry";

/** Frozen Portal → federated MFE host props (presentation / transport only). */
export type FederatedHostProps = {
  getAccessToken: () => string | undefined;
  basePath: string;
  pathname: string;
  search: string;
  alternateEntry?: string;
  appRoutes: FederatedAppRouteProp[];
  routeLabel?: string;
  permissions?: string[];
  isSuperadmin?: boolean;
};

export type FederatedRemoteModule = {
  mount: (el: HTMLElement, props: FederatedHostProps) => void;
  updateRoute?: (el: HTMLElement, props: FederatedHostProps) => void;
  unmount?: (el?: HTMLElement) => void;
};

export type FederatedContainerLoader = (entryUrl: string) => Promise<unknown>;

export async function loadFederatedContainer(entryUrl: string) {
  const mod: any = await import(/* @vite-ignore */ entryUrl);

  if (mod?.get) return mod;
  if (mod?.default?.get) return mod.default;

  throw new Error(`remoteEntry carregou, mas não expôs container.get(): ${entryUrl}`);
}

export function getViteFederationShareScope() {
  const w = window as any;
  return w.__federation_shared__?.default ?? w.__federation_shared__ ?? {};
}

export async function loadFederatedExposedModule(
  entryUrl: string,
  exposedModule = "./App",
  loadContainer: FederatedContainerLoader = loadFederatedContainer,
): Promise<FederatedRemoteModule> {
  ensurePortalFederationShareScope();

  const container = (await loadContainer(entryUrl)) as {
    init?: (shareScope: unknown) => Promise<void> | void;
    get: (id: string) => Promise<unknown> | unknown;
  };

  if (typeof container.init === "function") {
    try {
      await container.init(getViteFederationShareScope());
    } catch {
      // Alguns remotes podem já estar inicializados.
    }
  }

  const factory = await container.get(exposedModule);
  const mod = (await Promise.resolve(
    typeof factory === "function" ? factory() : factory,
  )) as FederatedRemoteModule;

  if (!mod?.mount) {
    throw new Error(`Módulo exposto "${exposedModule}" não possui mount().`);
  }

  return mod;
}

export function updateFederatedRemote(
  mod: FederatedRemoteModule,
  el: HTMLElement,
  props: FederatedHostProps,
) {
  if (typeof mod.updateRoute === "function") {
    mod.updateRoute(el, props);
    return;
  }

  if (typeof mod.mount === "function") {
    mod.mount(el, props);
  }
}

export function unmountFederatedRemote(
  mod: FederatedRemoteModule | null | undefined,
  el?: HTMLElement | null,
) {
  if (!mod?.unmount) return;

  try {
    mod.unmount(el ?? undefined);
  } catch {
    // Evita quebrar o host por falha no cleanup do plugin.
  }
}

export type FederatedMountSession = {
  mount: (
    el: HTMLElement,
    entryUrl: string,
    props: FederatedHostProps,
    exposedModule?: string,
  ) => Promise<void>;
  updateRoute: (props: FederatedHostProps) => void;
  unmount: () => void;
  isMounted: () => boolean;
  entryUrl: () => string | null;
  exposedModule: () => string | null;
};

export function createFederatedMountSession(options?: {
  loadModule?: typeof loadFederatedExposedModule;
}): FederatedMountSession {
  const loadModule = options?.loadModule ?? loadFederatedExposedModule;
  let generation = 0;
  let module: FederatedRemoteModule | null = null;
  let mountEl: HTMLElement | null = null;
  let currentEntry: string | null = null;
  let currentExposed: string | null = null;

  return {
    async mount(el, entryUrl, props, exposedModule = "./App") {
      this.unmount();
      const ownGeneration = ++generation;

      let loaded: FederatedRemoteModule;
      try {
        loaded = await loadModule(entryUrl, exposedModule);
      } catch (error) {
        if (ownGeneration !== generation) return;
        throw error;
      }

      if (ownGeneration !== generation) return;

      mountEl = el;
      currentEntry = entryUrl;
      currentExposed = exposedModule;
      module = loaded;
      mountEl.innerHTML = "";
      module.mount(mountEl, props);
    },
    updateRoute(props) {
      if (!module || !mountEl) return;
      updateFederatedRemote(module, mountEl, props);
    },
    unmount() {
      generation += 1;
      const el = mountEl;
      const mounted = module;
      module = null;
      mountEl = null;
      currentEntry = null;
      currentExposed = null;
      unmountFederatedRemote(mounted, el);
      if (el) {
        el.innerHTML = "";
      }
    },
    isMounted() {
      return module !== null;
    },
    entryUrl() {
      return currentEntry;
    },
    exposedModule() {
      return currentExposed;
    },
  };
}
