// src/ui/AppHost.tsx

import { useContext, useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem } from "../data/coreApi";

function normalize(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

/**
 * Loader runtime para microfrontend federado (Vite + @originjs/vite-plugin-federation)
 * Espera que o remote exponha:
 *   - container.get(exposed) -> factory -> módulo com mount/unmount
 *   - opcional: container.init(shareScope)
 */

async function loadFederatedContainer(entryUrl: string) {
  const mod: any = await import(/* @vite-ignore */ entryUrl);
  // no Vite federation, o container costuma vir como exports do módulo
  if (mod?.get) return mod;
  if (mod?.default?.get) return mod.default;
  throw new Error(`remoteEntry carregou, mas não expôs container.get(): ${entryUrl}`);
}

function getViteFederationShareScope() {
  const w = window as any;

  // Varia conforme versão/config: tentamos os nomes mais comuns
  // - __federation_shared__ é usado em várias builds do @originjs
  // - default scope costuma existir
  return w.__federation_shared__?.default ?? w.__federation_shared__ ?? {};
}

export const AppHost = () => {
  const { apps, token, refreshToken } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();

  const iframeRef = useRef<HTMLIFrameElement>(null);

  // host do microfrontend federado
  const federatedHostRef = useRef<HTMLDivElement>(null);
  const [federatedError, setFederatedError] = useState<string | null>(null);

  const app = useMemo(() => {
    return apps.find((a: AppItem) => {
      const base = normalize(a.basePath);
      return (
        location.pathname === base ||
        location.pathname.startsWith(base + "/")
      );
    });
  }, [apps, location.pathname]);

  /**
   * 🔥 External apps → abrir nova aba (efeito controlado)
   */
  useEffect(() => {
    if (!app) return;
    if (app.renderMode !== "external") return;
    if (!app.entryUrl) return;

    window.open(app.entryUrl, "_blank", "noopener,noreferrer");
    navigate("/", { replace: true });
  }, [app, navigate]);

  /**
   * 🔁 Sempre que token mudar → reenviar para iframe embutido
   */
  useEffect(() => {
    if (!token) return;
    if (!iframeRef.current) return;
    if (!app || app.renderMode !== "embedded") return;

    iframeRef.current.contentWindow?.postMessage(
      { type: "DELPI_AUTH", token },
      window.location.origin
    );
  }, [token, app]);

  /**
   * 🔁 Escuta pedido de refresh vindo do iframe
   */
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== window.location.origin) return;
      if (event.data?.type === "DELPI_REFRESH_REQUEST") refreshToken();
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [refreshToken]);

  /**
   * 🧩 Federated microfrontend (Vite Federation)
   */
  useEffect(() => {
    let isActive = true;
    let cleanup: (() => void) | null = null;

    async function mountFederated() {
      setFederatedError(null);

      if (!app) return;
      if (app.renderMode !== "federated") return;
      if (!app.entryUrl) {
        setFederatedError("entryUrl não definido.");
        return;
      }
      if (!federatedHostRef.current) return;

      // const scope = (app as any).scope ?? app.id; // recomendação: scope == app.id
      const exposedModule = (app as any).exposedModule ?? "./App"; // no manifest: "./App"

      // limpa conteúdo anterior antes de montar (evita “sobras”)
      federatedHostRef.current.innerHTML = "";

      try {
        const container = await loadFederatedContainer(app.entryUrl);

        // init do share scope (se suportado)
        if (typeof container.init === "function") {
          const shareScope = getViteFederationShareScope();
          try {
            await container.init(shareScope);
          } catch {
            // algumas versões lançam erro se init já foi chamado — ignorar
          }
        }

        if (!isActive) return;

        const factory = await container.get(exposedModule);
        const mod = factory?.();

        if (!mod?.mount) {
          throw new Error(
            `Módulo exposto "${exposedModule}" não possui função mount().`
          );
        }

        // props padrão que a Central entrega ao microfrontend
        const props = {
          token,
          basePath: app.basePath,
          pathname: location.pathname,
          search: location.search,
          // você pode adicionar "user", "permissions" etc. aqui se quiser
        };

        // mount
        mod.mount(federatedHostRef.current, props);

        // cleanup/unmount
        cleanup = () => {
          try {
            if (typeof mod.unmount === "function") mod.unmount();
          } catch {
            // ignore
          } finally {
            if (federatedHostRef.current) federatedHostRef.current.innerHTML = "";
          }
        };
      } catch (e: any) {
        setFederatedError(e?.message ?? String(e));
      }
    }

    mountFederated();

    return () => {
      isActive = false;
      if (cleanup) cleanup();
    };
    // importante: remonta ao trocar de app/rota base
  }, [app, token, location.pathname, location.search]);

  if (!app) return <div>App não encontrado.</div>;

  if (app.renderMode === "external") {
    return <div>Abrindo aplicação em nova aba...</div>;
  }

  if (app.renderMode === "embedded") {
    if (!app.entryUrl) return <div>entryUrl não definido.</div>;

    return (
      <iframe
        ref={iframeRef}
        title={app.name}
        src={app.entryUrl}
        className="content-iframe"
        style={{ width: "100%", height: "100%", border: "none" }}
      />
    );
  }

  if (app.renderMode === "federated") {
    return (
      <div style={{ width: "100%", height: "100%" }}>
        {federatedError ? (
          <div style={{ padding: 12 }}>
            <b>Falha ao carregar microfrontend</b>
            <div style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>
              {federatedError}
            </div>
          </div>
        ) : null}

        <div
          ref={federatedHostRef}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    );
  }

  return <div>Modo de renderização não suportado.</div>;
};