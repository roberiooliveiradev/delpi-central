import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  isTerminalImportJobStatus,
  pollChatActionProviderImportJob,
  shouldReloadRoutesForImportJob,
} from "./chatActionImportPolling";
import type { ChatExternalActionImportJob } from "./api/chatTypes";

vi.mock("./api/chatApi", () => ({
  getChatAgentActionProviderImportJob: vi.fn(),
}));

import { getChatAgentActionProviderImportJob } from "./api/chatApi";

function makeJob(
  patch: Partial<ChatExternalActionImportJob> = {},
): ChatExternalActionImportJob {
  return {
    jobId: "job-1",
    providerKey: "api-delpi",
    status: "running",
    phase: "import_actions",
    phaseLabel: "Cadastrando rotas",
    progress: { done: 0, total: 0, unit: "actions" },
    ...patch,
  };
}

describe("chatActionImportPolling", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("identifica status terminal do job", () => {
    expect(isTerminalImportJobStatus("completed")).toBe(true);
    expect(isTerminalImportJobStatus("failed")).toBe(true);
    expect(isTerminalImportJobStatus("running")).toBe(false);
  });

  it("sinaliza reload quando fase import_actions conclui", () => {
    const job = makeJob({
      progress: { done: 12, total: 12, unit: "actions" },
    });

    expect(shouldReloadRoutesForImportJob(job, false)).toBe(true);
    expect(shouldReloadRoutesForImportJob(job, true)).toBe(false);
  });

  it("faz poll até completed e dispara callback de rotas", async () => {
    const onImportActionsReady = vi.fn();

    vi.mocked(getChatAgentActionProviderImportJob)
      .mockResolvedValueOnce(
        makeJob({
          progress: { done: 5, total: 10, unit: "actions" },
        }),
      )
      .mockResolvedValueOnce(
        makeJob({
          progress: { done: 10, total: 10, unit: "actions" },
        }),
      )
      .mockResolvedValueOnce(
        makeJob({
          status: "completed",
          phase: "done",
          progress: { done: 10, total: 10, unit: "actions" },
        }),
      );

    const result = await pollChatActionProviderImportJob("api-delpi", "job-1", {
      intervalMs: 1,
      onImportActionsReady,
    });

    expect(result.status).toBe("completed");
    expect(onImportActionsReady).toHaveBeenCalledTimes(1);
    expect(getChatAgentActionProviderImportJob).toHaveBeenCalledTimes(3);
  });

  it("retorna failed sem continuar poll", async () => {
    vi.mocked(getChatAgentActionProviderImportJob).mockResolvedValueOnce(
      makeJob({
        status: "failed",
        phase: "failed",
        error: "OpenAPI indisponível",
      }),
    );

    const result = await pollChatActionProviderImportJob("api-delpi", "job-1", {
      intervalMs: 1,
    });

    expect(result.status).toBe("failed");
    expect(getChatAgentActionProviderImportJob).toHaveBeenCalledTimes(1);
  });
});
