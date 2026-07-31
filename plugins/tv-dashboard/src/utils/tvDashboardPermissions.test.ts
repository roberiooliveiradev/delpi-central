import { describe, expect, it } from "vitest";

import { canManageTemplates, TV_TEMPLATES_MANAGE } from "./tvDashboardPermissions";
import { parseTvDashboardRoute, templateEditPath, templatesLibraryPath } from "../routing";
import {
  resolveTemplateConfigWithLocalDraft,
  writeTemplateDraft,
  clearTemplateDraft,
} from "./templateDraftPreferences";

describe("canManageTemplates", () => {
  it("aceita permissão dedicada e superadmin", () => {
    expect(canManageTemplates({ permissions: [TV_TEMPLATES_MANAGE] })).toBe(true);
    expect(canManageTemplates({ permissions: ["tv-dashboard.write"] })).toBe(false);
    expect(canManageTemplates({ permissions: [], isSuperadmin: true })).toBe(true);
  });

  it("usa hasPermission do host quando disponível", () => {
    expect(
      canManageTemplates({
        hasPermission: (code) => code === TV_TEMPLATES_MANAGE,
      }),
    ).toBe(true);
  });
});

describe("template routes", () => {
  it("parseia /templates e /templates/:id", () => {
    expect(parseTvDashboardRoute("/apps/tv-dashboard/templates")).toEqual({
      view: "templates",
    });
    expect(parseTvDashboardRoute("/apps/tv-dashboard/templates/abc")).toEqual({
      view: "template-edit",
      id: "abc",
    });
    expect(templatesLibraryPath()).toBe("/apps/tv-dashboard/templates");
    expect(templateEditPath("x")).toBe("/apps/tv-dashboard/templates/x");
  });
});

describe("template draft F5", () => {
  it("preserva draft local com versão >= servidor", () => {
    const id = "tmpl-1";
    clearTemplateDraft(id);
    writeTemplateDraft(id, { version: 4, blocks: [{ id: "local" }] }, 2);
    const resolved = resolveTemplateConfigWithLocalDraft(
      id,
      { version: 4, blocks: [] },
      1,
    );
    expect(resolved.fromDraft).toBe(true);
    expect((resolved.nativeConfig.blocks as { id: string }[])[0].id).toBe("local");
    clearTemplateDraft(id);
  });
});
