import type { CSSProperties, ReactNode } from "react";

import type { ComunicadoShapeGeometry } from "./comunicadoShapeGeometry";
import { COMUNICADO_MARKER_RADIUS_DEFAULT, geometryBoundingFrame } from "./comunicadoShapeGeometry";
import { resolveShapeAdjustments } from "./comunicadoShapeAdjustments";
import type { ComunicadoBlockStyle, ComunicadoShapeKind } from "./comunicadoTypes";
import {
  arrowDownPath,
  arrowLeftPath,
  arrowLeftRightPath,
  arrowRightPath,
  arrowUpDownPath,
  arrowUpPath,
  bannerPath,
  calloutBubble,
  chevronLeftPath,
  chevronRightPath,
  cornerRx,
  crossPath,
  cylinderParts,
  documentPath,
  hexagonPoints,
  moonPath,
  notchedArrowPath,
  octagonPoints,
  parallelogramPoints,
  polygonPoints,
  roundSameSidePath,
  snipRectPoints,
  starPoints,
  trapezoidPoints,
  trianglePoints,
  wavePath,
} from "./comunicadoShapePaths";

export type ShapeGraphicColors = {
  fill: string;
  stroke: string;
  strokeWidth: number;
};

const PREVIEW_COLORS: ShapeGraphicColors = {
  fill: "transparent",
  /** Herda cor do tema (claro/escuro) via CSS `color` no preview. */
  stroke: "currentColor",
  strokeWidth: 1.75,
};

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
  adjustments: number[] = [],
  borderRadiusPx?: number,
): ReactNode {
  const { fill, stroke, strokeWidth } = colors;
  const sw = strokeWidth;
  const adj = adjustments;

  switch (kind) {
    case "point":
      return (
        <circle cx="50" cy="50" r="10" fill={fill} stroke={stroke} strokeWidth={sw > 0 ? sw : 0} />
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
        <polygon points={polygonPoints(trianglePoints(adj))} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "right-triangle":
      return (
        <polygon points={polygonPoints([8, 8, 8, 92, 92, 92])} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "parallelogram":
    case "flowchart-data":
      return (
        <polygon
          points={polygonPoints(parallelogramPoints(adj))}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    case "trapezoid":
    case "flowchart-preparation":
      return (
        <polygon points={polygonPoints(trapezoidPoints(adj))} fill={fill} stroke={stroke} strokeWidth={sw} />
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
    case "pentagon": {
      const tip = (adj[0] ?? 0.5) * 100;
      return (
        <polygon
          points={polygonPoints([tip, 6, 94, 38, 78, 92, 22, 92, 6, 38])}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    }
    case "hexagon":
      return (
        <polygon points={polygonPoints(hexagonPoints(adj))} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "octagon":
      return (
        <polygon points={polygonPoints(octagonPoints(adj))} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "cross":
      return <path d={crossPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "cylinder": {
      const { ry, bodyBottom } = cylinderParts(adj);
      return (
        <>
          <ellipse cx="50" cy={12 + ry} rx="34" ry={ry} fill={fill} stroke={stroke} strokeWidth={sw} />
          <path
            d={`M16 ${12 + ry} V${bodyBottom} C16 ${bodyBottom + ry} 84 ${bodyBottom + ry} 84 ${bodyBottom} V${12 + ry}`}
            fill={fill}
            stroke={stroke}
            strokeWidth={sw}
          />
          <ellipse
            cx="50"
            cy={bodyBottom}
            rx="34"
            ry={ry}
            fill={fill}
            stroke={stroke}
            strokeWidth={sw}
          />
        </>
      );
    }
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
    case "callout-cloud": {
      if (kind === "callout-cloud") {
        const bubble = calloutBubble(adj, 10);
        return (
          <>
            <path
              d="M28 58 C12 58 10 38 24 32 C18 16 40 6 52 16 C60 4 84 10 82 28 C96 30 96 54 80 56 Z"
              fill={fill}
              stroke={stroke}
              strokeWidth={sw}
            />
            <polygon points={bubble.tip} fill={fill} stroke={stroke} strokeWidth={sw} />
          </>
        );
      }
      return (
        <path
          d="M28 70 C12 70 10 50 24 44 C18 28 40 18 52 28 C60 16 84 22 82 40 C96 42 96 66 80 68 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
      );
    }
    case "moon":
      return <path d={moonPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "sun": {
      const core = (adj[0] ?? 0.35) * 40;
      return (
        <>
          <circle cx="50" cy="50" r={core} fill={fill} stroke={stroke} strokeWidth={sw} />
          {[0, 45, 90, 135, 180, 225, 270, 315].map((deg) => {
            const rad = (deg * Math.PI) / 180;
            const x1 = 50 + Math.cos(rad) * (core + 6);
            const y1 = 50 + Math.sin(rad) * (core + 6);
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
    }
    case "arrow-right":
      return <path d={arrowRightPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "arrow-left":
      return <path d={arrowLeftPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "arrow-up":
      return <path d={arrowUpPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "arrow-down":
      return <path d={arrowDownPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "arrow-left-right":
      return <path d={arrowLeftRightPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "arrow-up-down":
      return <path d={arrowUpDownPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "chevron-right":
      return (
        <path
          d={chevronRightPath(adj)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "chevron-left":
      return (
        <path
          d={chevronLeftPath(adj)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "notched-arrow-right":
      return <path d={notchedArrowPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "star":
      return (
        <polygon
          points={starPoints(5, 46, 18 + (adj[0] ?? 0.4) * 28)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "star-4":
      return (
        <polygon
          points={starPoints(4, 46, 18 + (adj[0] ?? 0.4) * 28)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "star-6":
      return (
        <polygon
          points={starPoints(6, 46, 18 + (adj[0] ?? 0.4) * 28)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "star-8":
      return (
        <polygon
          points={starPoints(8, 46, 16 + (adj[0] ?? 0.4) * 24)}
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
          strokeLinejoin="round"
        />
      );
    case "banner":
      return <path d={bannerPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "wave":
      return <path d={wavePath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "callout-rect": {
      const bubble = calloutBubble(adj, 10);
      return (
        <>
          <rect
            x={bubble.rect.x}
            y={bubble.rect.y}
            width={bubble.rect.w}
            height={bubble.rect.h}
            rx={10}
            fill={fill}
            stroke={stroke}
            strokeWidth={sw}
          />
          <polygon points={bubble.tip} fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    }
    case "callout-rounded": {
      const bubble = calloutBubble(adj, 20);
      return (
        <>
          <rect
            x={bubble.rect.x}
            y={bubble.rect.y}
            width={bubble.rect.w}
            height={bubble.rect.h}
            rx={bubble.rect.rx}
            fill={fill}
            stroke={stroke}
            strokeWidth={sw}
          />
          <polygon points={bubble.tip} fill={fill} stroke={stroke} strokeWidth={sw} />
        </>
      );
    }
    case "flowchart-document":
      return <path d={documentPath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "flowchart-terminator":
      return <rect x="8" y="28" width="84" height="44" rx="22" fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "snip-rect":
      return (
        <polygon points={polygonPoints(snipRectPoints(adj))} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    case "round-same-side-rect":
      return <path d={roundSameSidePath(adj)} fill={fill} stroke={stroke} strokeWidth={sw} />;
    case "equation-plus":
      return (
        <path
          d="M42 18 H58 V42 H82 V58 H58 V82 H42 V58 H18 V42 H42 Z"
          fill={fill}
          stroke={stroke}
          strokeWidth={sw}
        />
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
    default: {
      const fallback = kind === "rectangle" ? 0 : kind === "flowchart-process" ? 4 : 14;
      const rx =
        borderRadiusPx != null && borderRadiusPx > 0
          ? Math.min(38, borderRadiusPx)
          : cornerRx(adj, fallback);
      return (
        <rect x="8" y="12" width="84" height="76" rx={rx} fill={fill} stroke={stroke} strokeWidth={sw} />
      );
    }
  }
}

export function ComunicadoShapePreview({
  kind,
  className = "tdp-comunicado__shape-preview",
}: {
  kind: ComunicadoShapeKind;
  className?: string;
}) {
  const adjustments = resolveShapeAdjustments(kind, null);
  return (
    <svg viewBox="0 0 100 100" className={className} aria-hidden="true">
      {renderSvgShape(kind, PREVIEW_COLORS, adjustments)}
    </svg>
  );
}

export function ComunicadoShapeGraphic({
  kind,
  fill,
  stroke,
  strokeWidth,
  borderRadius,
  adjustments,
  style,
  geometry,
  markerRadius = COMUNICADO_MARKER_RADIUS_DEFAULT,
}: {
  kind: ComunicadoShapeKind;
  fill: string;
  stroke: string;
  strokeWidth: number;
  borderRadius?: number;
  adjustments?: number[];
  style?: ComunicadoBlockStyle | null;
  geometry?: ComunicadoShapeGeometry;
  markerRadius?: number;
}) {
  const resolvedAdj =
    adjustments ?? resolveShapeAdjustments(kind, style ?? { borderRadius, adjustments });

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
        {renderSvgShape(kind, { fill, stroke, strokeWidth }, resolvedAdj)}
      </svg>
    );
  }

  if (kind === "point") {
    return renderPointMarker(fill, stroke, strokeWidth, markerRadius);
  }

  const cssKinds: ComunicadoShapeKind[] = ["rectangle", "rounded-rect", "ellipse", "flowchart-process"];
  if (cssKinds.includes(kind)) {
    const cornerAdj = resolvedAdj[0] ?? (kind === "rectangle" ? 0 : kind === "flowchart-process" ? 0.05 : 0.16);
    const shapeStyle: CSSProperties = {
      width: "100%",
      height: "100%",
      backgroundColor: fill,
      border: `${strokeWidth}px solid ${stroke}`,
      borderRadius:
        kind === "ellipse"
          ? "50%"
          : borderRadius != null && borderRadius > 0
            ? borderRadius
            : `${cornerAdj * 50}%`,
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
      {renderSvgShape(kind, { fill, stroke, strokeWidth }, resolvedAdj, borderRadius)}
    </svg>
  );
}
