import { isHtmlEmpty } from "./htmlContent";

type MinuteVersionFields = {
  agenda_html?: string | null;
  body_html?: string | null;
  decisions_html?: string | null;
  pending_html?: string | null;
};

const SECTIONS = [
  { key: "agenda_html" as const, title: "Pauta" },
  { key: "body_html" as const, title: "Conteúdo" },
  { key: "decisions_html" as const, title: "Decisões" },
  { key: "pending_html" as const, title: "Pendências" },
];

/** Une seções legadas em um único HTML para edição contínua. */
export function mergeMinuteContentHtml(version: MinuteVersionFields | null | undefined): string {
  if (!version) return "<p></p>";

  const filled = SECTIONS.filter((section) => !isHtmlEmpty(version[section.key]));
  if (filled.length === 0) return "<p></p>";
  if (filled.length === 1) return String(version[filled[0].key] || "<p></p>");

  return filled
    .map((section) => {
      const html = String(version[section.key] || "");
      return `<h2>${section.title}</h2>${html}`;
    })
    .join("");
}

/** Persistência: conteúdo unificado vai para body_html; demais campos ficam vazios. */
export function splitMinuteContentForSave(contentHtml: string) {
  return {
    agenda_html: "<p></p>",
    body_html: contentHtml || "<p></p>",
    decisions_html: "<p></p>",
    pending_html: "<p></p>",
  };
}
