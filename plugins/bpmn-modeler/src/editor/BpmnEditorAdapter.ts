/**
 * BpmnEditorAdapter — única superfície por onde React conversa com o vendor
 * (bpmn-js / diagram-js / bpmn-moddle). Contrato FROZEN (P4 §7, §11).
 *
 * Vendor Leakage: nenhum outro arquivo fora de `src/editor/` pode importar
 * bpmn-js, diagram-js, bpmn-moddle ou acessar modeler.get/eventBus/
 * commandStack/elementRegistry/modeling/canvas/moddle.
 */
import Modeler from "bpmn-js/lib/Modeler";
import NavigatedViewer from "bpmn-js/lib/NavigatedViewer";
import {
  BpmnPropertiesPanelModule,
  BpmnPropertiesProviderModule,
} from "bpmn-js-properties-panel";

import { ApplyDiLayoutHandler } from "./layoutApply";
import type { DiLayoutOp } from "../layout/diProposal";

import "bpmn-js/dist/assets/diagram-js.css";
import "bpmn-js/dist/assets/bpmn-js.css";
import "bpmn-js/dist/assets/bpmn-font/css/bpmn.css";
import "@bpmn-io/properties-panel/assets/properties-panel.css";

export type EditorMode = "edit" | "viewer";

export type EditorImportFailure = {
  kind: "EDITOR_CAPABILITY_FAILURE";
  message: string;
};

export type ImportResult = { ok: true } | { ok: false; error: EditorImportFailure };

export type DiagramRef = { id: string; name?: string };

export type ElementRef = { id: string; name?: string; type: string };

export type ElementSummary = {
  id: string;
  name?: string;
  type: string;
  documentation?: string;
  attributes: Record<string, string>;
};

export type CommandTrigger = "execute" | "undo" | "redo" | "clear";

export type CanvasContextMenuEvent = {
  /** id do elemento BPMN sob o cursor; null = espaço vazio do canvas. */
  elementId: string | null;
  x: number;
  y: number;
};

export type EditorSubscriptions = {
  onChanged?: (trigger: CommandTrigger) => void;
  onSelectionChanged?: (elementIds: string[]) => void;
  onImportDone?: (result: ImportResult) => void;
  onError?: (error: EditorImportFailure) => void;
  onCanvasContextMenu?: (event: CanvasContextMenuEvent) => void;
};

export type Unsubscribe = () => void;

let tokenCounter = 0;
function newToken(): string {
  tokenCounter += 1;
  return `tok-${tokenCounter}`;
}

type EditorInstance = Modeler | InstanceType<typeof NavigatedViewer>;

/**
 * Theming canônico do renderer: CSS vars mapeadas no shell (light/dark via
 * `:root[data-theme]`). Fallbacks fixos rendem documento claro quando as vars
 * não existem (ex.: SVG exportado em `<img>` — contexto isolado sem vars).
 * DI colors do documento continuam vencendo (P5).
 */
export const BPMN_RENDERER_THEME = {
  defaultFillColor: "var(--delpi-ui-bpmn-element-fill, #ffffff)",
  defaultStrokeColor: "var(--delpi-ui-bpmn-element-stroke, #22242a)",
  defaultLabelColor: "var(--delpi-ui-bpmn-label-color, #22242a)",
} as const;

/**
 * Instância única por workspace. Recriação (troca de modo/modelo) =
 * destroy() + mount() + importXml() — nunca import por cima de edição viva.
 */
export class BpmnEditorAdapter {
  private modeler: EditorInstance | null = null;
  private mode: EditorMode = "edit";
  private subs: EditorSubscriptions = {};
  private layoutHandlerRegistered = false;

  // Branch-aware dirty tracking (P4 §13) — nunca stack depth.
  private stateTokens: string[] = [];
  private cursor = -1;
  private savedToken: string | null = null;

