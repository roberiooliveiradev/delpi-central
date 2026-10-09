/**
 * Preview derivado de BPMN (library thumbnails).
 *
 * Contrato: BPMN XML + BPMN-DI são a única fonte canônica — este módulo só
 * deriva um SVG descartável via o próprio renderer do vendor (NavigatedViewer
 * montado offscreen → fit-viewport → saveSVG → destroy). Nenhuma geometria ou
 * representação paralela é criada ou persistida.
 *
 * Vendor leakage: bpmn-js só pode ser importado dentro de `src/editor/`.
 */
import NavigatedViewer from "bpmn-js/lib/NavigatedViewer";

import { BPMN_RENDERER_THEME } from "./BpmnEditorAdapter";

const STAGE_W = 480;
const STAGE_H = 270;
const MAX_CONCURRENT = 2;
/** Zoom-out após fit-viewport — safe padding visual na thumb (~12%). */
const SAFE_PADDING_ZOOM = 0.88;

type CanvasSvc = {
  zoom(scale: string | number, position?: string): number;
};
type RegistrySvc = {
  filter(fn: (el: { type?: string; id?: string }) => boolean): Array<unknown>;
};

let inflight = 0;
const queue: Array<() => void> = [];

function acquireSlot(): Promise<void> {
  if (inflight < MAX_CONCURRENT) {
    inflight += 1;
    return Promise.resolve();
  }
  return new Promise((resolve) => queue.push(resolve));
}

function releaseSlot(): void {
  const next = queue.shift();
  if (next) {
    next();
  } else {
    inflight -= 1;
  }
}

export type BpmnThumbnailResult =
  | { kind: "svg"; svg: string }
  | { kind: "empty" };

/**
 * Renderiza o XML canônico e devolve `{ kind: "svg", svg }` (standalone, pronto
 * para `<img>`) ou `{ kind: "empty" }` quando o diagrama não tem elementos DI.
 * Falhas viram exceção — o chamador decide o placeholder.
 */
export async function renderBpmnThumbnail(
  xml: string,
): Promise<BpmnThumbnailResult> {
  await acquireSlot();
  const stage = document.createElement("div");
  stage.className = "bpmnm-thumb-stage";
  stage.style.cssText = `position:fixed;left:-10000px;top:0;width:${STAGE_W}px;height:${STAGE_H}px;visibility:hidden;pointer-events:none;`;
  document.body.appendChild(stage);
  const viewer = new NavigatedViewer({
    container: stage,
    bpmnRenderer: { ...BPMN_RENDERER_THEME },
  });
  try {
    await viewer.importXML(xml);
    const registry = viewer.get<RegistrySvc>("elementRegistry");
    const elements = registry.filter(
      (el) =>
        el.type !== "bpmn:Process" &&
        el.type !== "bpmn:Collaboration" &&
        el.type !== "label" &&
        el.id !== "__implicitroot",
    );
    if (elements.length === 0) return { kind: "empty" };
    const canvas = viewer.get<CanvasSvc>("canvas");
    const fitted = canvas.zoom("fit-viewport", "auto");
    canvas.zoom(Math.max(fitted * SAFE_PADDING_ZOOM, 0.05));
    const { svg } = await viewer.saveSVG();
    if (!svg) throw new Error("empty svg");
    return { kind: "svg", svg };
  } finally {
    viewer.destroy();
    stage.remove();
    releaseSlot();
  }
}
