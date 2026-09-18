import { describe, expect, it } from "vitest";

import { describeHttpError } from "../utils/apiErrorMessage";
import { buildProcessoPath, parseTransformometroPath } from "../utils/routeParser";
import { TRANSFORMOMETRO_ROUTES } from "./routes";
import { PROCESSO_WORKSPACE_SECTIONS } from "../ui/processes/processWorkspaceNav";
import {
  DEFERRED_NAV_ITEMS,
  PORTAL_LAUNCHER_GROUPS,
  PORTAL_PRODUCT_NAME,
  PORTAL_TOPBAR_ITEMS,
  PORTAL_WELCOME,
  PROCESS_LIST_EMPTY_MESSAGE,
  PROCESS_LIST_SUBTITLE,
  buildProcessListQuery,
  filterPortalCatalog,
  processListPlaceholder,
  resolvePortalTopBarId,
} from "./portalExperience";

describe("Portal Transforma+ navigation", () => {
  it("mantém o produto e a saudação sem nome inventado", () => {
    expect(PORTAL_PRODUCT_NAME).toBe("Portal Transforma+");
    expect(PORTAL_WELCOME).toBe("Bem-vindo ao Portal Transforma+");
  });

  it("coloca na TopBar só áreas com destino atual", () => {
    expect(PORTAL_TOPBAR_ITEMS.map((item) => item.label)).toEqual([
      "Início",
      "Visão geral",
      "Meus processos",
      "Administração",
    ]);
    const labels = PORTAL_TOPBAR_ITEMS.map((item) => item.label).join(" ");
    expect(labels).not.toMatch(/Atas|Configurações|Exportar|Sala|Tarefas|Ajuda/);
  });

  it("não coloca Configurações como área principal", () => {
    expect(PORTAL_TOPBAR_ITEMS.map((item) => item.label)).not.toContain("Configurações");
    const links = PORTAL_LAUNCHER_GROUPS.flatMap((group) => group.links.map((link) => link.label));
    expect(links).not.toContain("Configurações");
    expect(links).toEqual(
      expect.arrayContaining(["Atas", "Exportar/Importar", "Meus processos", "Visão geral", "Administração"]),
    );
    const visible = filterPortalCatalog("", { includeAdministration: false }).map((item) => item.label);
    expect(visible).not.toContain("Configurações");
    expect(visible).not.toContain("Administração");
    expect(visible).toContain("Exportar/Importar");
  });

  it("não promove sala, tarefas, ajuda, favoritos ou usuário a funcional", () => {
    expect(DEFERRED_NAV_ITEMS.map((item) => item.label)).toEqual([
      "Sala de interação",
      "Minhas tarefas",
      "Ajuda",
      "Favoritos",
      "Usuário",
    ]);
    expect(DEFERRED_NAV_ITEMS.every((item) => item.status === "TO_INVENTORY")).toBe(true);
    const topIds = PORTAL_TOPBAR_ITEMS.map((item) => item.id);
    for (const item of DEFERRED_NAV_ITEMS) {
      expect(topIds).not.toContain(item.id);
    }
  });

  it("preserva deep links fora da TopBar", () => {
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.home).view).toBe("home");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.dashboard).view).toBe("dashboard");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.administration).view).toBe(
      "administration",
    );
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.meetingMinutes).view).toBe("atas");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.settingsUnits).view).toBe("configuracoes");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.data).view).toBe("dados");
  });

  it("marca Administração nas rotas administrativas e não na home", () => {
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.home)).toBe("home");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.dashboard)).toBe("overview");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.processes)).toBe("processes");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.settingsUnits)).toBe("administration");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.data)).toBe("");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.meetingMinutes)).toBe("");
  });

  it("busca só funcionalidades, não entidades", () => {
    expect(filterPortalCatalog("atas").map((item) => item.label)).toContain("Atas");
    expect(filterPortalCatalog("sala")).toEqual([]);
    expect(filterPortalCatalog("").some((item) => item.id === "interaction")).toBe(false);
  });

  it("lista processos pelo contrato atual", () => {
    expect(PROCESS_LIST_SUBTITLE).toBe("Processos disponíveis no seu escopo de acesso.");
    expect(buildProcessListQuery("  compras ", "ativo")).toEqual({ q: "compras", status: "ativo" });
    expect(buildProcessListQuery("abc", "ativo")).not.toHaveProperty("filial_id");
  });

  it("separa 403, erro e lista vazia", () => {
    const forbidden = processListPlaceholder(403, describeHttpError(403));
    expect(forbidden).not.toBe(PROCESS_LIST_EMPTY_MESSAGE);
    expect(forbidden.toLowerCase()).not.toContain("nenhum processo");
    expect(processListPlaceholder(500, "Serviço indisponível")).toBe("Serviço indisponível");
  });

  it("abre o workspace existente sem seções alvo", () => {
    expect(parseTransformometroPath(buildProcessoPath("proc-1")).view).toBe("processo");
    expect(PROCESSO_WORKSPACE_SECTIONS.map((section) => section.id)).not.toContain("sipoc");
  });
});