  mount(container: HTMLElement, mode: EditorMode): void {
    this.destroy();
    this.mode = mode;
    const bpmnRenderer = { ...BPMN_RENDERER_THEME };
    if (mode === "edit") {
      this.modeler = new Modeler({
        container,
        bpmnRenderer,
        propertiesPanel: { parent: "#bpmn-properties-panel" },
        additionalModules: [
          BpmnPropertiesPanelModule,
          BpmnPropertiesProviderModule,
        ],
      });
    } else {
      this.modeler = new NavigatedViewer({ container, bpmnRenderer });
    }
    this.layoutHandlerRegistered = false;
    this.wireEvents();
  }

  destroy(): void {
    this.modeler?.destroy();
    this.modeler = null;
    this.layoutHandlerRegistered = false;
    this.stateTokens = [];
    this.cursor = -1;
    this.savedToken = null;
  }

  async importXml(xml: string): Promise<ImportResult> {
    if (!this.modeler) {
      const result: ImportResult = {
        ok: false,
        error: this.vendorFailure(new Error("Editor não montado."), "import"),
      };
      this.subs.onImportDone?.(result);
      return result;
    }
    try {
      await this.modeler.importXML(xml);
      this.fitViewport();
      this.stateTokens = [newToken()];
      this.cursor = 0;
      this.savedToken = this.stateTokens[0];
      const result: ImportResult = { ok: true };
      this.subs.onImportDone?.(result);
      return result;
    } catch (err) {
      const result: ImportResult = {
        ok: false,
        error: this.vendorFailure(err, "import"),
      };
      this.subs.onImportDone?.(result);
      return result;
    }
  }

  /** saveCandidate — exportXml estável (`format: false`, V1 congelada). */
  async exportXml(): Promise<string> {
    if (!this.modeler) throw this.capabilityError("Editor não montado.");
    try {
      const { xml } = await this.modeler.saveXML({ format: false });
      return xml ?? "";
    } catch (err) {
      throw this.capabilityError(this.describe(err, "export"));
    }
  }

  async exportSvg(): Promise<string> {
    if (!this.modeler) throw this.capabilityError("Editor não montado.");
    try {
      const { svg } = await this.modeler.saveSVG();
      return svg;
    } catch (err) {
      throw this.capabilityError(this.describe(err, "export-svg"));
    }
  }

  listDiagrams(): DiagramRef[] {
    if (!this.modeler) return [];
    try {
      const definitions = this.modeler.getDefinitions();
      const diagrams = definitions?.diagrams ?? [];
      return diagrams.map((d: { id: string; name?: string; plane?: { bpmnElement?: { name?: string } } }) => ({
        id: d.id,
        name: d.name ?? d.plane?.bpmnElement?.name,
      }));
    } catch {
      return [];
    }
  }

  openDiagram(diagramId: string): void {
    if (!this.modeler) return;
    const definitions = this.modeler.getDefinitions();
    const diagram = definitions?.diagrams?.find(
      (d: { id: string }) => d.id === diagramId,
    );
    if (diagram) {
      void this.modeler.open(diagram).then(() => this.fitViewport());
    }
  }

  isDirty(): boolean {
    if (this.cursor < 0 || this.savedToken === null) return false;
    return this.stateTokens[this.cursor] !== this.savedToken;
  }

  markSaved(): void {
    if (this.cursor >= 0) this.savedToken = this.stateTokens[this.cursor];
  }

  undo(): void {
    this.commandStack()?.undo();
  }

  redo(): void {
    this.commandStack()?.redo();
  }

  /**
   * Accept do layout preview — aplica ops de geometria DI como UM
   * comando lógico no editor vivo (P5 §18). commandStack.changed("execute")
   * → DIRTY; undo() reverte o batch inteiro. Somente modo "edit".
   */
  applyDiLayout(ops: DiLayoutOp[]): boolean {
    const cs = this.commandStack() as unknown as {
      registerHandler?: (command: string, handlerCls: unknown) => void;
      execute?: (command: string, context: unknown) => void;
    } | null;
    if (!cs?.execute) return false;
    if (!this.layoutHandlerRegistered) {
      cs.registerHandler?.("layout.applyDi", ApplyDiLayoutHandler);
      this.layoutHandlerRegistered = true;
    }
    cs.execute("layout.applyDi", { ops });
    return true;
  }

