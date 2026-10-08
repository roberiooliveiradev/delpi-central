import { describe, expect, it } from "vitest";

import { TRANSFORMOMETRO_ROUTES } from "../constants/routes";
import { USER_MANUAL_CONTENT, type UserManualLink } from "./userManualContent";

const REAL_PATHS = new Set(Object.values(TRANSFORMOMETRO_ROUTES));

describe("Transforma+ user manual", () => {
  it("usa UserManual compartilhado só com conteúdo do portal", () => {
    const text = JSON.stringify(USER_MANUAL_CONTENT);
    // Copy UI-specific permanece local — navegação, Hero, Favoritos.
    expect(text).toMatch(/Bom dia/);
    expect(text).toMatch(/todas as unidades/);
    expect(text).toMatch(/Favoritos/);
    expect(text).toMatch(/últimos acessos/i);
    expect(text).toMatch(/Metas e IDD/);
    expect(text).toMatch(/Economia bruta é o indicador do programa com meta/);
    expect(text).toMatch(/nota IDD/);
    expect(text).not.toMatch(/Strategic Indicators/);
    expect(text).not.toMatch(/Keycloak/);
    expect(text).not.toMatch(/ainda não faz(em)? parte deste portal/);
    expect(text).not.toMatch(/carteira/);
    const linked = USER_MANUAL_CONTENT.sections.flatMap(
      (section): readonly UserManualLink[] => section.links ?? [],
    );
    expect(
      linked
        .filter(
          (link) =>
            link.where !== "Minhas tarefas" &&
            link.where !== "Sala de interação" &&
            link.where !== "Workspace do processo",
        )
        .every((link) => !/sala|tarefa/i.test(`${link.want} ${link.where} ${link.path ?? ""}`)),
    ).toBe(true);
    expect(USER_MANUAL_CONTENT.sections.map((section) => section.id)).toEqual([
      "home",
      "overview",
      "targets-idd",
      "processes",
      "process-documentation",
      "revision-diagnostic",
      "my-tasks",
      "interaction",
      "teo",
      "minutes",
      "data",
      "administration",
      "settings",
    ]);
    expect(JSON.stringify(USER_MANUAL_CONTENT.sections)).toMatch(/Documentação do processo/);
    expect(JSON.stringify(USER_MANUAL_CONTENT.sections)).toMatch(/Nova tarefa/);
    expect(JSON.stringify(USER_MANUAL_CONTENT.sections)).not.toMatch(/schema|OpenAPI|plugin-ui/);
  });

  it("mantém semântica fora das seções mapeadas — Product Guide é a authority", () => {
    // Seções DERIVE: intro/bullets semânticos não são mais autoridade local —
    // vêm do Product Guide via helpGuideContent (ver helpGuideContent.test.ts).
    const mapped = ["home", "overview", "targets-idd", "processes", "process-documentation",
      "revision-diagnostic", "my-tasks", "interaction", "minutes", "data", "settings"];
    for (const id of mapped) {
      const section = USER_MANUAL_CONTENT.sections.find((s) => s.id === id);
      expect(section, id).toBeTruthy();
      expect(section?.intro, `${id} intro deve derivar do guide`).toBeUndefined();
    }
    // Bullets locais só existem onde há copy de tela (Hero/busca/navegação).
    const withLocalBullets = mapped.filter(
      (id) => (USER_MANUAL_CONTENT.sections.find((s) => s.id === id)?.bullets?.length ?? 0) > 0,
    );
    expect(withLocalBullets).toEqual(["home", "processes"]);
    // UI-specific: seções não mapeadas continuam locais.
    const teo = USER_MANUAL_CONTENT.sections.find((s) => s.id === "teo");
    expect(teo?.intro).toMatch(/ChatGPT/);
    const admin = USER_MANUAL_CONTENT.sections.find((s) => s.id === "administration");
    expect(admin?.intro).toMatch(/Administração/);
  });

  it("só liga caminhos reais do MFE", () => {
    const paths = USER_MANUAL_CONTENT.sections.flatMap((section) =>
      (section.links ?? [])
        .map((link) => link.path)
        .filter((path): path is NonNullable<typeof path> => path != null),
    );
    expect(paths.length).toBeGreaterThan(0);
    expect(paths.every((path) => REAL_PATHS.has(path))).toBe(true);
  });

  it("mantém a navegação da sala de interação local (links UI-specific)", () => {
    const interaction = USER_MANUAL_CONTENT.sections.find((section) => section.id === "interaction");
    expect(interaction).toBeTruthy();
    const text = JSON.stringify(interaction?.links ?? []);
    expect(text).toMatch(/Sala de interação/);
  });
});
