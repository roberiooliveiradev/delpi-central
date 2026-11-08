import type { DelpiDocumentBadgeTone, DelpiDocumentSpec } from "@delpi/plugin-ui/index";

import { PARTICIPANT_ROLES } from "../constants/kaizen";
import type { KaizenRecord, KaizenStatus, ParticipantRole } from "../types/kaizen";
import { formatCategoriesDisplay, categoriesFromRecord } from "./kaizenCategories";
import { formatCurrency, formatDate } from "./format";
import { savingsTypeLabel, statusLabel, unitLabel } from "./labels";

/** Limite de caracteres para caber em uma folha A4 (narrativa 2×2). */
export const KAIZEN_PDF_NARRATIVE_MAX_CHARS = 420;
export const KAIZEN_PDF_SUMMARY_VALUE_MAX_CHARS = 90;
export const KAIZEN_PDF_TITLE_MAX_CHARS = 120;

const ROLE_LABEL: Record<ParticipantRole, string> = Object.fromEntries(
  PARTICIPANT_ROLES.map((item) => [item.value, item.label]),
) as Record<ParticipantRole, string>;

export function truncateKaizenPdfText(
  value: string | null | undefined,
  maxChars: number,
  emptyFallback = "—",
): string {
  const trimmed = String(value ?? "").trim();
  if (!trimmed) return emptyFallback;
  if (trimmed.length <= maxChars) return trimmed;
  if (maxChars <= 1) return "…";
  return `${trimmed.slice(0, Math.max(0, maxChars - 1)).trimEnd()}…`;
}

function text(value: string | null | undefined, maxChars = KAIZEN_PDF_SUMMARY_VALUE_MAX_CHARS): string {
  return truncateKaizenPdfText(value, maxChars);
}

function badgeTone(status: KaizenStatus | string): DelpiDocumentBadgeTone {
  if (status === "implantado") return "approved";
  if (status === "cancelado" || status === "descontinuado") return "rejected";
  return "neutral";
}

function primaryAccountable(record: KaizenRecord): string {
  const fromParticipants = (record.participants ?? []).find((item) => item.role === "responsavel");
  if (fromParticipants?.name?.trim()) return fromParticipants.name.trim();
  return text(record.accountable);
}

function effectivenessLabel(record: KaizenRecord): string {
  const estimated = record.annual_savings;
  const realized = record.realized_annual_savings;
  if (estimated == null || realized == null || estimated === 0) return "—";
  const ratio = Math.round((realized / estimated) * 100);
  return `${ratio}% do estimado`;
}

function validityLabel(record: KaizenRecord): string {
  if (!record.date_implemented) return "Sem data de implantação";
  if (record.savings_active) {
    return `Ativa até ${formatDate(record.savings_valid_until)}`;
  }
  return `Encerrada em ${formatDate(record.savings_valid_until)}`;
}

function pushDateLine(
  lines: Array<{ label: string; value: string }>,
  label: string,
  value: string | null | undefined,
): void {
  if (!value) return;
  lines.push({ label, value: formatDate(value) });
}

export function buildKaizenDelpiDocumentSpec(
  record: KaizenRecord,
  photos?: { dataUrl: string; photoCount: number } | null,
): DelpiDocumentSpec {
  const title = truncateKaizenPdfText(record.title, KAIZEN_PDF_TITLE_MAX_CHARS, "Kaizen sem título");
  const status = statusLabel(record.status);
  const categories = formatCategoriesDisplay(categoriesFromRecord(record));

  const summaryLines: Array<{ label: string; value: string }> = [
    { label: "Unidade", value: unitLabel(record.branch_code) },
    { label: "Setor", value: text(record.sector) },
    { label: "Categorias", value: text(categories) },
    { label: "Investimento", value: formatCurrency(record.investment) },
    { label: "Responsável", value: primaryAccountable(record) },
    { label: "Tipo de economia", value: savingsTypeLabel(record.savings_type) },
    {
      label: "Economia/dia (est.)",
      value: formatCurrency(record.daily_savings),
    },
    {
      label: "Economia/dia (real.)",
      value: formatCurrency(record.realized_daily_savings),
    },
    {
      label: "Economia/ano (est.)",
      value: formatCurrency(record.annual_savings),
    },
    {
      label: "Economia/ano (real.)",
      value: formatCurrency(record.realized_annual_savings),
    },
    { label: "Efetividade", value: effectivenessLabel(record) },
    { label: "Validade dos ganhos", value: validityLabel(record) },
  ];

  pushDateLine(summaryLines, "Data da ideia", record.date_idea_received);
  pushDateLine(summaryLines, "Data do comitê", record.date_committee_approved);
  pushDateLine(summaryLines, "Implantação", record.date_implemented);
  pushDateLine(summaryLines, "Descontinuação", record.date_discontinued);

  const participants = record.participants ?? [];
  // Compacta a narrativa apenas quando há fotos, mantendo a ficha legível em A4.
  const narrativeLimit = photos ? 180 : KAIZEN_PDF_NARRATIVE_MAX_CHARS;
  const tables =
    participants.length > 0
      ? [
          {
            title: "Equipe",
            columns: [
              { key: "name", label: "Nome" },
              { key: "role", label: "Papel" },
            ],
            rows: participants.map((item) => ({
              name: text(item.name),
              role: ROLE_LABEL[item.role] ?? item.role,
            })),
          },
        ]
      : undefined;

  return {
    documentTitle: "Ficha Kaizen",
    subtitle: title,
    badge: status,
    badgeTone: badgeTone(record.status),
    runningMeta: title,
    summaryLines,
    textSections: [
      {
        title: "Processo",
        body: truncateKaizenPdfText(record.process_description, narrativeLimit),
      },
      {
        title: "Problema",
        body: truncateKaizenPdfText(record.problem_description, narrativeLimit),
      },
      {
        title: "Melhoria",
        body: truncateKaizenPdfText(record.improvement_description, narrativeLimit),
      },
      {
        title: "Resultado esperado",
        body: truncateKaizenPdfText(record.expected_result, narrativeLimit),
      },
    ],
    tables,
    imageSections: photos
      ? [{ title: "Evidências fotográficas", dataUrl: photos.dataUrl, alt: "Fotografias do Kaizen" }]
      : undefined,
    footerNote: photos
      ? "Ficha resumida. Fotos selecionadas da versão exibida; demais anexos e histórico disponíveis no Kaizômetro."
      : "Ficha resumida. Sem fotografias nesta versão; histórico e anexos disponíveis no Kaizômetro.",
    footerContext: title,
  };
}
