import type { ChatExternalActionImportJob } from "./api/chatTypes";
import { getChatAgentActionProviderImportJob } from "./api/chatApi";

export type ChatActionImportPollingOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  intervalMs?: number;
  maxAttempts?: number;
  onJobUpdate?: (job: ChatExternalActionImportJob) => void;
  onImportActionsReady?: (job: ChatExternalActionImportJob) => void | Promise<void>;
};

export function isTerminalImportJobStatus(status: string): boolean {
  return status === "completed" || status === "failed";
}

export function shouldReloadRoutesForImportJob(
  job: ChatExternalActionImportJob,
  alreadyReloaded: boolean,
): boolean {
  if (alreadyReloaded) {
    return false;
  }

  const { done, total } = job.progress;

  return job.phase === "import_actions" && total > 0 && done >= total;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function pollChatActionProviderImportJob(
  providerKey: string,
  jobId: string,
  options: ChatActionImportPollingOptions = {},
): Promise<ChatExternalActionImportJob> {
  const intervalMs = options.intervalMs ?? 1500;
  const maxAttempts = options.maxAttempts ?? 600;
  let routesReloaded = false;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const job = await getChatAgentActionProviderImportJob(providerKey, jobId, {
      getAccessToken: options.getAccessToken,
    });

    options.onJobUpdate?.(job);

    if (shouldReloadRoutesForImportJob(job, routesReloaded)) {
      routesReloaded = true;
      await options.onImportActionsReady?.(job);
    }

    if (isTerminalImportJobStatus(job.status)) {
      return job;
    }

    await sleep(intervalMs);
  }

  throw new Error("O import demorou mais do que o esperado. Tente novamente.");
}
