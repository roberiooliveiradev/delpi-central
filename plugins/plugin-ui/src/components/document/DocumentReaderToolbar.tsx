import { Download, Printer } from "lucide-react";
import { useState } from "react";

import { printDocumentReader } from "./DocumentReader";
import { downloadDocumentReaderPdf } from "./printDocumentReaderHtml";

export type DocumentReaderToolbarProps = {
  /** Rótulo à esquerda (ex.: "Documento"). */
  label?: string;
  printLabel?: string;
  downloadPdfLabel?: string;
  downloadingLabel?: string;
  /** Título da janela de impressão / PDF. */
  printTitle?: string;
  /**
   * Override opcional (ex.: PDF arquivado no servidor).
   * Sem override, Baixar PDF usa o HTML da prévia (mesmo fluxo da impressão).
   */
  onDownloadPdf?: () => void | Promise<void>;
  /** Quando false, esconde Baixar PDF. Default: true. */
  showDownloadPdf?: boolean;
  disabled?: boolean;
  className?: string;
};

/**
 * Toolbar canônica: Imprimir + Baixar PDF com a formatação do DocumentReader.
 * PDF padrão = janela dedicada (Salvar como PDF) — paridade com a prévia.
 */
export function DocumentReaderToolbar({
  label = "Documento",
  printLabel = "Imprimir",
  downloadPdfLabel = "Baixar PDF",
  downloadingLabel = "Gerando…",
  printTitle,
  onDownloadPdf,
  showDownloadPdf = true,
  disabled = false,
  className,
}: DocumentReaderToolbarProps) {
  const [downloading, setDownloading] = useState(false);

  async function handleDownload() {
    if (disabled || downloading) return;
    if (onDownloadPdf) {
      setDownloading(true);
      try {
        await onDownloadPdf();
      } finally {
        setDownloading(false);
      }
      return;
    }
    downloadDocumentReaderPdf({ title: printTitle });
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
        {showDownloadPdf ? (
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
