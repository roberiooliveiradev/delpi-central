/**
 * Lógica pura da troca guiada de OP (E2) — sem React nem fetch.
 *
 * Aqui vivem a política de requestId (idempotência por intenção), a
 * classificação dos códigos de erro da E1 e os textos de UI. O backend
 * é a autoridade; este módulo apenas traduz o contrato para decisões
 * de apresentação testáveis.
 */

import { ApiError } from "./api.ts";

/** Intenção confirmada da troca — chave idempotente + alvo esperado. */
export type RunHandoffIntent = {
  requestId: string;
  expectedNext: { productionOrder: string; operationCode: string };
};

/** Assinatura estável da intenção — define quando a chave pode ser reusada. */
export function handoffIntentSignature(
  intent: Pick<RunHandoffIntent, "expectedNext">,
): string {
  return JSON.stringify({
    productionOrder: String(intent.expectedNext.productionOrder ?? ""),
    operationCode: String(intent.expectedNext.operationCode ?? ""),
  });
}

/**
 * Geração do requestId: somente Web Crypto — `crypto.randomUUID()`
 * quando disponível; em contexto inseguro (tablet HTTP na intranet)
 * cai para `getRandomValues` (presente mesmo sem origem segura).
 *
 * SEM fallback de `Math.random`: chave idempotente fraca corromperia a
 * deduplicação do backend. Sem fonte criptográfica retorna `null` e o
 * controlador bloqueia a confirmação com mensagem recuperável — a troca
 * nunca sai com requestId previsível.
 */
export function newHandoffRequestId(): string | null {
  const cryptoApi = globalThis.crypto;
  if (typeof cryptoApi?.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }
  if (typeof cryptoApi?.getRandomValues !== "function") return null;
  const bytes = new Uint8Array(16);
  cryptoApi.getRandomValues(bytes);
  bytes[6] = (bytes[6]! & 0x0f) | 0x40;
  bytes[8] = (bytes[8]! & 0x3f) | 0x80;
  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
  return [
    hex.slice(0, 4).join(""),
    hex.slice(4, 6).join(""),
    hex.slice(6, 8).join(""),
    hex.slice(8, 10).join(""),
    hex.slice(10, 16).join(""),
  ].join("-");
}

/**
 * Intenção com resultado desconhecido — registrada antes do POST e só
 * removida quando o backend responde de forma definitiva (sucesso ou
 * erro estruturado). Vive no módulo (não no React): sobrevive a remount
 * do controlador ao navegar entre o card "Agora nesta bancada" e o
 * detalhe da operação, e impede que fechar/remontar a interface descarte
 * a intenção antes da reconciliação segura (E2.RQ-06).
 */
const pendingHandoffIntents = new Map<string, RunHandoffIntent>();

export function registerPendingHandoffIntent(
  runId: string,
  intent: RunHandoffIntent,
): void {
  pendingHandoffIntents.set(runId, intent);
}

export function pendingHandoffIntentFor(
  runId: string,
): RunHandoffIntent | null {
  return pendingHandoffIntents.get(runId) ?? null;
}

/** Só chamar quando a intenção foi resolvida de forma definitiva. */
export function clearPendingHandoffIntent(runId: string): void {
  pendingHandoffIntents.delete(runId);
}

/**
 * Resultado incerto: a resposta HTTP não chegou (rede/timeout) ou o
 * gateway respondeu 502/503 — a transação pode ter commitado. A única
 * resolução segura é repetir o MESMO requestId (replay idempotente)
 * ou reconciliar pelo estado autoritativo; nunca gerar nova chave.
 */
export function isUncertainHandoffError(err: unknown): boolean {
  if (err instanceof ApiError) {
    return err.status === 502 || err.status === 503;
  }
  return true;
}

