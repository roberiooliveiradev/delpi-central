/**
 * layout.applyDi — CommandHandler diagram-js que aplica uma proposta de
 * geometria BPMN-DI como UM ÚNICO comando lógico (P5 §18).
 *
 * Accept do preview → commandStack.execute("layout.applyDi", { ops })
 * → commandStack.changed("execute") → DIRTY → undo reverte o batch
 * inteiro (não N comandos individuais). Só APIs públicas do diagram-js
 * são usadas (registerHandler/execute); nada de internals privados.
 */
import { polylineMid, type DiBounds, type DiLayoutOp } from "../layout/diProposal";

type Point = { x: number; y: number };

type DiModdle = {
  bounds?: DiBounds & { $set?: (attrs: object) => void };
  waypoint?: Point[];
  label?: { bounds?: DiBounds } | null;
  $parent?: unknown;
  set?: (name: string, value: unknown) => void;
};

type RegistryElement = {
  id: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  waypoints?: Point[];
  di?: DiModdle;
  /** Label element associado (external label) — acompanha o owner. */
  label?: RegistryElement;
};

type OldEntry = {
  element: RegistryElement;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  waypoints?: Point[];
  diBounds?: DiBounds;
  diWaypoints?: Point[];
  /** Bounds do BPMNLabel (moddle); undefined = DI não tinha bounds. */
  labelBounds?: DiBounds;
  /** Coords anteriores do label element associado. */
  labelEl?: { x?: number; y?: number; width?: number; height?: number };
};

type Context = {
  ops: DiLayoutOp[];
  old?: OldEntry[];
};

type ElementRegistryLike = {
  get(id: string): RegistryElement | undefined;
  getGraphics(id: string): SVGElement | undefined;
};

type GraphicsFactoryLike = {
  update(type: "shape" | "connection", element: RegistryElement, gfx?: SVGElement): void;
};

type ModdleLike = {
  create<T>(descriptor: string, attrs: object): T;
};

export class ApplyDiLayoutHandler {
  static $inject = ["elementRegistry", "graphicsFactory", "moddle"];

  private readonly elementRegistry: ElementRegistryLike;
  private readonly graphicsFactory: GraphicsFactoryLike;
  private readonly moddle: ModdleLike;

  constructor(
    elementRegistry: ElementRegistryLike,
    graphicsFactory: GraphicsFactoryLike,
    moddle: ModdleLike,
  ) {
    this.elementRegistry = elementRegistry;
    this.graphicsFactory = graphicsFactory;
    this.moddle = moddle;
  }

