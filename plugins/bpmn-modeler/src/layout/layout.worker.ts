/**
 * ELK Web Worker — input: ELK graph JSON; output: grafo com geometria
 * ou erro estruturado LAYOUT_FAILED. Sem estado canônico (P5 §5/§9).
 */
import ELK from "elkjs/lib/elk.bundled.js";

import type { ElkNode } from "./elkGraph";

export type LayoutWorkerRequest = {
  jobId: string;
  graph: ElkNode;
};

export type LayoutWorkerResponse =
  | { jobId: string; ok: true; graph: ElkNode }
  | { jobId: string; ok: false; error: { code: "LAYOUT_FAILED"; message: string } };

const elk = new ELK();

self.onmessage = async (event: MessageEvent<LayoutWorkerRequest>) => {
  const { jobId, graph } = event.data;
  try {
    const laidOut = (await elk.layout(
      graph as never,
    )) as unknown as ElkNode;
    const response: LayoutWorkerResponse = { jobId, ok: true, graph: laidOut };
    self.postMessage(response);
  } catch (err) {
    const response: LayoutWorkerResponse = {
      jobId,
      ok: false,
      error: {
        code: "LAYOUT_FAILED",
        message: err instanceof Error ? err.message : String(err),
      },
    };
    self.postMessage(response);
  }
};
