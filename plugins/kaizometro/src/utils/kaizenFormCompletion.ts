import { visibleSavingsParamFields } from "../constants/kaizen";
import type { KaizenFormValues } from "../types/kaizen";

export type CompletionItem = { id: string; label: string; done: boolean };

export type FormCompletion = {
  percent: number;
  done: number;
  total: number;
  items: CompletionItem[];
};

function filled(value: string | null | undefined): boolean {
  return typeof value === "string" && value.trim().length > 0;
}

/** A economia está "preenchida" quando é qualitativa ou tem algum parâmetro/realizada. */
function isSavingsFilled(values: KaizenFormValues): boolean {
  if (values.savings_type === "qualitativo") return true;
  const params = visibleSavingsParamFields(values.savings_type);
  const anyParam = params.some((field) => filled(values[field]));
  return anyParam || filled(values.realized_daily_savings);
}

/** Percentual de preenchimento dos campos relevantes do cadastro (padrão quality-action-plans). */
export function computeKaizenFormCompletion(values: KaizenFormValues): FormCompletion {
  const items: CompletionItem[] = [
    { id: "title", label: "Título", done: filled(values.title) },
    { id: "branch", label: "Unidade", done: filled(values.branch_code) },
    { id: "sector", label: "Setor", done: filled(values.sector) },
    { id: "category", label: "Categoria", done: values.categories.length > 0 },
    {
      id: "team",
      label: "Equipe",
      done: values.participants.some((participant) => participant.name.trim().length > 0),
    },
    { id: "process", label: "Processo", done: filled(values.process_description) },
    { id: "improvement", label: "Melhoria", done: filled(values.improvement_description) },
    { id: "idea", label: "Recebimento da ideia", done: filled(values.date_idea_received) },
    {
      id: "committee",
      label: "Aprovação no comitê",
      done: filled(values.date_committee_approved),
    },
    { id: "date", label: "Implantação", done: filled(values.date_implemented) },
    { id: "savings", label: "Economia", done: isSavingsFilled(values) },
  ];

  const done = items.filter((item) => item.done).length;
  const percent = Math.round((done / items.length) * 100);
  return { percent, done, total: items.length, items };
}
