import { useEffect, useState } from "react";

import type { PublicSlide } from "./api";

const IFRAME_LOAD_TIMEOUT_MS = 20_000;

type Props = {
  slide: PublicSlide;
  active: boolean;
};

export function ExternalSlideView({ slide, active }: Props) {
  const url = slide.external?.url ?? "";
  const sandbox = slide.external?.sandbox ?? undefined;
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
    return (
      <div className="tdp-external-fallback">
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
          <p className="tdp-external-fallback__url">{url}</p>
        </div>
      ) : null}
      <iframe
        className="tdp-external-frame"
        src={url}
        title={slide.title}
        sandbox={sandbox}
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
