import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem, RouteItem } from "../data/coreApi";
import { pushRecentApp } from "../utils/recentApps";

const GOOGLE_LOGIN_POPUP_NAME = "delpi-google-login";
const GOOGLE_AUTO_LOGIN_DELAY_MS = 1200;

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

function isGoogleHostedApp(url: string | undefined) {
  if (!url) return false;

  try {
    const parsed = new URL(url, window.location.origin);

    return (
      parsed.hostname === "script.google.com" ||
      parsed.hostname.endsWith(".googleusercontent.com") ||
      parsed.hostname.endsWith(".google.com")
    );
  } catch {
    return false;
  }
}

function buildGoogleLoginUrl() {
  return "https://accounts.google.com/AccountChooser";
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
  const googleLoginPopupRef = useRef<Window | null>(null);
  const googleAutoLoginAttemptedRef = useRef<string | null>(null);

  const [federatedError, setFederatedError] = useState<string | null>(null);
  const [iframeReloadKey, setIframeReloadKey] = useState(0);
  const [showGoogleHelp, setShowGoogleHelp] = useState(false);
  const [googlePopupBlocked, setGooglePopupBlocked] = useState(false);

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

  function openGoogleLogin() {
    const popup = window.open(
      buildGoogleLoginUrl(),
      GOOGLE_LOGIN_POPUP_NAME,
      "width=560,height=760"
    );

    setShowGoogleHelp(true);

    if (!popup) {
      setGooglePopupBlocked(true);
      return;
    }

    setGooglePopupBlocked(false);
    googleLoginPopupRef.current = popup;

    const timer = window.setInterval(() => {
      if (!popup.closed) return;

      window.clearInterval(timer);

      if (googleLoginPopupRef.current === popup) {
        googleLoginPopupRef.current = null;
      }

      setShowGoogleHelp(false);
      reloadIframe();
    }, 800);
  }

  function openAppInNewTab() {
    if (!resolvedEntry) return;

    window.open(resolvedEntry, "_blank", "noopener,noreferrer");
  }

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
    setShowGoogleHelp(false);
    setGooglePopupBlocked(false);
    setIframeReloadKey(0);

    googleLoginPopupRef.current = null;
  }, [app?.id, location.pathname, resolvedEntry]);

  useEffect(() => {
    if (!app) return;
    if (app.renderMode !== "external") return;
    if (!resolvedEntry) return;

    window.open(resolvedEntry, "_blank", "noopener,noreferrer");
    navigate("/", { replace: true });
  }, [app, resolvedEntry, navigate]);

  useEffect(() => {
    if (!isGoogleApp) return;
    if (!resolvedEntry) return;

    const attemptKey = `${location.pathname}|${resolvedEntry}`;

    if (googleAutoLoginAttemptedRef.current === attemptKey) return;

    googleAutoLoginAttemptedRef.current = attemptKey;

    const timer = window.setTimeout(() => {
      openGoogleLogin();
    }, GOOGLE_AUTO_LOGIN_DELAY_MS);

    return () => window.clearTimeout(timer);
  }, [isGoogleApp, location.pathname, resolvedEntry]);

  useEffect(() => {
    if (!iframeRef.current) return;
    if (!app || app.renderMode !== "embedded") return;
    if (!resolvedEntry) return;

    const token = getAccessToken();
    if (!token) return;

    iframeRef.current.contentWindow?.postMessage(
      { type: "DELPI_AUTH", token },
      getUrlOrigin(resolvedEntry)
    );
  }, [app, resolvedEntry, location.pathname, getAccessToken, iframeReloadKey]);

  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;

      if (event.data?.type === "DELPI_REFRESH_REQUEST") {
        void refreshToken();
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
  }, [app, resolvedEntry, location.pathname, location.search, getAccessToken]);

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
        {isGoogleApp ? (
          <div className="app-host-google-bar">
            <div className="app-host-google-info">
              <div className="app-host-google-title">Aplicação Google</div>

              <div className="app-host-google-description">
                Se o Google negar acesso, o login será solicitado automaticamente.
              </div>

              {showGoogleHelp ? (
                <div className="app-host-google-help">
                  Após concluir o login, feche a janela aberta. O aplicativo será
                  recarregado automaticamente.
                </div>
              ) : null}

              {googlePopupBlocked ? (
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
                onClick={openGoogleLogin}
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
            </div>
          </div>
        ) : null}

        <iframe
          key={`${location.pathname}:${iframeReloadKey}`}
          ref={iframeRef}
          title={route?.label || app.name}
          src={iframeSrc}
          className="app-host-iframe"
          referrerPolicy="strict-origin-when-cross-origin"
          allow="clipboard-read; clipboard-write; fullscreen"
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