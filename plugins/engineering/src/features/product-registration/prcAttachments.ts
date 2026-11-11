/** PRC-REF-023-F03 — os helpers canônicos migraram para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada entre Portal Engenharia e Minhas Solicitações. A
 * autoridade de validação (MIME/tamanho/conteúdo) é a Engineering
 * API; aqui apenas pré-validação UX e rótulos. Shim de
 * compatibilidade. */

import {
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_BYTES,
  PRC_ATTACHMENT_MAX_COUNT,
  PRC_ATTACHMENT_MAX_MB,
  PRC_ATTACHMENT_MEDIA_LABELS,
  PRC_ATTACHMENT_STATE_LABELS,
  prcCheckAttachmentFile,
  prcFormatSize,
  type PrcAttachmentLocalCheck,
} from "@delpi/plugin-ui/index";
export {
  PRC_ATTACHMENT_ACCEPT,
  PRC_ATTACHMENT_MAX_BYTES,
  PRC_ATTACHMENT_MAX_COUNT,
  PRC_ATTACHMENT_MAX_MB,
  PRC_ATTACHMENT_MEDIA_LABELS,
  PRC_ATTACHMENT_STATE_LABELS,
  prcCheckAttachmentFile,
  prcFormatSize,
  type PrcAttachmentLocalCheck,
};
