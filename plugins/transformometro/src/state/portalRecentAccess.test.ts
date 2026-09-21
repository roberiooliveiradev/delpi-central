import { afterEach, describe, expect, it } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { buildProcessoPath } from "../utils/routeParser";
import {
  readPortalRecentAccess,
  recordPortalRecentAccess,
  resetPortalRecentAccessForTests,
  resolveRecentAccessCatalogItem,
  visiblePortalRecentAccess,
} from "./portalRecentAccess";

describe("portalRecentAccess", () => {
  afterEach(() => {
    resetPortalRecentAccessForTests();
  });

  it("coloca o mais recente primeiro, sem duplicata e com limite 5", () => {
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.dashboard);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.processes);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.help);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.meetingMinutes);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.data);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.administration, { canManage: true });
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.dashboard);
    const paths = readPortalRecentAccess().map((item) => item.path);
    expect(paths[0]).toBe(TRANSFORMOMETRO_ROUTES.dashboard);
    expect(new Set(paths).size).toBe(paths.length);
    expect(paths).toHaveLength(5);
    expect(paths).not.toContain(TRANSFORMOMETRO_ROUTES.processes);
  });

  it("não grava Início nem rota inexistente", () => {
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.home);
    recordPortalRecentAccess("/apps/transformometro/sala");
    expect(readPortalRecentAccess()).toEqual([]);
  });

  it("resolve processo detalhe para Meus processos e omite admin sem manage", () => {
    expect(resolveRecentAccessCatalogItem(buildProcessoPath("abc"))?.path).toBe(
      TRANSFORMOMETRO_ROUTES.processes,
    );
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.administration, { canManage: false });
    expect(readPortalRecentAccess(false)).toEqual([]);
    recordPortalRecentAccess(TRANSFORMOMETRO_ROUTES.administration, { canManage: true });
    expect(visiblePortalRecentAccess(readPortalRecentAccess(true), false)).toEqual([]);
  });

  it("tolera storage inválido", () => {
    const store = new Map<string, string>([
      ["transformometro.portal.recent-access.v1", "{not-json"],
    ]);
    (globalThis as { window?: unknown }).window = {
      localStorage: {
        getItem(key: string) {
          return store.get(key) ?? null;
        },
        setItem(key: string, value: string) {
          store.set(key, value);
        },
        removeItem(key: string) {
          store.delete(key);
        },
      },
    };
    resetPortalRecentAccessForTests();
    window.localStorage.setItem("transformometro.portal.recent-access.v1", "{not-json");
    expect(readPortalRecentAccess()).toEqual([]);
  });
});
