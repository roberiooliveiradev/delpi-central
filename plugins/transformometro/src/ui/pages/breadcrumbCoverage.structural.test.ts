import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const dir = dirname(fileURLToPath(import.meta.url));
const root = join(dir, "../..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("breadcrumb coverage — PageHeader.path / kit pagePath", () => {
  it("PageHeader renders canonical TmPagePath from path prop", () => {
    const header = read("components/PageHeader.tsx");
    expect(header).toMatch(/TmPagePath/);
    expect(header).toMatch(/path\?: PageHeaderPath/);
    expect(header).not.toMatch(/PortalTopBar/);
  });

  it("atas family wires shared builders", () => {
    expect(read("ui/pages/MeetingMinutesPage.tsx")).toMatch(/buildMeetingMinutesListPagePath/);
    expect(read("ui/pages/MeetingMinuteDetailPage.tsx")).toMatch(/buildMeetingMinuteDetailPagePath/);
    expect(read("ui/pages/MeetingMinuteEditorPage.tsx")).toMatch(/buildMeetingMinuteEditorPagePath/);
    expect(read("ui/pages/MeetingMinuteEditorPage.tsx")).toMatch(/Cancelar edição/);
    expect(read("ui/pages/MeetingMinuteSignPage.tsx")).toMatch(/buildMeetingMinuteSignPagePath/);
    expect(read("ui/pages/MeetingMinutesPendingPage.tsx")).toMatch(
      /buildMeetingMinutesPendingPagePath/,
    );
    expect(read("ui/pages/MySignaturePage.tsx")).toMatch(/buildMySignaturePagePath/);
  });

  it("root sections use buildRootSectionPagePath", () => {
    for (const file of [
      "ui/pages/ProcessesPage.tsx",
      "ui/pages/MyTasksPage.tsx",
      "ui/pages/DashboardPage.tsx",
      "ui/pages/DataTransferPage.tsx",
      "ui/pages/AdministrationPage.tsx",
      "ui/pages/HelpPage.tsx",
    ]) {
      expect(read(file)).toMatch(/buildRootSectionPagePath/);
    }
    expect(read("ui/pages/HelpPage.tsx")).not.toMatch(/lead=\{/);
  });

  it("settings workspace uses section/entity builders", () => {
    const settings = read("ui/pages/SettingsWorkspacePage.tsx");
    expect(settings).toMatch(/buildSettingsSectionPagePath|buildSettingsEntityPagePath/);
    expect(read("ui/pages/BranchesPage.tsx")).toMatch(/buildSettingsSectionPagePath/);
    expect(read("ui/pages/BranchDetailPage.tsx")).toMatch(/buildSettingsEntityPagePath/);
    expect(read("ui/pages/DepartmentsPage.tsx")).toMatch(/buildSettingsSectionPagePath/);
    expect(read("ui/pages/DepartmentDetailPage.tsx")).toMatch(/buildSettingsEntityPagePath/);
    expect(read("ui/pages/SharedResourcesPage.tsx")).toMatch(/buildSettingsSectionPagePath/);
    expect(read("ui/pages/SharedResourceDetailPage.tsx")).toMatch(/buildSettingsEntityPagePath/);
  });

  it("process workspace keeps TmPagePath chrome; person directory keeps kit pagePath", () => {
    expect(read("ui/processes/ProcessWorkspaceChrome.tsx")).toMatch(/TmPagePath/);
    expect(read("ui/pages/PersonDirectoryPage.tsx")).toMatch(/pagePath=\{\{/);
    expect(read("ui/pages/PortalHomePage.tsx")).not.toMatch(/path=\{/);
  });
});
