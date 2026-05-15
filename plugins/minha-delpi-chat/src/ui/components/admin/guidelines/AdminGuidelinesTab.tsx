import { useState } from "react";

import { GuidelineEditorPanel } from "./GuidelineEditorPanel";
import { GuidelineListPanel } from "./GuidelineListPanel";
import { GuidelineTestPanel } from "./GuidelineTestPanel";
import { GuidelineVersionPanel } from "./GuidelineVersionPanel";
import type { AdminGuideline, GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./AdminGuidelinesTab.css";

type AdminGuidelinesTabProps = GuidelineBackendPlaceholders & {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function AdminGuidelinesTab({
  guidelines,
  saveGuideline,
  publishGuideline,
  archiveGuideline,
  reloadAdminData,
  testGuidelines,
  getAccessToken,
}: AdminGuidelinesTabProps) {
  const [editingGuideline, setEditingGuideline] =
    useState<AdminGuideline | null>(null);

  return (
    <section className="mdc-admin-guidelines">
      <GuidelineListPanel
        guidelines={guidelines}
        publishGuideline={publishGuideline}
        archiveGuideline={archiveGuideline}
        onEditGuideline={setEditingGuideline}
      />

      <div className="mdc-admin-guidelines__workbench">
        <GuidelineEditorPanel
          editingGuideline={editingGuideline}
          onCancelEdit={() => setEditingGuideline(null)}
          onSave={saveGuideline}
        />

        <GuidelineTestPanel testGuidelines={testGuidelines} />
      </div>

      <GuidelineVersionPanel
        guidelines={guidelines}
        getAccessToken={getAccessToken}
        onRestored={reloadAdminData}
      />
    </section>
  );
}
