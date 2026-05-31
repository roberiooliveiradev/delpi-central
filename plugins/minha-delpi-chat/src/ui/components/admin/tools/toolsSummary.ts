import type { AdminLlmStatus, AdminToolHealthResponse } from "../../../../data/api/adminTypes";

export type ToolsSummary = {
  llmConfigured: boolean;
  llmLabel: string;
  healthLabel: string;
  globalActions: number;
  chatActions: number;
};

export function computeToolsSummary(
  llmStatus: AdminLlmStatus | null | undefined,
  health: AdminToolHealthResponse | null | undefined,
  globalActionCount: number,
  chatActionCount: number,
): ToolsSummary {
  const llmConfigured = Boolean(llmStatus?.provider || llmStatus?.model);
  const llmLabel = llmConfigured
    ? `${llmStatus?.provider ?? "Provider"} · ${llmStatus?.model ?? "modelo"}`
    : "Provider e modelo não informados";

  const healthLabel =
    health?.status === "ok"
      ? "Operacional"
      : health?.status === "warning"
        ? "Atenção"
        : health?.status === "error"
          ? "Com falhas"
          : "—";

  return {
    llmConfigured,
    llmLabel,
    healthLabel,
    globalActions: Math.max(0, globalActionCount),
    chatActions: Math.max(0, chatActionCount),
  };
}
