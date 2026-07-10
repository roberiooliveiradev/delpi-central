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
  fill: "#38bdf8",
  stroke: "#e2e8f0",
  strokeWidth: 1.5,
};

function polygonPoints(coords: number[]): string {
  const pairs: string[] = [];
  for (let index = 0; index < coords.length; index += 2) {
    pairs.push(`${coords[index]},${coords[index + 1]}`);
  }
  return pairs.join(" ");
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

  if (kind === "line-arrow-right") {
    return (
      <>
        <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke={stroke} strokeWidth={sw} />
        <polygon
          points={`${end.x},${end.y - 12} ${end.x + 18},${end.y} ${end.x},${end.y + 12}`}
          fill={stroke}
        />
      </>
    );
  }

  return <line x1={start.x} y1={start.y} x2={end.x} y2={end.y} stroke={stroke} strokeWidth={sw} />;
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
    case "triangle":
      return (
        <polygon
          points={polygonPoints([50, 8, 92, 92, 8, 92])}
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
    case "heart":
      return (
        <path
          d="M50 88 C20 62 6 44 14 26 C22 10 38 10 50 24 C62 10 78 10 86 26 C94 44 80 62 50 88 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
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
    case "star":
      return (
        <polygon
          points={polygonPoints([50, 6, 61, 38, 96, 38, 68, 58, 79, 92, 50, 72, 21, 92, 32, 58, 4, 38, 39, 38])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "star-4":
      return (
        <polygon
          points={polygonPoints([50, 4, 58, 42, 96, 50, 58, 58, 50, 96, 42, 58, 4, 50, 42, 42])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "callout-rect":
      return (
        <>
          <rect x="8" y="8" width="84" height="58" rx="10" fill={fill} stroke={stroke} strokeWidth={sw} />
          <polygon points="42,66 50,84 58,66" fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    case "flowchart-terminator":
      return <rect x="8" y="28" width="84" height="44" rx="22" fill={fill} stroke={stroke} strokeWidth={sw} />;
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

  if (kind === "line" || kind === "line-arrow-right") {
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
