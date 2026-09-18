import type { MachineLoadOperation } from "./api";

export type StatusView = {
  tone: "running" | "done" | "queued";
  label: string;
  operatorNote: string | null;
};

export function resolveStatus(operation: MachineLoadOperation): StatusView {
  const operator = operation.active_operator_name?.trim() || null;
  const balanceExhausted = hasExhaustedOperationBalance(operation);
  // Saldo zerado manda sobre cronômetro aberto no coletor (mesmo espírito do BFF/api-delpi).
  if (
    !balanceExhausted &&
    (operation.is_in_production || operation.production_status === "in_progress")
  ) {
    return {
      tone: "running",
      label: "Em produção",
      operatorNote: operator
        ? `Operador ${operator}${
            operation.production_started_time ? ` · desde ${operation.production_started_time}` : ""
          }`
        : null,
    };
  }
  // «Já apontada» / risco = só saldo da operação esgotado.
  // production_status "started" só diz que houve apontamento (pode ser parcial).
  if (balanceExhausted) {
    return {
      tone: "done",
      label: "Já apontada",
      operatorNote: operator ? `Último apontamento: ${operator}` : null,
    };
  }
  return {
    tone: "queued",
    label: "Na fila",
    operatorNote:
      operator && operation.production_status === "started"
        ? `Último apontamento: ${operator}`
        : null,
  };
}

/** Saldo da própria bancada; o do cabeçalho da OP só entra em snapshot antigo.
 *
 * O saldo do SC2 não distingue operação: `C2_QUJE` só anda no apontamento que dá
 * entrada em estoque, então a operação já concluída continuaria com saldo. */
export function operationPendingQty(operation: MachineLoadOperation): number {
  const own = operation.operation_pending_qty;
  if (typeof own === "number" && Number.isFinite(own)) return own;
  return operation.pending_qty;
}

/** Saldo da operação esgotado — candidato a «Já apontada» / Limpar fila. */
export function hasExhaustedOperationBalance(operation: MachineLoadOperation): boolean {
  const pending = operationPendingQty(operation);
  return Number.isFinite(pending) && pending <= 1e-9;
}

/** Já apontada / sem saldo — candidata a sumir no «Limpar fila» do cockpit. */
export function isFinishedOperation(operation: MachineLoadOperation): boolean {
  return hasExhaustedOperationBalance(operation);
}

/**
 * Vizinha na fila com saldo ainda a produzir.
 * Usada no avançar/voltar do detalhe — operações sem saldo não entram no caminho do operador.
 */
export function findAdjacentOpenOperation(
  items: readonly MachineLoadOperation[],
  fromIndex: number,
  direction: -1 | 1,
): MachineLoadOperation | null {
  if (fromIndex < 0 || fromIndex >= items.length) return null;
  let i = fromIndex + direction;
  while (i >= 0 && i < items.length) {
    const candidate = items[i]!;
    if (!isFinishedOperation(candidate)) return candidate;
    i += direction;
  }
  return null;
}

/** Chave estável de uma operação na fila — usada como id de navegação e como key do React. */
export function operationKey(operation: MachineLoadOperation): string {
  return `${operation.production_order}::${operation.operation_code}`;
}

export function formatQty(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return "—";
  return value.toLocaleString("pt-BR", {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  });
}

/** Unidade de chão de fábrica: TOTVS envia MI (milheiro); o operador lê como peça.
 * Plural «PÇS» por padrão; singular «PÇ» só quando a quantidade é exatamente 0,001. */
export function formatUnit(unit: string | null, quantity?: number | null): string {
  const cleaned = (unit ?? "").trim();
  const isPiece = !cleaned || cleaned.toUpperCase() === "MI";
  if (!isPiece) return cleaned;
  if (
    quantity !== null &&
    quantity !== undefined &&
    Number.isFinite(quantity) &&
    Math.abs(quantity - 0.001) < 1e-9
  ) {
    return "PÇ";
  }
  return "PÇS";
}
