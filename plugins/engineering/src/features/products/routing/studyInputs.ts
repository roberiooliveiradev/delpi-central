/** Validação dos inputs PROVIDed do estudo de balanceamento — módulo
 * neutro compartilhado entre a aba Roteiro da Ficha do Produto e a
 * ferramenta Processos > Balanceamento de Linha. As regras espelham o
 * domínio (demanda e disponível > 0, pausas < turno, opcionais
 * positivos quando presentes); a validação efetiva é sempre do
 * contrato `POST /v1/products/{code}/line-balance`. */

import type { StudyInputs } from "./routingStudyDraft";

export type BalanceRunParamsInput = {
  demand: number;
  available_minutes: number;
  num_stations?: number;
  batch_size?: number;
  branch?: string;
};

export type StudyValidation = {
  errors: string[];
  params: BalanceRunParamsInput | null;
  taktPreview: number | null;
};

export function numberOrUndefined(text: string): number | undefined {
  const trimmed = text.trim();
  if (!trimmed) return undefined;
  const n = Number(trimmed.replace(",", "."));
  return Number.isFinite(n) ? n : undefined;
}

export function validateStudyInputs(
  inputs: StudyInputs,
  branch: string,
): StudyValidation {
  const demandN = numberOrUndefined(inputs.demand);
  const shiftN = numberOrUndefined(inputs.shiftMinutes);
  const breakParsed = numberOrUndefined(inputs.breakMinutes);
  const breakN = breakParsed ?? 0;
  const stationsN = numberOrUndefined(inputs.numStations);
  const batchN = numberOrUndefined(inputs.batchSize);

  const errors: string[] = [];
  if (inputs.demand.trim() && !(demandN !== undefined && demandN > 0)) {
    errors.push("Demanda deve ser um número maior que zero.");
  }
  if (inputs.shiftMinutes.trim() && !(shiftN !== undefined && shiftN > 0)) {
    errors.push("Duração do turno deve ser maior que zero.");
  }
  if (
    inputs.breakMinutes.trim() &&
    (breakParsed === undefined || breakParsed < 0)
  ) {
    errors.push("Pausas devem ser um número não negativo.");
  }
  if (
    shiftN !== undefined &&
    shiftN > 0 &&
    inputs.breakMinutes.trim() &&
    breakN >= shiftN
  ) {
    errors.push("Pausas devem ser menores que a duração do turno.");
  }
  if (
    inputs.numStations.trim() &&
    !(stationsN !== undefined && stationsN > 0)
  ) {
    errors.push("Número de postos deve ser positivo.");
  }
  if (inputs.batchSize.trim() && !(batchN !== undefined && batchN > 0)) {
    errors.push("Tamanho do lote deve ser positivo.");
  }
  const available = shiftN !== undefined ? shiftN - breakN : undefined;
  const valid =
    demandN !== undefined &&
    demandN > 0 &&
    available !== undefined &&
    available > 0 &&
    errors.length === 0;
  const params = valid
    ? {
        demand: demandN!,
        available_minutes: available!,
        ...(stationsN ? { num_stations: stationsN } : {}),
        ...(batchN ? { batch_size: batchN } : {}),
        ...(branch ? { branch } : {}),
      }
    : null;
  const taktPreview =
    params && demandN ? params.available_minutes / demandN : null;
  return { errors, params, taktPreview };
}

export const SAVE_STATUS_LABEL: Record<string, string> = {
  saving: "Salvando…",
  saved: "Salvo nesta aba",
  save_error: "Não foi possível salvar o rascunho",
  storage_unavailable:
    "Rascunho não persistido — armazenamento de sessão indisponível",
};