  canUndo(): boolean {
    return this.commandStack()?.canUndo() ?? false;
  }

  canRedo(): boolean {
    return this.commandStack()?.canRedo() ?? false;
  }

  zoomIn(): void {
    this.svc<{ stepZoom(d: number): void }>("zoomScroll")?.stepZoom(0.2);
  }

  zoomOut(): void {
    this.svc<{ stepZoom(d: number): void }>("zoomScroll")?.stepZoom(-0.2);
  }

  fitViewport(): void {
    this.svc<{ zoom(scale: string, pos?: string): void }>("canvas")?.zoom(
      "fit-viewport",
      "auto",
    );
  }

  /** Re-medir o viewport do renderer quando o container muda de tamanho
   *  (resize da janela, sidebar, toolbar wrap). Preserva zoom/pan do usuário. */
  resized(): void {
    this.svc<{ resized(): void }>("canvas")?.resized();
  }

  selectAll(): void {
    const registry = this.svc<{
      getAll(): Array<{ id: string; type: string; parent?: unknown }>;
    }>("elementRegistry");
    const selection = this.svc<{
      select(elements: unknown[]): void;
    }>("selection");
    if (!registry || !selection) return;
    const elements = registry
      .getAll()
      .filter((el) => el.type !== "label" && el.parent != null);
    selection.select(elements);
  }

  /** Direct editing vendor (rename inline) — modo edit apenas. */
  directEdit(elementId: string): void {
    if (this.mode !== "edit") return;
    const element = this.svc<{ get(id: string): unknown }>("elementRegistry")?.get(
      elementId,
    );
    if (!element) return;
    try {
      this.svc<{ activate(el: unknown): void }>("directEditing")?.activate(element);
    } catch {
      // elemento sem suporte a direct editing (ex.: label implícita) — no-op
    }
  }

  /** Exclusão via commandStack (undo/redo preservados) — modo edit apenas. */
  removeElement(elementId: string): void {
    if (this.mode !== "edit") return;
    const registry = this.svc<{
      get(id: string): { type?: string } | undefined;
    }>("elementRegistry");
    const element = registry?.get(elementId);
    if (!element) return;
    const modeling = this.svc<{
      removeShape(el: unknown): void;
      removeConnection(el: unknown): void;
    }>("modeling");
    if (!modeling) return;
    const type = element.type ?? "";
    if (type.endsWith("Flow") || type === "bpmn:Association" || type === "bpmn:DataInputAssociation" || type === "bpmn:DataOutputAssociation") {
      modeling.removeConnection(element);
    } else {
      modeling.removeShape(element);
    }
  }

  findElements(query: { name?: string; id?: string }): ElementRef[] {
    const registry = this.svc<{
      getAll(): Array<{ id: string; type: string; businessObject?: { name?: string } }>;
    }>("elementRegistry");
    if (!registry) return [];
    const all = registry.getAll() as Array<{
      id: string;
      type: string;
      businessObject?: { name?: string };
    }>;
    return all
      .filter((el) => {
        if (query.id && el.id === query.id) return true;
        if (
          query.name &&
          el.businessObject?.name
            ?.toLowerCase()
            .includes(query.name.toLowerCase())
        )
          return true;
        return false;
      })
      .map((el) => ({
        id: el.id,
        name: el.businessObject?.name,
        type: el.type,
      }));
  }

  selectElement(id: string): void {
    const registry = this.svc<{ get(id: string): unknown }>("elementRegistry");
    const element = registry?.get(id);
    if (!element) return;
    this.svc<{ select(el: unknown): void }>("selection")?.select(element);
    this.svc<{ scrollToElement(el: unknown): void }>("canvas")?.scrollToElement(element);
  }

