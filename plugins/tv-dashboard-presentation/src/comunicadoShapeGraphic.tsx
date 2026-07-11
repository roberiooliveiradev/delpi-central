import type { CSSProperties, ReactNode } from "react";

import type { ComunicadoShapeGeometry } from "./comunicadoShapeGeometry";
import { COMUNICADO_MARKER_RADIUS_DEFAULT, geometryBoundingFrame } from "./comunicadoShapeGeometry";
import type { ComunicadoShapeKind } from "./comunicadoTypes";

export type ShapeGraphicColors = {
  fill: string;
  stroke: string;
  strokeWidth: number;
};

const PREVIEW_COLORS: ShapeGraphicColors = {
  fill: "transparent",
  stroke: "#1f2937",
  strokeWidth: 1.75,
};

function polygonPoints(coords: number[]): string {
  const pairs: string[] = [];
  for (let index = 0; index < coords.length; index += 2) {
    pairs.push(`${coords[index]},${coords[index + 1]}`);
  }
  return pairs.join(" ");
}

function starPoints(points: number, outer = 46, inner = 20, cx = 50, cy = 50): string {
  const coords: number[] = [];
  for (let i = 0; i < points * 2; i += 1) {
    const radius = i % 2 === 0 ? outer : inner;
    const angle = (Math.PI / points) * i - Math.PI / 2;
    coords.push(cx + radius * Math.cos(angle), cy + radius * Math.sin(angle));
  }
  return polygonPoints(coords);
}

function renderLineGeometry(
  geometry: Extract<ComunicadoShapeGeometry, { primitive: "line" }>,
  kind: ComunicadoShapeKind,
  colors: ShapeGraphicColors,
): ReactNode {
  const bbox = geometryBoundingFrame(geometry);
  const { stroke, strokeWidth } = colors;
  const sw = Math.max(3, strokeWidth * 2);
  const normalized = geometry.points.map((point) => ({
    x: bbox.w > 0 ? ((point.x - bbox.x) / bbox.w) * 100 : 50,
    y: bbox.h > 0 ? ((point.y - bbox.y) / bbox.h) * 100 : 50,
  }));
  const [start, end] = normalized;
  if (!start || !end) return null;

  const head = (tip: { x: number; y: number }, from: { x: number; y: number }) => {
    const dx = tip.x - from.x;
    const dy = tip.y - from.y;
    const len = Math.max(Math.hypot(dx, dy), 1);
    const ux = dx / len;
    const uy = dy / len;
    const px = -uy;
    const py = ux;
    const baseX = tip.x - ux * 16;
    const baseY = tip.y - uy * 16;
    return `${tip.x},${tip.y} ${baseX + px * 10},${baseY + py * 10} ${baseX - px * 10},${baseY - py * 10}`;
  };

  return (
    <>
      <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke={stroke} strokeWidth={sw} />
      {kind === "line-arrow-right" || kind === "line-arrow-both" ? (
        <polygon points={head(end, start)} fill={stroke} />
      ) : null}
      {kind === "line-arrow-left" || kind === "line-arrow-both" ? (
        <polygon points={head(start, end)} fill={stroke} />
      ) : null}
    </>
  );
}

function renderPointMarker(
  fill: string,
  stroke: string,
  strokeWidth: number,
  markerRadius: number,
): ReactNode {
  const size = markerRadius * 2;
  return (
    <svg
      viewBox={`0 0 ${size} ${size}`}
      className="tdp-comunicado__shape-svg tdp-comunicado__shape-svg--point"
      aria-hidden="true"
      style={{ width: size, height: size, overflow: "visible" }}
    >
      <circle
        cx={markerRadius}
        cy={markerRadius}
        r={markerRadius}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeWidth > 0 ? strokeWidth : 0}
      />
    </svg>
  );
}

