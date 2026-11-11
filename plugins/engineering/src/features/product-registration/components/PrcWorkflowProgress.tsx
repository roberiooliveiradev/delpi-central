/** UI-FIX-07 — a implementação migrou para `@delpi/plugin-ui`
 * (`PrcWorkflowProgress`), fonte única para Portal Engenharia e
 * Minhas Solicitações. Wrapper preserva o ponto de import local. */

import { PrcWorkflowProgress as SharedPrcWorkflowProgress } from "@delpi/plugin-ui/index";

export function PrcWorkflowProgress({ status }: { status: string }) {
  return <SharedPrcWorkflowProgress status={status} />;
}