/** Códigos estruturados do contrato E1 (409 → data.code). */
export const HANDOFF_ERROR_CODES = [
  "no_next_operation",
  "current_not_in_queue",
  "queue_changed",
  "balance_unknown",
  "run_not_active",
  "device_mismatch",
  "epoch_conflict",
  "count_boundary_stale",
  "request_conflict",
  "pending_classification",
  "pulse_unavailable",
] as const;

export type HandoffErrorCode = (typeof HANDOFF_ERROR_CODES)[number];

export type HandoffConflictAction =
  | "refresh_preview" // prévia nova + escolha explícita do operador
  | "classify" // abrir o fluxo existente de classificação de parada
  | "reconcile" // reler run/fila — o estado autoritativo mudou
  | "none";

export type HandoffConflictView = {
  code: HandoffErrorCode | string;
  title: string;
  message: string;
  /** Ação sugerida ao operador além de cancelar. */
  action: HandoffConflictAction;
  /** A opção "Ir para a próxima OP" deve ficar desabilitada. */
  blocksNext: boolean;
};

/**
 * Tradução dos 409 estruturados da E1 para decisão de UI.
 * Nenhum código autoriza encerramento automático — o Stop tradicional
 * continua uma escolha consciente do operador na opção A.
 */
export function handoffConflictView(
  code: string | undefined,
  serverMessage?: string | null,
): HandoffConflictView {
  const message = String(serverMessage ?? "").trim();
  switch (code) {
    case "count_boundary_stale":
      return {
        code,
        title: "Contagem atualizada pelo contador",
        message:
          message ||
          "A contagem do contador avançou desde a prévia. Confira a prévia atualizada e confirme de novo.",
        action: "refresh_preview",
        blocksNext: true,
      };
    case "queue_changed":
      return {
        code,
        title: "Sequência alterada pelo PCP",
        message:
          message ||
          "A fila publicada mudou desde a prévia. Confira a nova próxima OP antes de confirmar.",
        action: "refresh_preview",
        blocksNext: true,
      };
    case "no_next_operation":
      return {
        code,
        title: "Sem próxima OP",
        message:
          message || "Não há próxima OP disponível para este posto.",
        action: "none",
        blocksNext: true,
      };
    case "balance_unknown":
      return {
        code,
        title: "Saldo da próxima OP indisponível",
        message:
          message ||
          "O saldo da próxima operação não foi informado. Regularize a fila no PCP para trocar de OP.",
        action: "none",
        blocksNext: true,
      };
    case "pending_classification":
      return {
        code,
        title: "Parada sem motivo",
        message:
          message ||
          "Há uma parada sem motivo informado. Classifique-a antes de trocar de OP.",
        action: "classify",
        blocksNext: true,
      };
    case "pulse_unavailable":
      return {
        code,
        title: "Contador indisponível",
        message:
          message ||
          "O contador do posto está indisponível. A troca precisa do contador para ancorar a nova OP.",
        action: "refresh_preview",
        blocksNext: true,
      };
    case "device_mismatch":
    case "epoch_conflict":
      return {
        code,
        title: "Contador divergente",
        message:
          message ||
          "O contador observado não corresponde ao registrado para este posto. Avise a liderança.",
        action: "none",
        blocksNext: true,
      };
    case "current_not_in_queue":
    case "run_not_active":
      return {
        code,
        title: "Produção já atualizada",
        message:
          message ||
          "Esta produção não está mais ativa nesta posição da fila. O painel será atualizado.",
        action: "reconcile",
        blocksNext: true,
      };
    case "request_conflict":
      return {
        code,
        title: "Pedido já registrado",
        message:
          message ||
          "Este pedido já foi registrado com outros dados. Atualize a prévia e confirme de novo.",
        action: "refresh_preview",
        blocksNext: true,
      };
    default:
      return {
        code: code ?? "unknown",
        title: "Troca indisponível",
        message: message || "Não foi possível trocar de OP agora. Tente novamente.",
        action: "refresh_preview",
        blocksNext: true,
      };
  }
}
