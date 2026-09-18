import { afterEach, describe, expect, it } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import {
  readPortalFavorites,
  resetPortalFavoritesForTests,
  togglePortalFavorite,
  visiblePortalFavorites,
} from "./portalFavorites";

describe("portalFavorites", () => {
  afterEach(() => {
    resetPortalFavoritesForTests();
  });

  it("adiciona, remove e relê depois do persist", () => {
    const added = togglePortalFavorite({
      path: TRANSFORMOMETRO_ROUTES.dashboard,
      label: "Visão geral",
    });
    expect(added.map((item) => item.path)).toEqual([TRANSFORMOMETRO_ROUTES.dashboard]);
    expect(readPortalFavorites()).toEqual(added);
    expect(
      togglePortalFavorite({ path: TRANSFORMOMETRO_ROUTES.dashboard, label: "Visão geral" }),
    ).toEqual([]);
  });

  it("não guarda rota desconhecida nem Administração sem manage", () => {
    togglePortalFavorite({ path: "/apps/transformometro/sala", label: "Sala" });
    togglePortalFavorite({
      path: TRANSFORMOMETRO_ROUTES.administration,
      label: "Administração",
    });
    expect(readPortalFavorites().map((item) => item.path)).toEqual([
      TRANSFORMOMETRO_ROUTES.administration,
    ]);
    expect(visiblePortalFavorites(readPortalFavorites(), false)).toEqual([]);
    expect(visiblePortalFavorites(readPortalFavorites(), true).map((item) => item.path)).toEqual([
      TRANSFORMOMETRO_ROUTES.administration,
    ]);
  });
});
