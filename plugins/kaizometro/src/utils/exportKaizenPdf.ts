import { printDelpiDocumentSpec } from "@delpi/plugin-ui/index";

import type { KaizenRecord } from "../types/kaizen";
import { buildKaizenDelpiDocumentSpec } from "./kaizenPdfSpec";
import { loadKaizenPdfPhotoSheet } from "./kaizenPdfPhotos";

export { buildKaizenDelpiDocumentSpec } from "./kaizenPdfSpec";

/** Exporta a revisão selecionada, incluindo as fotos disponíveis dessa revisão. */
export async function exportKaizenPdf(
  record: KaizenRecord,
  revisionId: string | null = null,
): Promise<boolean> {
  const photos = await loadKaizenPdfPhotoSheet(record.id, revisionId);
  return printDelpiDocumentSpec(buildKaizenDelpiDocumentSpec(record, photos));
}
