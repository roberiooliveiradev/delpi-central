import { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Camera, CheckCircle2, ImagePlus, Trash2, X } from "lucide-react";

import type { ResponseAttachment } from "../api/audit5sApi";
import {
  clearResponseAttachmentPreviewCache,
  fetchResponseAttachmentPreviewUrl,
} from "../utils/responseAttachments";

type Props = {
  auditId: string;
  criterionId: string;
  attachment?: ResponseAttachment | null;
  disabled: boolean;
  uploading: boolean;
  reusesForNcBefore?: boolean;
  onUpload: (file: File) => Promise<void>;
  onRemove: () => Promise<void>;
};

export function CriterionPhotoSection({
  auditId,
  criterionId,
  attachment,
  disabled,
  uploading,
  reusesForNcBefore = false,
  onUpload,
  onRemove,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const lightboxTitleId = useId();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [removing, setRemoving] = useState(false);
  const [lightboxOpen, setLightboxOpen] = useState(false);

  const busy = disabled || uploading || removing;

  useEffect(() => {
    let active = true;
    setPreviewUrl(null);
    setError(null);
    setLightboxOpen(false);
    if (!attachment) return;

    void fetchResponseAttachmentPreviewUrl(auditId, criterionId, attachment)
      .then((url) => {
        if (active) setPreviewUrl(url);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : "Erro ao carregar foto.");
        }
      });

    return () => {
      active = false;
    };
  }, [attachment, auditId, criterionId]);

  useEffect(() => {
    if (!lightboxOpen) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setLightboxOpen(false);
      }
    };
    document.addEventListener("keydown", onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [lightboxOpen]);

  const openCameraPicker = () => {
    if (busy) return;
    const input = inputRef.current;
    if (!input) return;
    input.setAttribute("capture", "environment");
    input.click();
  };

  const handleSelect = async (file: File) => {
    setError(null);
    try {
      if (attachment) {
        clearResponseAttachmentPreviewCache(attachment.id);
      }
      await onUpload(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao anexar foto.");
    }
  };

  const handleRemove = async () => {
    if (!attachment) return;
    setError(null);
    setRemoving(true);
    try {
      clearResponseAttachmentPreviewCache(attachment.id);
      setLightboxOpen(false);
      await onRemove();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao remover foto.");
    } finally {
      setRemoving(false);
    }
  };

  return (
    <div className="a5s-criterion-photo">
      <div className="a5s-criterion-photo__head">
        <label>Foto (opcional)</label>
        {attachment ? (
          <span className="a5s-criterion-photo__badge">
            <CheckCircle2 size={14} aria-hidden />
            Anexada
          </span>
        ) : null}
      </div>
      <p className="a5s-criterion-photo__hint">
        {attachment
          ? "Toque na foto para ampliar. Use o botão abaixo para substituir pela câmera."
          : reusesForNcBefore
            ? "Registre uma foto opcional deste critério. Em notas Ruim ou Médio, ela também pode ser reutilizada como evidência do antes na NC."
            : "Registre uma foto opcional para documentar este critério durante a avaliação."}
      </p>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="a5s-criterion-photo__input"
        disabled={busy}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void handleSelect(file);
          event.target.value = "";
        }}
      />

      {attachment && previewUrl ? (
        <button
          type="button"
          className="a5s-criterion-photo__media a5s-criterion-photo__media--preview"
          onClick={() => setLightboxOpen(true)}
          aria-label="Ampliar foto do critério"
        >
          <img src={previewUrl} alt="Foto do critério" className="a5s-criterion-photo__preview" />
        </button>
      ) : attachment && !error ? (
        <p className="a5s-criterion-photo__loading">Carregando foto...</p>
      ) : (
        <button
          type="button"
          className="a5s-criterion-photo__media a5s-criterion-photo__media--empty"
          disabled={busy}
          onClick={openCameraPicker}
          aria-label="Abrir câmera para fotografar o critério"
        >
          <Camera size={28} aria-hidden />
          <span>{uploading ? "Enviando..." : "Toque para fotografar"}</span>
        </button>
      )}

      <div className="a5s-criterion-photo__actions">
        <button
          type="button"
          className="a5s-btn a5s-btn--ghost a5s-btn--small"
          disabled={busy}
          onClick={openCameraPicker}
        >
          <ImagePlus size={15} aria-hidden />
          {uploading ? "Enviando..." : attachment ? "Substituir foto" : "Tirar / anexar foto"}
        </button>
        {attachment ? (
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--small a5s-criterion-photo__remove"
            disabled={busy}
            onClick={() => void handleRemove()}
          >
            <Trash2 size={15} aria-hidden />
            {removing ? "Removendo..." : "Remover"}
          </button>
        ) : null}
      </div>

      {error ? <p className="a5s-criterion-photo__error">{error}</p> : null}

      {lightboxOpen && previewUrl
        ? createPortal(
            <div
              className="a5s-photo-lightbox"
              role="presentation"
              onClick={() => setLightboxOpen(false)}
            >
              <div
                className="a5s-photo-lightbox__dialog"
                role="dialog"
                aria-modal="true"
                aria-labelledby={lightboxTitleId}
                onClick={(event) => event.stopPropagation()}
              >
                <div className="a5s-photo-lightbox__header">
                  <h2 id={lightboxTitleId} className="a5s-photo-lightbox__title">
                    Foto do critério
                  </h2>
                  <button
                    ref={closeButtonRef}
                    type="button"
                    className="a5s-photo-lightbox__close"
                    aria-label="Fechar visualização"
                    onClick={() => setLightboxOpen(false)}
                  >
                    <X size={20} aria-hidden />
                  </button>
                </div>
                <div className="a5s-photo-lightbox__body">
                  <img
                    src={previewUrl}
                    alt="Foto ampliada do critério"
                    className="a5s-photo-lightbox__image"
                  />
                </div>
              </div>
            </div>,
            document.body,
          )
        : null}
    </div>
  );
}
