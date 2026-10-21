export type SourceRect = { x: number; y: number; width: number; height: number };

export type CropInput = {
  imageWidth: number;
  imageHeight: number;
  viewportWidth: number;
  viewportHeight: number;
  zoom: number;
  offsetX: number;
  offsetY: number;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

/** Recorte visível da imagem original a partir do zoom e do deslocamento do quadro. */
export function sourceRect(input: CropInput): SourceRect {
  const imageWidth = Math.max(1, input.imageWidth);
  const imageHeight = Math.max(1, input.imageHeight);
  const viewportWidth = Math.max(1, input.viewportWidth);
  const viewportHeight = Math.max(1, input.viewportHeight);
  const zoom = clamp(input.zoom, 1, 8);
  const fit = Math.min(viewportWidth / imageWidth, viewportHeight / imageHeight);
  const scale = fit * zoom;
  const width = clamp(viewportWidth / scale, 1, imageWidth);
  const height = clamp(viewportHeight / scale, 1, imageHeight);
  const maxX = imageWidth - width;
  const maxY = imageHeight - height;
  const centerX = maxX / 2;
  const centerY = maxY / 2;
  const x = clamp(centerX + clamp(input.offsetX, -1, 1) * centerX, 0, maxX);
  const y = clamp(centerY + clamp(input.offsetY, -1, 1) * centerY, 0, maxY);
  return { x, y, width, height };
}