function renderSvgShape(
  kind: ComunicadoShapeKind,
  colors: ShapeGraphicColors,
  borderRadius?: number,
): ReactNode {
  const { fill, stroke, strokeWidth } = colors;
  const sw = strokeWidth;

  switch (kind) {
    case "point":
      return (
        <circle
          cx="50"
          cy="50"
          r="10"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw > 0 ? sw : 0}
        />
      );
    case "line":
      return <line x1="4" y1="50" x2="96" y2="50" stroke={stroke} strokeWidth={Math.max(3, sw * 2)} />;
    case "line-arrow-right":
      return (
        <>
          <line x1="4" y1="50" x2="78" y2="50" stroke={stroke} strokeWidth={Math.max(3, sw * 2)} />
          <polygon points="78,38 96,50 78,62" fill={stroke} />
        </>
      );
    case "line-arrow-left":
      return (
        <>
          <polygon points="22,38 4,50 22,62" fill={stroke} />
          <line x1="22" y1="50" x2="96" y2="50" stroke={stroke} strokeWidth={Math.max(3, sw * 2)} />
        </>
      );
    case "line-arrow-both":
      return (
        <>
          <polygon points="22,38 4,50 22,62" fill={stroke} />
          <line x1="22" y1="50" x2="78" y2="50" stroke={stroke} strokeWidth={Math.max(3, sw * 2)} />
          <polygon points="78,38 96,50 78,62" fill={stroke} />
        </>
      );
    case "triangle":
      return (
        <polygon
          points={polygonPoints([50, 8, 92, 92, 8, 92])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "right-triangle":
      return (
        <polygon
          points={polygonPoints([8, 8, 8, 92, 92, 92])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "parallelogram":
    case "flowchart-data":
      return (
        <polygon
          points={polygonPoints([22, 12, 94, 12, 78, 88, 6, 88])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "trapezoid":
    case "flowchart-preparation":
      return (
        <polygon
          points={polygonPoints([22, 12, 78, 12, 94, 88, 6, 88])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "diamond":
    case "flowchart-decision":
      return (
        <polygon
          points={polygonPoints([50, 6, 94, 50, 50, 94, 6, 50])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "pentagon":
      return (
        <polygon
          points={polygonPoints([50, 6, 94, 38, 78, 92, 22, 92, 6, 38])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "hexagon":
      return (
        <polygon
          points={polygonPoints([50, 4, 90, 27, 90, 73, 50, 96, 10, 73, 10, 27])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "octagon":
      return (
        <polygon
          points={polygonPoints([30, 6, 70, 6, 94, 30, 94, 70, 70, 94, 30, 94, 6, 70, 6, 30])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "cross":
      return (
        <path
          d="M38 8 H62 V38 H92 V62 H62 V92 H38 V62 H8 V38 H38 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "cylinder":
      return (
        <>
          <ellipse cx="50" cy="22" rx="34" ry="12" fill={fill} stroke={stroke} strokeWidth={sw} />
          <path d="M16 22 V72 C16 84 84 84 84 72 V22" fill={fill} stroke={stroke} strokeWidth={sw} />
          <ellipse cx="50" cy="72" rx="34" ry="12" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "heart":
      return (
        <path
          d="M50 88 C20 62 6 44 14 26 C22 10 38 10 50 24 C62 10 78 10 86 26 C94 44 80 62 50 88 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "lightning":
      return (
        <polygon
          points={polygonPoints([58, 6, 34, 46, 50, 46, 30, 94, 70, 48, 52, 48])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "cloud":
    case "callout-cloud":
      return (
        <path
          d="M28 70 C12 70 10 50 24 44 C18 28 40 18 52 28 C60 16 84 22 82 40 C96 42 96 66 80 68 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "moon":
      return (
        <path
          d="M62 12 C38 16 22 40 28 66 C34 88 58 98 78 88 C54 92 36 72 40 48 C44 28 54 16 62 12 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "sun":
      return (
        <>
          <circle cx="50" cy="50" r="18" fill={fill} stroke={stroke} strokeWidth={sw} />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
            const rad = (deg * Math.PI) / 180;
            const x1 = 50 + Math.cos(rad) * 24;
            const y1 = 50 + Math.sin(rad) * 24;
            const x2 = 50 + Math.cos(rad) * 42;
            const y2 = 50 + Math.sin(rad) * 42;
            return (
              <line
                key={deg}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={stroke}
                strokeWidth={Math.max(2, sw)}
              />
            );
          })}
        </>
      );
    case "arrow-right":
      return (
        <path
          d="M4 50 H58 L44 34 L54 24 L96 50 L54 76 L44 66 L58 50 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "arrow-left":
      return (
        <path
          d="M96 50 H42 L56 34 L46 24 L4 50 L46 76 L56 66 L42 50 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "arrow-up":
      return (
        <path
          d="M50 4 L76 46 L62 46 L62 96 L38 96 L38 46 L24 46 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "arrow-down":
      return (
        <path
          d="M50 96 L24 54 L38 54 L38 4 L62 4 L62 54 L76 54 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "arrow-left-right":
      return (
        <path
          d="M4 50 L24 30 L24 42 H76 L76 30 L96 50 L76 70 L76 58 H24 L24 70 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "arrow-up-down":
      return (
        <path
          d="M50 4 L70 24 L58 24 V76 L70 76 L50 96 L30 76 L42 76 V24 L30 24 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "chevron-right":
      return (
        <path
          d="M28 12 L72 50 L28 88 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "chevron-left":
      return (
        <path
          d="M72 12 L28 50 L72 88 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "notched-arrow-right":
      return (
        <path
          d="M8 30 H62 L50 18 L70 18 L96 50 L70 82 L50 82 L62 70 H8 L20 50 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "star":
      return (
        <polygon points={starPoints(5)} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
      );
    case "star-4":
      return (
        <polygon points={starPoints(4)} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
      );
    case "star-6":
      return (
        <polygon points={starPoints(6)} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
      );
    case "star-8":
      return (
        <polygon points={starPoints(8, 46, 22)} fill={fill} stroke={stroke} strokeWidth={sw} strokeLinejoin="round" />
      );
    case "banner":
      return (
        <path
          d="M8 28 H92 L84 50 L92 72 H8 L16 50 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "wave":
      return (
        <path
          d="M8 40 C24 20 40 60 56 40 C72 20 88 60 92 40 V72 C76 92 60 52 44 72 C28 92 12 52 8 72 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "callout-rect":
      return (
        <>
          <rect x="8" y="8" width="84" height="58" rx="10" fill={fill} stroke={stroke} strokeWidth={sw} />
          <polygon points="42,66 50,84 58,66" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "callout-rounded":
      return (
        <>
          <rect x="10" y="10" width="80" height="54" rx="20" fill={fill} stroke={stroke} strokeWidth={sw} />
          <polygon points="40,64 50,88 60,64" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "flowchart-document":
      return (
        <path
          d="M12 10 H88 V70 C70 82 50 58 12 70 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "flowchart-terminator":
      return <rect x="8" y="28" width="84" height="44" rx="22" fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "snip-rect":
      return (
        <polygon
          points={polygonPoints([8, 12, 78, 12, 92, 26, 92, 88, 8, 88])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "round-same-side-rect":
      return (
        <path
          d="M18 12 H82 Q92 12 92 22 V88 H8 V22 Q8 12 18 12 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "equation-plus":
      return (
        <path d="M42 18 H58 V42 H82 V58 H58 V82 H42 V58 H18 V42 H42 Z" fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "equation-minus":
      return <rect x="18" y="42" width="64" height="16" fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "equation-multiply":
      return (
        <path
          d="M28 22 L50 44 L72 22 L82 32 L60 54 L82 76 L72 86 L50 64 L28 86 L18 76 L40 54 L18 32 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "equation-divide":
      return (
        <>
          <circle cx="50" cy="28" r="8" fill={fill} stroke={stroke} strokeWidth={sw} />
          <rect x="18" y="42" width="64" height="16" fill={fill} stroke={stroke} strokeWidth={sw} />
          <circle cx="50" cy="72" r="8" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "equation-equal":
      return (
        <>
          <rect x="18" y="34" width="64" height="12" fill={fill} stroke={stroke} strokeWidth={sw} />
          <rect x="18" y="54" width="64" height="12" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "ellipse":
      return <ellipse cx="50" cy="50" rx="42" ry="34" fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "rounded-rect":
    case "flowchart-process":
    case "rectangle":
    default:
      return (
        <rect
          x="8"
          y="12"
          width="84"
          height="76"
          rx={kind === "rectangle" ? 0 : borderRadius ?? 14}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
  }
}

export function ComunicadoShapePreview({
  kind,
  className = "tdp-comunicado__shape-preview",
}: {
  kind: ComunicadoShapeKind;
  className?: string;
}) {
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      {renderSvgShape(kind, PREVIEW_COLORS)}
    </svg>
  );
}

export function ComunicadoShapeGraphic({
  kind,
  fill,
  stroke,
  strokeWidth,
  borderRadius,
  geometry,
  markerRadius = COMUNICADO_MARKER_RADIUS_DEFAULT,
}: {
  kind: ComunicadoShapeKind;
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius?: number;
  geometry?: ComunicadoShapeGeometry;
  markerRadius?: number;
}) {
  if (geometry?.primitive === "point") {
    return renderPointMarker(fill, stroke, strokeWidth, markerRadius);
  }

  if (geometry?.primitive === "line") {
    return (
      <svg viewBox="0 0 100 100" className="tdp-comunicado__shape-svg" aria-hidden="true" preserveAspectRatio="none">
        {renderLineGeometry(geometry, kind, { fill, stroke, strokeWidth })}
      </svg>
    );
  }

  if (kind === "line" || kind === "line-arrow-right" || kind === "line-arrow-left" || kind === "line-arrow-both") {
    return (
      <svg viewBox="0 0 100 100" className="tdp-comunicado__shape-svg" aria-hidden="true">
        {renderSvgShape(kind, { fill, stroke, strokeWidth })}
      </svg>
    );
  }

  if (kind === "point") {
    return renderPointMarker(fill, stroke, strokeWidth, markerRadius);
  }

  const cssKinds: ComunicadoShapeKind[] = ["rectangle", "rounded-rect", "ellipse", "flowchart-process"];
  if (cssKinds.includes(kind)) {
    const shapeStyle: CSSProperties = {
      width: "100%",
      height: "100%",
      backgroundColor: fill,
      border: `${strokeWidth}px solid ${stroke}`,
      borderRadius:
        kind === "ellipse"
          ? "50%"
          : kind === "rounded-rect" || kind === "flowchart-process"
            ? borderRadius ?? 16
            : 0,
    };
    return <div className="tdp-comunicado__shape-fill" style={shapeStyle} />;
  }

  if (kind === "flowchart-terminator") {
    const shapeStyle: CSSProperties = {
      width: "100%",
      height: "100%",
      backgroundColor: fill,
      border: `${strokeWidth}px solid ${stroke}`,
      borderRadius: 9999,
    };
    return <div className="tdp-comunicado__shape-fill" style={shapeStyle} />;
  }

  return (
    <svg viewBox="0 0 100 100" className="tdp-comunicado__shape-svg" preserveAspectRatio="none" aria-hidden="true">
      {renderSvgShape(kind, { fill, stroke, strokeWidth }, borderRadius)}
    </svg>
  );
}
