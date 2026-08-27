/** Remove fundo branco de PNGs de assinatura para exibição sobre marca d'água. */

export type NormalizeSignatureDisplayOptions = {
  whiteThreshold?: number;
};

const DEFAULT_WHITE_THRESHOLD = 245;

/**
 * Espelha `transparent_signature_png` do PDF CIPA: pixels claros viram alpha 0.
 * Idempotente para PNGs já transparentes.
 */
export async function normalizeSignatureDisplayPngBlob(
  source: Blob,
  options: NormalizeSignatureDisplayOptions = {},
): Promise<Blob> {
  const whiteThreshold = options.whiteThreshold ?? DEFAULT_WHITE_THRESHOLD;

  try {
    const bitmap = await createImageBitmap(source);
    const canvas = document.createElement("canvas");
    canvas.width = bitmap.width;
    canvas.height = bitmap.height;
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      bitmap.close();
      return source;
    }
    ctx.drawImage(bitmap, 0, 0);
    bitmap.close();

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const { data } = imageData;
    for (let i = 0; i < data.length; i += 4) {
      const red = data[i];
      const green = data[i + 1];
      const blue = data[i + 2];
      if (red >= whiteThreshold && green >= whiteThreshold && blue >= whiteThreshold) {
        data[i + 3] = 0;
      }
    }
    ctx.putImageData(imageData, 0, 0);

    return await new Promise<Blob>((resolve) => {
      canvas.toBlob((blob) => resolve(blob ?? source), "image/png");
    });
  } catch {
    return source;
  }
}
