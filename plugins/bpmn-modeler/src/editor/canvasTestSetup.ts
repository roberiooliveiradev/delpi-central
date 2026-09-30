/**
 * Stubs de APIs SVG/DOM que jsdom não implementa e que bpmn-js/diagram-js
 * exigem para mount+import (Canvas.viewbox, transforms, text measure).
 *
 * Escopo: somente testes do adapter — nunca importado por código de produção.
 * As matrizes implementam álgebra real (não no-op) para que zoom/fit
 * produzam resultados observáveis.
 */

type StubMatrix = {
  a: number; b: number; c: number; d: number; e: number; f: number;
  inverse(): StubMatrix;
  multiply(m: StubMatrix): StubMatrix;
  translate(x: number, y: number): StubMatrix;
  scale(s: number): StubMatrix;
  scaleNonUniform(x: number, y: number): StubMatrix;
  rotate(angle: number): StubMatrix;
};

function matrix(
  a = 1, b = 0, c = 0, d = 1, e = 0, f = 0,
): StubMatrix {
  return {
    a, b, c, d, e, f,
    inverse() {
      const det = a * d - b * c || 1;
      return matrix(
        d / det, -b / det, -c / det, a / det,
        (c * f - d * e) / det, (b * e - a * f) / det,
      );
    },
    multiply(m) {
      return matrix(
        a * m.a + c * m.b,
        b * m.a + d * m.b,
        a * m.c + c * m.d,
        b * m.c + d * m.d,
        a * m.e + c * m.f + e,
        b * m.e + d * m.f + f,
      );
    },
    translate(x, y) {
      return matrix(a, b, c, d, a * x + c * y + e, b * x + d * y + f);
    },
    scale(s) {
      return matrix(a * s, b * s, c * s, d * s, e, f);
    },
    scaleNonUniform(x, y) {
      return matrix(a * x, b * x, c * y, d * y, e, f);
    },
    rotate(angle) {
      const rad = (angle * Math.PI) / 180;
      const cos = Math.cos(rad);
      const sin = Math.sin(rad);
      return this.multiply(matrix(cos, sin, -sin, cos, 0, 0));
    },
  };
}

type StubTransform = {
  matrix: StubMatrix;
  type?: number;
  setMatrix(m: StubMatrix): void;
  setTranslate(x: number, y: number): void;
  setScale(sx: number, sy: number): void;
  setRotate(angle: number, cx: number, cy: number): void;
};

function makeTransform(m: StubMatrix = matrix()): StubTransform {
  return {
    matrix: m,
    setMatrix(nm) {
      this.matrix = nm;
    },
    setTranslate(x, y) {
      this.matrix = matrix(1, 0, 0, 1, x, y);
    },
    setScale(sx, sy) {
      this.matrix = matrix(sx, 0, 0, sy, 0, 0);
    },
    setRotate(angle, cx, cy) {
      this.matrix = matrix()
        .translate(cx, cy)
        .rotate(angle)
        .translate(-cx, -cy);
    },
  };
}

type StubTransformList = {
  numberOfItems: number;
  clear(): void;
  initialize(t: StubTransform): StubTransform;
  getItem(i: number): StubTransform;
  insertItemBefore(t: StubTransform, i: number): StubTransform;
  replaceItem(t: StubTransform, i: number): StubTransform;
  removeItem(i: number): StubTransform;
  appendItem(t: StubTransform): StubTransform;
  createSVGTransformFromMatrix(m: StubMatrix): StubTransform;
  consolidate(): StubTransform;
};

function parseMatrixAttr(el: Element | null): StubMatrix {
  const attr = el?.getAttribute?.("transform") ?? "";
  const result = matrix();
  let current = result;
  for (const match of attr.matchAll(/matrix\(([^)]*)\)/g)) {
    const p = match[1].split(/[\s,]+/).map(Number);
    current = current.multiply(
      matrix(p[0], p[1], p[2], p[3], p[4] ?? 0, p[5] ?? 0),
    );
  }
  return current;
}

