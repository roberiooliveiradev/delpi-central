import { describe, expect, it } from "vitest";

import { buildAdminHref, legacyTabToNav, parseAdminRouteSegments } from "./adminNavigation";
import { buildChatHref, parseChatRoute } from "./chatRoutes";

const AGENT_ID = "b185b233-b06a-4d23-8450-6ac3c0f7428d";

describe("adminNavigation", () => {
  it("abre painel em /admin", () => {
    expect(buildAdminHref({ section: "overview" })).toBe("/apps/minha-delpi-chat/admin");
    expect(parseChatRoute("/apps/minha-delpi-chat/admin")).toEqual({
      kind: "admin",
      section: "overview",
      subTab: null,
      agentId: null,
    });
  });

  it("deep link conhecimento/documentos", () => {
    const href = buildAdminHref({ section: "knowledge", subTab: "documents" });

    expect(href).toBe("/apps/minha-delpi-chat/admin/conhecimento/documentos");
    expect(parseChatRoute(href)).toMatchObject({
      kind: "admin",
      section: "knowledge",
      subTab: "documents",
    });
  });

  it("preserva agente em especializacao", () => {
    const href = buildAdminHref({
      section: "agents",
      subTab: "specialization",
      agentId: AGENT_ID,
    });

    expect(href).toBe(
      `/apps/minha-delpi-chat/admin/agentes/especializacao/${AGENT_ID}`,
    );
    expect(parseChatRoute(href)).toEqual({
      kind: "admin-agent",
      agentId: AGENT_ID,
      section: "agents",
      subTab: "specialization",
    });
  });

  it("compatibilidade rota legada /admin/agentes/:id", () => {
    expect(parseAdminRouteSegments(["agentes", AGENT_ID])).toEqual({
      agentId: AGENT_ID,
    });
    expect(buildChatHref({ kind: "admin-agent", agentId: AGENT_ID })).toBe(
      `/apps/minha-delpi-chat/admin/agentes/especializacao/${AGENT_ID}`,
    );
  });

  it("mapeia tab legada metrics para qualidade", () => {
    expect(legacyTabToNav("metrics")).toMatchObject({
      section: "quality",
      subTab: "metrics",
    });
  });

  it("aceita slug legado /admin/metrics", () => {
    expect(parseChatRoute("/apps/minha-delpi-chat/admin/metrics")).toMatchObject({
      kind: "admin",
      section: "quality",
      subTab: "metrics",
    });
  });

  it("aceita slug legado /admin/skills", () => {
    expect(parseChatRoute("/apps/minha-delpi-chat/admin/skills")).toMatchObject({
      kind: "admin",
      section: "knowledge",
      subTab: "behaviors",
    });
  });

  it("deep links das seis áreas do admin", () => {
    const cases = [
      { section: "knowledge" as const, subTab: "behaviors" as const, path: "/conhecimento/comportamentos" },
      { section: "agents" as const, subTab: "simulation" as const, path: "/agentes/simulacao" },
      { section: "quality" as const, subTab: "evaluations" as const, path: "/qualidade/avaliacoes" },
      { section: "platform" as const, subTab: "intelligence" as const, path: "/plataforma/inteligencia" },
      { section: "governance" as const, subTab: "security" as const, path: "/governanca/seguranca" },
      { section: "governance" as const, subTab: "audit" as const, path: "/governanca/auditoria" },
    ];

    for (const item of cases) {
      const href = buildAdminHref({ section: item.section, subTab: item.subTab });

      expect(href).toBe(`/apps/minha-delpi-chat/admin${item.path}`);
      expect(parseChatRoute(href)).toMatchObject({
        kind: "admin",
        section: item.section,
        subTab: item.subTab,
      });
    }
  });
});
