import { fetchKaizenEvidenceObjectUrl, fetchKaizenEvidences } from "../api/kaizenApi";
import type { KaizenEvidence, KaizenEvidenceStage } from "../types/kaizen";

/** A ficha A4 prioriza uma foto Antes e uma Depois, sem duplicar revisões. */
export const KAIZEN_PDF_MAX_PHOTOS = 2;

export function selectKaizenPdfPhotos(
  evidences: KaizenEvidence[],
  revisionId: string | null,
): KaizenEvidence[] {
  const eligible = evidences.filter(
    (item) =>
      (item.revision_id ?? null) === revisionId &&
      item.type !== "link" &&
      (item.mime_type ?? "").startsWith("image/"),
  );
  const prioritized: KaizenEvidence[] = [];
  for (const stage of ["antes", "depois", "geral"] as const) {
    const image = eligible.find((item) => item.stage === stage);
    if (image) prioritized.push(image);
  }
  for (const image of eligible) {
    if (!prioritized.some((item) => item.id === image.id)) prioritized.push(image);
  }
  return prioritized.slice(0, KAIZEN_PDF_MAX_PHOTOS);
}

function photoLabel(stage: KaizenEvidenceStage): string {
  return stage === "antes" ? "ANTES" : stage === "depois" ? "DEPOIS" : "EVIDÊNCIA";
}

function loadImage(url: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("Não foi possível abrir uma das fotos do Kaizen."));
    img.src = url;
  });
}

function buildContactSheet(
  photos: Array<{ evidence: KaizenEvidence; image: HTMLImageElement }>,
): string {
  const canvas = document.createElement("canvas");
  canvas.width = 960;
  canvas.height = 186;
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("O navegador não conseguiu preparar as fotos para o PDF.");

  const gap = 14;
  const tileWidth = (canvas.width - gap * (photos.length - 1)) / photos.length;
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  photos.forEach(({ evidence, image }, index) => {
    const x = index * (tileWidth + gap);
    ctx.fillStyle = "#f8fafc";
    ctx.fillRect(x, 0, tileWidth, canvas.height);
    ctx.strokeStyle = "#cbd5e1";
    ctx.strokeRect(x + 0.5, 0.5, tileWidth - 1, canvas.height - 1);

    ctx.font = "bold 16px Arial, sans-serif";
    ctx.fillStyle = "#023667";
    ctx.fillText(photoLabel(evidence.stage), x + 12, 23);

    // Ajusta ao espaço sem cortar nem deformar a fotografia.
    const imageX = x + 8;
    const imageY = 31;
    const imageWidth = tileWidth - 16;
    const imageHeight = 147;
    const ratio = Math.min(imageWidth / image.naturalWidth, imageHeight / image.naturalHeight);
    const width = image.naturalWidth * ratio;
    const height = image.naturalHeight * ratio;
    ctx.drawImage(
      image,
      imageX + (imageWidth - width) / 2,
      imageY + (imageHeight - height) / 2,
      width,
      height,
    );
  });

  return canvas.toDataURL("image/jpeg", 0.85);
}

/**
 * Busca somente fotos da revisão exibida, inclusive com autenticação.
 * Falhas não são ocultadas: o usuário deve saber quando faltaram fotos.
 */
export async function loadKaizenPdfPhotoSheet(
  kaizenId: string,
  revisionId: string | null,
): Promise<{ dataUrl: string; photoCount: number } | null> {
  const photos = selectKaizenPdfPhotos(await fetchKaizenEvidences(kaizenId), revisionId);
  if (!photos.length) return null;

  const urls: string[] = [];
  try {
    const loaded: Array<{ evidence: KaizenEvidence; image: HTMLImageElement }> = [];
    for (const evidence of photos) {
      const url = await fetchKaizenEvidenceObjectUrl(kaizenId, evidence.id);
      urls.push(url);
      loaded.push({ evidence, image: await loadImage(url) });
    }
    return { dataUrl: buildContactSheet(loaded), photoCount: loaded.length };
  } finally {
    urls.forEach((url) => URL.revokeObjectURL(url));
  }
}
