import { useEffect, useState } from "react";

import { fetchPublicDeliveryMapDrawingPdf } from "./api";

type Props = {
  token: string;
  branch: string;
  paCode: string;
  onClose: () => void;
};

export function DeliveryMapPublicDrawingViewer({ token, branch, paCode, onClose }: Props) {
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [message, setMessage] = useState<string | null>(null);
  const [objectUrl, setObjectUrl] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    let createdUrl: string | null = null;
    setStatus("loading");
    setMessage(null);
    setObjectUrl(null);

    void fetchPublicDeliveryMapDrawingPdf(token, branch, paCode)
      .then((blob) => {
        if (!active) return;
        createdUrl = URL.createObjectURL(blob);
        setObjectUrl(createdUrl);
        setStatus("ready");
      })
      .catch((err: unknown) => {
        if (!active) return;
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Desenho não encontrado para este PA.");
      });

    return () => {
      active = false;
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [token, branch, paCode]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="pcp-pub-viewer" role="dialog" aria-modal="true" aria-labelledby="pcp-pub-dm-viewer-title">
      <div className="pcp-pub-viewer__bar">
        <h2 id="pcp-pub-dm-viewer-title">Desenho {paCode}</h2>
        <button type="button" className="pcp-pub__ghost pcp-pub__ghost--plain" onClick={onClose}>
          Fechar
        </button>
      </div>
      {status === "loading" ? <p className="pcp-pub-viewer__state">Carregando desenho…</p> : null}
      {status === "error" ? <p className="pcp-pub-viewer__state pcp-pub-viewer__state--error">{message}</p> : null}
      {status === "ready" && objectUrl ? (
        <iframe className="pcp-pub-viewer__frame" title={`Desenho ${paCode}`} src={objectUrl} />
      ) : null}
    </div>
  );
}
