// src/ui/AppHost.tsx

import { useContext, useEffect, useMemo, useRef } from "react";
import { useLocation } from "react-router-dom";
import { AuthContext } from "../state/AuthContext";
import type { AppItem } from "../data/coreApi";

function normalize(path: string) {
  return path.startsWith("/") ? path : `/${path}`;
}

export const AppHost = () => {
  const { apps, token, refreshToken } = useContext(AuthContext);
  const location = useLocation();
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

  // 🔁 Sempre que token mudar → reenviar
  useEffect(() => {
    if (!token) return;
    if (!iframeRef.current) return;

    iframeRef.current.contentWindow?.postMessage(
      {
        type: "DELPI_AUTH",
        token,
      },
      "http://localhost"
    );
  }, [token]);

  // 🔁 Escuta pedido de refresh vindo do Swagger
  useEffect(() => {
    function handleMessage(event: MessageEvent) {
      if (event.origin !== "http://localhost") return;

      if (event.data?.type === "DELPI_REFRESH_REQUEST") {
        refreshToken();
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [refreshToken]);

  if (!app) return <div>App não encontrado.</div>;
  if (!app.entryUrl) return <div>entryUrl não definido.</div>;

  if (app.type === "iframe") {
    return (
      <iframe
        ref={iframeRef}
        title={app.name}
        src={app.entryUrl}
        style={{
          width: "100%",
          height: "100%",
          border: "none",
        }}
      />
    );
  }

  return <div>Tipo de app não suportado.</div>;
};