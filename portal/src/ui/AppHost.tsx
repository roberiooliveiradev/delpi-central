import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem, RouteItem } from "../data/coreApi";
import {
  isGoogleHostedApp,
  useGoogleEmbeddedAppLogin,
} from "../hooks/useGoogleEmbeddedAppLogin";
import { pushRecentApp } from "../utils/recentApps";
import {
  clearEmbeddedDeepLink,
  consumeEmbeddedDeepLink,
  peekEmbeddedDeepLink,
  pendingMatchesCurrentApp,
  portalPathMatchesAppBase,
} from "../utils/embeddedAppNotification";

function normalize(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

function getUrlOrigin(url: string | undefined) {
  if (!url) return window.location.origin;

  try {
    return new URL(url, window.location.origin).origin;
  } catch {
    return window.location.origin;
  }
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
  const { apps, getAccessToken, refreshToken } = useContext(AuthContext);

  const location = useLocation();
  const navigate = useNavigate();

  const iframeRef = useRef<HTMLIFrameElement>(null);
  const federatedHostRef = useRef<HTMLDivElement>(null);
  const mountedModuleRef = useRef<any>(null);

  const [federatedError, setFederatedError] = useState<string | null>(null);
  const [iframeReloadKey, setIframeReloadKey] = useState(0);

  const app = useMemo(() => {
    return (
      apps.find((a: AppItem) => {
        const base = normalize(a.basePath);
        return location.pathname === base || location.pathname.startsWith(base + "/");
      }) ?? null
    );
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

  const iframeSrc = useMemo(() => {
    if (!resolvedEntry) return undefined;

    const separator = resolvedEntry.includes("?") ? "&" : "?";
    return `${resolvedEntry}${separator}_delpiReload=${iframeReloadKey}`;
  }, [resolvedEntry, iframeReloadKey]);

  const isGoogleApp = useMemo(() => {
    return app?.renderMode === "embedded" && isGoogleHostedApp(resolvedEntry);
  }, [app?.renderMode, resolvedEntry]);

  function reloadIframe() {
    setIframeReloadKey((current) => current + 1);
  }

  function openAppInNewTab() {
    if (!resolvedEntry) return;
    window.open(resolvedEntry, "_blank", "noopener,noreferrer");
  }

  function postNavigateToIframe(path: string, onDelivered?: () => void) {
    if (!app || app.renderMode !== "embedded") return;
    if (!resolvedEntry) return;

    const normalized = path.startsWith("/") ? path : `/${path}`;
    const targetOrigin = getUrlOrigin(resolvedEntry);

    const send = () => {
      const win = iframeRef.current?.contentWindow;
      if (!win) return false;
      win.postMessage({ type: "DELPI_NAVIGATE", path: normalized }, targetOrigin);
      onDelivered?.();
      return true;
    };

    if (send()) return;

    let attempts = 0;
    const timer = window.setInterval(() => {
      attempts += 1;
      if (send() || attempts >= 15) {
        window.clearInterval(timer);
      }
    }, 200);
  }

  function trySendPendingEmbeddedNavigate() {
    const pending = peekEmbeddedDeepLink();
    if (!pending || !app) return;
    if (!pendingMatchesCurrentApp(pending, app.basePath)) return;

    postNavigateToIframe(pending.deepPath, () => {
      clearEmbeddedDeepLink();
    });
  }

  function sendAuthToIframe() {
    if (!iframeRef.current) return;
    if (!app || app.renderMode !== "embedded") return;
    if (!resolvedEntry) return;

    const token = getAccessToken();
    if (!token) return;

    iframeRef.current.contentWindow?.postMessage(
      { type: "DELPI_AUTH", token },
      getUrlOrigin(resolvedEntry)
    );

    window.setTimeout(trySendPendingEmbeddedNavigate, 200);
    window.setTimeout(trySendPendingEmbeddedNavigate, 600);
    window.setTimeout(trySendPendingEmbeddedNavigate, 1200);
  }

  function sendLogoutToIframe() {
    if (!iframeRef.current) return;
    if (!app || app.renderMode !== "embedded") return;
    if (!resolvedEntry) return;

    iframeRef.current.contentWindow?.postMessage(
      { type: "DELPI_LOGOUT" },
      getUrlOrigin(resolvedEntry)
    );
  }

  const googleLogin = useGoogleEmbeddedAppLogin({
    enabled: Boolean(isGoogleApp),
    pathname: location.pathname,
    resolvedEntry,
    onReloadIframe: reloadIframe,
  });

  useEffect(() => {
    if (app?.id) {
      pushRecentApp(app.id);
    }
  }, [app]);

  useEffect(() => {
    const isEmbedded = app?.renderMode === "embedded";
    document.body.classList.toggle("portal-has-embedded-app", !!isEmbedded);

    return () => {
      document.body.classList.remove("portal-has-embedded-app");
    };
  }, [app?.renderMode]);

  useEffect(() => {
    setIframeReloadKey(0);
  }, [app?.id, location.pathname, resolvedEntry]);

  useEffect(() => {
    if (!app) return;
    if (app.renderMode !== "external") return;
    if (!resolvedEntry) return;

    window.open(resolvedEntry, "_blank", "noopener,noreferrer");
    navigate("/", { replace: true });
  }, [app, resolvedEntry, navigate]);

  useEffect(() => {
    sendAuthToIframe();
  }, [app, resolvedEntry, location.pathname, getAccessToken, iframeReloadKey]);

  useEffect(() => {
    function handleNotificationNavigate(event: Event) {
      const custom = event as CustomEvent<{ portalRoute?: string; deepPath?: string }>;
      const deepPath = custom.detail?.deepPath;
      if (!deepPath || !app) return;

      if (!portalPathMatchesAppBase(location.pathname, app.basePath)) {
        return;
      }

      postNavigateToIframe(deepPath);
    }

    window.addEventListener("DELPI_NOTIFICATION_NAVIGATE", handleNotificationNavigate);
    return () => {
      window.removeEventListener("DELPI_NOTIFICATION_NAVIGATE", handleNotificationNavigate);
    };
  }, [app, location.pathname, resolvedEntry]);

  useEffect(() => {
    if (app?.renderMode === "embedded") {
      trySendPendingEmbeddedNavigate();
    }
  }, [app?.id, app?.renderMode, location.pathname, iframeReloadKey, resolvedEntry]);

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (!resolvedEntry) return;

      const iframeOrigin = getUrlOrigin(resolvedEntry);
      if (event.origin !== iframeOrigin) return;

      if (event.data?.type === "DELPI_AUTH_READY") {
        sendAuthToIframe();
        return;
      }

      if (event.data?.type === "DELPI_REFRESH_REQUEST") {
        void refreshToken().then(() => {
          window.setTimeout(sendAuthToIframe, 100);
        });
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [
    app,
    resolvedEntry,
    location.pathname,
    getAccessToken,
    iframeReloadKey,
    refreshToken,
  ]);

  useEffect(() => {
    function handleGlobalLogout() {
      sendLogoutToIframe();
    }

    window.addEventListener("DELPI_GLOBAL_LOGOUT", handleGlobalLogout);

    return () => {
      window.removeEventListener("DELPI_GLOBAL_LOGOUT", handleGlobalLogout);
    };
  }, [app, resolvedEntry, iframeReloadKey]);

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
            // Alguns remotes podem já estar inicializados.
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
          getAccessToken,
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

    void mountFederated();

    return () => {
      isActive = false;

      if (mountedModuleRef.current?.unmount) {
        try {
          mountedModuleRef.current.unmount(federatedHostRef.current ?? undefined);
        } catch {
          // Evita quebrar o host por falha no cleanup do plugin.
        }
      }

      mountedModuleRef.current = null;

      if (federatedHostRef.current) {
        federatedHostRef.current.innerHTML = "";
      }
    };
  }, [app?.id, app?.renderMode, resolvedEntry, getAccessToken]);

  useEffect(() => {
    if (!app) return;
    if (app.renderMode !== "federated") return;
    if (!federatedHostRef.current) return;
    if (!mountedModuleRef.current) return;

    const props = {
      getAccessToken,
      basePath: app.basePath,
      pathname: location.pathname,
      search: location.search,
    };

    const mod = mountedModuleRef.current;

    if (typeof mod.updateRoute === "function") {
      mod.updateRoute(federatedHostRef.current, props);
      return;
    }

    if (typeof mod.mount === "function") {
      mod.mount(federatedHostRef.current, props);
    }
  }, [app?.id, app?.renderMode, app?.basePath, location.pathname, getAccessToken]);

  useEffect(() => {
    const forwardTokenUpdate = async () => {
      const token = getAccessToken();
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
    };

    const onFocus = () => {
      void forwardTokenUpdate();
    };

    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [getAccessToken]);

  if (!app) return <div>App não encontrado.</div>;

  if (app.renderMode === "external") {
    return <div>Abrindo aplicação...</div>;
  }

  if (app.renderMode === "embedded") {
    if (!resolvedEntry || !iframeSrc) return <div>entryUrl não definido.</div>;

    return (
      <div className="app-host app-host-embedded">
        {isGoogleApp && googleLogin.barVisible ? (
          <div className="app-host-google-bar">
            <div className="app-host-google-info">
              <div className="app-host-google-title">Aplicação Google</div>

              <div className="app-host-google-description">
                Se o Google negar acesso, entre com sua conta em uma nova aba.
              </div>

              {googleLogin.showHelp ? (
                <div className="app-host-google-help">
                  Após concluir o login, volte para esta aba. O aplicativo será
                  recarregado automaticamente.
                </div>
              ) : null}

              {googleLogin.popupBlocked ? (
                <div className="app-host-google-warning">
                  O navegador bloqueou a abertura automática do login. Clique em
                  “Entrar no Google”.
                </div>
              ) : null}
            </div>

            <div className="app-host-google-actions">
              <button
                type="button"
                className="app-host-google-button"
                onClick={googleLogin.openGoogleLogin}
              >
                Entrar no Google
              </button>

              <button
                type="button"
                className="app-host-google-button"
                onClick={reloadIframe}
              >
                Recarregar app
              </button>

              <button
                type="button"
                className="app-host-google-button"
                onClick={openAppInNewTab}
              >
                Abrir em nova aba
              </button>

              <button
                type="button"
                className="app-host-google-button app-host-google-close-button"
                onClick={googleLogin.closeBar}
                aria-label="Fechar barra de opções do Google"
                title="Fechar"
              >
                Fechar
              </button>
            </div>
          </div>
        ) : null}

        {isGoogleApp && !googleLogin.barVisible ? (
          <button
            type="button"
            className="app-host-google-floating-button"
            onClick={googleLogin.showBar}
            aria-label="Abrir opções do Google"
            title="Opções Google"
          >
            <span className="app-host-google-floating-icon" aria-hidden="true">
              G
            </span>

            <span className="app-host-google-floating-label">Opções Google</span>
          </button>
        ) : null}

        <iframe
          key={`${location.pathname}:${iframeReloadKey}`}
          ref={iframeRef}
          title={route?.label || app.name}
          src={iframeSrc}
          className="app-host-iframe"
          referrerPolicy="strict-origin-when-cross-origin"
          allow="clipboard-read; clipboard-write; fullscreen"
          onLoad={sendAuthToIframe}
        />
      </div>
    );
  }

  if (app.renderMode === "federated") {
    return (
      <div className="app-host app-host-federated">
        {federatedError ? (
          <div className="app-host-federated-error">
            <b>Falha ao carregar microfrontend</b>
            <div className="app-host-federated-error-message">{federatedError}</div>
          </div>
        ) : null}

        <div ref={federatedHostRef} />
      </div>
    );
  }

  return <div>Modo não suportado.</div>;
};