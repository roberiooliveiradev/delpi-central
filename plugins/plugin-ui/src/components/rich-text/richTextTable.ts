import type {
  DelpiTableInsertPreset,
  DelpiTableInsertSelection,
} from "../charts/chartCatalogTypes";
import { execRichTextCommand } from "./richTextCommands";

const TABLE_CLASS = "delpi-ui-rich-text-table";
const PRESET_CLASS: Record<DelpiTableInsertPreset, string> = {
  grid: `${TABLE_CLASS}--grid`,
  minimal: `${TABLE_CLASS}--minimal`,
  banded: `${TABLE_CLASS}--banded`,
};

function focusEditor(editor: HTMLElement | null) {
  editor?.focus();
}

/** HTML de tabela WYSIWYG (cabeçalho na 1ª linha + preset visual). */
export function buildRichTextTableHtml(selection: DelpiTableInsertSelection): string {
  const rows = Math.max(1, Math.min(20, Math.round(selection.rows)));
  const cols = Math.max(1, Math.min(12, Math.round(selection.cols)));
  const preset = selection.preset in PRESET_CLASS ? selection.preset : "grid";
  const className = [TABLE_CLASS, PRESET_CLASS[preset]].join(" ");

  const bodyRows: string[] = [];
  for (let row = 0; row < rows; row += 1) {
    const cells: string[] = [];
    for (let col = 0; col < cols; col += 1) {
      if (row === 0) {
        cells.push(`<th>Coluna ${col + 1}</th>`);
      } else {
        cells.push("<td><br></td>");
      }
    }
    bodyRows.push(`<tr>${cells.join("")}</tr>`);
  }

  return `<table class="${className}"><tbody>${bodyRows.join("")}</tbody></table><p><br></p>`;
}

/** Insere tabela na seleção/caret do contentEditable. */
export function insertRichTextTable(
  editor: HTMLElement | null,
  selection: DelpiTableInsertSelection,
) {
  if (!editor) return;
  focusEditor(editor);
  execRichTextCommand("insertHTML", buildRichTextTableHtml(selection));
}

/** Tabela que contém a seleção atual (ou null). */
export function findRichTextTableAtSelection(
  editor: HTMLElement | null,
): HTMLTableElement | null {
  if (!editor) return null;
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const node = selection.getRangeAt(0).commonAncestorContainer;
  const element = node instanceof Element ? node : node.parentElement;
  const table = element?.closest("table");
  if (!table || !editor.contains(table)) return null;
  return table as HTMLTableElement;
}

/**
 * Normaliza HTML colado: marca tabelas com classes do editor e remove
 * scripts/handlers. Retorna null se não houver conteúdo útil.
 */
export function normalizeRichTextPastedHtml(html: string): string | null {
  const trimmed = html.trim();
  if (!trimmed) return null;
  const doc = new DOMParser().parseFromString(trimmed, "text/html");
  doc.querySelectorAll("script, style, iframe, object, embed, form").forEach((el) => {
    el.remove();
  });
  doc.querySelectorAll("*").forEach((el) => {
    for (const attr of Array.from(el.attributes)) {
      if (attr.name.startsWith("on")) el.removeAttribute(attr.name);
    }
  });

  const tables = doc.querySelectorAll("table");
  if (tables.length === 0 && !/<[a-z][\s\S]*>/i.test(trimmed)) {
    return null;
  }

  tables.forEach((table) => {
    table.classList.add(TABLE_CLASS);
    const hasPreset = Array.from(table.classList).some((name) =>
      name.startsWith(`${TABLE_CLASS}--`),
    );
    if (!hasPreset) table.classList.add(PRESET_CLASS.grid);
  });

  return doc.body.innerHTML;
}

export type { DelpiTableInsertPreset, DelpiTableInsertSelection };
