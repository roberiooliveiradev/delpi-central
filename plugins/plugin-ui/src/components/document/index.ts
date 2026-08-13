export {
  DocumentFooter,
  DocumentHeader,
  DocumentPage,
  DocumentReader,
  DocumentSignatureBlock,
  printDocumentReader,
  type DocumentFooterProps,
  type DocumentHeaderProps,
  type DocumentPageProps,
  type DocumentReaderProps,
  type DocumentSignatureBlockProps,
  type PrintDocumentReaderOptions,
} from "./DocumentReader";
export {
  DocumentPageWatermark,
  type DocumentPageWatermarkProps,
} from "./DocumentPageWatermark";
export {
  DocumentReaderToolbar,
  type DocumentReaderToolbarProps,
} from "./DocumentReaderToolbar";
export {
  buildAbntPrintFooterHtml,
  buildAbntPrintHeaderHtml,
  buildDocumentReaderPrintHtml,
  collectPrintScopeClasses,
  downloadDocumentReaderPdf,
  ensurePrintWatermarkTileCoverage,
  extractWatermarkInnerHtml,
  findActiveDocumentPage,
  parseDocumentPrintHtml,
  prepareDocumentPagePrintClone,
  printDocumentReaderInWindow,
} from "./printDocumentReaderHtml";
