/**
 * Geometria SVG (viewBox 0–100) parametrizada por adjustments PowerPoint-like.
 */
export function polygonPoints(coords: number[]): string {
  const pairs: string[] = [];
  for (let index = 0; index < coords.length; index += 2) {
    pairs.push(`${coords[index]},${coords[index + 1]}`);
  }
  return pairs.join(" ");
}

export function starPoints(
  points: number,
  outer = 46,
  inner = 20,
  cx = 50,
  cy = 50,
): string {
  const coords: number[] = [];
  for (let i = 0; i < points * 2; i += 1) {
    const radius = i % 2 === 0 ? outer : inner;
    const angle = (Math.PI / points) * i - Math.PI / 2;
    coords.push(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
  }
  return polygonPoints(coords);
}

function a(values: number[], index: number, fallback: number): number {
  const raw = values[index];
  return typeof raw === "number" && Number.isFinite(raw) ? raw : fallback;
}

/**
 * Seta estilo PowerPoint (7 vértices) — corpo retangular + cabeça triangular.
 * Sem “barbas” intermediárias que geravam pontas finas no SVG.
 */
export function arrowRightPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const neckX = 100 - head * 100;
  const half = shaft * 50;
  const y1 = 50 - half;
  const y2 = 50 + half;
  return `M4 ${y1} H${neckX} V8 L96 50 L${neckX} 92 V${y2} H4 Z`;
}

export function arrowLeftPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const neckX = head * 100;
  const half = shaft * 50;
  const y1 = 50 - half;
  const y2 = 50 + half;
  return `M96 ${y1} H${neckX} V8 L4 50 L${neckX} 92 V${y2} H96 Z`;
}

export function arrowUpPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const neckY = head * 100;
  const half = shaft * 50;
  const x1 = 50 - half;
  const x2 = 50 + half;
  return `M${x1} 96 V${neckY} H8 L50 4 L92 ${neckY} H${x2} V96 Z`;
}

export function arrowDownPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const neckY = 100 - head * 100;
  const half = shaft * 50;
  const x1 = 50 - half;
  const x2 = 50 + half;
  return `M${x1} 4 V${neckY} H8 L50 96 L92 ${neckY} H${x2} V4 Z`;
}

export function arrowLeftRightPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const left = head * 100;
  const right = 100 - head * 100;
  const half = shaft * 50;
  const y1 = 50 - half;
  const y2 = 50 + half;
  return `M${left} ${y1} H${right} V8 L96 50 L${right} 92 V${y2} H${left} V92 L4 50 L${left} 8 Z`;
}

export function arrowUpDownPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const top = head * 100;
  const bottom = 100 - head * 100;
  const half = shaft * 50;
  const x1 = 50 - half;
  const x2 = 50 + half;
  return `M${x1} ${top} V${bottom} H8 L50 96 L92 ${bottom} H${x2} V${top} H92 L50 4 L8 ${top} Z`;
}

export function parallelogramPoints(values: number[]): number[] {
  const slant = a(values, 0, 0.2) * 100;
  return [8 + slant, 12, 94, 12, 94 - slant, 88, 6, 88];
}

export function trapezoidPoints(values: number[]): number[] {
  const inset = a(values, 0, 0.22) * 100;
  return [8 + inset, 12, 92 - inset, 12, 94, 88, 6, 88];
}

export function trianglePoints(values: number[]): number[] {
  const tip = a(values, 0, 0.5) * 100;
  return [tip, 8, 92, 92, 8, 92];
}

export function hexagonPoints(values: number[]): number[] {
  const inset = a(values, 0, 0.2) * 40;
  return [50, 4, 100 - inset, 27, 100 - inset, 73, 50, 96, inset, 73, inset, 27];
}

export function octagonPoints(values: number[]): number[] {
  const cut = a(values, 0, 0.25) * 40;
  return [
    8 + cut,
    6,
    92 - cut,
    6,
    94,
    6 + cut,
    94,
    94 - cut,
    92 - cut,
    94,
    8 + cut,
    94,
    6,
    94 - cut,
    6,
    6 + cut,
  ];
}

export function crossPath(values: number[]): string {
  const arm = a(values, 0, 0.28) * 50;
  const a0 = 50 - arm;
  const a1 = 50 + arm;
  return `M${a0} 8 H${a1} V${a0} H92 V${a1} H${a1} V92 H${a0} V${a1} H8 V${a0} H${a0} Z`;
}

