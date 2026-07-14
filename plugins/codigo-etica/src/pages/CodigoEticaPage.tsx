import { useCallback, useState } from "react";
import {
  BookOpen,
  Download,
  ExternalLink,
  Minus,
  Plus,
  Scan,
} from "lucide-react";
import logoMinhaDelpi from "../assets/logoMinhaDelpi.svg";
import { CodigoEticaPdfReader } from "../components/CodigoEticaPdfReader";
import {
  CODIGO_ETICA_PDF_FILENAME,
  CODIGO_ETICA_PDF_PATH,
  PAGE_EYEBROW,
  PAGE_INTRO,
  PDF_ZOOM_FIT,
  PDF_ZOOM_MAX,
  PDF_ZOOM_MIN,
  PDF_ZOOM_STEP,
} from "../constants/document";

function openPdfInNewTab() {
  window.open(CODIGO_ETICA_PDF_PATH, "_blank", "noopener,noreferrer");
}

function clampZoom(value: number): number {
  return Math.min(PDF_ZOOM_MAX, Math.max(PDF_ZOOM_MIN, value));
}

export function CodigoEticaPage() {
  const [zoomPercent, setZoomPercent] = useState(PDF_ZOOM_FIT);

  const zoomOut = useCallback(() => {
    setZoomPercent((prev) => clampZoom(prev - PDF_ZOOM_STEP));
  }, []);

  const zoomIn = useCallback(() => {
    setZoomPercent((prev) => clampZoom(prev + PDF_ZOOM_STEP));
  }, []);

  const zoomFit = useCallback(() => {
    setZoomPercent(PDF_ZOOM_FIT);
  }, []);

  return (
    <div className="dashboard-codigo-etica ce-page">
      <header className="ce-hero">
        <div className="ce-hero__brand">
          <img
            className="ce-hero__logo"
            src={logoMinhaDelpi}
            alt="Minha DELPI"
          />
          <span className="ce-hero__divider" aria-hidden="true" />
          <div className="ce-hero__titles">
            <p className="ce-hero__eyebrow">{PAGE_EYEBROW}</p>
            <h1 className="ce-hero__title">Código de Ética</h1>
          </div>
        </div>
        <BookOpen
          className="ce-hero__watermark"
          aria-hidden="true"
          strokeWidth={1.25}
        />
      </header>

      <p className="ce-intro">{PAGE_INTRO}</p>

      <div className="ce-toolbar">
        <button
          type="button"
          className="ce-btn ce-btn--primary"
          onClick={openPdfInNewTab}
        >
          <ExternalLink size={16} strokeWidth={2} aria-hidden="true" />
          Abrir em nova aba
        </button>
        <a
          className="ce-btn ce-btn--secondary"
          href={CODIGO_ETICA_PDF_PATH}
          download={CODIGO_ETICA_PDF_FILENAME}
          rel="noopener noreferrer"
        >
          <Download size={16} strokeWidth={2} aria-hidden="true" />
          Baixar PDF
        </a>

        <div className="ce-zoom" role="group" aria-label="Zoom do documento">
          <button
            type="button"
            className="ce-zoom__btn"
            onClick={zoomOut}
            disabled={zoomPercent <= PDF_ZOOM_MIN}
            aria-label="Diminuir zoom"
          >
            <Minus size={16} strokeWidth={2} aria-hidden="true" />
          </button>
          <span className="ce-zoom__value" aria-live="polite">
            {zoomPercent}%
          </span>
          <button
            type="button"
            className="ce-zoom__btn"
            onClick={zoomIn}
            disabled={zoomPercent >= PDF_ZOOM_MAX}
            aria-label="Aumentar zoom"
          >
            <Plus size={16} strokeWidth={2} aria-hidden="true" />
          </button>
          <button
            type="button"
            className="ce-zoom__btn ce-zoom__btn--fit"
            onClick={zoomFit}
            aria-label="Ajustar à largura"
            title="Ajustar à largura"
          >
            <Scan size={16} strokeWidth={2} aria-hidden="true" />
            <span>Ajustar à largura</span>
          </button>
        </div>
      </div>

      <div className="ce-viewer">
        <CodigoEticaPdfReader zoomPercent={zoomPercent} />
      </div>
    </div>
  );
}
