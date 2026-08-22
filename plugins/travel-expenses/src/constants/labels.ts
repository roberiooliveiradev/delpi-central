export const STATUS_LABELS: Record<string, string> = {
  draft: "Rascunho",
  submitted: "Enviada",
  returned: "Devolvida",
  approved: "Aprovada",
  in_finance: "No financeiro",
  closed: "Encerrada",
};

export const UNIT_LABELS: Record<string, string> = {
  "01": "Santa Catarina",
  "02": "Espírito Santo",
};

export const CATEGORY_LABELS: Record<string, string> = {
  lodging: "Hospedagem",
  meals: "Alimentação",
  fuel: "Combustível",
  ground_transport: "Deslocamento",
  air_transport: "Aéreo",
  toll: "Pedágio",
  parking: "Estacionamento",
  communication: "Comunicação",
  other: "Outros",
};

export function formatBrl(value: number | undefined | null) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    Number(value || 0),
  );
}

export function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  const [year, month, day] = value.slice(0, 10).split("-");
  if (!year || !month || !day) return value;
  return `${day}/${month}/${year}`;
}
