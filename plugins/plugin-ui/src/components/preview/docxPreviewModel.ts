import { normalizeRichTextPastedHtml } from "../rich-text/richTextTable";

export type DocxPreviewData = {
  html: string;
  truncated: boolean;
};

const MAX_DOCX_HTML_CHARS = 250_000;

/** Aplica classes de tabela do rich text quando o DOCX trouxer `<table>`. */
function normalizeDocxHtml(html: string): string {
  if (!/<table[\s>]/i.test(html)) return html;
  return normalizeRichTextPastedHtml(html) || html;
}

export async function parseDocxPreview(blob: Blob): Promise<DocxPreviewData> {
  const mammoth = await import("mammoth");
  const arrayBuffer = await blob.arrayBuffer();
  const result = await mammoth.convertToHtml({ arrayBuffer });
  const html = normalizeDocxHtml(result.value.trim());

  if (!html) {
    return {
      html: "<p>Documento vazio.</p>",
      truncated: false,
    };
  }

  if (html.length > MAX_DOCX_HTML_CHARS) {
    return {
      html: html.slice(0, MAX_DOCX_HTML_CHARS),
      truncated: true,
    };
  }

  return {
    html,
    truncated: false,
  };
}
