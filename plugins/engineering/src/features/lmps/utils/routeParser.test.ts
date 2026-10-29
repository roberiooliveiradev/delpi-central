import { describe, expect, it } from "vitest";

import { LMPS_BASE_PATH } from "../constants/routes";
import { normalizeLmpsPath, parseLmpsPath } from "./routeParser";

describe("parseLmpsPath — rotas nested do Portal Engenharia", () => {
  it("base path migrou para o namespace do Portal", () => {
    expect(LMPS_BASE_PATH).toBe("/apps/engineering/lmps");
  });

  it("raiz da feature resolve o dashboard", () => {
    expect(parseLmpsPath("/apps/engineering/lmps")).toEqual({
      view: "dashboard",
    });
    expect(parseLmpsPath("/apps/engineering/lmps/")).toEqual({
      view: "dashboard",
    });
  });

  it("detalhe de OV extrai o sale_number decodificado", () => {
    expect(parseLmpsPath("/apps/engineering/lmps/ov/003696")).toEqual({
      view: "ov-detail",
      saleNumber: "003696",
    });
  });

  it("rotas de NC resolvem views pendentes governadas", () => {
    expect(parseLmpsPath("/apps/engineering/lmps/nonconformities").view).toBe(
      "nonconformities",
    );
    expect(
      parseLmpsPath("/apps/engineering/lmps/nonconformities/abc-123"),
    ).toEqual({ view: "nonconformity-detail", ncId: "abc-123" });
    expect(
      parseLmpsPath("/apps/engineering/lmps/nonconformities/new").view,
    ).toBe("nonconformity-new");
  });

  it("caminhos fora do namespace caem no dashboard da feature", () => {
    expect(parseLmpsPath("/apps/engineering/outra-coisa").view).toBe(
      "dashboard",
    );
    expect(parseLmpsPath("").view).toBe("dashboard");
  });

  it("normalize remove barra final preservando a raiz", () => {
    expect(normalizeLmpsPath("/apps/engineering/lmps/")).toBe(
      "/apps/engineering/lmps",
    );
    expect(normalizeLmpsPath("")).toBe(LMPS_BASE_PATH);
  });
});
