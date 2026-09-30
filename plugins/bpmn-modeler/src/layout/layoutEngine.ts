/**
 * Layout engine adapter — worker primeiro; fallback para main thread
 * apenas quando o worker está indisponível no ambiente (P5 §9), nunca
 * silencioso: `usedFallback` sinaliza o diagnóstico.
 *
 * Contrato: input ELK graph → output geometria | LAYOUT_FAILED;
 * cancellation via abort do job corrente; timeout do profile.
 */

import { LAYOUT_PROFILE_V1 } from "./layoutProfile";
import type { ElkNode } from "./elkGraph";
import type {
  LayoutWorkerRequest,
  LayoutWorkerResponse,
} from "./layout.worker";

export type LayoutResult =
  | { ok: true; graph: ElkNode; usedFallback: boolean }
  | { ok: false; error: { code: "LAYOUT_FAILED" | "LAYOUT_TIMEOUT" | "LAYOUT_CANCELLED"; message: string } };

export type LayoutJob = {
  promise: Promise<LayoutResult>;
  cancel: () => void;
};

let workerInstance: Worker | null | undefined;
let jobCounter = 0;
const pending = new Map<
  string,
  { resolve: (r: LayoutWorkerResponse) => void; reject: (e: Error) => void }
>();

function getWorker(): Worker | null {
  if (workerInstance !== undefined) return workerInstance;
  try {
    workerInstance = new Worker(
      new URL("./layout.worker.ts", import.meta.url),
      { type: "module" },
    );
    workerInstance.onmessage = (event: MessageEvent<LayoutWorkerResponse>) => {
      const entry = pending.get(event.data.jobId);
      if (entry) {
        pending.delete(event.data.jobId);
        entry.resolve(event.data);
      }
    };
    workerInstance.onerror = (event) => {
      const err = new Error(event.message || "worker failure");
      for (const [, entry] of pending) entry.reject(err);
      pending.clear();
    };
    return workerInstance;
  } catch {
    workerInstance = null;
    return null;
  }
}

async function layoutOnMainThread(graph: ElkNode): Promise<ElkNode> {
  const { default: ELK } = await import("elkjs/lib/elk.bundled.js");
  const elk = new ELK();
  return (await elk.layout(graph as never)) as unknown as ElkNode;
}

export function runLayout(graph: ElkNode): LayoutJob {
  const jobId = `layout-${++jobCounter}`;
  let cancelled = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const promise = new Promise<LayoutResult>((resolve) => {
    const finish = (result: LayoutResult) => {
      if (timer) clearTimeout(timer);
      resolve(result);
    };

    timer = setTimeout(() => {
      pending.delete(jobId);
      finish({
        ok: false,
        error: { code: "LAYOUT_TIMEOUT", message: "Layout excedeu o tempo limite." },
      });
    }, LAYOUT_PROFILE_V1.timeoutMs);

    const worker = getWorker();
    if (worker) {
      pending.set(jobId, {
        resolve: (response) => {
          if (cancelled) return;
          if (response.ok) {
            finish({ ok: true, graph: response.graph, usedFallback: false });
          } else {
            finish({
              ok: false,
              error: { code: "LAYOUT_FAILED", message: response.error.message },
            });
          }
        },
        reject: (err) => {
          if (cancelled) return;
          finish({
            ok: false,
            error: { code: "LAYOUT_FAILED", message: err.message },
          });
        },
      });
      worker.postMessage({ jobId, graph } satisfies LayoutWorkerRequest);
    } else {
      // Worker indisponível — fallback main thread com diagnóstico (P5 §9).
      layoutOnMainThread(graph)
        .then((laidOut) => {
          if (!cancelled)
            finish({ ok: true, graph: laidOut, usedFallback: true });
        })
        .catch((err) => {
          if (!cancelled)
            finish({
              ok: false,
              error: {
                code: "LAYOUT_FAILED",
                message: err instanceof Error ? err.message : String(err),
              },
            });
        });
    }
  });

  return {
    promise,
    cancel: () => {
      cancelled = true;
      pending.delete(jobId);
    },
  };
}