function makeTransformList(el: Element): StubTransformList {
  const items: StubTransform[] = [];
  let lastAttr: string | undefined;

  function syncFromAttribute() {
    const attr = el.getAttribute?.("transform") ?? "";
    if (attr !== lastAttr) {
      lastAttr = attr;
      items.length = 0;
        items.push(makeTransform(parseMatrixAttr(el)));
    }
  }

  return {
    get numberOfItems() {
      syncFromAttribute();
      return items.length;
    },
    clear() {
      syncFromAttribute();
      items.length = 0;
    },
    initialize(t) {
      syncFromAttribute();
      items.length = 0;
      items.push(t);
      return t;
    },
    getItem(i) {
      syncFromAttribute();
      return items[i];
    },
    insertItemBefore(t, i) {
      syncFromAttribute();
      items.splice(i, 0, t);
      return t;
    },
    replaceItem(t, i) {
      syncFromAttribute();
      items[i] = t;
      return t;
    },
    removeItem(i) {
      syncFromAttribute();
      return items.splice(i, 1)[0];
    },
    appendItem(t) {
      syncFromAttribute();
      items.push(t);
      return t;
    },
    createSVGTransformFromMatrix(m) {
      return makeTransform(m);
    },
    consolidate() {
      syncFromAttribute();
      const combined = items.reduce(
        (acc, t) => acc.multiply(t?.matrix ?? matrix()),
        matrix(),
      );
      items.length = 0;
      items.push(makeTransform(combined));
      return makeTransform(combined);
    },
  };
}

const transformLists = new WeakMap<Element, StubTransformList>();

let installed = false;

export function installCanvasDomStubs(): void {
  if (installed) return;
  installed = true;

  const g = globalThis as Record<string, unknown>;

  g.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  g.IntersectionObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };

  // diagram-js Text measurement usa canvas 2d — jsdom retorna null e loga
  // "not implemented". Override direto para manter stderr limpo.
  const canvasProto = (
    g.HTMLCanvasElement as { prototype?: Record<string, unknown> } | undefined
  )?.prototype;
  if (canvasProto) {
    canvasProto.getContext = () => ({
      measureText: (text: string) => ({ width: text.length * 8 }),
      clearRect() {},
      save() {},
      restore() {},
      font: "",
      textBaseline: "",
      fillText() {},
    });
  }

  (g.CSS as { escape?: (s: string) => string } | undefined) ??= {};
  (CSS as { escape?: (s: string) => string }).escape ??= (value: string) =>
    value.replace(/[^a-zA-Z0-9_-]/g, (ch) => `\\${ch}`);

  g.SVGMatrix ??= class {
    constructor() {
      return matrix();
    }
  };
  g.DOMPoint ??= class {
    x: number;
    y: number;
    z: number;
    w: number;
    constructor(x = 0, y = 0, z = 0, w = 1) {
      this.x = x;
      this.y = y;
      this.z = z;
      this.w = w;
    }
    matrixTransform(m: StubMatrix) {
      return {
        x: m.a * this.x + m.c * this.y + m.e,
        y: m.b * this.x + m.d * this.y + m.f,
        z: this.z,
        w: this.w,
      };
    }
  };

  const svgProto = SVGElement.prototype as unknown as Record<string, unknown>;

  svgProto.getBBox ??= () => ({ x: 0, y: 0, width: 0, height: 0 });
  svgProto.getCTM = function (this: Element) {
    return parseMatrixAttr(this);
  };
  svgProto.getScreenCTM = function (this: Element) {
    return parseMatrixAttr(this);
  };

  Object.defineProperty(SVGElement.prototype, "transform", {
    configurable: true,
    get() {
      let list = transformLists.get(this as Element);
      if (!list) {
        list = makeTransformList(this as Element);
        transformLists.set(this as Element, list);
      }
      return { baseVal: list, animVal: list };
    },
  });

  const svgSvgProto = (
    g.SVGSVGElement as { prototype?: Record<string, unknown> } | undefined
  )?.prototype;
  if (svgSvgProto) {
    svgSvgProto.createSVGMatrix ??= () => matrix();
    svgSvgProto.createSVGPoint ??= () =>
      new (g.DOMPoint as new (x?: number, y?: number) => unknown)();
    svgSvgProto.createSVGTransform ??= () => makeTransform();
    svgSvgProto.getCTM ??= () => matrix();
    svgSvgProto.getScreenCTM ??= () => matrix();
  }

  // diagram-js usa clientWidth/Height e getBoundingClientRect do container —
  // jsdom retorna 0, o que quebraria viewbox/scale. Viewport stub 1000x600.
  const proto = HTMLElement.prototype as unknown as {
    getBoundingClientRect?: () => DOMRect;
  };
  const originalRect = proto.getBoundingClientRect;
  proto.getBoundingClientRect = function (this: HTMLElement) {
    if (
      this.classList?.contains("djs-container") ||
      this.classList?.contains("bjs-container") ||
      this.classList?.contains("canvas-host")
    ) {
      return {
        x: 0, y: 0, top: 0, left: 0,
        width: 1000, height: 600,
        right: 1000, bottom: 600,
        toJSON: () => ({}),
      } as DOMRect;
    }
    return originalRect?.call(this) ??
      ({
        x: 0, y: 0, top: 0, left: 0, width: 0, height: 0,
        right: 0, bottom: 0, toJSON: () => ({}),
      } as DOMRect);
  };
}
