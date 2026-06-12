import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, ExternalLink } from "lucide-react";

import { useGoogleEmbeddedForm } from "../hooks/useGoogleEmbeddedForm";

const IFRAME_LOAD_TIMEOUT_MS = 20_000;

type ManutencaoGeralFormEmbedProps = {
  formUrl: string;
  pathname?: string;
  homePath: string;
  onNavigate: (path: string) => void;
};

export function ManutencaoGeralFormEmbed({
  formUrl,
  pathname,
  homePath,
  onNavigate,
}: ManutencaoGeralFormEmbedProps) {
  const [iframeReloadKey, setIframeReloadKey] = useState(0);
  const [iframeReady, setIframeReady] = useState(false);

  const reloadIframe = useCallback(() => {
    setIframeReady(false);
    setIframeReloadKey((current) => current + 1);
  }, []);

  const googleLogin = useGoogleEmbeddedForm({
    formUrl,
    pathname,
    onReloadIframe: reloadIframe,
  });

  useEffect(() => {
    if (iframeReady) return;

    const timer = window.setTimeout(() => {
      setIframeReady(true);
    }, IFRAME_LOAD_TIMEOUT_MS);

    return () => window.clearTimeout(timer);
  }, [iframeReady, iframeReloadKey]);

  function openFormInNewTab() {
    window.open(formUrl, "_blank", "noopener,noreferrer");
  }

  return (
    <section className="dm-form-embed" aria-label="Formulário de manutenção geral">
      <button
        type="button"
        className="dm-embed-floating-button dm-embed-floating-button--left"
        onClick={() => onNavigate(homePath)}
        aria-label="Voltar ao início do módulo"
        title="Início"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        <span className="dm-embed-floating-button__label">Início</span>
      </button>

      {googleLogin.barVisible ? (
        <div className="dm-google-bar">
          <div className="dm-google-bar__info">
            <div className="dm-google-bar__title">Aplicação Google</div>
            <div className="dm-google-bar__description">
              Se o Google negar acesso, entre com sua conta em uma nova aba.
            </div>
            {googleLogin.showHelp ? (
              <div className="dm-google-bar__help">
                Após concluir o login, volte para esta aba. O formulário será recarregado
                automaticamente.
              </div>
            ) : null}
            {googleLogin.popupBlocked ? (
              <div className="dm-google-bar__warning">
                O navegador bloqueou a abertura automática do login. Clique em “Entrar no Google”.
              </div>
            ) : null}
          </div>

          <div className="dm-google-bar__actions">
            <button type="button" className="dm-google-bar__button" onClick={googleLogin.openGoogleLogin}>
              Entrar no Google
            </button>
            <button type="button" className="dm-google-bar__button" onClick={reloadIframe}>
              Recarregar
            </button>
            <button type="button" className="dm-google-bar__button" onClick={openFormInNewTab}>
              <ExternalLink size={14} aria-hidden="true" />
              Abrir em nova aba
            </button>
            <button
              type="button"
              className="dm-google-bar__button dm-google-bar__button--close"
              onClick={googleLogin.closeBar}
              aria-label="Fechar barra de opções do Google"
              title="Fechar"
            >
              Fechar
            </button>
          </div>
        </div>
      ) : null}

      {!googleLogin.barVisible && googleLogin.optionsAvailable ? (
        <button
          type="button"
          className="dm-embed-floating-button dm-embed-floating-button--right"
          onClick={googleLogin.showBar}
          aria-label="Abrir opções do Google"
          title="Opções Google"
        >
          <span className="dm-embed-floating-button__badge" aria-hidden="true">
            G
          </span>
          <span className="dm-embed-floating-button__label">Opções Google</span>
        </button>
      ) : null}

      {!iframeReady ? (
        <div className="dm-form-embed__loading" aria-live="polite">
          Carregando formulário…
        </div>
      ) : null}

      <div className="dm-form-embed__frame">
        <iframe
          key={`manutencao-geral:${iframeReloadKey}`}
          title="Formulário de manutenção geral"
          src={formUrl}
          className={["dm-form-embed__iframe", iframeReady ? "is-ready" : "is-loading"].join(" ")}
          referrerPolicy="strict-origin-when-cross-origin"
          allow="clipboard-read; clipboard-write; fullscreen"
          onLoad={() => setIframeReady(true)}
        />
      </div>
    </section>
  );
}
