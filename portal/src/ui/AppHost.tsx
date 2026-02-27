// src/ui/AppHost.tsx

import { useContext, useEffect, useMemo, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem } from "../data/coreApi";

function normalize(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

export const AppHost = () => {
  const { apps, token, refreshToken } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();
  const iframeRef = useRef<HTMLIFrameElement>(null);

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

    // Opcional: redireciona para home após abrir
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
      {
        type: "DELPI_AUTH",
        token,
      },
      window.location.origin
    );
  }, [token, app]);

  /**
   * 🔁 Escuta pedido de refresh vindo do iframe
   */
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
        style={{
          width: "100%",
          height: "100%",
          border: "none",
        }}
      />
    );
  }

  if (app.renderMode === "federated") {
    // Placeholder para futura integração Module Federation
    return <div>Microfrontend federado não implementado ainda.</div>;
  }

  return <div>Modo de renderização não suportado.</div>;
};