  getElementSummary(id: string): ElementSummary | null {
    if (!this.modeler) return null;
    const element = this.svc<{
      get(id: string): {
        type: string;
        businessObject?: {
          id?: string;
          name?: string;
          documentation?: Array<{ text?: string }>;
          $attrs?: Record<string, unknown>;
        };
      } | undefined;
    }>("elementRegistry")?.get(id);
    if (!element) return null;
    const bo = element.businessObject;
    const attributes: Record<string, string> = {};
    if (bo?.$attrs) {
      for (const [key, value] of Object.entries(bo.$attrs)) {
        attributes[key] = String(value);
      }
    }
    const documentation = bo?.documentation?.[0]?.text;
    return {
      id: bo?.id ?? id,
      name: bo?.name,
      type: element.type,
      documentation,
      attributes,
    };
  }

  subscribe(events: EditorSubscriptions): Unsubscribe {
    this.subs = events;
    return () => {
      this.subs = {};
    };
  }

  // ---- internos ----

  private svc<T>(name: string): T | null {
    if (!this.modeler) return null;
    try {
      return this.modeler.get(name) as T;
    } catch {
      return null;
    }
  }

  private wireEvents(): void {
    const eventBus = this.svc<{
      on(name: string, cb: (event: never) => void): void;
    }>("eventBus");
    if (!eventBus) return;
    eventBus.on("commandStack.changed", (event: { trigger?: string }) => {
      const trigger = (event.trigger ?? "execute") as CommandTrigger;
      this.applyCommand(trigger);
      this.subs.onChanged?.(trigger);
    });
    eventBus.on(
      "selection.changed",
      (event: { newSelection?: Array<{ id: string }> }) => {
        this.subs.onSelectionChanged?.(
          (event.newSelection ?? []).map((el) => el.id),
        );
      },
    );
    eventBus.on(
      "element.contextmenu",
      (event: {
        element?: { id?: string; type?: string };
        originalEvent?: MouseEvent;
      }) => {
        const cb = this.subs.onCanvasContextMenu;
        if (!cb) return;
        const mouse = event.originalEvent;
        if (mouse) mouse.preventDefault();
        const el = event.element;
        const isRoot = !el || el.type === "bpmn:Process" || el.type === "bpmn:Collaboration";
        cb({
          elementId: isRoot ? null : (el?.id ?? null),
          x: mouse?.clientX ?? 0,
          y: mouse?.clientY ?? 0,
        });
      },
    );
  }

  private applyCommand(trigger: CommandTrigger): void {
    switch (trigger) {
      case "execute":
        this.stateTokens = this.stateTokens.slice(0, this.cursor + 1);
        this.stateTokens.push(newToken());
        this.cursor += 1;
        break;
      case "undo":
        if (this.cursor > 0) this.cursor -= 1;
        break;
      case "redo":
        if (this.cursor < this.stateTokens.length - 1) this.cursor += 1;
        break;
      case "clear":
        this.stateTokens = [newToken()];
        this.cursor = 0;
        this.savedToken = this.stateTokens[0];
        break;
    }
  }

  private commandStack(): {
    undo(): void;
    redo(): void;
    canUndo(): boolean;
    canRedo(): boolean;
  } | null {
    if (!this.modeler || this.mode !== "edit") return null;
    return this.svc("commandStack");
  }

  private vendorFailure(err: unknown, phase: string): EditorImportFailure {
    return {
      kind: "EDITOR_CAPABILITY_FAILURE",
      message: this.describe(err, phase),
    };
  }

  private capabilityError(message: string): Error {
    const error = new Error(message);
    error.name = "EDITOR_CAPABILITY_FAILURE";
    return error;
  }

  private describe(err: unknown, phase: string): string {
    const detail = err instanceof Error ? err.message : String(err);
    return `vendor ${phase} failure: ${detail}`;
  }
}
