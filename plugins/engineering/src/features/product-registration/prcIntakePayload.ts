/** PRC-REF-023-F03 — os builders de payload migraram para
 * `@delpi/plugin-ui` (`utils/prcProductRegistration`), fonte única
 * compartilhada entre Portal Engenharia e Minhas Solicitações. Este
 * shim preserva as assinaturas históricas injetando a origem
 * `portal-engineering` (o consumidor my-requests informa a própria
 * `source` diretamente no builder compartilhado). */

import {
  buildCreateIntakeBody as sharedCreate,
  buildCreateReasons,
  buildUpdateIntakeBody as sharedUpdate,
  linkChangesWithReasons,
} from "@delpi/plugin-ui/index";

export { linkChangesWithReasons, buildCreateReasons };

export const PRC_PORTAL_SOURCE = "portal-engineering";

export function buildCreateIntakeBody(args: {
  refData: Parameters<typeof sharedCreate>[0]["refData"];
  values: Record<string, string>;
  reasons: Record<string, string>;
  suppliers: Parameters<typeof sharedCreate>[0]["suppliers"];
}): ReturnType<typeof sharedCreate> {
  return sharedCreate({ ...args, source: PRC_PORTAL_SOURCE });
}

export function buildUpdateIntakeBody(args: {
  refData: Parameters<typeof sharedUpdate>[0]["refData"];
  officialCode: string;
  scalarDiff: Parameters<typeof sharedUpdate>[0]["scalarDiff"];
  linkOps: Parameters<typeof sharedUpdate>[0]["linkOps"];
  reasons: Record<string, string>;
  suppliers: Parameters<typeof sharedUpdate>[0]["suppliers"];
  baselineFingerprint?: string | null;
  editContextReadAt?: string | null;
}): ReturnType<typeof sharedUpdate> {
  return sharedUpdate({ ...args, source: PRC_PORTAL_SOURCE });
}
