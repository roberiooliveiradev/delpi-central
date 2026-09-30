/**
 * Layout engine adapter — Web Worker only (P5 §9 / P6).
 *
 * ELK executa exclusivamente em worker dedicado (elk-worker.min.js via
 * `workerFactory`). Se o Worker estiver indisponível ou falhar, o job
 * rejeita com LAYOUT_FAILED e o canvas principal permanece intacto —
 * não existe fallback main thread.
 *
 * Contrato: input ELK graph → output geometria | LAYOUT_FAILED;
 * cancellation via abort do job corrente; timeout do profile.
 */

import ELK from "elkjs/lib/elk-api.js";

import { LAYOUT_PROFILE_V1 } from "./layoutProfile";
import type { ElkNode } from "./elkGraph";

export type LayoutResult =
  | { ok: true; graph: ElkNode }
  | { ok: false; error: { code: "LAYOUT_FAILED" | "LAYOUT_TIMEOUT" | "LAYOUT_CANCELLED"; message: string } };

export type LayoutJob = {
  promise: Promise<LayoutResult>;
  cancel: () => void;
};

let elkInstance: ELK | null | undefined;
const workerErrorSubs = new Set<(err: Error) => void>();

function getElk(): ELK | null {
  if (elkInstance !== undefined) return elkInstance;
  try {
    elkInstance = new ELK({
      workerFactory: () => {
        const worker = new Worker(
          new URL("./layout.worker.ts", import.meta.url),
          { type: "module" },
        );
        worker.onerror = (event) => {
          const err = new Error(event.message || "layout worker failure");
          elkInstance = undefined;
          for (const sub of workerErrorSubs) sub(err);
        };
        return worker;
      },
    });
    return elkInstance;
  } catch {
    elkInstance = null;
    return null;
  }
}

export function runLayout(graph: ElkNode): LayoutJob {
  let cancelled = false;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const promise = new Promise<LayoutResult>((resolve) => {
    const finish = (result: LayoutResult) => {
      if (timer) clearTimeout(timer);
      workerErrorSubs.delete(onWorkerError);
      resolve(result);
    };
    const onWorkerError = (err: Error) => {
      if (cancelled) return;
      finish({
        ok: false,
        error: { code: "LAYOUT_FAILED", message: err.message },
      });
    };
    workerErrorSubs.add(onWorkerError);

    timer = setTimeout(() => {
      finish({
        ok: false,
        error: {
          code: "LAYOUT_TIMEOUT",
          message: "Layout excedeu o tempo limite.",
        },
      });
    }, LAYOUT_PROFILE_V1.timeoutMs);

    const elk = getElk();
    if (!elk) {
      // Worker indisponível — layout unavailable (P5 §9); canvas intacto.
      finish({
        ok: false,
        error: {
          code: "LAYOUT_FAILED",
          message: "Layout indisponível: Web Worker não suportado neste ambiente.",
        },
      });
      return;
    }

    (elk.layout(graph as never) as Promise<ElkNode>).then(
      (laidOut) => {
        if (cancelled) return;
        finish({ ok: true, graph: laidOut });
      },
      (err) => {
        if (cancelled) return;
        finish({
          ok: false,
          error: {
            code: "LAYOUT_FAILED",
            message: err instanceof Error ? err.message : String(err),
          },
        });
      },
    );
  });

  return {
    promise,
    cancel: () => {
      cancelled = true;
      workerErrorSubs.delete(onWorkerError);
    },
  };
}
