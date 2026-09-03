import { printDelpiDocumentSpec } from "@delpi/plugin-ui/index";

import type { KaizenRecord } from "../types/kaizen";
import { buildKaizenDelpiDocumentSpec } from "./kaizenPdfSpec";

export { buildKaizenDelpiDocumentSpec } from "./kaizenPdfSpec";

export function exportKaizenPdf(record: KaizenRecord): boolean {
  return printDelpiDocumentSpec(buildKaizenDelpiDocumentSpec(record));
}
