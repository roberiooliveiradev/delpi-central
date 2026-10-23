/**
 * Apresentação de fonte externa e instante de consulta (S9.B/S9.C,
 * estendido ao enriquecimento E14 em S9.R1).
 *
 * Fuso fixo de apresentação — independente do relógio da máquina.
 * Os timestamps vêm com offset explícito (ISO-8601); aqui só projetamos
 * o instante para exibição, nunca alteramos o valor do contrato.
 */
export const PORTAL_TIME_ZONE = "America/Sao_Paulo";
export const PORTAL_TIME_ZONE_LABEL = "horário de Brasília";

export function formatRetrievedAt(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const parts = new Intl.DateTimeFormat("pt-BR", {
    timeZone: PORTAL_TIME_ZONE,
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  const get = (type: string) =>
    parts.find((part) => part.type === type)?.value ?? "";
  return `${get("day")}/${get("month")}/${get("year")} às ${get("hour")}:${get("minute")} (${PORTAL_TIME_ZONE_LABEL})`;
}

/**
 * Nome amigável do provedor externo — o identificador técnico
 * (`provider_id`/`source_id`) permanece intacto no contrato; aqui só
 * mapeamos a apresentação. Fallback honesto: mostra o próprio
 * identificador, sem inventar marca.
 */
const PROVIDER_DISPLAY_NAMES: Record<string, string> = {
  "brasilapi-cnpj-v1": "BrasilAPI — dados públicos de terceiros",
};

export function providerDisplayName(providerId: string): string {
  return PROVIDER_DISPLAY_NAMES[providerId] ?? providerId;
}
