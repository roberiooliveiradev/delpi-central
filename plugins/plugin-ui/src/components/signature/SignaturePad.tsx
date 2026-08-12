import { Eraser, Redo2, Undo2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { HelpTooltip } from "../help/HelpTooltip";

export type SignatureStrokeWidth = "thin" | "medium" | "thick";

export type SignaturePadProps = {
  width?: number;
  height?: number;
  disabled?: boolean;
  strokeWidth?: SignatureStrokeWidth;
  onChange?: (blob: Blob | null) => void;
  onStrokeWidthChange?: (value: SignatureStrokeWidth) => void;
  className?: string;
  labels?: {
    hint?: string;
    clear?: string;
    undo?: string;
    redo?: string;
    strokeThin?: string;
    strokeMedium?: string;
    strokeThick?: string;
    strokeHelp?: string;
    toolsHelp?: string;
  };
};

type Point = { x: number; y: number; lineWidth: number };
type Stroke = Point[];

const STROKE_BASE: Record<SignatureStrokeWidth, number> = {
  thin: 1.6,
  medium: 2.4,
  thick: 3.6,
};

function velocityWidth(base: number, prev: Point | null, next: { x: number; y: number }): number {
  if (!prev) return base;
  const dx = next.x - prev.x;
  const dy = next.y - prev.y;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const factor = Math.max(0.55, Math.min(1.15, 1.1 - dist / 28));
  return base * factor;
}

export function SignaturePad({
  width = 640,
  height = 220,
  disabled = false,
  strokeWidth: strokeWidthProp,
  onChange,
  onStrokeWidthChange,
  className,
  labels,
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const currentStroke = useRef<Stroke>([]);
  const strokesRef = useRef<Stroke[]>([]);
  const redoRef = useRef<Stroke[]>([]);
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [redoStack, setRedoStack] = useState<Stroke[]>([]);
  const [internalStrokeWidth, setInternalStrokeWidth] = useState<SignatureStrokeWidth>("medium");
  const strokeWidth = strokeWidthProp ?? internalStrokeWidth;

  const setStrokeWidth = useCallback(
    (value: SignatureStrokeWidth) => {
      if (strokeWidthProp === undefined) setInternalStrokeWidth(value);
      onStrokeWidthChange?.(value);
    },
    [onStrokeWidthChange, strokeWidthProp],
  );

  const syncCanvasSize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = Math.max(1, window.devicePixelRatio || 1);
    const cssWidth = width;
    const cssHeight = height;
    canvas.width = Math.round(cssWidth * dpr);
    canvas.height = Math.round(cssHeight * dpr);
    canvas.style.width = `${cssWidth}px`;
    canvas.style.height = `${cssHeight}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#0f172a";
  }, [width, height]);

  const redraw = useCallback(
    (nextStrokes: Stroke[]) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.clearRect(0, 0, width, height);
      for (const stroke of nextStrokes) {
        if (stroke.length === 0) continue;
        for (let i = 1; i < stroke.length; i += 1) {
          const prev = stroke[i - 1];
          const point = stroke[i];
          ctx.beginPath();
          ctx.lineWidth = point.lineWidth;
          ctx.moveTo(prev.x, prev.y);
          ctx.lineTo(point.x, point.y);
          ctx.stroke();
        }
      }
    },
    [height, width],
  );

  useEffect(() => {
    syncCanvasSize();
    redraw(strokesRef.current);
  }, [syncCanvasSize, redraw]);

  useEffect(() => {
    strokesRef.current = strokes;
  }, [strokes]);

  useEffect(() => {
    redoRef.current = redoStack;
  }, [redoStack]);

  function pointFromEvent(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * width,
      y: ((event.clientY - rect.top) / rect.height) * height,
    };
  }

  function emitPng(hasInk: boolean) {
    const canvas = canvasRef.current;
    if (!canvas || !onChange) return;
    if (!hasInk) {
      onChange(null);
      return;
    }
    canvas.toBlob((blob) => onChange(blob), "image/png");
  }

  function handlePointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    if (disabled) return;
    event.preventDefault();
    try {
      canvasRef.current?.setPointerCapture?.(event.pointerId);
    } catch {
      /* jsdom */
    }
    drawing.current = true;
    const base = STROKE_BASE[strokeWidth];
    const pos = pointFromEvent(event);
    currentStroke.current = [{ x: pos.x, y: pos.y, lineWidth: base }];
  }

  function handlePointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current || disabled) return;
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!ctx) return;
    const pos = pointFromEvent(event);
    const stroke = currentStroke.current;
    const prev = stroke[stroke.length - 1] ?? null;
    const base = STROKE_BASE[strokeWidth];
    const lineWidth = velocityWidth(base, prev, pos);
    const next: Point = { x: pos.x, y: pos.y, lineWidth };
    if (prev) {
      ctx.beginPath();
      ctx.lineWidth = lineWidth;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "#0f172a";
      ctx.moveTo(prev.x, prev.y);
      ctx.lineTo(next.x, next.y);
      ctx.stroke();
    }
    stroke.push(next);
  }

  function handlePointerUp() {
    if (!drawing.current) return;
    drawing.current = false;
    const finished = currentStroke.current;
    currentStroke.current = [];
    if (finished.length < 2) return;
    const next = [...strokesRef.current, finished];
    setStrokes(next);
    setRedoStack([]);
    emitPng(true);
  }

  function undo() {
    if (disabled || strokes.length === 0) return;
    const next = strokes.slice(0, -1);
    const removed = strokes[strokes.length - 1];
    setStrokes(next);
    setRedoStack([...redoStack, removed]);
    redraw(next);
    emitPng(next.length > 0);
  }

  function redo() {
    if (disabled || redoStack.length === 0) return;
    const restored = redoStack[redoStack.length - 1];
    const nextRedo = redoStack.slice(0, -1);
    const next = [...strokes, restored];
    setStrokes(next);
    setRedoStack(nextRedo);
    redraw(next);
    emitPng(true);
  }

  function clear() {
    if (disabled) return;
    setStrokes([]);
    setRedoStack([]);
    redraw([]);
    onChange?.(null);
  }

  const hasDrawing = strokes.length > 0;
  const undoLabel = labels?.undo || "Desfazer";
  const redoLabel = labels?.redo || "Refazer";
  const clearLabel = labels?.clear || "Limpar";

  return (
    <div className={["delpi-ui-signature-pad", className].filter(Boolean).join(" ")}>
      <div className="delpi-ui-signature-pad__paper">
        <canvas
          ref={canvasRef}
          className="delpi-ui-signature-pad__canvas"
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          onPointerCancel={handlePointerUp}
        />
      </div>
      <div className="delpi-ui-signature-pad__hint-row">
        <p className="delpi-ui-signature-pad__hint">
          {labels?.hint || "Assine dentro da área acima"}
        </p>
        <HelpTooltip
          content={
            labels?.toolsHelp ||
            "Desenhe com o mouse ou o dedo. Use desfazer/refazer por traço e escolha a espessura antes de assinar."
          }
          ariaLabel="Ajuda da assinatura manuscrita"
          placement="bottom"
        />
      </div>
      <div className="delpi-ui-signature-pad__actions" role="toolbar" aria-label="Ferramentas de assinatura">
        <div className="delpi-ui-signature-pad__action-group">
          <button
            type="button"
            className="delpi-ui-icon-btn delpi-ui-signature-pad__icon-btn"
            aria-label={undoLabel}
            disabled={disabled || strokes.length === 0}
            onClick={undo}
            data-testid="signature-pad-undo"
          >
            <Undo2 size={18} aria-hidden />
            <span className="delpi-ui-signature-pad__btn-label">{undoLabel}</span>
          </button>
          <button
            type="button"
            className="delpi-ui-icon-btn delpi-ui-signature-pad__icon-btn"
            aria-label={redoLabel}
            disabled={disabled || redoStack.length === 0}
            onClick={redo}
            data-testid="signature-pad-redo"
          >
            <Redo2 size={18} aria-hidden />
            <span className="delpi-ui-signature-pad__btn-label">{redoLabel}</span>
          </button>
          <button
            type="button"
            className="delpi-ui-icon-btn delpi-ui-icon-btn--danger delpi-ui-signature-pad__icon-btn delpi-ui-signature-pad__clear"
            aria-label={clearLabel}
            disabled={disabled || !hasDrawing}
            onClick={clear}
            data-testid="signature-pad-clear"
          >
            <Eraser size={18} aria-hidden />
            <span className="delpi-ui-signature-pad__btn-label">{clearLabel}</span>
          </button>
        </div>
        <div className="delpi-ui-signature-pad__stroke" role="group" aria-label="Espessura do traço">
          <span className="delpi-ui-signature-pad__stroke-label">Espessura</span>
          <HelpTooltip
            content={
              labels?.strokeHelp ||
              "Fino, médio ou grosso altera a largura do próximo traço. A espessura também varia levemente com a velocidade."
            }
            ariaLabel="Ajuda da espessura"
            placement="bottom"
          />
          {(
            [
              ["thin", labels?.strokeThin || "Fino", "delpi-ui-signature-pad__stroke-swatch--thin"],
              ["medium", labels?.strokeMedium || "Médio", "delpi-ui-signature-pad__stroke-swatch--medium"],
              ["thick", labels?.strokeThick || "Grosso", "delpi-ui-signature-pad__stroke-swatch--thick"],
            ] as const
          ).map(([value, label, swatchClass]) => (
            <button
              key={value}
              type="button"
              className={[
                "delpi-ui-signature-pad__stroke-btn",
                strokeWidth === value ? "is-active" : "",
              ]
                .filter(Boolean)
                .join(" ")}
              onClick={() => setStrokeWidth(value)}
              disabled={disabled}
              aria-pressed={strokeWidth === value}
              aria-label={label}
              title={label}
              data-testid={`signature-pad-stroke-${value}`}
            >
              <span className={["delpi-ui-signature-pad__stroke-swatch", swatchClass].join(" ")} />
              <span className="delpi-ui-signature-pad__btn-label">{label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
