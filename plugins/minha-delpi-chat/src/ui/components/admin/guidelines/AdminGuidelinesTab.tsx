import { useMemo, useState } from "react";

import { GuidelineEditorPanel } from "./GuidelineEditorPanel";
import { GuidelineListPanel } from "./GuidelineListPanel";
import { GuidelinesSummaryStrip } from "./GuidelinesSummaryStrip";
import { GuidelineTestPanel } from "./GuidelineTestPanel";
import { GuidelineVersionPanel } from "./GuidelineVersionPanel";
import {
  computeGuidelinesSummary,
  filterGuidelinesByStatus,
  type GuidelineStatusFilter,
} from "./guidelinesSummary";
import type { AdminRbacSummary } from "../../../../data/api/adminTypes";
import type { AdminGuideline, GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./AdminGuidelinesTab.css";

type AdminGuidelinesTabProps = GuidelineBackendPlaceholders & {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  rbac?: AdminRbacSummary | null;
};

export function AdminGuidelinesTab({
  guidelines,
  saveGuideline,
  publishGuideline,
  archiveGuideline,
  reloadAdminData,
  testGuidelines,
  getAccessToken,
  rbac,
}: AdminGuidelinesTabProps) {
  const [editingGuideline, setEditingGuideline] =
    useState<AdminGuideline | null>(null);
  const [statusFilter, setStatusFilter] = useState<GuidelineStatusFilter>("all");

  const summary = useMemo(
    () => computeGuidelinesSummary(guidelines),
    [guidelines],
  );
  const visibleGuidelines = useMemo(
    () => filterGuidelinesByStatus(guidelines, statusFilter),
    [guidelines, statusFilter],
  );

  const canCreateGuidelines = Boolean(rbac?.capabilities.canCreateGuidelines);
  const canPublishGuidelines = Boolean(rbac?.capabilities.canPublishGuidelines);
  const canArchiveGuidelines = Boolean(rbac?.capabilities.canArchiveGuidelines);

  return (
    <section className="mdc-admin-guidelines">
      <div className="mdc-admin-guidelines__toolbar">
        <GuidelinesSummaryStrip
          summary={summary}
          activeFilter={statusFilter}
          onFilterChange={setStatusFilter}
        />

        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          disabled={!canCreateGuidelines}
          title={
            canCreateGuidelines
              ? "Criar nova diretriz"
              : "Sem permissão para criar diretrizes"
          }
          onClick={() => setEditingGuideline(null)}
        >
          Nova diretriz
        </button>
      </div>

      <GuidelineListPanel
        guidelines={visibleGuidelines}
        statusFilter={statusFilter}
        totalCount={guidelines.length}
        publishGuideline={publishGuideline}
        archiveGuideline={archiveGuideline}
        onEditGuideline={setEditingGuideline}
        canCreateGuidelines={canCreateGuidelines}
        canPublishGuidelines={canPublishGuidelines}
        canArchiveGuidelines={canArchiveGuidelines}
      />

      <div className="mdc-admin-guidelines__workbench mdc-admin-split">
        <div className="mdc-admin-split__aside">
          <GuidelineEditorPanel
            editingGuideline={editingGuideline}
            onCancelEdit={() => setEditingGuideline(null)}
            onSave={saveGuideline}
            canCreateGuidelines={canCreateGuidelines}
          />
        </div>

        <div className="mdc-admin-split__main">
          <GuidelineTestPanel testGuidelines={testGuidelines} />
        </div>
      </div>

      <GuidelineVersionPanel
        guidelines={guidelines}
        getAccessToken={getAccessToken}
        onRestored={reloadAdminData}
        canCreateGuidelines={canCreateGuidelines}
      />
    </section>
  );
}
