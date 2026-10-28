import { describe, expect, it } from "vitest";

import {
  buildPluginPath,
  checklistAdminEventsPath,
  checklistAdminVersionDocumentPath,
  checklistAdminVersionPath,
  CONTROLLERSHIP_FINANCE_BASE_PATH,
  normalizeBasePath,
  normalizePathname,
  resolveActiveNavId,
  resolvePluginRoute,
} from "./pluginRoutes";

describe("pluginRoutes", () => {
  it("resolve a rota raiz como home", () => {
    const resolved = resolvePluginRoute("/apps/controllership-finance");
    expect(resolved.view).toBe("home");
    expect(resolved.relativePath).toBe("");
  });

  it("normaliza trailing slash no base path", () => {
    const resolved = resolvePluginRoute("/apps/controllership-finance/");
    expect(resolved.view).toBe("home");
  });

  it("resolve a rota de estoque histórico", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/stock-inventory",
    );
    expect(resolved.view).toBe("stock_inventory");
    expect(resolved.relativePath).toBe("closing/stock-inventory");
    expect(buildPluginPath("stock_inventory")).toBe(
      "/apps/controllership-finance/closing/stock-inventory",
    );
  });

  it("resolve a rota de pendências", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/pendencies",
    );
    expect(resolved.view).toBe("pendencies");
    expect(resolved.relativePath).toBe("closing/pendencies");
    expect(buildPluginPath("pendencies")).toBe(
      "/apps/controllership-finance/closing/pendencies",
    );
  });

  it("resolve as rotas de pacotes e cockpit", () => {
    const pkg = resolvePluginRoute(
      "/apps/controllership-finance/closing/packages",
    );
    expect(pkg.view).toBe("packages");
    expect(pkg.relativePath).toBe("closing/packages");
    expect(buildPluginPath("packages")).toBe(
      "/apps/controllership-finance/closing/packages",
    );
    const cockpit = resolvePluginRoute(
      "/apps/controllership-finance/closing/cockpit",
    );
    expect(cockpit.view).toBe("cockpit");
    expect(buildPluginPath("cockpit")).toBe(
      "/apps/controllership-finance/closing/cockpit",
    );
  });

  it("deep links de pacotes e cockpit com competência", () => {
    const pkg = resolvePluginRoute(
      "/apps/controllership-finance/closing/packages/2026-11",
    );
    expect(pkg.view).toBe("packages");
    expect(pkg.checklistPeriod).toBe("2026-11");
    const cockpit = resolvePluginRoute(
      "/apps/controllership-finance/closing/cockpit/2026-11",
    );
    expect(cockpit.view).toBe("cockpit");
    expect(cockpit.checklistPeriod).toBe("2026-11");
    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/packages/2026-13",
      ).view,
    ).toBe("not_found");
  });

  it("resolve a rota do workspace Fechamento mensal", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.relativePath).toBe("closing/monthly-closing");
    expect(buildPluginPath("monthly_closing")).toBe(
      "/apps/controllership-finance/closing/monthly-closing",
    );
    expect(
      buildPluginPath(
        "monthly_closing",
        "/apps/controllership-finance",
        "tab=documents",
      ),
    ).toBe("/apps/controllership-finance/closing/monthly-closing?tab=documents");
  });

  it("deep link de competência no Fechamento mensal", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing/2026-10",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/monthly-closing/2026-13",
      ).view,
    ).toBe("not_found");
  });

  it("deep link de documento preserva competência e referência", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing/2026-10/documents/abc-123",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(resolved.documentRef).toBe("abc-123");

    const byItem = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing/2026-10/documents/item:doc-entradas",
    );
    expect(byItem.documentRef).toBe("item:doc-entradas");

    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/monthly-closing/2026-10/documents/new",
      ).documentRef,
    ).toBe("new");
  });

  it("rota de documento com período inválido cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/monthly-closing/2026-13/documents/x",
      "/apps/controllership-finance/closing/monthly-closing/2026-10/documents",
      "/apps/controllership-finance/closing/monthly-closing/2026-10/extra/x",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("deep link de relatório preserva competência e chave", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/monthly-closing/2026-10/reports/financial-settlements",
    );
    expect(resolved.view).toBe("monthly_closing");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(resolved.reportKey).toBe("financial-settlements");

    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/monthly-closing/2026-10/reports/stock-inventory",
      ).reportKey,
    ).toBe("stock-inventory");
  });

  it("rota de relatório com período ou chave inválidos cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/monthly-closing/2026-13/reports/stock-inventory",
      "/apps/controllership-finance/closing/monthly-closing/2026-10/reports",
      "/apps/controllership-finance/closing/monthly-closing/2026-10/reports/a_b",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("resolve a rota dedicada do destinatário externo (DRE-019)", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/documents",
    );
    expect(resolved.view).toBe("received_documents");
    expect(resolved.relativePath).toBe("closing/documents");
    expect(resolved.checklistPeriod).toBeUndefined();
    expect(buildPluginPath("received_documents")).toBe(
      "/apps/controllership-finance/closing/documents",
    );
  });

  it("deep link de entrega recebida preserva a competência", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/documents/2026-10",
    );
    expect(resolved.view).toBe("received_documents");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(
      resolvePluginRoute(
        "/apps/controllership-finance/closing/documents/2026-13",
      ).view,
    ).toBe("not_found");
  });

  it("deep link de documento recebido preserva competência e referência", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/documents/2026-10/documents/abc-123",
    );
    expect(resolved.view).toBe("received_documents");
    expect(resolved.checklistPeriod).toBe("2026-10");
    expect(resolved.documentRef).toBe("abc-123");
  });

  it("rota do destinatário malformada cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/documents/2026-10/documents",
      "/apps/controllership-finance/closing/documents/2026-10/extra",
      "/apps/controllership-finance/closing/documents/10-2026",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("resolve a Home DRE (RW02) e monta o path de entrada", () => {
    const resolved = resolvePluginRoute("/apps/controllership-finance/home");
    expect(resolved.view).toBe("dre_home");
    expect(resolved.relativePath).toBe("home");
    expect(buildPluginPath("dre_home")).toBe(
      "/apps/controllership-finance/home",
    );
  });

  it("rota legada received-documents foi descontinuada (RW03)", () => {
    for (const path of [
      "/apps/controllership-finance/received-documents",
      "/apps/controllership-finance/received-documents/2026-10",
      "/apps/controllership-finance/received-documents/2026-10/documents/abc-123",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("resolve a rota do checklist da competência", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/checklist",
    );
    expect(resolved.view).toBe("checklist");
    expect(resolved.relativePath).toBe("closing/checklist");
    expect(resolved.checklistPeriod).toBeUndefined();
    expect(buildPluginPath("checklist")).toBe(
      "/apps/controllership-finance/closing/checklist",
    );
  });

  it("resolve deep link com competência no checklist", () => {
    const resolved = resolvePluginRoute(
      "/apps/controllership-finance/closing/checklist/2026-10",
    );
    expect(resolved.view).toBe("checklist");
    expect(resolved.checklistPeriod).toBe("2026-10");
  });

  it("deep link de checklist com período inválido cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/checklist/2026-13",
      "/apps/controllership-finance/closing/checklist/10-2026",
      "/apps/controllership-finance/closing/checklist/extra/2026-10",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("qualquer subrota não implementada cai em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/overview",
      "/apps/controllership-finance/my-tasks",
      "/apps/controllership-finance/help",
      "/apps/controllership-finance/administration",
      "/other-app/x",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("normalizePathname remove query e hash", () => {
    expect(normalizePathname("/apps/controllership-finance?q=x#y")).toBe(
      "/apps/controllership-finance",
    );
  });

  it("normalizeBasePath cai no canônico quando vazio", () => {
    expect(normalizeBasePath("")).toBe(CONTROLLERSHIP_FINANCE_BASE_PATH);
    expect(normalizeBasePath(undefined)).toBe(CONTROLLERSHIP_FINANCE_BASE_PATH);
  });

  it("buildPluginPath home preserva ?q= para deep link", () => {
    expect(buildPluginPath("home", "/apps/controllership-finance", "?q=ini")).toBe(
      "/apps/controllership-finance?q=ini",
    );
    expect(buildPluginPath("home", "/apps/controllership-finance")).toBe(
      "/apps/controllership-finance",
    );
  });

  it("resolve a navegação em cascata do checklist admin (UX-015)", () => {
    const version = resolvePluginRoute(
      "/apps/controllership-finance/closing/admin/versions/3",
    );
    expect(version.view).toBe("checklist_version");
    expect(version.adminVersion).toBe("3");

    const doc = resolvePluginRoute(
      "/apps/controllership-finance/closing/admin/versions/3/documents/CK-E-01",
    );
    expect(doc.view).toBe("checklist_version_document");
    expect(doc.adminVersion).toBe("3");
    expect(doc.documentItemKey).toBe("CK-E-01");

    const events = resolvePluginRoute(
      "/apps/controllership-finance/closing/admin/events",
    );
    expect(events.view).toBe("checklist_admin_events");
    expect(events.adminVersion).toBeUndefined();

    const versionEvents = resolvePluginRoute(
      "/apps/controllership-finance/closing/admin/versions/3/events",
    );
    expect(versionEvents.view).toBe("checklist_admin_events");
    expect(versionEvents.adminVersion).toBe("3");
  });

  it("deep links admin malformados caem em not_found", () => {
    for (const path of [
      "/apps/controllership-finance/closing/admin/versions",
      "/apps/controllership-finance/closing/admin/versions/abc",
      "/apps/controllership-finance/closing/admin/versions/3/documents",
      "/apps/controllership-finance/closing/admin/versions/3/extra",
    ]) {
      expect(resolvePluginRoute(path).view).toBe("not_found");
    }
  });

  it("path builders da cascata admin geram paths canônicos", () => {
    expect(checklistAdminVersionPath(3)).toBe(
      "/apps/controllership-finance/closing/admin/versions/3",
    );
    expect(
      checklistAdminVersionDocumentPath(3, "CK-E-01"),
    ).toBe(
      "/apps/controllership-finance/closing/admin/versions/3/documents/CK-E-01",
    );
    expect(checklistAdminEventsPath()).toBe(
      "/apps/controllership-finance/closing/admin/events",
    );
    expect(checklistAdminEventsPath(3)).toBe(
      "/apps/controllership-finance/closing/admin/versions/3/events",
    );
  });

  it("resolveActiveNavId marca somente home", () => {
    expect(resolveActiveNavId("home")).toBe("home");
    expect(resolveActiveNavId("not_found")).toBeNull();
  });
});
