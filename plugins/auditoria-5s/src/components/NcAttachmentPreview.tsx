import { useEffect, useState } from "react";

import type { NcAttachment } from "../api/audit5sApi";
import { fetchNcAttachmentPreviewUrl } from "../utils/ncAttachments";
import { PhotoLightbox } from "./PhotoLightbox";

type Props = {
  ncId: string;
  attachment: NcAttachment;
  label: string;
};

export function NcAttachmentPreview({ ncId, attachment, label }: Props) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  useEffect(() => {
    let active = true;
    setLightboxOpen(false);
    void fetchNcAttachmentPreviewUrl(ncId, attachment)
      .then((url) => {
        if (active) setPreviewUrl(url);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Erro ao carregar imagem.");
        }
      });
    return () => {
      active = false;
    };
  }, [attachment, ncId]);

  if (error) {
    return <p className="a5s-nc-evidence__error">{error}</p>;
  }

  if (!previewUrl) {
    return <p className="a5s-nc-evidence__loading">Carregando {label.toLowerCase()}...</p>;
  }

  return (
    <>
      <button
        type="button"
        className="a5s-nc-evidence__preview-btn"
        onClick={() => setLightboxOpen(true)}
        aria-label={`Ampliar foto — ${label}`}
      >
        <img src={previewUrl} alt={label} className="a5s-nc-evidence__preview" />
      </button>
      <PhotoLightbox
        open={lightboxOpen}
        src={previewUrl}
        title={label}
        alt={`Foto ampliada — ${label}`}
        onClose={() => setLightboxOpen(false)}
      />
    </>
  );
}
