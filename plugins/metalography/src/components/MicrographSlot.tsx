import { useEffect, useState } from "react";
import { ActionButton, FieldLabel, NativeRangeControl } from "@delpi/plugin-ui/index";

import { sourceRect } from "../domain/imageCrop";

const VIEWPORT = { width: 480, height: 320 };
const MAX_BYTES = 8 * 1024 * 1024;

type MicrographSlotProps = {
  slot: "original" | "measured";
  title: string;
  present: boolean;
  remoteUrl: string | null;
  readOnly: boolean;
  disabled: boolean;
  onCommit: (file: File) => void;
  onRemove: () => void;
};

export function MicrographSlot({
  slot,
  title,
  present,
  remoteUrl,
  readOnly,
  disabled,
  onCommit,
  onRemove,
}: MicrographSlotProps) {
  const [source, setSource] = useState<HTMLImageElement | null>(null);
  const [zoom, setZoom] = useState(1);
  const [offsetX, setOffsetX] = useState(0);
  const [offsetY, setOffsetY] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (source?.src.startsWith("blob:")) URL.revokeObjectURL(source.src);
    };
  }, [source]);

  async function onPick(file: File | undefined) {
    setError(null);
    if (!file) return;
    if (!["image/jpeg", "image/png"].includes(file.type)) {
      setError("Use apenas JPEG ou PNG.");
      return;
    }
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      setSource(image);
      setZoom(1);
      setOffsetX(0);
      setOffsetY(0);
    };
    image.onerror = () => setError("Não foi possível ler a imagem.");
    image.src = url;
  }

  async function applyCrop() {
    if (!source) return;
    const rect = sourceRect({
      imageWidth: source.naturalWidth,
      imageHeight: source.naturalHeight,
      viewportWidth: VIEWPORT.width,
      viewportHeight: VIEWPORT.height,
      zoom,
      offsetX,
      offsetY,
    });
    const canvas = document.createElement("canvas");
    canvas.width = VIEWPORT.width;
    canvas.height = VIEWPORT.height;
    const context = canvas.getContext("2d");
    if (!context) return;
    context.drawImage(source, rect.x, rect.y, rect.width, rect.height, 0, 0, VIEWPORT.width, VIEWPORT.height);
    const type = source.src.startsWith("data:image/png") || source.src.includes(".png") ? "image/png" : "image/jpeg";
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob(resolve, type, 0.92));
    if (!blob) {
      setError("Não foi possível preparar a imagem.");
      return;
    }
    if (blob.size > MAX_BYTES) {
      setError("A imagem recortada passa de 8 MB. Aproxime menos ou use um arquivo menor.");
      return;
    }
    const extension = type === "image/png" ? "png" : "jpg";
    onCommit(new File([blob], `${slot}.${extension}`, { type }));
    setSource(null);
  }

  return (
    <section className="mg-micrograph" aria-labelledby={`mg-slot-${slot}`}>
      <h3 id={`mg-slot-${slot}`}>{title}</h3>
      {remoteUrl ? <img src={remoteUrl} alt={title} /> : <p>Nenhuma micrografia gravada.</p>}
      {source ? <img src={source.src} alt="Pré-visualização antes de salvar" /> : null}
      {error ? <p role="alert">{error}</p> : null}
      {readOnly ? null : (
        <div className="mg-micrograph__tools">
          <FieldLabel htmlFor={`mg-file-${slot}`} label="Enviar imagem" />
          <input
            id={`mg-file-${slot}`}
            type="file"
            accept="image/jpeg,image/png"
            disabled={disabled}
            onChange={(event) => void onPick(event.target.files?.[0])}
          />
          {source ? (
            <>
              <label htmlFor={`mg-zoom-${slot}`}>
                Zoom
                <NativeRangeControl
                  id={`mg-zoom-${slot}`}
                  min={1}
                  max={4}
                  step={0.1}
                  value={zoom}
                  onChange={setZoom}
                  aria-label="Zoom da micrografia"
                />
              </label>
              <label htmlFor={`mg-x-${slot}`}>
                Horizontal
                <NativeRangeControl
                  id={`mg-x-${slot}`}
                  min={-1}
                  max={1}
                  step={0.05}
                  value={offsetX}
                  onChange={setOffsetX}
                  aria-label="Deslocamento horizontal"
                />
              </label>
              <label htmlFor={`mg-y-${slot}`}>
                Vertical
                <NativeRangeControl
                  id={`mg-y-${slot}`}
                  min={-1}
                  max={1}
                  step={0.05}
                  value={offsetY}
                  onChange={setOffsetY}
                  aria-label="Deslocamento vertical"
                />
              </label>
              <ActionButton type="button" variant="primary" disabled={disabled} onClick={() => void applyCrop()}>
                Usar recorte
              </ActionButton>
            </>
          ) : null}
          {present ? (
            <ActionButton type="button" variant="ghost" disabled={disabled} onClick={onRemove}>
              Remover
            </ActionButton>
          ) : null}
        </div>
      )}
    </section>
  );
}
