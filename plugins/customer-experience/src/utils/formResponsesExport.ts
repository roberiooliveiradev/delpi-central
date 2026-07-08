import type { FormDetail, FormQuestion, FormResponseItem } from "../types";
import {
  exportTableCsv,
  exportTableExcel,
  exportTablePdf,
  type ExportTable,
  sanitizeFilename,
} from "./exportDocument";

export type ResponseExportFormat = "csv" | "xlsx" | "pdf";

function formatAnswerValue(value: string | number | string[] | null | undefined): string {
  if (value == null) return "";
  if (Array.isArray(value)) return value.join("; ");
  return String(value);
}

function formatDatePt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString("pt-BR");
}

/** Colunas estáveis: metadados + uma coluna por pergunta ativa (ordem do formulário). */
export function buildResponsesExportTable(
  form: FormDetail,
  items: FormResponseItem[],
): ExportTable {
  const questions: FormQuestion[] = form.questions ?? [];
  const headers = ["Nome", "Empresa", "Data", ...questions.map((q) => q.label || "Pergunta")];

  const rows = items.map((item) => {
    const byQuestion = new Map(item.answers.map((a) => [a.questionId, a.value]));
    return [
      item.respondentName ?? "",
      item.respondentCompany ?? "",
      formatDatePt(item.createdAt),
      ...questions.map((q) => formatAnswerValue(byQuestion.get(q.id ?? "") ?? null)),
    ];
  });

  return {
    title: `Respostas — ${form.title}`,
    sheetName: "Respostas",
    headers,
    rows,
  };
}

export async function exportFormResponses(
  form: FormDetail,
  items: FormResponseItem[],
  format: ResponseExportFormat,
): Promise<void> {
  const table = buildResponsesExportTable(form, items);
  const filename = `respostas-${sanitizeFilename(form.title)}`;
  if (format === "csv") {
    exportTableCsv(table, filename);
    return;
  }
  if (format === "xlsx") {
    await exportTableExcel(table, filename);
    return;
  }
  await exportTablePdf(table, filename);
}
