import { useCallback, useEffect, useRef, useState } from "react";
import { ExternalLink, RefreshCw, Shield } from "lucide-react";
import { API_DELPI_DOCS_URL } from "../constants/routes";
import { getAuthToken } from "../lib/auth";
import {
  setupDocsMessageListener,
  setupDocsThemeObserver,
  syncDocsIframeBridge,
} from "../lib/docsAuthBridge";
import { resolvePortalTheme } from "../lib/portalTheme";

type Props = {
  onNavigate: (path: string) => void;
};

export function DocumentacaoPage({ onNavigate }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [hasToken, setHasToken] = useState(() => Boolean(getAuthToken()));
  const [resolvedTheme, setResolvedTheme] = useState(() => resolvePortalTheme());

  const refreshAuthState = useCallback(() => {
    setHasToken(Boolean(getAuthToken()));
    setResolvedTheme(resolvePortalTheme());
    syncDocsIframeBridge(iframeRef.current);
  }, []);

  useEffect(() => {
    refreshAuthState();

    const cleanupMessages = setupDocsMessageListener(iframeRef.current, refreshAuthState);
    const cleanupTheme = setupDocsThemeObserver(iframeRef.current);

    const onTokenUpdate = (event: Event) => {
      const custom = event as CustomEvent<{ token?: string }>;
      if (custom.detail?.token) {
        setHasToken(true);
      } else {
        setHasToken(Boolean(getAuthToken()));
      }
      syncDocsIframeBridge(iframeRef.current);
    };

    window.addEventListener("DELPI_TOKEN_UPDATE", onTokenUpdate);
    window.addEventListener("focus", refreshAuthState);

    return () => {
      cleanupMessages();
      cleanupTheme();
      window.removeEventListener("DELPI_TOKEN_UPDATE", onTokenUpdate);
      window.removeEventListener("focus", refreshAuthState);
    };
  }, [reloadKey, refreshAuthState]);

  const handleLoad = () => {
    syncDocsIframeBridge(iframeRef.current);
    window.setTimeout(() => syncDocsIframeBridge(iframeRef.current), 400);
    window.setTimeout(() => syncDocsIframeBridge(iframeRef.current), 1200);
  };

  const docsSrc = `${API_DELPI_DOCS_URL}?_reload=${reloadKey}`;

  return (
    <div className="adc-page adc-page--docs">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Documentação da API</h1>
          <p className="adc-subtitle">
            Referência interativa com JWT do portal e tema {resolvedTheme === "dark" ? "escuro" : "claro"}.
          </p>
        </div>
        <div className="adc-header__actions">
          <span
            className={`adc-badge ${hasToken ? "adc-badge--ok" : "adc-badge--err"}`}
            title={hasToken ? "Token disponível" : "Sem token — faça login no portal"}
          >
            <Shield size={14} />
            {hasToken ? "JWT ativo" : "Sem JWT"}
          </span>
          <button
            type="button"
            className="adc-btn adc-btn--ghost"
            onClick={() => setReloadKey((k) => k + 1)}
          >
            <RefreshCw size={16} />
            Recarregar
          </button>
          <a
            className="adc-btn adc-btn--ghost"
            href={API_DELPI_DOCS_URL}
            target="_blank"
            rel="noopener noreferrer"
          >
            <ExternalLink size={16} />
            Nova aba
          </a>
        </div>
      </header>

      {!hasToken ? (
        <div className="adc-panel adc-panel--warn">
          Faça login no portal para autorizar automaticamente as chamadas na documentação.
        </div>
      ) : null}

      <iframe
        ref={iframeRef}
        key={reloadKey}
        className="adc-docs-frame"
        data-delpi-theme={resolvedTheme}
        title="Documentação interativa — API DELPI"
        src={docsSrc}
        onLoad={handleLoad}
      />
    </div>
  );
}
