import { useEffect, useRef, type CSSProperties, type PointerEvent } from "react";

import {
  clampCrop,
  cropPointerMode,
  fitCanvas,
  nextCrop,
  sourceRect,
  type CropRect,
} from "../domain/referenceCrop";

type CropDialogProps = {
  open: boolean;
  title: string;
  image: HTMLImageElement | null;
  box?: CSSProperties;
  onCancel: () => void;
  onApply: (file: File, previewUrl: string) => void;
};

export function CropDialog({ open, title, image, box, onCancel, onApply }: CropDialogProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const cropRef = useRef<CropRect | null>(null);
  const dragRef = useRef<{ mode: string; startX: number; startY: number; start: CropRect } | null>(null);

  function draw() {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || !image) return;
    const size = fitCanvas(image.naturalWidth || image.width, image.naturalHeight || image.height);
    canvas.width = size.cw;
    canvas.height = size.ch;
    canvas.style.aspectRatio = `${size.cw} / ${size.ch}`;
    const crop = clampCrop(cropRef.current ?? { x: 0, y: 0, w: size.cw, h: size.ch }, size.cw, size.ch);
    cropRef.current = crop;
    const right = crop.x + crop.w;
    const bottom = crop.y + crop.h;
    context.clearRect(0, 0, size.cw, size.ch);
    context.drawImage(image, 0, 0, size.cw, size.ch);
    context.fillStyle = "rgba(6,29,45,.56)";
    context.fillRect(0, 0, size.cw, crop.y);
    context.fillRect(0, bottom, size.cw, size.ch - bottom);
    context.fillRect(0, crop.y, crop.x, crop.h);
    context.fillRect(right, crop.y, size.cw - right, crop.h);
    context.strokeStyle = "#ffffff";
    context.globalAlpha = 0.62;
    context.lineWidth = Math.max(1.5, Math.min(size.cw, size.ch) * 0.0014);
    context.setLineDash([Math.max(5, size.cw * 0.004), Math.max(4, size.cw * 0.003)]);
    context.beginPath();
    context.moveTo(crop.x + crop.w / 3, crop.y);
    context.lineTo(crop.x + crop.w / 3, bottom);
    context.moveTo(crop.x + (2 * crop.w) / 3, crop.y);
    context.lineTo(crop.x + (2 * crop.w) / 3, bottom);
    context.moveTo(crop.x, crop.y + crop.h / 3);
    context.lineTo(right, crop.y + crop.h / 3);
    context.moveTo(crop.x, bottom - crop.h / 3);
    context.lineTo(right, bottom - crop.h / 3);
    context.stroke();
    context.setLineDash([]);
    context.globalAlpha = 1;
    context.strokeStyle = "#00a4ce";
    context.lineWidth = Math.max(2.5, Math.min(size.cw, size.ch) * 0.002);
    context.strokeRect(crop.x, crop.y, crop.w, crop.h);
    const radius = Math.max(7, Math.min(size.cw, size.ch) * 0.012);
    const points: Array<[number, number]> = [
      [crop.x, crop.y],
      [crop.x + crop.w / 2, crop.y],
      [right, crop.y],
      [crop.x, bottom - crop.h / 2],
      [right, bottom - crop.h / 2],
      [crop.x, bottom],
      [crop.x + crop.w / 2, bottom],
      [right, bottom],
    ];
    for (const point of points) {
      context.beginPath();
      context.arc(point[0], point[1], radius, 0, Math.PI * 2);
      context.fillStyle = "#ffffff";
      context.fill();
      context.strokeStyle = "#00a4ce";
      context.lineWidth = Math.max(2, radius * 0.22);
      context.stroke();
    }
  }

  useEffect(() => {
    if (!open) return;
    cropRef.current = null;
    const frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [open, image]);

  function pointer(event: PointerEvent<HTMLCanvasElement>) {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const x = Math.max(0, Math.min(canvas.width, ((event.clientX - rect.left) * canvas.width) / Math.max(1, rect.width)));
    const y = Math.max(0, Math.min(canvas.height, ((event.clientY - rect.top) * canvas.height) / Math.max(1, rect.height)));
    return { x, y };
  }

  function onPointerDown(event: PointerEvent<HTMLCanvasElement>) {
    if (!image || !canvasRef.current) return;
    const size = fitCanvas(image.naturalWidth || image.width, image.naturalHeight || image.height);
    const crop = clampCrop(cropRef.current ?? { x: 0, y: 0, w: size.cw, h: size.ch }, size.cw, size.ch);
    const point = pointer(event);
    const mode = cropPointerMode(point, crop, size);
    if (mode === "new") cropRef.current = { x: point.x, y: point.y, w: 1, h: 1 };
    dragRef.current = { mode, startX: point.x, startY: point.y, start: { ...crop } };
    event.currentTarget.setPointerCapture(event.pointerId);
    draw();
  }

  function onPointerMove(event: PointerEvent<HTMLCanvasElement>) {
    const drag = dragRef.current;
    if (!drag || !image) return;
    const size = fitCanvas(image.naturalWidth || image.width, image.naturalHeight || image.height);
    cropRef.current = nextCrop(drag.mode, drag.start, { x: drag.startX, y: drag.startY }, pointer(event), size);
    draw();
  }

  function onPointerUp() {
    const drag = dragRef.current;
    dragRef.current = null;
    if (!drag || !image || drag.mode !== "new" || !cropRef.current) {
      draw();
      return;
    }
    const size = fitCanvas(image.naturalWidth || image.width, image.naturalHeight || image.height);
    const minSize = Math.max(12, Math.min(size.cw, size.ch) * 0.02);
    if (cropRef.current.w < minSize || cropRef.current.h < minSize) {
      cropRef.current = { x: 0, y: 0, w: size.cw, h: size.ch };
    }
    draw();
  }

  function apply() {
    const canvas = canvasRef.current;
    if (!canvas || !image || !cropRef.current) return;
    const size = fitCanvas(image.naturalWidth || image.width, image.naturalHeight || image.height);
    const crop = clampCrop(cropRef.current, size.cw, size.ch);
    const source = sourceRect(crop, size);
    const maxOutput = 6000;
    const scale = Math.min(1, maxOutput / Math.max(source.w, source.h));
    const output = document.createElement("canvas");
    output.width = Math.max(1, Math.round(source.w * scale));
    output.height = Math.max(1, Math.round(source.h * scale));
    const context = output.getContext("2d");
    if (!context) return;
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, output.width, output.height);
    context.drawImage(image, source.x, source.y, source.w, source.h, 0, 0, output.width, output.height);
    output.toBlob((blob) => {
      if (!blob) return;
      const file = new File([blob], "micrografia.jpg", { type: "image/jpeg" });
      onApply(file, output.toDataURL("image/jpeg", 0.96));
    }, "image/jpeg", 0.96);
  }

  return (
    <div className={open ? "crop-modal open" : "crop-modal"} aria-hidden={open ? "false" : "true"} style={open ? box : undefined} onClick={(event) => { if (event.target === event.currentTarget) onCancel(); }} onKeyDown={(event) => { if (event.key === "Escape") { event.stopPropagation(); onCancel(); } }}>
      <div className="crop-panel" role="dialog" aria-modal="true" aria-labelledby="crop-title">
        <div className="crop-head">
          <div>
            <h3 id="crop-title">{title}</h3>
            <p>Arraste as alças para recortar por qualquer lado. Com a imagem inteira selecionada, arraste sobre ela para desenhar um recorte. No relatório, a imagem mantém sua proporção e pode deixar áreas brancas nas laterais.</p>
          </div>
          <button type="button" className="crop-close" onClick={onCancel} aria-label="Fechar">×</button>
        </div>
        <div className="crop-stage"><canvas ref={canvasRef} onPointerDown={onPointerDown} onPointerMove={onPointerMove} onPointerUp={onPointerUp} onPointerCancel={() => { dragRef.current = null; }} /></div>
        <div className="crop-tools">
          <span>Arraste dentro da seleção para movê-la; arraste uma alça para ajustar a borda.</span>
          <button type="button" className="secondary" onClick={() => { cropRef.current = null; draw(); }}>Mostrar imagem inteira</button>
        </div>
        <div className="crop-actions">
          <button type="button" className="secondary" onClick={onCancel}>Cancelar</button>
          <button type="button" className="primary" onClick={apply}>Aplicar recorte</button>
        </div>
      </div>
    </div>
  );
}
