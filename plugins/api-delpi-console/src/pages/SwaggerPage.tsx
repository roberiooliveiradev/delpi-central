import { useEffect, useRef, useState } from "react";
import { ExternalLink, RefreshCw, Shield } from "lucide-react";
import { API_DELPI_SWAGGER_URL } from "../constants/routes";
import { getAuthToken } from "../lib/auth";
import { postAuthToSwaggerIframe, setupSwaggerMessageListener } from "../lib/swaggerBridge";

type Props = {
  onNavigate: (path: string) => void;
};

export function SwaggerPage({ onNavigate }: Props) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const hasToken = Boolean(getAuthToken());

  useEffect(() => {
    const cleanup = setupSwaggerMessageListener(iframeRef.current, () => {
      setReloadKey((k) => k + 1);
    });

    const onTokenUpdate = () => postAuthToSwaggerIframe(iframeRef.current);
    window.addEventListener("DELPI_TOKEN_UPDATE", onTokenUpdate);
    window.addEventListener("focus", onTokenUpdate);

    return () => {
      cleanup();
      window.removeEventListener("DELPI_TOKEN_UPDATE", onTokenUpdate);
      window.removeEventListener("focus", onTokenUpdate);
    };
  }, [reloadKey]);

  const handleLoad = () => {
    postAuthToSwaggerIframe(iframeRef.current);
    window.setTimeout(() => postAuthToSwaggerIframe(iframeRef.current), 400);
    window.setTimeout(() => postAuthToSwaggerIframe(iframeRef.current), 1200);
  };

  const swaggerSrc = `${API_DELPI_SWAGGER_URL}?_reload=${reloadKey}`;

  return (
    <div className="adc-page adc-page--swagger">
      <header className="adc-header adc-header--compact">
        <div>
          <button type="button" className="adc-link" onClick={() => onNavigate("")}>
            ← Início
          </button>
          <h1>Swagger UI</h1>
          <p className="adc-subtitle">
            Interface oficial FastAPI — «Try it out» com JWT do portal pré-autorizado.
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
            href={API_DELPI_SWAGGER_URL}
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
          Faça login no portal para autorizar automaticamente o Bearer no Swagger.
        </div>
      ) : null}

      <iframe
        ref={iframeRef}
        key={reloadKey}
        className="adc-swagger-frame"
        title="Swagger UI — API DELPI"
        src={swaggerSrc}
        onLoad={handleLoad}
      />
    </div>
  );
}
