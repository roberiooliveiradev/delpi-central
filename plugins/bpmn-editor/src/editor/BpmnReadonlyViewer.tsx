/**
 * BpmnReadonlyViewer — viewer BPMN live, somente navegação
 * (G9-LAYOUT-1 §4–§10, §41; hardening G9-LOAD-1 §7).
 *
 * O MESMO renderer do vendor que o editor usa (NavigatedViewer), montado
 * num container real do host — não é imagem nem snapshot raster: o DOM/SVG
 * do bpmn-js é interativo para pan e wheel zoom. O modo NavigatedViewer
 * não registra modeling/contextPad/palette/directEditing — não existe
 * caminho de edição a partir desta superfície (prova: readonlyViewer.test).
 *
 * Toda inicialização alcança estado terminal: constructor ou import
 * falhando/travando → "error" (o host decide retry/remount); fit-viewport
 * falhando → "ready" degradado (o conteúdo já está renderizado e
 * navegável — fit é cosmético, decisão explícita G9-LOAD-1 §11).
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
  /** Override do budget do import (default BPMN_VIEWER_IMPORT_TIMEOUT_MS) —
   *  injetável em teste. */
  importTimeoutMs?: number;
};

/**
 * Budget do import: parse+render é CPU-bound e normalmente < 1s; um
 * importXML que nunca resolve (vendor travado) não pode segurar o card
 * em loading infinito (G9-LOAD-1 §7/§10).
 */
export const BPMN_VIEWER_IMPORT_TIMEOUT_MS = 15_000;

function loadLog(stage: string, extra?: Record<string, unknown>): void {
  // Observabilidade segura: apenas estágio + classe/mensagem de erro.
  // Nunca token, XML ou payload sensível (G9-LOAD-1 §9).
  console.debug("[BPMN_LOAD]", { stage, ...extra });
}

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

function errorMeta(err: unknown): Record<string, unknown> {
  return {
    errorClass: err instanceof Error ? err.name : typeof err,
    errorMessage: err instanceof Error ? err.message : String(err),
  };
}

export function BpmnReadonlyViewer({
  xml,
  controls = true,
  fitOnLoad = true,
  className,
  onStatusChange,
  importTimeoutMs = BPMN_VIEWER_IMPORT_TIMEOUT_MS,
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
    let cancelled = false;
    emit("loading");
    loadLog("viewer-create");

    // Constructor failure → estado terminal "error" (nunca crash do
    // subtree nem parent preso em loading).
    let viewer: InstanceType<typeof NavigatedViewer>;
    try {
      viewer = new NavigatedViewer({
        container: host,
        bpmnRenderer: { ...BPMN_RENDERER_THEME },
      });
    } catch (err) {
      loadLog("error", { stage: "viewer-create", ...errorMeta(err) });
      if (!cancelled) emit("error");
      return;
    }
    viewerRef.current = viewer;

    // Timeout do import: Promise.race garante estado terminal mesmo se a
    // promise do vendor nunca resolver.
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      rejectTimeout(new Error("import excedeu o tempo limite"));
    }, importTimeoutMs);
    let rejectTimeout: (err: Error) => void = () => undefined;
    const timeout = new Promise<never>((_, reject) => {
      rejectTimeout = reject;
    });

    loadLog("import-xml");
    Promise.race([viewer.importXML(xml), timeout])
      .then(() => {
        clearTimeout(timer);
        if (cancelled) return;
        const next = hasRenderableElements(viewer) ? "ready" : "empty";
        if (next === "ready" && fitOnLoad) {
          loadLog("fit-viewport");
          try {
            // Contrato verificado contra diagram-js/bpmn-js 18.x:
            // zoom('fit-viewport', center) — string truthy ("auto") pede
            // centralização do fit (Canvas.prototype._fitViewport).
            viewer.get<{ zoom(s: string, p?: string): void }>("canvas").zoom(
              "fit-viewport",
              "auto",
            );
          } catch (err) {
            // ready degradado: conteúdo renderizado e navegável, fit falhou
            loadLog("fit-viewport-failed", errorMeta(err));
          }
        }
        emit(next);
        if (next === "ready") loadLog("ready");
      })
      .catch((err) => {
        clearTimeout(timer);
        if (cancelled) return;
        loadLog("error", {
          stage: timedOut ? "import-xml-timeout" : "import-xml",
          ...errorMeta(err),
        });
        if (timedOut) {
          // viewer travado no import — libera a instância imediatamente
          try {
            viewer.destroy();
          } catch {
            /* noop */
          }
          if (viewerRef.current === viewer) viewerRef.current = null;
        }
        emit("error");
      });
    return () => {
      cancelled = true;
      clearTimeout(timer);
      try {
        viewer.destroy();
      } catch {
        /* noop */
      }
      if (viewerRef.current === viewer) viewerRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [xml]);

  const stepZoom = (delta: number) =>
    viewerRef.current
      ?.get<{ stepZoom(d: number): void }>("zoomScroll")
      ?.stepZoom(delta);
  const fitViewport = () => {
    try {
      viewerRef.current
        ?.get<{ zoom(s: string, p?: string): void }>("canvas")
        ?.zoom("fit-viewport", "auto");
    } catch (err) {
      loadLog("fit-viewport-failed", errorMeta(err));
    }
  };

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