  execute(context: Context): unknown[] {
    const old: OldEntry[] = [];
    const changed: RegistryElement[] = [];
    for (const op of context.ops) {
      const element = this.elementRegistry.get(op.elementId);
      const di = element?.di;
      if (!element || !di) continue;

      const labelEl = element.label;
      const labelDi = di.label;
      const prev: OldEntry = {
        element,
        x: element.x,
        y: element.y,
        width: element.width,
        height: element.height,
        waypoints: element.waypoints,
        diBounds: di.bounds ? { ...di.bounds } : undefined,
        diWaypoints: di.waypoint,
        labelBounds: labelDi?.bounds ? { ...labelDi.bounds } : undefined,
        labelEl: labelEl
          ? {
              x: labelEl.x,
              y: labelEl.y,
              width: labelEl.width,
              height: labelEl.height,
            }
          : undefined,
      };

      // delta do owner antes de mutar — label externa acompanha o owner.
      let dx = 0;
      let dy = 0;
      if (op.bounds && element.x !== undefined && element.y !== undefined) {
        dx = op.bounds.x - element.x;
        dy = op.bounds.y - element.y;
      } else if (op.waypoints && element.waypoints?.length) {
        const midOld = polylineMid(element.waypoints);
        const midNew = polylineMid(op.waypoints);
        dx = midNew.x - midOld.x;
        dy = midNew.y - midOld.y;
      }

      if (op.bounds && element.width !== undefined) {
        element.x = op.bounds.x;
        element.y = op.bounds.y;
        element.width = op.bounds.width;
        element.height = op.bounds.height;
        if (di.bounds) {
          di.bounds.x = op.bounds.x;
          di.bounds.y = op.bounds.y;
          di.bounds.width = op.bounds.width;
          di.bounds.height = op.bounds.height;
        } else {
          di.bounds = this.moddle.create<DiBounds>("dc:Bounds", {
            ...op.bounds,
          });
        }
      }

      if (op.waypoints) {
        element.waypoints = op.waypoints.map((p) => ({ x: p.x, y: p.y }));
        di.waypoint = op.waypoints.map((p) => {
          const pt = this.moddle.create<Point & { $parent?: unknown }>(
            "dc:Point",
            { x: p.x, y: p.y },
          );
          pt.$parent = di;
          return pt;
        });
      }

      // Label externa: acompanha o owner pelo delta (preserva offset
      // custom e dims). BPMNLabel explícito recebe bounds resolvidas.
      if (labelEl && (dx !== 0 || dy !== 0 || op.labelBounds)) {
        const lb = op.labelBounds;
        labelEl.x = lb ? lb.x : (labelEl.x ?? 0) + dx;
        labelEl.y = lb ? lb.y : (labelEl.y ?? 0) + dy;
        if (lb) {
          labelEl.width = lb.width;
          labelEl.height = lb.height;
        }
        if (labelDi) {
          const nb = {
            x: labelEl.x ?? 0,
            y: labelEl.y ?? 0,
            width: labelEl.width ?? 0,
            height: labelEl.height ?? 0,
          };
          if (labelDi.bounds) {
            Object.assign(labelDi.bounds, nb);
          } else {
            const created = this.moddle.create<DiBounds & { $parent?: unknown }>(
              "dc:Bounds",
              nb,
            );
            created.$parent = labelDi;
            labelDi.bounds = created;
          }
        }
        this.graphicsFactory.update(
          "shape",
          labelEl,
          this.elementRegistry.getGraphics(labelEl.id),
        );
      }

      const type = element.waypoints ? "connection" : "shape";
      this.graphicsFactory.update(
        type,
        element,
        this.elementRegistry.getGraphics(element.id),
      );
      old.push(prev);
      changed.push(element);
    }
    context.old = old;
    return changed;
  }

  revert(context: Context): unknown[] {
    const restored: RegistryElement[] = [];
    for (const prev of context.old ?? []) {
      const { element } = prev;
      const di = element.di;
      element.x = prev.x;
      element.y = prev.y;
      element.width = prev.width;
      element.height = prev.height;
      element.waypoints = prev.waypoints;
      if (di) {
        // moddle objects expõem $type getter-only — copiar somente
        // as propriedades geométricas, nunca Object.assign inteiro.
        if (prev.diBounds) {
          if (di.bounds) {
            di.bounds.x = prev.diBounds.x;
            di.bounds.y = prev.diBounds.y;
            di.bounds.width = prev.diBounds.width;
            di.bounds.height = prev.diBounds.height;
          } else {
            di.bounds = this.moddle.create<DiBounds>("dc:Bounds", {
              ...prev.diBounds,
            });
          }
        } else {
          di.bounds = undefined;
        }
        if (prev.diWaypoints) di.waypoint = prev.diWaypoints;
        if (di.label) {
          if (prev.labelBounds) {
            const nb = {
              x: prev.labelBounds.x,
              y: prev.labelBounds.y,
              width: prev.labelBounds.width,
              height: prev.labelBounds.height,
            };
            if (di.label.bounds) {
              Object.assign(di.label.bounds, nb);
            } else {
              const created = this.moddle.create<DiBounds & { $parent?: unknown }>(
                "dc:Bounds",
                nb,
              );
              created.$parent = di.label;
              di.label.bounds = created;
            }
          } else {
            // bounds criado pelo execute (DI não tinha) — remover
            di.label.bounds = undefined;
          }
        }
      }
      const labelEl = prev.labelEl ? element.label : undefined;
      if (labelEl && prev.labelEl) {
        labelEl.x = prev.labelEl.x;
        labelEl.y = prev.labelEl.y;
        labelEl.width = prev.labelEl.width;
        labelEl.height = prev.labelEl.height;
        this.graphicsFactory.update(
          "shape",
          labelEl,
          this.elementRegistry.getGraphics(labelEl.id),
        );
      }
      const type = element.waypoints ? "connection" : "shape";
      this.graphicsFactory.update(
        type,
        element,
        this.elementRegistry.getGraphics(element.id),
      );
      restored.push(element);
    }
    return restored;
  }
}
