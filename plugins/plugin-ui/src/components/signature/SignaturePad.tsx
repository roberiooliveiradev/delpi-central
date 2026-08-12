import { Eraser, Maximize2, Minimize2, Redo2, Undo2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";

export type SignatureStrokeWidth = "thin" | "medium" | "thick";

export type SignaturePadProps = {
  /** Largura lógica de referência (proporção / fallback). O canvas acompanha o container. */
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
    expand?: string;
    exitFullscreen?: string;
    expandHelp?: string;
  };
};

type Point = { x: number; y: number; lineWidth: number };
type Stroke = Point[];
type PadSize = { width: number; height: number };

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

function scaleStrokes(strokes: Stroke[], from: PadSize, to: PadSize): Stroke[] {
  if (from.width <= 0 || from.height <= 0) return strokes;
  const sx = to.width / from.width;
  const sy = to.height / from.height;
  const sw = (sx + sy) / 2;
  return strokes.map((stroke) =>
    stroke.map((point) => ({
      x: point.x * sx,
      y: point.y * sy,
      lineWidth: point.lineWidth * sw,
    })),
  );
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
  const rootRef = useRef<HTMLDivElement>(null);
  const paperRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const currentStroke = useRef<Stroke>([]);
  const strokesRef = useRef<Stroke[]>([]);
  const redoRef = useRef<Stroke[]>([]);
  const sizeRef = useRef<PadSize>({ width, height });
  const [size, setSize] = useState<PadSize>({ width, height });
  const [strokes, setStrokes] = useState<Stroke[]>([]);
  const [redoStack, setRedoStack] = useState<Stroke[]>([]);
  const [fullscreen, setFullscreen] = useState(false);
  const [internalStrokeWidth, setInternalStrokeWidth] = useState<SignatureStrokeWidth>("medium");
  const strokeWidth = strokeWidthProp ?? internalStrokeWidth;

  const setStrokeWidth = useCallback(
    (value: SignatureStrokeWidth) => {
      if (strokeWidthProp === undefined) setInternalStrokeWidth(value);
      onStrokeWidthChange?.(value);
    },
    [onStrokeWidthChange, strokeWidthProp],
  );

  const redraw = useCallback((nextStrokes: Stroke[], padSize: PadSize) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, padSize.width, padSize.height);
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
  }, []);

  const applyCanvasBitmap = useCallback(
    (padSize: PadSize, nextStrokes: Stroke[]) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const dpr = Math.max(1, window.devicePixelRatio || 1);
      canvas.width = Math.round(padSize.width * dpr);
      canvas.height = Math.round(padSize.height * dpr);
      canvas.style.width = "100%";
      canvas.style.height = "100%";
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.strokeStyle = "#0f172a";
      redraw(nextStrokes, padSize);
    },
    [redraw],
  );

  const measureAndSync = useCallback(() => {
    const paper = paperRef.current;
    const ratio = height / Math.max(width, 1);
    let nextW = width;
    let nextH = height;
    if (paper) {
      const measured = Math.round(paper.clientWidth);
      if (measured > 0) {
        nextW = measured;
        nextH = fullscreen
          ? Math.max(Math.round(window.innerHeight * 0.52), Math.round(measured * ratio))
          : Math.max(height, Math.round(measured * ratio));
      }
    }
    const nextSize = { width: nextW, height: nextH };
    const prev = sizeRef.current;
    let nextStrokes = strokesRef.current;
    if (prev.width !== nextSize.width || prev.height !== nextSize.height) {
      nextStrokes = scaleStrokes(nextStrokes, prev, nextSize);
      strokesRef.current = nextStrokes;
      setStrokes(nextStrokes);
      if (redoRef.current.length) {
        const nextRedo = scaleStrokes(redoRef.current, prev, nextSize);
        redoRef.current = nextRedo;
        setRedoStack(nextRedo);
      }
      sizeRef.current = nextSize;
      setSize(nextSize);
    }
    if (paper) {
      paper.style.minHeight = `${nextSize.height}px`;
    }
    applyCanvasBitmap(nextSize, nextStrokes);
  }, [applyCanvasBitmap, fullscreen, height, width]);

  useEffect(() => {
    measureAndSync();
    const paper = paperRef.current;
    if (!paper || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => measureAndSync());
    observer.observe(paper);
    return () => observer.disconnect();
  }, [measureAndSync]);

  useEffect(() => {
    strokesRef.current = strokes;
  }, [strokes]);

  useEffect(() => {
    redoRef.current = redoStack;
  }, [redoStack]);

  useEffect(() => {
    if (!fullscreen) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setFullscreen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = previous;
      window.removeEventListener("keydown", onKey);
    };
  }, [fullscreen]);

  useEffect(() => {
    measureAndSync();
  }, [fullscreen, measureAndSync]);

  function pointFromEvent(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const pad = sizeRef.current;
    return {
      x: ((event.clientX - rect.left) / Math.max(rect.width, 1)) * pad.width,
      y: ((event.clientY - rect.top) / Math.max(rect.height, 1)) * pad.height,
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
    redraw(next, sizeRef.current);
    emitPng(next.length > 0);
  }

  function redo() {
    if (disabled || redoStack.length === 0) return;
    const restored = redoStack[redoStack.length - 1];
    const nextRedo = redoStack.slice(0, -1);
    const next = [...strokes, restored];
    setStrokes(next);
    setRedoStack(nextRedo);
    redraw(next, sizeRef.current);
    emitPng(true);
  }

  function clear() {
    if (disabled) return;
    setStrokes([]);
    setRedoStack([]);
    redraw([], sizeRef.current);
    onChange?.(null);
  }

  const hasDrawing = strokes.length > 0;
  const undoLabel = labels?.undo || "Desfazer";
  const redoLabel = labels?.redo || "Refazer";
  const clearLabel = labels?.clear || "Limpar";
  const expandLabel = labels?.expand || "Tela cheia";
  const exitLabel = labels?.exitFullscreen || "Sair da tela cheia";

  return (
    <div
      ref={rootRef}
      className={[
        "delpi-ui-signature-pad",
        fullscreen ? "delpi-ui-signature-pad--fullscreen" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      style={
        fullscreen
          ? ({ ["--delpi-ui-signature-overlay-z" as string]: DELPI_UI_OVERLAY_Z_INDEX.modal } as CSSProperties)
          : undefined
      }
    >
      <div className="delpi-ui-signature-pad__chrome">
        <div className="delpi-ui-signature-pad__chrome-title">
          {fullscreen ? "Assinatura em tela cheia" : null}
        </div>
        <div className="delpi-ui-signature-pad__chrome-actions">
          <HelpTooltip
            content={
              labels?.expandHelp ||
              "Abre a área de assinatura em tela cheia para facilitar o traço no mouse ou no toque. Esc fecha."
            }
            ariaLabel="Ajuda da tela cheia"
            placement="bottom"
          />
          <button
            type="button"
            className="delpi-ui-icon-btn delpi-ui-signature-pad__icon-btn"
            aria-label={fullscreen ? exitLabel : expandLabel}
            aria-pressed={fullscreen}
            onClick={() => setFullscreen((value) => !value)}
            data-testid="signature-pad-fullscreen"
          >
            {fullscreen ? <Minimize2 size={18} aria-hidden /> : <Maximize2 size={18} aria-hidden />}
            <span className="delpi-ui-signature-pad__btn-label">
              {fullscreen ? exitLabel : expandLabel}
            </span>
          </button>
        </div>
      </div>

      <div ref={paperRef} className="delpi-ui-signature-pad__paper">
        <canvas
          ref={canvasRef}
          className="delpi-ui-signature-pad__canvas"
          width={size.width}
          height={size.height}
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
