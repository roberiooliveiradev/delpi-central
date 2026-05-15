import type { AdminLlmStatus } from "../../../../data/api/adminTypes";
import { ExternalActionsPanel } from "./ExternalActionsPanel";
import { LlmProviderPanel } from "./LlmProviderPanel";
import { ToolHealthPanel } from "./ToolHealthPanel";
import type { AdminToolsBackendPlaceholders } from "./toolsTypes";

import "./AdminToolsTab.css";

type AdminToolsTabProps = AdminToolsBackendPlaceholders & {
  llmStatus: AdminLlmStatus | null;
};

export function AdminToolsTab({
  llmStatus,
  loadExternalActions,
  testExternalAction,
  syncOpenApiProviders,
  loadToolHealth,
}: AdminToolsTabProps) {
  return (
    <section className="mdc-admin-tools">
      <LlmProviderPanel llmStatus={llmStatus} />

      <ExternalActionsPanel
        loadExternalActions={loadExternalActions}
        testExternalAction={testExternalAction}
        syncOpenApiProviders={syncOpenApiProviders}
      />

      <ToolHealthPanel loadToolHealth={loadToolHealth} />
    </section>
  );
}
