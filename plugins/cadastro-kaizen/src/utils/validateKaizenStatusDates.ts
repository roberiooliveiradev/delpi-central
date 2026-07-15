import type { KaizenFormValues, KaizenStatus } from "../types/kaizen";

/** Espelha `kaizen_status_date_rules` da API. */
export function validateKaizenStatusDates(values: {
  status: KaizenStatus | string;
  date_committee_approved?: string | null;
  date_implemented?: string | null;
}): string | null {
  const status = String(values.status || "").trim().toLowerCase();
  const committee = String(values.date_committee_approved || "").trim();
  const implemented = String(values.date_implemented || "").trim();

  if (status === "aprovado" && !committee) {
    return "Informe a data de aprovação no comitê para o status Aprovado.";
  }
  if (status === "implantado" && !implemented) {
    return "Informe a data de implantação para o status Implantado.";
  }
  return null;
}

export function validateKaizenFormStatusDates(values: KaizenFormValues): string | null {
  return validateKaizenStatusDates(values);
}