/** Chevron (faixa em V) — profundidade controla o avanço da ponta. */
export function chevronRightPath(values: number[]): string {
  const depth = a(values, 0, 0.45) * 100;
  const band = Math.min(28, Math.max(12, depth * 0.35));
  const tip = Math.min(96, 8 + depth);
  const inner = Math.max(8, tip - band);
  return `M8 12 L${tip} 50 L8 88 H${8 + band} L${inner} 50 L${8 + band} 12 Z`;
}

export function chevronLeftPath(values: number[]): string {
  const depth = a(values, 0, 0.45) * 100;
  const band = Math.min(28, Math.max(12, depth * 0.35));
  const tip = Math.max(4, 92 - depth);
  const inner = Math.min(92, tip + band);
  return `M92 12 L${tip} 50 L92 88 H${92 - band} L${inner} 50 L${92 - band} 12 Z`;
}

/** Seta com entalhe na base (PowerPoint notched right arrow). */
export function notchedArrowPath(values: number[]): string {
  const head = a(values, 0, 0.35);
  const shaft = a(values, 1, 0.28);
  const neckX = 100 - head * 100;
  const half = shaft * 50;
  const y1 = 50 - half;
  const y2 = 50 + half;
  const notch = Math.min(18, half * 0.85);
  return `M4 ${y1} H${neckX} V8 L96 50 L${neckX} 92 V${y2} H4 L${4 + notch} 50 Z`;
}

export function bannerPath(values: number[]): string {
  const fold = a(values, 0, 0.18) * 40;
  return `M8 28 H${92 - fold} L92 50 L${92 - fold} 72 H8 L${8 + fold} 50 Z`;
}

export function wavePath(values: number[]): string {
  const amp = a(values, 0, 0.22) * 40;
  const mid = 40;
  return `M8 ${mid} C24 ${mid - amp} 40 ${mid + amp} 56 ${mid} C72 ${mid - amp} 88 ${mid + amp} 92 ${mid} V${mid + 32} C76 ${mid + 32 + amp} 60 ${mid + 32 - amp} 44 ${mid + 32} C28 ${mid + 32 + amp} 12 ${mid + 32 - amp} 8 ${mid + 32} Z`;
}

export function snipRectPoints(values: number[]): number[] {
  const snip = a(values, 0, 0.2) * 40;
  return [8, 12, 92 - snip, 12, 92, 12 + snip, 92, 88, 8, 88];
}

export function roundSameSidePath(values: number[]): string {
  const r = a(values, 0, 0.18) * 40;
  return `M${8 + r} 12 H${92 - r} Q92 12 92 ${12 + r} V88 H8 V${12 + r} Q8 12 ${8 + r} 12 Z`;
}

export function documentPath(values: number[]): string {
  const curve = a(values, 0, 0.2) * 30;
  return `M12 10 H88 V${70 + curve * 0.2} C70 ${82 + curve} 50 ${58 - curve} 12 ${70 + curve * 0.2} Z`;
}

export function calloutBubble(
  values: number[],
  rx: number,
): { rect: { x: number; y: number; w: number; h: number; rx: number }; tip: string } {
  const px = a(values, 0, 0.5) * 100;
  const py = Math.min(98, a(values, 1, 0.9) * 100);
  const corner = a(values, 2, rx / 50);
  const bodyH = 58;
  const tipBase = bodyH + 8;
  return {
    rect: { x: 8, y: 8, w: 84, h: bodyH, rx: corner * 50 },
    tip: `${px - 8},${tipBase} ${px},${py} ${px + 8},${tipBase}`,
  };
}

export function moonPath(values: number[]): string {
  const c = a(values, 0, 0.45);
  const shift = 20 + c * 30;
  return `M62 12 C38 16 22 40 28 66 C34 88 58 98 78 88 C${54 + shift * 0.2} 92 ${36 + shift * 0.1} 72 ${40 + shift * 0.15} 48 C${44 + shift * 0.1} 28 ${54} 16 62 12 Z`;
}

export function cylinderParts(values: number[]): { ry: number; bodyBottom: number } {
  const cap = a(values, 0, 0.18);
  const ry = 8 + cap * 24;
  return { ry, bodyBottom: 72 + (0.18 - cap) * 20 };
}

export function cornerRx(values: number[], fallback: number): number {
  return a(values, 0, fallback / 50) * Math.min(84, 76);
}
