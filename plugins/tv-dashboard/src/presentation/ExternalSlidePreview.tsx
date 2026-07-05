import { useEffect, useState } from "react";

type Props = {
  url?: string | null;
  title: string;
  sandbox?: string | null;
  active: boolean;
};

const IFRAME_LOAD_TIMEOUT_MS = 20_000;

export function ExternalSlidePreview({ url, title, sandbox, active }: Props) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setLoaded(false);
    setFailed(false);
  }, [url]);

  useEffect(() => {
    if (!active || !url) return;
    const timer = window.setTimeout(() => {
      if (!loaded) setFailed(true);
    }, IFRAME_LOAD_TIMEOUT_MS);
    return () => window.clearTimeout(timer);
  }, [active, url, loaded]);

  if (!url) {
    return <div className="tdp-empty">URL externa não configurada.</div>;
  }

  return (
    <div className="tdp-external-wrap">
      {failed ? (
        <div className="tdp-external-fallback">
          <p>Não foi possível exibir este link em iframe.</p>
          <p className="tdp-external-fallback__hint">
            Verifique se o site permite incorporação (ex.: Power BI «Publicar na Web»).
          </p>
        </div>
      ) : null}
      <iframe
        className="tdp-external-frame"
        src={url}
        title={title}
        sandbox={sandbox ?? undefined}
        allow="fullscreen"
        onLoad={() => {
          setLoaded(true);
          setFailed(false);
        }}
        style={failed ? { visibility: "hidden", position: "absolute" } : undefined}
      />
    </div>
  );
}
