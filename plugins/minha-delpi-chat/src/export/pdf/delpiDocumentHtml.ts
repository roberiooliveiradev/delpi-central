import { buildDelpiBrandBarHtml, buildDelpiDocumentStyles } from "./delpiDocumentStyles";
import {
  buildDelpiDocumentColgroup,
  resolveDelpiDocumentColumnLayouts,
  resolveDelpiDocumentTableClassName,
} from "./delpiDocumentTableLayout";
import type {
  DelpiDocumentImageSection,
  DelpiDocumentSpec,
  DelpiDocumentSummaryLine,
  DelpiDocumentTable,
} from "./types";

export function escapeDelpiDocumentHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function resolveDelpiLogoUrl(): string | undefined {
  return typeof window !== "undefined" ? `${window.location.origin}/logoDelpi.svg` : undefined;
}

function buildLogoMarkup(logoUrl?: string): string {
  return logoUrl
    ? `<img class="cert-logo" src="${escapeDelpiDocumentHtml(logoUrl)}" alt="DELPI Conexões Elétricas" />`
    : "";
}

function buildSealHtml(badge: string | undefined, badgeTone: DelpiDocumentSpec["badgeTone"]): string {
  if (!badge?.trim()) {
    return "";
  }

  const toneClass =
    badgeTone === "approved"
      ? "cert-seal--approved"
      : badgeTone === "rejected"
        ? "cert-seal--rejected"
        : "cert-seal--neutral";

  return `<div class="cert-seal ${toneClass}">${escapeDelpiDocumentHtml(badge)}</div>`;
}

function buildCompactSealHtml(badge: string | undefined, badgeTone: DelpiDocumentSpec["badgeTone"]): string {
  if (!badge?.trim()) {
    return "";
  }

  const toneClass =
    badgeTone === "approved"
      ? "cert-seal--approved"
      : badgeTone === "rejected"
        ? "cert-seal--rejected"
        : "cert-seal--neutral";

  return `<div class="cert-seal cert-seal--compact ${toneClass}">${escapeDelpiDocumentHtml(badge)}</div>`;
}

function buildRunningHeaderHtml(
  spec: DelpiDocumentSpec,
  logoMarkup: string,
): string {
  const compactLogo = logoMarkup.replace('class="cert-logo"', 'class="cert-logo cert-logo--compact"');
  const runningMeta = spec.runningMeta || spec.subtitle || "";

  return `
    <div class="cert-print-running-header" aria-hidden="true">
      <div class="cert-print-running-header__inner">
        <div class="cert-print-running-header__brand">
          ${compactLogo}
          <div class="cert-print-running-header__text">
            <p class="cert-title cert-title--compact">${escapeDelpiDocumentHtml(spec.documentTitle)}</p>
            ${
              runningMeta
                ? `<p class="cert-running-meta">${escapeDelpiDocumentHtml(runningMeta)}</p>`
                : ""
            }
          </div>
        </div>
        ${buildCompactSealHtml(spec.badge, spec.badgeTone)}
      </div>
      ${buildDelpiBrandBarHtml("cert-print-running-header__bar")}
    </div>
  `;
}

function buildFirstPageHeaderHtml(
  spec: DelpiDocumentSpec,
  logoMarkup: string,
): string {
  return `
    <header class="cert-header cert-first-header">
      <div class="cert-header__top">
        <div class="cert-header__brand">
          ${logoMarkup}
          <div>
            <h1 class="cert-title">${escapeDelpiDocumentHtml(spec.documentTitle)}</h1>
            ${
              spec.subtitle
                ? `<p class="cert-subtitle">${escapeDelpiDocumentHtml(spec.subtitle)}</p>`
                : ""
            }
          </div>
        </div>
        ${buildSealHtml(spec.badge, spec.badgeTone)}
      </div>
      ${buildDelpiBrandBarHtml("cert-header__brand-bar")}
    </header>
  `;
}

function buildSummaryHtml(lines: DelpiDocumentSummaryLine[]): string {
  if (!lines.length) {
    return "";
  }

  const cells = lines
    .map(
      (line) =>
        `<p class="cert-info-line"><strong>${escapeDelpiDocumentHtml(line.label)}</strong>${escapeDelpiDocumentHtml(line.value)}</p>`,
    )
    .join("");

  return `
    <div class="cert-summary">
      <div class="cert-summary__grid">${cells}</div>
    </div>
  `;
}

const CODE_COLUMN_KEYS = new Set([
  "code",
  "product",
  "operation",
  "test",
  "center",
  "work_center",
]);

function sanitizeExportCellValue(raw: string, columnKey: string): string {
  const text = String(raw ?? "—");

  if (!CODE_COLUMN_KEYS.has(columnKey)) {
    return text;
  }

  const trimmed = text.trim();

  if (trimmed.startsWith("`") && trimmed.endsWith("`") && trimmed.length > 2) {
    return trimmed.slice(1, -1);
  }

  return text;
}

