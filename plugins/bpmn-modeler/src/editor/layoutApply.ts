/**
 * layout.applyDi — CommandHandler diagram-js que aplica uma proposta de
 * geometria BPMN-DI como UM ÚNICO comando lógico (P5 §18).
 *
 * Accept do preview → commandStack.execute("layout.applyDi", { ops })
 * → commandStack.changed("execute") → DIRTY → undo reverte o batch
 * inteiro (não N comandos individuais). Só APIs públicas do diagram-js
 * são usadas (registerHandler/execute); nada de internals privados.
 */
import type { DiBounds, DiLayoutOp } from "../layout/diProposal";

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
  labelBounds?: DiBounds;
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

      const prev: OldEntry = {
        element,
        x: element.x,
        y: element.y,
        width: element.width,
        height: element.height,
        waypoints: element.waypoints,
        diBounds: di.bounds ? { ...di.bounds } : undefined,
        diWaypoints: di.waypoint,
        labelBounds: di.label?.bounds ? { ...di.label.bounds } : undefined,
      };

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
        if (prev.labelBounds && di.label?.bounds) {
          di.label.bounds.x = prev.labelBounds.x;
          di.label.bounds.y = prev.labelBounds.y;
          di.label.bounds.width = prev.labelBounds.width;
          di.label.bounds.height = prev.labelBounds.height;
        }
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
