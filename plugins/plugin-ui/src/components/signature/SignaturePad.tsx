import { useEffect, useRef, useState } from "react";

export type SignaturePadProps = {
  width?: number;
  height?: number;
  disabled?: boolean;
  onChange?: (blob: Blob | null) => void;
  className?: string;
  labels?: {
    hint?: string;
    clear?: string;
  };
};

export function SignaturePad({
  width = 640,
  height = 220,
  disabled = false,
  onChange,
  className,
  labels,
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);
  const [hasDrawing, setHasDrawing] = useState(false);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    // O branco é apenas visual (CSS). O PNG deve manter transparência para
    // funcionar sobre marca-d'água e fundos de documentos.
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, [width, height]);

  function getContext(): CanvasRenderingContext2D | null {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext("2d");
    if (!ctx) return null;
    ctx.lineWidth = 2.4;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#0f172a";
    return ctx;
  }

  function pointFromEvent(event: React.PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    return {
      x: ((event.clientX - rect.left) / rect.width) * canvas.width,
      y: ((event.clientY - rect.top) / rect.height) * canvas.height,
    };
  }

  function emitPng() {
    const canvas = canvasRef.current;
    if (!canvas || !onChange) return;
    canvas.toBlob((blob) => onChange(blob), "image/png");
  }

  function handlePointerDown(event: React.PointerEvent<HTMLCanvasElement>) {
    if (disabled) return;
    event.preventDefault();
    canvasRef.current?.setPointerCapture(event.pointerId);
    drawing.current = true;
    lastPoint.current = pointFromEvent(event);
  }

  function handlePointerMove(event: React.PointerEvent<HTMLCanvasElement>) {
    if (!drawing.current || disabled) return;
    const ctx = getContext();
    const next = pointFromEvent(event);
    const prev = lastPoint.current;
    if (!ctx || !prev) return;
    ctx.beginPath();
    ctx.moveTo(prev.x, prev.y);
    ctx.lineTo(next.x, next.y);
    ctx.stroke();
    lastPoint.current = next;
    setHasDrawing(true);
  }

  function handlePointerUp() {
    if (!drawing.current) return;
    drawing.current = false;
    lastPoint.current = null;
    if (hasDrawing) emitPng();
  }

  function clear() {
    const canvas = canvasRef.current;
    const ctx = getContext();
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawing(false);
    onChange?.(null);
  }

  return (
    <div className={["delpi-ui-signature-pad", className].filter(Boolean).join(" ")}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="delpi-ui-signature-pad__canvas"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      />
      <p className="delpi-ui-signature-pad__hint">
        {labels?.hint || "Assine dentro da área acima"}
      </p>
      <button
        type="button"
        className="delpi-ui-signature-pad__clear"
        onClick={clear}
        disabled={disabled || !hasDrawing}
      >
        {labels?.clear || "Limpar"}
      </button>
    </div>
  );
}
