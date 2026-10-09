/**
 * BpmnReadonlyViewer — viewer BPMN live, somente navegação
 * (G9-LAYOUT-1 §4–§10, §41).
 *
 * O MESMO renderer do vendor que o editor usa (NavigatedViewer), montado
 * num container real do host — não é imagem nem snapshot raster: o DOM/SVG
 * do bpmn-js é interativo para pan e wheel zoom. O modo NavigatedViewer
 * não registra modeling/contextPad/palette/directEditing — não existe
 * caminho de edição a partir desta superfície (prova: readonlyViewer.test).
 *
 * Vendor leakage: bpmn-js só pode ser importado dentro de `src/editor/`.
 */
import { useEffect, useRef, useState } from "react";
import NavigatedViewer from "bpmn-js/lib/NavigatedViewer";

import { BPMN_RENDERER_THEME } from "./rendererTheme";
import { BPMNM_ROOT_CLASS } from "../ui/kit";

import "bpmn-js/dist/assets/diagram-js.css";
import "bpmn-js/dist/assets/bpmn-js.css";
import "bpmn-js/dist/assets/bpmn-font/css/bpmn.css";

export type BpmnReadonlyViewerStatus =
  | "loading"
  | "ready"
  | "empty"
  | "error";

export type BpmnReadonlyViewerProps = {
  /** BPMN XML canônico (com BPMN-DI). Mudança de xml remonta o viewer. */
  xml: string;
  /** Controles de navegação no canto inferior direito (+/−/fit). */
  controls?: boolean;
  /** Aplica canvas.zoom("fit-viewport") após o import (default true). */
  fitOnLoad?: boolean;
  className?: string;
  /** Callback de status — o host decide empty/loading/error UI. */
  onStatusChange?: (status: BpmnReadonlyViewerStatus) => void;
};

type ViewerSvc = {
  get<T>(name: string): T;
};

/** Elementos "visíveis" no registry — processo/colaboração raiz e labels
 *  implícitas não contam (mesmo critério do thumbnail G9). */
function hasRenderableElements(viewer: ViewerSvc): boolean {
  const registry = viewer.get<{
    filter(fn: (el: { type?: string; id?: string }) => boolean): unknown[];
  }>("elementRegistry");
  return (
    registry.filter(
      (el) =>
        el.type !== "bpmn:Process" &&
        el.type !== "bpmn:Collaboration" &&
        el.type !== "label" &&
        el.id !== "__implicitroot",
    ).length > 0
  );
}

export function BpmnReadonlyViewer({
  xml,
  controls = true,
  fitOnLoad = true,
  className,
  onStatusChange,
}: BpmnReadonlyViewerProps) {
  const hostRef = useRef<HTMLDivElement | null>(null);
  const viewerRef = useRef<InstanceType<typeof NavigatedViewer> | null>(null);
  const [status, setStatus] = useState<BpmnReadonlyViewerStatus>("loading");
  const statusCb = useRef(onStatusChange);
  statusCb.current = onStatusChange;

  const emit = (s: BpmnReadonlyViewerStatus) => {
    setStatus(s);
    statusCb.current?.(s);
  };

  useEffect(() => {
    const host = hostRef.current;
    if (!host) return;
    const viewer = new NavigatedViewer({
      container: host,
      bpmnRenderer: { ...BPMN_RENDERER_THEME },
    });
    viewerRef.current = viewer;
    let cancelled = false;
    emit("loading");
    viewer
      .importXML(xml)
      .then(() => {
        if (cancelled) return;
        const next = hasRenderableElements(viewer) ? "ready" : "empty";
        if (next === "ready" && fitOnLoad) {
          viewer.get<{ zoom(s: string, p?: string): void }>("canvas").zoom(
            "fit-viewport",
            "auto",
          );
        }
        emit(next);
      })
      .catch(() => {
        if (!cancelled) emit("error");
      });
    return () => {
      cancelled = true;
      viewer.destroy();
      viewerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [xml]);

  const stepZoom = (delta: number) =>
    viewerRef.current
      ?.get<{ stepZoom(d: number): void }>("zoomScroll")
      ?.stepZoom(delta);
  const fitViewport = () =>
    viewerRef.current
      ?.get<{ zoom(s: string, p?: string): void }>("canvas")
      ?.zoom("fit-viewport", "auto");

  return (
    <div
      className={`${BPMNM_ROOT_CLASS} bpmnm-readonly-viewer${
        className ? ` ${className}` : ""
      }`}
      data-testid="bpmn-readonly-viewer"
      data-status={status}
    >
      <div ref={hostRef} className="bpmnm-readonly-viewer__canvas" />
      {controls && status === "ready" ? (
        <div
          className="bpmnm-readonly-viewer__controls"
          role="group"
          aria-label="Navegação do diagrama"
        >
          <button
            type="button"
            aria-label="Ampliar"
            title="Ampliar"
            onClick={() => stepZoom(0.25)}
          >
            +
          </button>
          <button
            type="button"
            aria-label="Reduzir"
            title="Reduzir"
            onClick={() => stepZoom(-0.25)}
          >
            −
          </button>
          <button
            type="button"
            aria-label="Ajustar à tela"
            title="Ajustar à tela"
            onClick={fitViewport}
          >
            ⤢
          </button>
        </div>
      ) : null}
    </div>
  );
}
