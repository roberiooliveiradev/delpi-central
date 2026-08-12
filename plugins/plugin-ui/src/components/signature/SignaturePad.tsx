import { Eraser, Maximize2, Minimize2, Redo2, Undo2 } from "lucide-react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
} from "react";

import { HelpTooltip } from "../help/HelpTooltip";
import { DELPI_UI_OVERLAY_Z_INDEX } from "../../overlayLayers";
import { centerSignaturePngBlob } from "./centerSignaturePngBlob";

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

/** Escala traços entre tamanhos lógicos do pad (exportado para testes). */
export function scaleSignatureStrokes(strokes: Stroke[], from: PadSize, to: PadSize): Stroke[] {
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

  const commitStrokes = useCallback((next: Stroke[]) => {
    strokesRef.current = next;
    setStrokes(next);
  }, []);

  const commitRedo = useCallback((next: Stroke[]) => {
    redoRef.current = next;
    setRedoStack(next);
  }, []);

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
      // Bitmap só via JS — atributos React width/height no <canvas> apagam o buffer
      // após setSize (tela cheia) sem redesenhar.
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
      nextStrokes = scaleSignatureStrokes(nextStrokes, prev, nextSize);
      commitStrokes(nextStrokes);
      if (redoRef.current.length) {
        commitRedo(scaleSignatureStrokes(redoRef.current, prev, nextSize));
      }
      sizeRef.current = nextSize;
    }
    if (paper) {
      paper.style.minHeight = `${nextSize.height}px`;
    }
    applyCanvasBitmap(nextSize, nextStrokes);
  }, [applyCanvasBitmap, commitRedo, commitStrokes, fullscreen, height, width]);

  useLayoutEffect(() => {
    measureAndSync();
    const paper = paperRef.current;
    if (!paper || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => measureAndSync());
    observer.observe(paper);
    return () => observer.disconnect();
  }, [measureAndSync]);

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
    canvas.toBlob((blob) => {
      if (!blob) {
        onChange(null);
        return;
      }
      void centerSignaturePngBlob(blob).then((centered) => onChange(centered));
    }, "image/png");
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
    commitStrokes(next);
    commitRedo([]);
    emitPng(true);
  }

  function undo() {
    if (disabled || strokesRef.current.length === 0) return;
    const current = strokesRef.current;
    const next = current.slice(0, -1);
    const removed = current[current.length - 1];
    commitStrokes(next);
    commitRedo([...redoRef.current, removed]);
    redraw(next, sizeRef.current);
    emitPng(next.length > 0);
  }

  function redo() {
    if (disabled || redoRef.current.length === 0) return;
    const stack = redoRef.current;
    const restored = stack[stack.length - 1];
    const nextRedo = stack.slice(0, -1);
    const next = [...strokesRef.current, restored];
    commitStrokes(next);
    commitRedo(nextRedo);
    redraw(next, sizeRef.current);
    emitPng(true);
  }

  function clear() {
    if (disabled) return;
    commitStrokes([]);
    commitRedo([]);
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
