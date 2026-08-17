/** Converte PNG/JPEG de assinatura em blob PNG no tamanho do pad. */

const ALLOWED_EXTENSION = /\.(png|jpe?g)$/i;

export function isSignatureImageFile(file: File): boolean {
  const mime = (file.type || "").trim().toLowerCase();
  if (mime === "image/png" || mime === "image/jpeg" || mime === "image/jpg") {
    return true;
  }
  // Windows/Android às vezes enviam type vazio — confiar na extensão.
  if (!mime || mime === "application/octet-stream") {
    return ALLOWED_EXTENSION.test(file.name || "");
  }
  return false;
}

async function bitmapFromImageElement(file: File): Promise<ImageBitmap | HTMLImageElement> {
  const url = URL.createObjectURL(file);
  try {
    const image = await new Promise<HTMLImageElement>((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error("Falha ao decodificar a imagem."));
      img.src = url;
    });
    if (typeof createImageBitmap === "function") {
      try {
        return await createImageBitmap(image);
      } catch {
        return image;
      }
    }
    return image;
  } finally {
    URL.revokeObjectURL(url);
  }
}

async function loadBitmap(file: File): Promise<ImageBitmap | HTMLImageElement> {
  if (typeof createImageBitmap === "function") {
    try {
      return await createImageBitmap(file);
    } catch {
      /* fallback abaixo */
    }
  }
  return bitmapFromImageElement(file);
}

function sourceSize(source: ImageBitmap | HTMLImageElement): { width: number; height: number } {
  return {
    width: Math.max(1, source.width || 0),
    height: Math.max(1, source.height || 0),
  };
}

/**
 * Redimensiona a imagem ao canvas do pad e devolve PNG.
 * Retorna null se o arquivo não for PNG/JPEG aceito.
 */
export async function blobFromSignatureImageFile(
  file: File,
  width = 640,
  height = 220,
): Promise<Blob | null> {
  if (!isSignatureImageFile(file)) return null;

  const bitmap = await loadBitmap(file);
  const canvas = document.createElement("canvas");
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    if ("close" in bitmap && typeof bitmap.close === "function") bitmap.close();
    return null;
  }
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  const { width: srcW, height: srcH } = sourceSize(bitmap);
  const scale = Math.min(width / srcW, height / srcH);
  const drawW = srcW * scale;
  const drawH = srcH * scale;
  const dx = (width - drawW) / 2;
  const dy = (height - drawH) / 2;
  ctx.drawImage(bitmap, dx, dy, drawW, drawH);
  if ("close" in bitmap && typeof bitmap.close === "function") bitmap.close();

  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/png");
  });
}
