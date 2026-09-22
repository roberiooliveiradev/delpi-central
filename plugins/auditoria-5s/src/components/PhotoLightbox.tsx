import { useEffect, useId, useRef } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

type Props = {
  open: boolean;
  src: string;
  title: string;
  alt: string;
  onClose: () => void;
};

export function PhotoLightbox({ open, src, title, alt, onClose }: Props) {
  const titleId = useId();
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onCloseRef.current();
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
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="a5s-photo-lightbox"
      role="presentation"
      onClick={() => onCloseRef.current()}
    >
      <div
        className="a5s-photo-lightbox__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="a5s-photo-lightbox__header">
          <h2 id={titleId} className="a5s-photo-lightbox__title">
            {title}
          </h2>
          <button
            ref={closeButtonRef}
            type="button"
            className="a5s-photo-lightbox__close"
            aria-label="Fechar visualização"
            onClick={() => onCloseRef.current()}
          >
            <X size={20} aria-hidden />
          </button>
        </div>
        <div className="a5s-photo-lightbox__body">
          <img src={src} alt={alt} className="a5s-photo-lightbox__image" />
        </div>
      </div>
    </div>,
    document.body,
  );
}
