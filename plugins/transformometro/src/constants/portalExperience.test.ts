import { describe, expect, it } from "vitest";

import { describeHttpError } from "../utils/apiErrorMessage";
import { buildProcessoPath, parseTransformometroPath } from "../utils/routeParser";
import { TRANSFORMOMETRO_ROUTES } from "./routes";
import {
  PORTAL_HOME_LINKS,
  PORTAL_HOME_SUBTITLE,
  PORTAL_NAV_LINKS,
  PORTAL_PRODUCT_NAME,
  PORTAL_WELCOME,
  PROCESS_LIST_EMPTY_MESSAGE,
  PROCESS_LIST_SUBTITLE,
  buildProcessListQuery,
  isPortalNavActive,
  processListPlaceholder,
} from "./portalExperience";
import { PROCESSO_WORKSPACE_SECTIONS } from "../ui/processes/processWorkspaceNav";

describe("Portal Transforma+ wave 1", () => {
  it("marca o produto na experiência sem virar dashboard", () => {
    expect(PORTAL_PRODUCT_NAME).toBe("Portal Transforma+");
    expect(PORTAL_WELCOME).toBe("Bem-vindo ao Portal Transforma+");
    expect(PORTAL_HOME_SUBTITLE.toLowerCase()).not.toContain("kpi");
    expect(PORTAL_HOME_LINKS.map((link) => link.label)).not.toContain("Início");
  });

  it("abre Início no launcher e mantém Visão geral no dashboard", () => {
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.home).view).toBe("home");
    expect(parseTransformometroPath(TRANSFORMOMETRO_ROUTES.dashboard).view).toBe("dashboard");
    expect(parseTransformometroPath("/apps/transformometro/").view).toBe("home");
  });

  it("expõe só a navegação aprovada", () => {
    expect(PORTAL_NAV_LINKS.map((link) => link.label)).toEqual([
      "Início",
      "Visão geral",
      "Meus processos",
      "Atas",
      "Configurações",
      "Exportar/Importar",
    ]);
    expect(PORTAL_NAV_LINKS.map((link) => link.path)).toEqual([
      TRANSFORMOMETRO_ROUTES.home,
      TRANSFORMOMETRO_ROUTES.dashboard,
      TRANSFORMOMETRO_ROUTES.processes,
      TRANSFORMOMETRO_ROUTES.meetingMinutes,
      TRANSFORMOMETRO_ROUTES.settingsUnits,
      TRANSFORMOMETRO_ROUTES.data,
    ]);
    const joined = PORTAL_NAV_LINKS.map((link) => link.path).join(" ");
    expect(joined).not.toMatch(/diagnostic|portfolio|tasks|ajuda/);
  });

  it("não trata a home como Visão geral ativa", () => {
    expect(isPortalNavActive(TRANSFORMOMETRO_ROUTES.home, TRANSFORMOMETRO_ROUTES.home)).toBe(true);
    expect(isPortalNavActive(TRANSFORMOMETRO_ROUTES.dashboard, TRANSFORMOMETRO_ROUTES.home)).toBe(
      false,
    );
    expect(
      isPortalNavActive(TRANSFORMOMETRO_ROUTES.dashboard, TRANSFORMOMETRO_ROUTES.dashboard),
    ).toBe(true);
  });

  it("lista processos pelo contrato atual, sem ownership nem filtro inventado", () => {
    expect(PROCESS_LIST_SUBTITLE).toBe("Processos disponíveis no seu escopo de acesso.");
    expect(buildProcessListQuery("  compras ", "ativo")).toEqual({ q: "compras", status: "ativo" });
    expect(buildProcessListQuery(" ", "")).toEqual({});
    expect(buildProcessListQuery("abc", "ativo")).not.toHaveProperty("gestor_responsavel");
    expect(buildProcessListQuery("abc", "ativo")).not.toHaveProperty("filial_id");
  });

  it("separa 403, erro e lista vazia", () => {
    const forbidden = processListPlaceholder(403, describeHttpError(403));
    const failed = processListPlaceholder(500, "Serviço indisponível");
    expect(forbidden).not.toBe(PROCESS_LIST_EMPTY_MESSAGE);
    expect(forbidden.toLowerCase()).not.toContain("nenhum processo");
    expect(failed).toBe("Serviço indisponível");
    expect(failed).not.toBe(PROCESS_LIST_EMPTY_MESSAGE);
    expect(processListPlaceholder(null, null)).toBe(PROCESS_LIST_EMPTY_MESSAGE);
  });

  it("abre o workspace existente e não cria seções alvo", () => {
    const path = buildProcessoPath("proc-1");
    expect(parseTransformometroPath(path).view).toBe("processo");
    expect(PROCESSO_WORKSPACE_SECTIONS.map((section) => section.id)).toEqual([
      "visao-geral",
      "dados",
      "mapeamento",
      "diagrama",
      "arquivos",
      "melhorias",
      "priorizacao",
      "timeline",
    ]);
  });
});
