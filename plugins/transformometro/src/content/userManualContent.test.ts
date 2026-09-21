import { describe, expect, it } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { USER_MANUAL_CONTENT } from "./userManualContent";

const REAL_PATHS = new Set(Object.values(TRANSFORMOMETRO_ROUTES));

describe("Transforma+ user manual", () => {
  it("usa UserManual compartilhado só com conteúdo do portal", () => {
    const text = JSON.stringify(USER_MANUAL_CONTENT);
    expect(text).toMatch(/Bom dia/);
    expect(text).toMatch(/todas as unidades/);
    expect(text).toMatch(/Favoritos/);
    expect(text).toMatch(/últimos acessos/i);
    expect(text).toMatch(/Metas e IDD/);
    expect(text).toMatch(/Economia bruta é o indicador do programa com meta/);
    expect(text).toMatch(/Use Período rápido para escolher intervalos comuns/);
    expect(text).toMatch(/nota IDD/);
    expect(text).not.toMatch(/Strategic Indicators/);
    expect(text).not.toMatch(/Keycloak/);
    expect(text).toMatch(/ainda não fazem parte deste portal/);
    expect(text).not.toMatch(/carteira/);
    const linked = USER_MANUAL_CONTENT.sections.flatMap((section) => section.links ?? []);
    expect(linked.every((link) => !/sala|tarefa/i.test(`${link.want} ${link.where} ${link.path ?? ""}`))).toBe(
      true,
    );
    expect(USER_MANUAL_CONTENT.sections.map((section) => section.id)).toEqual([
      "home",
      "overview",
      "targets-idd",
      "processes",
      "minutes",
      "data",
      "administration",
      "settings",
    ]);
  });

  it("só liga caminhos reais do MFE", () => {
    const paths = USER_MANUAL_CONTENT.sections.flatMap((section) =>
      (section.links ?? []).map((link) => link.path).filter((path): path is string => Boolean(path)),
    );
    expect(paths.length).toBeGreaterThan(0);
    expect(paths.every((path) => REAL_PATHS.has(path))).toBe(true);
  });
});
