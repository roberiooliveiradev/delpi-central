import type { MColumnSchemaDto } from "@delpi/tv-dashboard-presentation";

import { API_BASE, httpGet, httpPost } from "../../../api/httpClient";
import type {
  DataQueryCapabilities,
  DataQueryCompileResult,
  DataQueryFunction,
  DataQueryMutationAction,
  DataQueryPreview,
} from "../domain/dataQueryTypes";
import { adaptCompileResult, adaptPreviewResult } from "./dataQueryApiAdapters";

type Envelope<T> = { success: boolean; message?: string; data: T };

async function unwrap<T>(promise: Promise<Envelope<T>>): Promise<T> {
  const result = await promise;
  if (!result.success) throw new Error(result.message || "Falha na API de consultas.");
  return result.data;
}

export type CompileInput = {
  script: string;
  sourceSchema?: MColumnSchemaDto[];
  queryBindings?: Array<{ name: string; sourceId: string }>;
  targetStepName?: string | null;
};

export interface DataQueryApi {
  capabilities(signal?: AbortSignal): Promise<DataQueryCapabilities>;
  compile(input: CompileInput, signal?: AbortSignal): Promise<DataQueryCompileResult>;
  mutate(
    input: CompileInput,
    action: DataQueryMutationAction,
    signal?: AbortSignal,
  ): Promise<DataQueryCompileResult>;
  functions(signal?: AbortSignal): Promise<DataQueryFunction[]>;
  preview(
    input: {
      block: Record<string, unknown>;
      nativeConfig: Record<string, unknown>;
      playlistId: string;
      targetStepName?: string | null;
      forceRefresh?: boolean;
    },
    signal?: AbortSignal,
  ): Promise<DataQueryPreview>;
}

function compileBody(input: CompileInput) {
  return {
    profile: "m-delpi-v1",
    script: input.script,
    sourceSchema: input.sourceSchema ?? [],
    queryBindings: input.queryBindings ?? [],
    targetStepName: input.targetStepName ?? null,
    culture: "pt-BR",
  };
}

export const dataQueryApi: DataQueryApi = {
  capabilities: (signal) =>
    unwrap(httpGet<Envelope<DataQueryCapabilities>>(`${API_BASE}/data/m/capabilities`, { signal })),
  async compile(input, signal) {
    return adaptCompileResult(
      await unwrap(
        httpPost<Envelope<unknown>>(`${API_BASE}/data/m/compile`, compileBody(input), { signal }),
      ),
    );
  },
  async mutate(input, action, signal) {
    return adaptCompileResult(
      await unwrap(
        httpPost<Envelope<unknown>>(
          `${API_BASE}/data/m/mutate`,
          { ...compileBody(input), action },
          { signal },
        ),
      ),
    );
  },
  async functions(signal) {
    const result = await unwrap(
      httpGet<Envelope<{ items: DataQueryFunction[] }>>(
        `${API_BASE}/data/m/functions?profile=m-delpi-v1`,
        { signal },
      ),
    );
    return result.items;
  },
  async preview(input, signal) {
    return adaptPreviewResult(
      await unwrap(
        httpPost<Envelope<unknown>>(
          `${API_BASE}/data/preview-block`,
          {
            block: input.block,
            nativeConfig: input.nativeConfig,
            playlistId: input.playlistId,
            forceRefresh: Boolean(input.forceRefresh),
            targetStepName: input.targetStepName ?? null,
            previewOptions: { maxRows: 200, includeColumnProfile: false },
          },
          { signal },
        ),
      ),
    );
  },
};