export function buildDelpiDocumentTableSection(table: DelpiDocumentTable): string {
  if (table.presentation === "outline" && table.outline?.trim()) {
    const sectionTitle = table.title?.trim();

    return `
    <section class="cert-section">
      ${
        sectionTitle
          ? `<h2 class="cert-section__title">${escapeDelpiDocumentHtml(sectionTitle)}</h2>`
          : ""
      }
      <pre class="cert-structure-outline">${escapeDelpiDocumentHtml(table.outline.trim())}</pre>
    </section>
  `;
  }

  const columns = table.columns ?? [];
  const rows = table.rows ?? [];

  if (!columns.length || !rows.length) {
    return "";
  }

  const columnLayouts = resolveDelpiDocumentColumnLayouts(columns, table.layoutKey);
  const tableClassName = resolveDelpiDocumentTableClassName(table.layoutKey);
  const colgroup = buildDelpiDocumentColgroup(columns, table.layoutKey);

  const header = columns
    .map((column, index) => {
      const layout = columnLayouts[index];
      const classAttr = layout?.className ? ` class="${layout.className}"` : "";

      return `<th${classAttr}>${escapeDelpiDocumentHtml(String(column.label || column.key || ""))}</th>`;
    })
    .join("");

  const body = rows
    .map((row) => {
      const cells = columns
        .map((column, index) => {
          const raw = sanitizeExportCellValue(String(row[column.key] ?? "—"), column.key);
          const layout = columnLayouts[index];
          const classes = [layout?.className].filter(Boolean);

          if (table.highlightStatusColumn && column.key === "status") {
            const lower = raw.toLowerCase();

            if (lower.includes("erro") || lower.includes("crítico")) {
              classes.push("cert-status--error");
            } else if (lower === "ok") {
              classes.push("cert-status--ok");
            }
          }

          const className = classes.length ? ` class="${classes.join(" ")}"` : "";

          return `<td${className}>${escapeDelpiDocumentHtml(raw)}</td>`;
        })
        .join("");

      return `<tr>${cells}</tr>`;
    })
    .join("");

  const sectionTitle = table.title?.trim();

  return `
    <section class="cert-section">
      ${
        sectionTitle
          ? `<h2 class="cert-section__title">${escapeDelpiDocumentHtml(sectionTitle)}</h2>`
          : ""
      }
      <table class="${tableClassName}">
        ${colgroup}
        <thead><tr>${header}</tr></thead>
        <tbody>${body}</tbody>
      </table>
    </section>
  `;
}

function buildImageSection(section: DelpiDocumentImageSection): string {
  if (!section.dataUrl.trim()) {
    return "";
  }

  const title = section.title?.trim();

  return `
    <section class="cert-section">
      ${
        title
          ? `<h2 class="cert-section__title">${escapeDelpiDocumentHtml(title)}</h2>`
          : ""
      }
      <img
        class="cert-chart-image"
        src="${escapeDelpiDocumentHtml(section.dataUrl)}"
        alt="${escapeDelpiDocumentHtml(section.alt || title || "Gráfico")}"
      />
    </section>
  `;
}

function buildPrintFooterMeta(footerContext: string): string {
  const issuedAt = new Date().toLocaleString("pt-BR");

  return `
    <footer class="cert-print-footer">
      ${buildDelpiBrandBarHtml("cert-footer__brand-bar")}
      <div class="cert-footer__meta">
        <p class="cert-footer__site">www.delpi.com.br</p>
        <p><strong>Referência:</strong> ${escapeDelpiDocumentHtml(footerContext)} · <strong>Emitido em:</strong> ${escapeDelpiDocumentHtml(
          issuedAt,
        )} · Gerado pelo Minha DELPI</p>
      </div>
    </footer>
  `;
}

export function buildDelpiDocumentHtml(
  spec: DelpiDocumentSpec,
  logoUrl?: string,
): string {
  const logoMarkup = buildLogoMarkup(logoUrl);
  const tableSections = (spec.tables ?? []).map(buildDelpiDocumentTableSection).join("");
  const imageSections = (spec.imageSections ?? []).map(buildImageSection).join("");
  const footerContext = spec.footerContext || spec.documentTitle;
  const footerNote =
    spec.footerNote || "Relatório gerado eletronicamente pelo Minha DELPI.";

  return `<!DOCTYPE html>
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <title>${escapeDelpiDocumentHtml(spec.documentTitle)}</title>
    <style>${buildDelpiDocumentStyles()}</style>
  </head>
  <body>
    ${buildRunningHeaderHtml(spec, logoMarkup)}
    <table class="cert-print-layout">
      <tbody>
        <tr>
          <td>
            <div class="cert-main cert-body-content">
              ${buildFirstPageHeaderHtml(spec, logoMarkup)}
              ${buildSummaryHtml(spec.summaryLines ?? [])}
              ${imageSections}
              ${tableSections}
              <footer class="cert-footer">
                <p>${escapeDelpiDocumentHtml(footerNote)}</p>
              </footer>
            </div>
          </td>
        </tr>
      </tbody>
      <tfoot>
        <tr>
          <td>
            <div class="cert-print-footer-spacer" aria-hidden="true"></div>
          </td>
        </tr>
      </tfoot>
    </table>
    ${buildPrintFooterMeta(footerContext)}
  </body>
</html>`;
}

export function buildDefaultExportSummaryLines(recordCount: number): DelpiDocumentSummaryLine[] {
  return [
    { label: "Registros", value: String(recordCount) },
    { label: "Emitido em", value: new Date().toLocaleString("pt-BR") },
  ];
}
