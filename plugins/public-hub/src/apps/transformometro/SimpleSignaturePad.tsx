import { useEffect, useRef, useState } from "react";

type Props = {
  disabled?: boolean;
  onChange?: (blob: Blob | null) => void;
};

export function SimpleSignaturePad({ disabled = false, onChange }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const lastPoint = useRef<{ x: number; y: number } | null>(null);
  const [hasDrawing, setHasDrawing] = useState(false);
  const width = 640;
  const height = 220;

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }, []);

  function getContext(): CanvasRenderingContext2D | null {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d") ?? null;
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
    <div className="tm-sign__pad">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="tm-sign__canvas"
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
      />
      <p className="tm-sign__pad-hint">Assine dentro da área acima</p>
      <button type="button" className="tm-sign__link-btn" onClick={clear} disabled={disabled || !hasDrawing}>
        Limpar
      </button>
    </div>
  );
}
