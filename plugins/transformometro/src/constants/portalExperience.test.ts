import { describe, expect, it } from "vitest";

import { describeHttpError } from "../utils/apiErrorMessage";
import { buildProcessoPath, parseTransformometroPath } from "../utils/routeParser";
import { TRANSFORMOMETRO_ROUTES } from "./routes";
import { PROCESSO_WORKSPACE_SECTIONS } from "../ui/processes/processWorkspaceNav";
import {
  DEFERRED_NAV_ITEMS,
  PORTAL_LAUNCHER_GROUPS,
  PORTAL_PAGE_COPY,
  PORTAL_PRODUCT_NAME,
  PORTAL_TOPBAR_ITEMS,
  PORTAL_WELCOME,
  PROCESS_LIST_EMPTY_MESSAGE,
  PROCESS_LIST_SUBTITLE,
  buildProcessListQuery,
  filterPortalCatalog,
  isPortalSearchShortcut,
  processListPlaceholder,
  resolvePortalTopBarId,
  visiblePortalLauncherGroups,
  visiblePortalTopBarItems,
} from "./portalExperience";
import { USER_MANUAL_CONTENT, visibleManualLinks } from "../content/userManualContent";

describe("Portal Transforma+ navigation", () => {
  it("mantém o produto e a saudação sem nome inventado", () => {
    expect(PORTAL_PRODUCT_NAME).toBe("Portal Transforma+");
    expect(PORTAL_WELCOME).toBe("Bem-vindo ao Portal Transforma+");
  });

  it("coloca na TopBar só áreas com destino atual", () => {
    expect(PORTAL_TOPBAR_ITEMS.map((item) => item.label)).toEqual([
      "Início",
      "Visão geral",
      "Sala de interação",
      "Minhas tarefas",
      "Meus processos",
      "Administração",
      "Ajuda",
    ]);
    const labels = PORTAL_TOPBAR_ITEMS.map((item) => item.label).join(" ");
    expect(labels).not.toMatch(/Atas|Configurações|Exportar|Favoritos/);
  });

  it("não coloca Configurações como área principal", () => {
    expect(PORTAL_TOPBAR_ITEMS.map((item) => item.label)).not.toContain("Configurações");
    const links = PORTAL_LAUNCHER_GROUPS.flatMap((group) => group.links.map((link) => link.label));
    expect(links).not.toContain("Configurações");
    expect(links).toEqual(
      expect.arrayContaining([
        "Atas",
        "Exportar / Importar",
        "Meus processos",
        "Minhas tarefas",
        "Sala de interação",
        "Visão geral",
        "Administração",
      ]),
    );
    const visible = filterPortalCatalog("", { includeAdministration: false }).map((item) => item.label);
    expect(visible).not.toContain("Configurações");
    expect(visible).not.toContain("Administração");
    expect(visible).toContain("Exportar / Importar");
  });

  it("mantém item Usuário fora da nav; identity fica no slot actions", () => {
    expect(DEFERRED_NAV_ITEMS.map((item) => item.label)).toEqual(["Usuário"]);
    expect(DEFERRED_NAV_ITEMS.every((item) => item.status === "TO_INVENTORY")).toBe(true);
    const topIds = PORTAL_TOPBAR_ITEMS.map((item) => item.id);
    for (const item of DEFERRED_NAV_ITEMS) {
      expect(topIds).not.toContain(item.id);
    }
    expect(topIds).toContain("help");
    expect(topIds).toContain("interaction");
  });

  it("process detail/instance/revision mantêm Meus processos active", () => {
    const processoId = "fa81824d-1c88-4472-bb0b-f91359b517c8";
    const instanciaId = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee";
    const revisaoId = "11111111-2222-3333-4444-555555555555";
    expect(resolvePortalTopBarId(`${TRANSFORMOMETRO_ROUTES.processes}/${processoId}`)).toBe(
      "processes",
    );
    expect(
      resolvePortalTopBarId(
        `${TRANSFORMOMETRO_ROUTES.processes}/${processoId}/instancias/${instanciaId}`,
      ),
    ).toBe("processes");
    expect(
      resolvePortalTopBarId(
        `${TRANSFORMOMETRO_ROUTES.processes}/${processoId}/instancias/${instanciaId}/revisoes/${revisaoId}`,
      ),
    ).toBe("processes");
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
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.myTasks).view).toBe("myTasks");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.interactionRooms).view).toBe(
      "interactionRooms",
    );
    expect(
      parseTransformometroPath(`${TRANSFORMOMETRO_ROUTES.interactionRooms}/room-1`).roomId,
    ).toBe("room-1");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.help).view).toBe("help");
    expect(parseTransformometroPath("/apps/transformometro/ajuda").view).toBe("help");
    expect(parseTransformometroPath("/apps/transformometro/manual").view).toBe("dashboard");
  });

  it("marca Administração nas rotas administrativas e não na home", () => {
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.home)).toBe("home");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.dashboard)).toBe("overview");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.myTasks)).toBe("tasks");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.interactionRooms)).toBe("interaction");
    expect(resolvePortalTopBarId(`${TRANSFORMOMETRO_ROUTES.interactionRooms}/room-1`)).toBe(
      "interaction",
    );
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.processes)).toBe("processes");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.settingsUnits)).toBe("administration");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.data)).toBe("");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.meetingMinutes)).toBe("");
    expect(resolvePortalTopBarId(TRANSFORMOMETRO_ROUTES.help)).toBe("help");
  });

  it("busca só funcionalidades, não entidades", () => {
    expect(filterPortalCatalog("atas").map((item) => item.label)).toContain("Atas");
    expect(filterPortalCatalog("visão geral").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.dashboard,
    );
    expect(filterPortalCatalog("meus processos").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.processes,
    );
    expect(filterPortalCatalog("exportar").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.data,
    );
    expect(filterPortalCatalog("manual").map((item) => item.path)).toContain(TRANSFORMOMETRO_ROUTES.help);
    expect(filterPortalCatalog("sala").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.interactionRooms,
    );
    expect(filterPortalCatalog("").some((item) => item.id === "interaction")).toBe(true);
    expect(filterPortalCatalog("administração", { includeAdministration: false })).toEqual([]);
    expect(filterPortalCatalog("unidades", { includeAdministration: false })).toEqual([]);
    expect(filterPortalCatalog("unidades", { includeAdministration: true }).map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.settingsUnits,
    );
    expect(filterPortalCatalog("ajuda", { includeAdministration: false }).map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.help,
    );
    expect(filterPortalCatalog("favoritos")).toEqual([]);
    expect(filterPortalCatalog("tarefas").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.myTasks,
    );
    expect(filterPortalCatalog("assinatura").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.mySignature,
    );
    expect(filterPortalCatalog("pendentes").map((item) => item.path)).toContain(
      TRANSFORMOMETRO_ROUTES.meetingMinutesPending,
    );
    expect(isPortalSearchShortcut({ key: "k", ctrlKey: true, metaKey: false })).toBe(true);
    expect(isPortalSearchShortcut({ key: "K", ctrlKey: false, metaKey: true })).toBe(true);
    expect(isPortalSearchShortcut({ key: "k", ctrlKey: false, metaKey: false })).toBe(false);
    expect(isPortalSearchShortcut({ key: "Escape", ctrlKey: true, metaKey: false })).toBe(false);
  });

  it("lista processos pelo contrato atual", () => {
    expect(PROCESS_LIST_SUBTITLE).toBe("Processos disponíveis no Portal Transforma+.");
    expect(buildProcessListQuery("  compras ", "ativo")).toEqual({ q: "compras", status: "ativo" });
    expect(buildProcessListQuery("abc", "ativo")).not.toHaveProperty("filial_id");
  });

  it("separa 403, erro e lista vazia", () => {
    const forbidden = processListPlaceholder(403, describeHttpError(403));
    expect(forbidden).not.toBe(PROCESS_LIST_EMPTY_MESSAGE);
    expect(forbidden.toLowerCase()).not.toContain("nenhum processo");
    expect(processListPlaceholder(500, "Serviço indisponível")).toBe("Serviço indisponível");
  });

  it("usa o PageHero das páginas principais", () => {
    expect(PORTAL_PAGE_COPY.home).toMatchObject({
      eyebrow: "Portal Transforma+",
      title: "Bem-vindo ao Portal Transforma+",
      description: "Acompanhe processos, melhorias e resultados da transformação.",
    });
    expect(PORTAL_PAGE_COPY.overview.title).toBe("Visão geral");
    expect(PORTAL_PAGE_COPY.processes).toMatchObject({
      eyebrow: "PROCESSOS",
      title: "Meus processos",
      description: "Processos disponíveis no Portal Transforma+.",
    });
    expect(PORTAL_PAGE_COPY.meetingMinutes).toMatchObject({
      eyebrow: "REGISTROS",
      title: "Atas",
    });
    expect(PORTAL_PAGE_COPY.data).toMatchObject({
      eyebrow: "DADOS",
      title: "Exportar / Importar",
    });
    expect(PORTAL_PAGE_COPY.administration.title).toBe("Administração");
    expect(PORTAL_PAGE_COPY.settings.title).toBe("Configurações");
    expect(PORTAL_PAGE_COPY.help).toMatchObject({
      eyebrow: "Ajuda",
      title: "Manual do usuário",
      description: "Consulte orientações para navegar e utilizar o Portal Transforma+.",
    });
    expect(PORTAL_LAUNCHER_GROUPS.map((group) => group.title)).toEqual([
      "Gestão",
      "Operação",
      "Processos",
      "Registros",
      "Administração",
      "Ajuda",
    ]);
  });

  it("abre o workspace existente sem seções alvo", () => {
    expect(parseTransformometroPath(buildProcessoPath("proc-1")).view).toBe("processo");
    expect(PROCESSO_WORKSPACE_SECTIONS.map((section) => section.id)).not.toContain("sipoc");
  });

  it("o manual cobre o portal e não cita capability inexistente", () => {
    const titles = USER_MANUAL_CONTENT.sections.map((section) => section.title);
    expect(titles).toEqual(
      expect.arrayContaining([
        "Visão geral",
        "Meus processos",
        "Minhas tarefas",
        "Sala de interação",
        "Atas",
        "Exportar / Importar",
        "Administração",
        "Configurações",
      ]),
    );
    const text = JSON.stringify(USER_MANUAL_CONTENT);
    expect(text).not.toMatch(/Keycloak|MCP|GPT Actions|JWT|plugin-ui|WebSocket/);
    expect(text).toContain("A sala reúne a conversa de um processo.");
    expect(text).not.toContain("ainda não faz parte deste portal");
    expect(text).toContain("usuários responsáveis pela administração do Portal");
    for (const section of USER_MANUAL_CONTENT.sections) {
      for (const link of visibleManualLinks(section.links, false)) {
        expect(link.path).toBeTruthy();
        const view = parseTransformometroPath(link.path!).view;
        expect(["home", "help", "dashboard", "processos", "myTasks", "interactionRooms", "atas", "dados"]).toContain(view);
      }
    }
    const adminLinks = USER_MANUAL_CONTENT.sections.flatMap((section) =>
      visibleManualLinks(section.links, true).filter((link) => link.requiresManage),
    );
    expect(adminLinks.map((link) => link.path)).toEqual(
      expect.arrayContaining([
        TRANSFORMOMETRO_ROUTES.administration,
        TRANSFORMOMETRO_ROUTES.settingsUnits,
      ]),
    );
    expect(visibleManualLinks(adminLinks, false)).toEqual([]);
  });

  it("esconde Administração sem manage e não promove Favoritos", () => {
    expect(visiblePortalTopBarItems(false).map((item) => item.label)).toEqual([
      "Início",
      "Visão geral",
      "Sala de interação",
      "Minhas tarefas",
      "Meus processos",
      "Ajuda",
    ]);
    expect(visiblePortalTopBarItems(true).map((item) => item.label)).toContain("Administração");
    expect(visiblePortalTopBarItems(true).map((item) => item.label)).not.toContain("Configurações");
    expect(visiblePortalTopBarItems(true).map((item) => item.label)).not.toContain("Favoritos");

    const home = visiblePortalLauncherGroups(false).flatMap((group) => group.links.map((link) => link.label));
    expect(home).toEqual(
      expect.arrayContaining(["Visão geral", "Meus processos", "Atas", "Exportar / Importar", "Manual do usuário"]),
    );
    expect(home).not.toContain("Administração");
    expect(home).not.toContain("Configurações");
    expect(visiblePortalLauncherGroups(true).flatMap((group) => group.links.map((link) => link.label))).toContain(
      "Administração",
    );
  });
});
