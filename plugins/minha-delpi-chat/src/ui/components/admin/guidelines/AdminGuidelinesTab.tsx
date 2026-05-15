import { GuidelineEditorPanel } from "./GuidelineEditorPanel";
import { GuidelineListPanel } from "./GuidelineListPanel";
import { GuidelineTestPanel } from "./GuidelineTestPanel";
import { GuidelineVersionPanel } from "./GuidelineVersionPanel";
import type { GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./AdminGuidelinesTab.css";

type AdminGuidelinesTabProps = GuidelineBackendPlaceholders;

export function AdminGuidelinesTab({
  guidelines,
  saveGuideline,
  publishGuideline,
  archiveGuideline,
  reloadAdminData,
  testGuidelines,
  getAccessToken,
}: AdminGuidelinesTabProps & {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
}) {
  return (
    <section className="mdc-admin-guidelines">
      <GuidelineListPanel
        guidelines={guidelines}
        publishGuideline={publishGuideline}
        archiveGuideline={archiveGuideline}
      />

      <div className="mdc-admin-guidelines__workbench">
        <GuidelineEditorPanel onSave={saveGuideline} />
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
