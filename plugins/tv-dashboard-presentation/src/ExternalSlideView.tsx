import { useEffect, useState } from "react";

const IFRAME_LOAD_TIMEOUT_MS = 20_000;

export type ExternalSlideViewProps = {
  url?: string | null;
  title: string;
  sandbox?: string | null;
  active: boolean;
  /** Classe do empty quando não há URL (default: tdp-external-fallback). */
  emptyClassName?: string;
};

/**
 * Viewer canônico de slide externo (iframe) — prévia admin e TV pública.
 */
export function ExternalSlideView({
  url,
  title,
  sandbox,
  active,
  emptyClassName = "tdp-external-fallback",
}: ExternalSlideViewProps) {
  const href = url ?? "";
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setLoaded(false);
    setFailed(false);
  }, [href]);

  useEffect(() => {
    if (!active || !href) return;
    const timer = window.setTimeout(() => {
      if (!loaded) setFailed(true);
    }, IFRAME_LOAD_TIMEOUT_MS);
    return () => window.clearTimeout(timer);
  }, [active, href, loaded]);

  if (!href) {
    return (
      <div className={emptyClassName}>
        <p>URL externa não configurada.</p>
      </div>
    );
  }

  return (
    <div className="tdp-external-wrap">
      {failed ? (
        <div className="tdp-external-fallback">
          <p>Não foi possível exibir este link em iframe.</p>
          <p className="tdp-external-fallback__hint">
            Verifique se o site permite incorporação (ex.: Power BI «Publicar na Web»).
          </p>
          <p className="tdp-external-fallback__url">{href}</p>
        </div>
      ) : null}
      <iframe
        className="tdp-external-frame"
        src={href}
        title={title}
        sandbox={sandbox ?? undefined}
        allow="fullscreen"
        referrerPolicy="no-referrer-when-downgrade"
        onLoad={() => {
          setLoaded(true);
          setFailed(false);
        }}
        style={failed ? { visibility: "hidden", position: "absolute" } : undefined}
      />
    </div>
  );
}
