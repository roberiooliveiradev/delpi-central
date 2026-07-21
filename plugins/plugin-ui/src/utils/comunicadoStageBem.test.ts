import { describe, expect, it } from "vitest";

import {
  COMUNICADO_UI_PREFIX,
  comunicadoDualSuffix,
  comunicadoStageBemClasses,
  ensureComunicadoDualClass,
} from "./comunicadoStageBem";

describe("comunicadoStageBem", () => {
  it("ensureComunicadoDualClass espelha tdp-comunicado → delpi-ui-comunicado", () => {
    expect(ensureComunicadoDualClass("tdp-comunicado__block tdp-comunicado__block--text")).toBe(
      [
        "tdp-comunicado__block",
        `${COMUNICADO_UI_PREFIX}__block`,
        "tdp-comunicado__block--text",
        `${COMUNICADO_UI_PREFIX}__block--text`,
      ].join(" "),
    );
  });

  it("preserve tokens que não são comunicado", () => {
    expect(ensureComunicadoDualClass("tdp-native-screen tdp-comunicado")).toBe(
      `tdp-native-screen tdp-comunicado ${COMUNICADO_UI_PREFIX}`,
    );
  });

  it("comunicadoStageBemClasses emite dual-class no root/stage", () => {
    const cn = comunicadoStageBemClasses("tdp");
    expect(cn.root).toContain("tdp-native-screen");
    expect(cn.root).toContain("tdp-comunicado");
    expect(cn.root).toContain(COMUNICADO_UI_PREFIX);
    expect(cn.stage).toContain("tdp-comunicado__stage");
    expect(cn.stage).toContain(`${COMUNICADO_UI_PREFIX}__stage`);
  });

  it("comunicadoDualSuffix cobre modificadores", () => {
    expect(comunicadoDualSuffix("__block--anim-fade")).toContain(
      `${COMUNICADO_UI_PREFIX}__block--anim-fade`,
    );
  });
});
