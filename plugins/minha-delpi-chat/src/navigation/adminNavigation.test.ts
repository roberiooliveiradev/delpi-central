import { describe, expect, it } from "vitest";

import {
  buildAdminAgentHref,
  buildAdminHref,
  legacyTabToNav,
  normalizeAdminNav,
  parseAdminPathSegments,
} from "./adminNavigation";
import { buildChatHref, parseChatRoute } from "./chatRoutes";

const AGENT_ID = "b185b233-b06a-4d23-8450-6ac3c0f7428d";

describe("adminNavigation", () => {
  it("normaliza painel sem sub-aba", () => {
    expect(normalizeAdminNav({ section: "overview" })).toEqual({
      section: "overview",
    });
  });

  it("mapeia aba legada skills para comportamentos", () => {
    expect(legacyTabToNav("skills")).toEqual({
      section: "knowledge",
      subTab: "behaviors",
    });
  });

  it("monta href de qualidade/métricas", () => {
    expect(
      buildAdminHref({ section: "quality", subTab: "metrics" }),
    ).toBe("/apps/minha-delpi-chat/admin/qualidade/metricas");
  });

  it("parseia segmentos de conhecimento", () => {
    expect(parseAdminPathSegments(["conhecimento", "diretrizes"])).toEqual({
      section: "knowledge",
      subTab: "guidelines",
    });
  });

  it("monta e parseia a sub-aba de aprendizagem com página padrão", () => {
    expect(buildAdminHref({ section: "knowledge", subTab: "learning" })).toBe(
      "/apps/minha-delpi-chat/admin/conhecimento/aprendizagem/pipeline",
    );
    expect(parseAdminPathSegments(["conhecimento", "aprendizagem"])).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "pipeline",
    });
  });

  it("monta e parseia página interna de aprendizagem", () => {
    expect(
      buildAdminHref({
        section: "knowledge",
        subTab: "learning",
        page: "vocabulary",
      }),
    ).toBe("/apps/minha-delpi-chat/admin/conhecimento/aprendizagem/vocabulario");

    expect(
      parseAdminPathSegments(["conhecimento", "aprendizagem", "memoria"]),
    ).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "memory",
    });
  });

  it("trata /admin/agentes sem sub-aba como painel", () => {
    expect(parseAdminPathSegments(["agentes"])).toEqual({
      section: "overview",
    });
  });

  it("ignora sub-aba desconhecida", () => {
    expect(parseAdminPathSegments(["qualidade", "inexistente"])).toEqual({
      section: "overview",
    });
  });
});

describe("chatRoutes admin", () => {
  it("parseia /admin como painel", () => {
    expect(parseChatRoute("/apps/minha-delpi-chat/admin")).toEqual({
      kind: "admin",
      nav: { section: "overview" },
    });
  });

  it("parseia /admin/agentes incompleto como painel", () => {
    expect(parseChatRoute("/apps/minha-delpi-chat/admin/agentes")).toEqual({
      kind: "admin",
      nav: { section: "overview" },
    });
  });

  it("parseia plataforma/inteligencia", () => {
    expect(
      parseChatRoute("/apps/minha-delpi-chat/admin/plataforma/inteligencia"),
    ).toEqual({
      kind: "admin",
      nav: { section: "platform", subTab: "intelligence" },
    });
  });

  it("parseia agente admin por uuid legado e canônico", () => {
    expect(
      parseChatRoute(`/apps/minha-delpi-chat/admin/agentes/${AGENT_ID}`),
    ).toEqual({
      kind: "admin-agent",
      agentId: AGENT_ID,
    });

    expect(parseChatRoute(buildAdminAgentHref(AGENT_ID))).toEqual({
      kind: "admin-agent",
      agentId: AGENT_ID,
    });
  });

  it("monta href do painel", () => {
    expect(buildChatHref({ kind: "admin", nav: { section: "overview" } })).toBe(
      "/apps/minha-delpi-chat/admin",
    );
  });
});
