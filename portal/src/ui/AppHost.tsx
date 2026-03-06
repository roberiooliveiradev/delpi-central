// src/ui/AppHost.tsx
import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem, RouteItem } from "../data/coreApi";
import { pushRecentApp } from "../utils/recentApps";

function normalize(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

async function loadFederatedContainer(entryUrl: string) {
  const mod: any = await import(/* @vite-ignore */ entryUrl);

  if (mod?.get) return mod;
  if (mod?.default?.get) return mod.default;

  throw new Error(`remoteEntry carregou, mas não expôs container.get(): ${entryUrl}`);
}

function getViteFederationShareScope() {
  const w = window as any;
  return w.__federation_shared__?.default ?? w.__federation_shared__ ?? {};
}

export const AppHost = () => {
  const { apps, token, refreshToken } = useContext(AuthContext);

  const location = useLocation();
  const navigate = useNavigate();

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const federatedHostRef = useRef<HTMLDivElement>(null);
  const mountedModuleRef = useRef<any>(null);

  const [federatedError, setFederatedError] = useState<string | null>(null);

  const app = useMemo(() => {
    return apps.find((a: AppItem) => {
      const base = normalize(a.basePath);
      return location.pathname === base || location.pathname.startsWith(base + "/");
    }) ?? null;
  }, [apps, location.pathname]);

  const route = useMemo<RouteItem | null>(() => {
    if (!app) return null;
    return app.routes?.find((r) => r.path === location.pathname) ?? null;
  }, [app, location.pathname]);

  const resolvedEntry = useMemo<string | undefined>(() => {
    if (!app) return undefined;

    const routeEntry = route?.entry?.trim();

    if (routeEntry) return routeEntry;
    if (app.entryUrl?.trim()) return app.entryUrl.trim();

    return undefined;
  }, [app, route]);

  useEffect(() => {
    if (app?.id) {
      pushRecentApp(app.id);
    }
  }, [app]);

  useEffect(() => {
    if (!app) return;
    if (app.renderMode !== "external") return;
    if (!resolvedEntry) return;

    window.open(resolvedEntry, "_blank", "noopener,noreferrer");
    navigate("/", { replace: true });
  }, [app, resolvedEntry, navigate]);

  useEffect(() => {
    if (!token) return;
    if (!iframeRef.current) return;
    if (!app || app.renderMode !== "embedded") return;

    iframeRef.current.contentWindow?.postMessage(
      { type: "DELPI_AUTH", token },
      window.location.origin
    );
  }, [token, app, location.pathname]);

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;

      if (event.data?.type === "DELPI_REFRESH_REQUEST") {
        refreshToken();
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [refreshToken]);

  useEffect(() => {
    let isActive = true;

    async function mountFederated() {
      setFederatedError(null);

      if (!app) return;
      if (app.renderMode !== "federated") return;

      if (!resolvedEntry) {
        setFederatedError("entryUrl não definido.");
        return;
      }

      if (!federatedHostRef.current) return;

      federatedHostRef.current.innerHTML = "";

      try {
        const container = await loadFederatedContainer(resolvedEntry);

        if (typeof container.init === "function") {
          const shareScope = getViteFederationShareScope();
          try {
            await container.init(shareScope);
          } catch {
            //
          }
        }

        if (!isActive) return;

        const exposedModule = (app as any).exposedModule ?? "./App";

        const factory = await container.get(exposedModule);
        const mod = factory?.();

        if (!mod?.mount) {
          throw new Error(`Módulo exposto "${exposedModule}" não possui mount().`);
        }

        const props = {
          token,
          basePath: app.basePath,
          pathname: location.pathname,
          search: location.search,
        };

        mod.mount(federatedHostRef.current, props);
        mountedModuleRef.current = mod;
      } catch (e: any) {
        setFederatedError(e?.message ?? String(e));
      }
    }

    mountFederated();

    return () => {
      isActive = false;

      if (mountedModuleRef.current?.unmount) {
        try {
          mountedModuleRef.current.unmount();
        } catch {
          //
        }
      }

      mountedModuleRef.current = null;

      if (federatedHostRef.current) {
        federatedHostRef.current.innerHTML = "";
      }
    };
  }, [app, resolvedEntry, location.pathname, location.search, token]);

  useEffect(() => {
    if (!token) return;
    if (!mountedModuleRef.current) return;

    if (typeof mountedModuleRef.current.updateToken === "function") {
      mountedModuleRef.current.updateToken(token);
    } else {
      window.dispatchEvent(
        new CustomEvent("DELPI_TOKEN_UPDATE", {
          detail: { token },
        })
      );
    }
  }, [token]);

  if (!app) return <div>App não encontrado.</div>;

  if (app.renderMode === "external") {
    return <div>Abrindo aplicação...</div>;
  }

  if (app.renderMode === "embedded") {
    if (!resolvedEntry) return <div>entryUrl não definido.</div>;

    return (
      <iframe
        key={location.pathname}
        ref={iframeRef}
        title={route?.label || app.name}
        src={resolvedEntry}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
        }}
      />
    );
  }

  if (app.renderMode === "federated") {
    return (
      <div>
        {federatedError ? (
          <div style={{ padding: 12 }}>
            <b>Falha ao carregar microfrontend</b>
            <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
              {federatedError}
            </div>
          </div>
        ) : null}

        <div ref={federatedHostRef} />
      </div>
    );
  }

  return <div>Modo não suportado.</div>;
};