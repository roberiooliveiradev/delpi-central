/** PRC-REF-023-F02/F03 — a implementação canônica migrou para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada entre Portal Engenharia e Minhas Solicitações. Shim
 * de compatibilidade. */

import {
  addSupportFiles,
  newSupportFileId,
  removeSupportFile,
  type PrcSupportFile,
  type PrcSupportPickResult,
} from "@delpi/plugin-ui/index";
export {
  addSupportFiles,
  newSupportFileId,
  removeSupportFile,
  type PrcSupportFile,
  type PrcSupportPickResult,
};
