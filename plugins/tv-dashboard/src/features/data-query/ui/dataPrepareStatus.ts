export type DataPrepareStatusTone =
  | "neutral"
  | "busy"
  | "success"
  | "warning"
  | "error";

export type DataPrepareStatus = {
  tone: DataPrepareStatusTone;
  message: string;
  meta: string | null;
};

type AsyncStatus = "idle" | "loading" | "success" | "error";

export type DataPrepareStatusInput = {
  compileStatus: AsyncStatus;
  compileError: string | null;
  previewStatus: AsyncStatus;
  previewError: string | null;
  previewUpdatedAt: number | null;
  hasPreview: boolean;
  rowCount: number | null;
  runtimeErrorCount: number;
  dirtyCount: number;
  isApplying: boolean;
  applyError: string | null;
  now?: number;
};

function relativeUpdatedLabel(updatedAt: number | null, now: number): string | null {
  if (!updatedAt) return null;
  const seconds = Math.round(Math.max(0, now - updatedAt) / 1000);
  if (seconds < 5) return "atualizado agora";
  if (seconds < 60) return `atualizado há ${seconds}s`;
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `atualizado há ${minutes} min`;
  return `atualizado há ${Math.round(minutes / 60)} h`;
}

function statusMeta(input: DataPrepareStatusInput): string | null {
  const items: string[] = [];
  const updated = relativeUpdatedLabel(input.previewUpdatedAt, input.now ?? Date.now());
  if (updated) items.push(updated);
  if (input.rowCount != null) items.push(`${input.rowCount} linha(s)`);
  if (input.dirtyCount > 0) items.push(`${input.dirtyCount} consulta(s) alterada(s)`);
  return items.length > 0 ? items.join(" · ") : null;
}

export function resolveDataPrepareStatus(
  input: DataPrepareStatusInput,
): DataPrepareStatus {
  const error = input.applyError ?? input.compileError ?? input.previewError;
  if (error) return { tone: "error", message: error, meta: null };
  if (input.isApplying) {
    return { tone: "busy", message: "Aplicando alterações…", meta: null };
  }
  if (input.compileStatus === "loading") {
    return { tone: "busy", message: "Compilando consulta…", meta: null };
  }
  if (input.previewStatus === "loading") {
    return {
      tone: "busy",
      message: input.hasPreview ? "Atualizando prévia…" : "Carregando prévia…",
      meta: null,
    };
  }
  if (input.runtimeErrorCount > 0) {
    return {
      tone: "warning",
      message: `${input.runtimeErrorCount} erro(s) de célula na prévia`,
      meta: statusMeta(input),
    };
  }
  if (input.hasPreview) {
    return {
      tone: "success",
      message: "Prévia atualizada",
      meta: statusMeta(input),
    };
  }
  return {
    tone: "neutral",
    message: "Sem prévia disponível",
    meta: input.dirtyCount > 0
      ? `${input.dirtyCount} consulta(s) alterada(s)`
      : null,
  };
}
