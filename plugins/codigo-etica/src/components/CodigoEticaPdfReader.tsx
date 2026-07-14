import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactElement,
} from "react";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/TextLayer.css";
import "react-pdf/dist/Page/AnnotationLayer.css";
import {
  CODIGO_ETICA_PDF_FILENAME,
  CODIGO_ETICA_PDF_PATH,
  PDF_ERROR_MESSAGE,
  PDF_LOADING_MESSAGE,
  PDF_ZOOM_FIT,
} from "../constants/document";

// Worker no mesmo módulo do Document (exigência do react-pdf).
pdfjs.GlobalWorkerOptions.workerSrc = `${import.meta.env.BASE_URL}assets/pdf.worker.min.js`;

type CodigoEticaPdfReaderProps = {
  zoomPercent: number;
};

function clampPageWidth(containerWidth: number, zoomPercent: number): number {
  if (containerWidth <= 0) return 0;
  return Math.max(1, Math.floor(containerWidth * (zoomPercent / PDF_ZOOM_FIT)));
}

function formatPdfError(error: unknown): string {
  if (!error) return "erro desconhecido";
  if (error instanceof Error) {
    const details =
      "details" in error && error.details != null
        ? ` (${String(error.details)})`
        : "";
    return `${error.name || "Error"}: ${error.message || "(sem mensagem)"}${details}`;
  }
  return String(error);
}

export function CodigoEticaPdfReader({
  zoomPercent,
}: CodigoEticaPdfReaderProps): ReactElement {
  const shellRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(0);
  const [numPages, setNumPages] = useState(0);
  const [status, setStatus] = useState<"loading" | "ready" | "error">(
    "loading",
  );

  useEffect(() => {
    const el = shellRef.current;
    if (!el) return;

    const updateWidth = () => {
      const next = Math.floor(el.clientWidth);
      setContainerWidth((prev) => (prev === next ? prev : next));
    };

    updateWidth();
    const observer = new ResizeObserver(updateWidth);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const pageWidth = useMemo(
    () => clampPageWidth(containerWidth, zoomPercent),
    [containerWidth, zoomPercent],
  );

  const onLoadSuccess = useCallback(({ numPages: total }: { numPages: number }) => {
    setNumPages(total);
    setStatus("ready");
  }, []);

  const onLoadError = useCallback((error: Error) => {
    console.warn("[codigo-etica] react-pdf onLoadError", formatPdfError(error), error);
    setNumPages(0);
    setStatus("error");
  }, []);

  const pages = useMemo(() => {
    if (status !== "ready" || pageWidth <= 0 || numPages <= 0) return null;
    return Array.from({ length: numPages }, (_, index) => {
      const pageNumber = index + 1;
      return (
        <div key={pageNumber} className="ce-pdf-page">
          <Page
            pageNumber={pageNumber}
            width={pageWidth}
            renderTextLayer={false}
            renderAnnotationLayer={false}
            loading={null}
          />
        </div>
      );
    });
  }, [numPages, pageWidth, status]);

  return (
    <div ref={shellRef} className="ce-pdf-reader">
      {status === "loading" ? (
        <p className="ce-pdf-reader__status" role="status">
          {PDF_LOADING_MESSAGE}
        </p>
      ) : null}

      {status === "error" ? (
        <p className="ce-pdf-reader__status ce-pdf-reader__status--error" role="alert">
          {PDF_ERROR_MESSAGE}{" "}
          <a
            href={CODIGO_ETICA_PDF_PATH}
            target="_blank"
            rel="noopener noreferrer"
          >
            {CODIGO_ETICA_PDF_FILENAME}
          </a>
        </p>
      ) : null}

      {status !== "error" ? (
        <Document
          file={CODIGO_ETICA_PDF_PATH}
          loading={null}
          onLoadSuccess={onLoadSuccess}
          onLoadError={onLoadError}
          className="ce-pdf-document"
        >
          {pages}
        </Document>
      ) : null}
    </div>
  );
}
