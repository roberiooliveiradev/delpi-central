import { parseBrDatetimeDisplay } from "./datetimeLocal";

export type ReposicaoFormField =
  | "codigoPeca"
  | "dataReposicao"
  | "dataUltimaReposicao"
  | "golpes"
  | "motivoId";

export type ReposicaoFormErrors = Partial<Record<ReposicaoFormField, string>>;

const ISO_DATETIME_LOCAL = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;

export function resolveDatetimeLocalValue(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  if (ISO_DATETIME_LOCAL.test(trimmed)) return trimmed;
  const parsed = parseBrDatetimeDisplay(trimmed);
  if (parsed === null || parsed === "") return null;
  return parsed;
}

function datetimeLocalToMs(value: string): number | null {
  const resolved = resolveDatetimeLocalValue(value);
  if (!resolved) return null;
  const date = new Date(resolved);
  return Number.isNaN(date.getTime()) ? null : date.getTime();
}

export function validateReposicaoForm(input: {
  codigoPeca: string;
  dataReposicao: string;
  dataUltimaReposicao: string;
  golpes: number;
  motivoId: number | "";
  requireDataUltima?: boolean;
}): ReposicaoFormErrors {
  const errors: ReposicaoFormErrors = {};

  if (!input.codigoPeca.trim()) {
    errors.codigoPeca = "Selecione a peça.";
  }

  if (!resolveDatetimeLocalValue(input.dataReposicao)) {
    errors.dataReposicao = "Informe a data da reposição no formato dd/mm/aaaa HH:mm.";
  }

  if (input.requireDataUltima && !resolveDatetimeLocalValue(input.dataUltimaReposicao)) {
    errors.dataUltimaReposicao = "Informe a data da última reposição no formato dd/mm/aaaa HH:mm.";
  } else if (
    input.dataUltimaReposicao.trim() &&
    !resolveDatetimeLocalValue(input.dataUltimaReposicao)
  ) {
    errors.dataUltimaReposicao = "Data da última reposição inválida. Use dd/mm/aaaa HH:mm.";
  }

  if (input.motivoId === "") {
    errors.motivoId = "Selecione o motivo.";
  }

  if (!Number.isFinite(input.golpes) || input.golpes <= 0) {
    errors.golpes = "Informe golpes maior que zero ou use «Sugerir golpes».";
  }

  const reposicaoMs = datetimeLocalToMs(input.dataReposicao);
  const ultimaMs = datetimeLocalToMs(input.dataUltimaReposicao);
  if (
    reposicaoMs !== null &&
    ultimaMs !== null &&
    reposicaoMs <= ultimaMs &&
    !errors.dataReposicao &&
    !errors.dataUltimaReposicao
  ) {
    errors.dataReposicao = "Data de reposição deve ser posterior à última reposição.";
  }

  return errors;
}

export function mapReposicaoApiError(message: string): ReposicaoFormErrors {
  const normalized = message.trim();
  if (!normalized) return {};

  if (/peça/i.test(normalized)) return { codigoPeca: normalized };
  if (/motivo/i.test(normalized)) return { motivoId: normalized };
  if (/golpes/i.test(normalized)) return { golpes: normalized };
  if (/posterior à última reposição/i.test(normalized)) return { dataReposicao: normalized };
  if (/última reposição/i.test(normalized)) return { dataUltimaReposicao: normalized };
  if (/data de reposição/i.test(normalized)) return { dataReposicao: normalized };

  return { dataReposicao: normalized };
}

export function hasReposicaoFormErrors(errors: ReposicaoFormErrors): boolean {
  return Object.keys(errors).length > 0;
}
