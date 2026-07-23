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

/** Polígono regular (heptágono, decágono, …) centrado no viewBox 0–100. */
export function regularPolygonPoints(
  sides: number,
  radius = 46,
  cx = 50,
  cy = 50,
): number[] {
  const coords: number[] = [];
  for (let i = 0; i < sides; i += 1) {
    const angle = (Math.PI * 2 * i) / sides - Math.PI / 2;
    coords.push(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
  }
  return coords;
}

export function roundOneRectPath(values: number[]): string {
  const r = a(values, 0, 0.22) * 40;
  return `M8 12 H92 V${88 - r} Q92 88 ${92 - r} 88 H8 Z`;
}

export function snipDiagonalRectPoints(values: number[]): number[] {
  const snip = a(values, 0, 0.22) * 36;
  return [8, 12, 92 - snip, 12, 92, 12 + snip, 92, 88 - snip, 92 - snip, 88, 8, 88];
}

export function teardropPath(): string {
  return "M50 8 C78 8 92 28 92 50 C92 78 72 92 50 92 C28 92 8 72 8 50 C8 32 22 18 38 14 C42 28 50 36 62 36 C54 22 50 12 50 8 Z";
}

export function framePath(values: number[]): string {
  const t = 8 + a(values, 0, 0.2) * 16;
  return `M8 8 H92 V92 H8 Z M${8 + t} ${8 + t} V${92 - t} H${92 - t} V${8 + t} Z`;
}

export function cornerLPath(values: number[]): string {
  const arm = 28 + a(values, 0, 0.35) * 24;
  return `M8 8 H${8 + arm} V${92 - arm} H92 V92 H8 Z`;
}

export function donutPath(values: number[]): string {
  const inner = 12 + a(values, 0, 0.35) * 18;
  return `M50 8 A42 42 0 1 1 49.9 8 Z M50 ${50 - inner} A${inner} ${inner} 0 1 0 50.1 ${50 - inner} Z`;
}

export function piePath(values: number[]): string {
  const sweep = 0.35 + a(values, 0, 0.45) * 0.5;
  const angle = -Math.PI / 2 + sweep * Math.PI * 2;
  const x = 50 + 42 * Math.cos(angle);
  const y = 50 + 42 * Math.sin(angle);
  const large = sweep > 0.5 ? 1 : 0;
  return `M50 50 L50 8 A42 42 0 ${large} 1 ${x} ${y} Z`;
}

export function cubePath(): string {
  /* Isométrico sólido (faces sugeridas por arestas internas no stroke). */
  return "M20 32 L50 14 L80 32 L80 68 L50 86 L20 68 Z M20 32 L50 50 L80 32 M50 50 V86";
}

export function foldedCornerPath(values: number[]): string {
  const fold = 18 + a(values, 0, 0.25) * 20;
  return `M8 8 H${92 - fold} L92 ${8 + fold} V92 H8 Z M${92 - fold} 8 V${8 + fold} H92`;
}

export function bentArrowPath(values: number[]): string {
  const head = a(values, 0, 0.28);
  const shaft = a(values, 1, 0.22);
  const half = shaft * 40;
  const neck = 100 - head * 70;
  return `M12 ${50 - half} H55 V28 H${neck} V12 L92 40 L${neck} 68 V52 H${55 + half} V${50 + half} H12 Z`;
}

export function uTurnArrowPath(values: number[]): string {
  const shaft = a(values, 0, 0.22) * 36;
  return `M28 88 V40 C28 18 48 10 68 10 C88 10 92 28 92 40 V58 H${92 - shaft} V40 C${92 - shaft} 30 80 ${18 + shaft * 0.2} 68 ${18 + shaft * 0.2} C56 ${18 + shaft * 0.2} ${28 + shaft} 28 ${28 + shaft} 40 V72 H44 L28 96 L12 72 H${28} Z`;
}

export function quadArrowPath(values: number[]): string {
  const shaft = a(values, 0, 0.22) * 28;
  const s0 = 50 - shaft;
  const s1 = 50 + shaft;
  return `M50 6 L70 28 H${s1} V${s0} H72 L94 50 L72 72 H${s1} V${s1} H70 L50 94 L30 72 H${s0} V${s1} H28 L6 50 L28 28 H${s0} V${s0} H30 Z`;
}

export function curvedRightArrowPath(values: number[]): string {
  const thick = 10 + a(values, 0, 0.25) * 14;
  return `M18 78 C18 40 40 18 72 18 H78 L68 4 L96 22 L68 40 L78 28 H72 C48 28 34 44 34 ${78 - thick} H18 Z`;
}

export function stripedRightArrowPath(values: number[]): string {
  const head = a(values, 0, 0.32);
  const neckX = 100 - head * 100;
  return `M4 28 H${neckX} V12 L96 50 L${neckX} 88 V72 H4 Z`;
}

export function burstPoints(points = 16, outer = 46, inner = 28): string {
  return starPoints(points, outer, inner);
}

export function scrollPath(): string {
  return "M22 16 H78 C88 16 92 24 92 32 V68 C92 78 84 84 74 84 H26 C16 84 8 76 8 66 V34 C8 22 14 16 22 16 Z M22 16 C14 16 14 28 22 28 H78 M22 84 C14 84 14 72 22 72 H74";
}

export function calloutLineParts(values: number[]): {
  rect: { x: number; y: number; w: number; h: number };
  line: { x1: number; y1: number; x2: number; y2: number };
} {
  const px = 8 + a(values, 0, 0.15) * 24;
  const py = 70 + a(values, 1, 0.7) * 26;
  return {
    rect: { x: 28, y: 16, w: 60, h: 48 },
    line: { x1: 28, y1: 52, x2: px, y2: py },
  };
}
