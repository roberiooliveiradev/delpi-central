/**
 * Node.js entry — server-side execution of the CANONICAL auto-layout
 * pipeline (Organizar → preview ops), same code path the editor runs:
 *
 *   snapshotFromXml → applyTextFitSizing → buildElkGraph → ELK layout →
 *   buildDiOps / buildDiXml → injectDiIntoXml(stripBpmnDi(xml))
 *
 * Differences from the browser path are execution-only, never algorithmic:
 * ELK runs on the main thread (no Web Worker) and DOMParser/XMLSerializer
 * are polyfilled via @xmldom/xmldom by the bundle preamble. Semantics are
 * untouched — only BPMN-DI geometry is computed.
 *
 * Contract (stdin → stdout, JSON line):
 *   in : { "xml": string }
 *   out: { ok: true, xml, changed, movedElements }
 *        | { ok: false, error: { code, message } }
 */

// Node execution: elk.bundled.js = same ELK engine on the main thread
// (the browser path uses elk-api.js + the dedicated Web Worker).
import ELK from "elkjs/lib/elk.bundled.js";

import {
  buildElkGraph,
  type ElkNode,
  type LayoutSnapshot,
} from "./elkGraph";
import {
  applyTextFitSizing,
  buildDiOps,
  buildDiXml,
  injectDiIntoXml,
  planeElementFor,
  snapshotFromXml,
  stripBpmnDi,
  type DiLayoutOp,
} from "./diProposal";
import { LAYOUT_PROFILE_V1 } from "./layoutProfile";

export type OrganizeResult =
  | {
      ok: true;
      xml: string;
      changed: boolean;
      movedElements: number;
    }
  | { ok: false; error: { code: string; message: string } };

const EPS = 0.5; // geometry tolerance (px) for no-change detection

function geometryChanged(
  ops: DiLayoutOp[],
  snapshot: LayoutSnapshot,
): { changed: boolean; moved: number } {
  const nodes = new Map(snapshot.nodes.map((n) => [n.id, n]));
  const edges = new Map(snapshot.edges.map((e) => [e.id, e]));
  let moved = 0;
  for (const op of ops) {
    if (op.bounds) {
      const n = nodes.get(op.elementId);
      const b = op.bounds;
      if (
        n?.x == null ||
        n?.y == null ||
        Math.abs(b.x - n.x) > EPS ||
        Math.abs(b.y - n.y) > EPS ||
        Math.abs(b.width - (n.width ?? 0)) > EPS ||
        Math.abs(b.height - (n.height ?? 0)) > EPS
      ) {
        moved += 1;
      }
    }
    if (op.waypoints) {
      const e = edges.get(op.elementId);
      const cur = e?.points ?? [];
      const next = op.waypoints;
      if (
        cur.length !== next.length ||
        cur.some(
          (p, i) =>
            Math.abs(p.x - next[i].x) > EPS ||
            Math.abs(p.y - next[i].y) > EPS,
        )
      ) {
        moved += 1;
      }
    }
  }
  return { changed: moved > 0, moved };
}

export async function organizeBpmnXml(xml: string): Promise<OrganizeResult> {
  try {
    const snapshot = applyTextFitSizing(snapshotFromXml(xml));
    const graph = buildElkGraph(snapshot);
    const elk = new ELK();
    const laidOut = (await Promise.race([
      elk.layout(graph),
      new Promise((_, reject) =>
        setTimeout(
          () => reject(new Error("LAYOUT_TIMEOUT")),
          LAYOUT_PROFILE_V1.timeoutMs ?? 30_000,
        ),
      ),
    ])) as ElkNode;

    const planeElement = planeElementFor(xml);
    if (!planeElement) {
      return {
        ok: false,
        error: {
          code: "NO_PLANE",
          message: "BPMN plane element not found (process/collaboration).",
        },
      };
    }

    const ops = buildDiOps(laidOut, snapshot);
    const { changed, moved } = geometryChanged(ops, snapshot);
    const diXml = buildDiXml(laidOut, snapshot, planeElement);
    const organized = injectDiIntoXml(stripBpmnDi(xml), diXml);
    if (organized === xml) {
      return { ok: true, xml, changed: false, movedElements: 0 };
    }
    return { ok: true, xml: organized, changed, movedElements: moved };
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      ok: false,
      error: {
        code: message === "LAYOUT_TIMEOUT" ? "LAYOUT_TIMEOUT" : "LAYOUT_FAILED",
        message,
      },
    };
  }
}

// ---- stdin → stdout runner ----
// The esbuild CJS bundle defines require/module in scope — `require.main
// === module` fires only when this file is the process entry point.
declare const require: { main?: unknown } | undefined;
declare const module: unknown;

const isMainModule =
  typeof require !== "undefined" && require.main === module;

if (isMainModule) {
  let input = "";
  process.stdin.setEncoding("utf-8");
  process.stdin.on("data", (chunk) => (input += chunk));
  process.stdin.on("end", async () => {
    const result = await (async () => {
      try {
        const payload = JSON.parse(input || "{}");
        if (typeof payload.xml !== "string" || !payload.xml.trim()) {
          return {
            ok: false,
            error: { code: "VALIDATION", message: "xml is required." },
          };
        }
        return await organizeBpmnXml(payload.xml);
      } catch (err) {
        return {
          ok: false,
          error: {
            code: "BAD_INPUT",
            message: err instanceof Error ? err.message : String(err),
          },
        };
      }
    })();
    process.stdout.write(JSON.stringify(result));
  });
}
