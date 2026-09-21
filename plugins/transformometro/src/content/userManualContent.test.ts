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
    expect(text).not.toMatch(/ainda não faz(em)? parte deste portal/);
    expect(text).not.toMatch(/carteira/);
    const linked = USER_MANUAL_CONTENT.sections.flatMap((section) => section.links ?? []);
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
    const processes = USER_MANUAL_CONTENT.sections.find((section) => section.id === "processes");
    expect(JSON.stringify(processes)).toMatch(/workspace/i);
    expect(JSON.stringify(processes)).toMatch(/tarefas relacionadas/i);
    expect(USER_MANUAL_CONTENT.sections.map((section) => section.id)).toEqual([
      "home",
      "overview",
      "targets-idd",
      "processes",
      "process-documentation",
      "my-tasks",
      "interaction",
      "minutes",
      "data",
      "administration",
      "settings",
    ]);
    expect(JSON.stringify(USER_MANUAL_CONTENT.sections)).toMatch(/Documentação do processo/);
    const tasks = USER_MANUAL_CONTENT.sections.find((section) => section.id === "my-tasks");
    expect(tasks?.intro).toMatch(/assinatura/i);
    expect(JSON.stringify(tasks)).toMatch(/Nova tarefa/);
    expect(JSON.stringify(tasks)).not.toMatch(/schema|OpenAPI|plugin-ui/);
  });

  it("só liga caminhos reais do MFE", () => {
    const paths = USER_MANUAL_CONTENT.sections.flatMap((section) =>
      (section.links ?? []).map((link) => link.path).filter((path): path is string => Boolean(path)),
    );
    expect(paths.length).toBeGreaterThan(0);
    expect(paths.every((path) => REAL_PATHS.has(path))).toBe(true);
  });

  it("documenta a sala de interação com Localizar, anexos, colar imagem e histórico", () => {
    const interaction = USER_MANUAL_CONTENT.sections.find((section) => section.id === "interaction");
    expect(interaction).toBeTruthy();
    const text = JSON.stringify(interaction);
    expect(text).toMatch(/Localizar/);
    expect(text).toMatch(/colar uma imagem/i);
    expect(text).toMatch(/remover o anexo/i);
    expect(text).toMatch(/Carregar mensagens anteriores/);
    expect(text).toMatch(/fotos de perfil/i);
  });
});
