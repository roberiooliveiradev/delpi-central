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

  it("monta href canônico EN de qualidade/métricas", () => {
    expect(
      buildAdminHref({ section: "quality", subTab: "metrics" }),
    ).toBe("/apps/minha-delpi-chat/admin/quality/metrics/overview");
  });

  it("parseia segmentos EN e PT de conhecimento", () => {
    expect(parseAdminPathSegments(["knowledge", "guidelines"])).toEqual({
      section: "knowledge",
      subTab: "guidelines",
    });
    expect(parseAdminPathSegments(["conhecimento", "diretrizes"])).toEqual({
      section: "knowledge",
      subTab: "guidelines",
    });
  });

  it("monta e parseia aprendizagem com página padrão (EN + alias PT)", () => {
    expect(buildAdminHref({ section: "knowledge", subTab: "learning" })).toBe(
      "/apps/minha-delpi-chat/admin/knowledge/learning/pipeline",
    );
    expect(parseAdminPathSegments(["knowledge", "learning"])).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "pipeline",
    });
    expect(parseAdminPathSegments(["conhecimento", "aprendizagem"])).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "pipeline",
    });
  });

  it("monta EN e parseia alias PT de página interna", () => {
    expect(
      buildAdminHref({
        section: "knowledge",
        subTab: "learning",
        page: "vocabulary",
      }),
    ).toBe("/apps/minha-delpi-chat/admin/knowledge/learning/vocabulary");

    expect(
      parseAdminPathSegments(["conhecimento", "aprendizagem", "memoria"]),
    ).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "memory",
    });
    expect(
      parseAdminPathSegments(["knowledge", "learning", "memory"]),
    ).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "memory",
    });
  });

  it("trata /admin/agents e /admin/agentes sem sub-aba como painel", () => {
    expect(parseAdminPathSegments(["agents"])).toEqual({
      section: "overview",
    });
    expect(parseAdminPathSegments(["agentes"])).toEqual({
      section: "overview",
    });
  });

  it("ignora sub-aba desconhecida", () => {
    expect(parseAdminPathSegments(["quality", "inexistente"])).toEqual({
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

  it("parseia /admin/agents incompleto como painel", () => {
    expect(parseChatRoute("/apps/minha-delpi-chat/admin/agents")).toEqual({
      kind: "admin",
      nav: { section: "overview" },
    });
  });

  it("parseia plataforma/inteligencia (PT) e platform/intelligence (EN)", () => {
    expect(
      parseChatRoute("/apps/minha-delpi-chat/admin/plataforma/inteligencia"),
    ).toEqual({
      kind: "admin",
      nav: { section: "platform", subTab: "intelligence" },
    });
    expect(
      parseChatRoute("/apps/minha-delpi-chat/admin/platform/intelligence"),
    ).toEqual({
      kind: "admin",
      nav: { section: "platform", subTab: "intelligence" },
    });
  });

  it("parseia agente admin por uuid legado PT e canônico EN", () => {
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
    expect(buildAdminAgentHref(AGENT_ID)).toBe(
      `/apps/minha-delpi-chat/admin/agents/specialization/${AGENT_ID}`,
    );
  });

  it("monta href do painel", () => {
    expect(buildChatHref({ kind: "admin", nav: { section: "overview" } })).toBe(
      "/apps/minha-delpi-chat/admin",
    );
  });
});
