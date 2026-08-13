import { Download, Printer } from "lucide-react";
import { useState } from "react";

import { printDocumentReader } from "./DocumentReader";

export type DocumentReaderToolbarProps = {
  /** Rótulo à esquerda (ex.: "Documento"). */
  label?: string;
  printLabel?: string;
  downloadPdfLabel?: string;
  downloadingLabel?: string;
  /** Título da janela de impressão. */
  printTitle?: string;
  /** Se omitido, o botão Baixar PDF não aparece. */
  onDownloadPdf?: () => void | Promise<void>;
  disabled?: boolean;
  className?: string;
};

/**
 * Toolbar canônica do DocumentReader: Imprimir (janela dedicada) + Baixar PDF
 * (callback autenticado do consumidor — nunca `<a href>` sem Authorization).
 */
export function DocumentReaderToolbar({
  label = "Documento",
  printLabel = "Imprimir",
  downloadPdfLabel = "Baixar PDF",
  downloadingLabel = "Gerando…",
  printTitle,
  onDownloadPdf,
  disabled = false,
  className,
}: DocumentReaderToolbarProps) {
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    if (!onDownloadPdf || disabled || downloading) return;
    setDownloading(true);
    try {
      await onDownloadPdf();
    } finally {
      setDownloading(false);
    }
  }

  return (
    <div
      className={["delpi-ui-document-reader-toolbar", className].filter(Boolean).join(" ")}
    >
      <span className="delpi-ui-document-reader-toolbar__label">{label}</span>
      <div className="delpi-ui-document-reader-toolbar__actions">
        <button
          type="button"
          className="delpi-ui-document-reader-toolbar__btn"
          disabled={disabled}
          onClick={() => printDocumentReader({ title: printTitle })}
          data-testid="document-reader-print"
        >
          <Printer size={15} aria-hidden />
          {printLabel}
        </button>
        {onDownloadPdf ? (
          <button
            type="button"
            className="delpi-ui-document-reader-toolbar__btn"
            disabled={disabled || downloading}
            onClick={() => void handleDownload()}
            data-testid="document-reader-download-pdf"
          >
            <Download size={15} aria-hidden />
            {downloading ? downloadingLabel : downloadPdfLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}
