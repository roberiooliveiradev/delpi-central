/** PRC-REF-023-F03 — a implementação canônica destes adaptadores de
 * contrato migrou para `@delpi/plugin-ui`
 * (`utils/prcProductRegistration`), fonte única compartilhada entre
 * Portal Engenharia e Minhas Solicitações. Este módulo permanece como
 * shim de compatibilidade dos imports existentes. */

import {
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
  linkDiffConflicts,
  linkKeyOf,
  type LinkDiffResult,
  type PrcLinkKey,
  type PrcLinkOp,
  type PrcLinkRow,
  type PrcOfficialLink,
  type PrcScalarChange,
} from "@delpi/plugin-ui/index";
export {
  computeLinkDiff,
  computeLinkDiffDetailed,
  computeScalarDiff,
  linkDiffConflicts,
  linkKeyOf,
  type LinkDiffResult,
  type PrcLinkKey,
  type PrcLinkOp,
  type PrcLinkRow,
  type PrcOfficialLink,
  type PrcScalarChange,
};
