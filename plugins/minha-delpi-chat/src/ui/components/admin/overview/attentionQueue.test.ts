import { describe, expect, it } from "vitest";

import { buildAttentionQueue } from "./attentionQueue";

describe("buildAttentionQueue", () => {
  it("retorna vazio quando não há sinais", () => {
    expect(
      buildAttentionQueue({
        toolHealth: { items: [{ id: "llm", label: "LLM", status: "ok", description: "ok" }] },
        security: {
          windowHours: 24,
          since: "2026-01-01T00:00:00Z",
          blockedCount: 0,
          flaggedCount: 0,
          scannedCount: 0,
          totalEvents: 0,
          flagDistribution: [],
        },
        learning: null,
        evaluations: null,
        metrics: { sessions: 10, messages: 20, knowledgeDocuments: 0, activeKnowledgeDocuments: 0, knowledgeChunks: 0, auditLogs: 0, recentToolCalls24h: 0, recentErrors24h: 0, errorRate24h: 0.01 },
      }),
    ).toEqual([]);
  });

  it("prioriza ferramenta em erro e regressão falhando", () => {
    const items = buildAttentionQueue({
      toolHealth: {
        items: [
          { id: "core", label: "Core API", status: "error", description: "timeout" },
          { id: "catalog", label: "Catálogo", status: "warning", description: "lento" },
        ],
      },
      security: {
        windowHours: 24,
        since: "2026-01-01T00:00:00Z",
        blockedCount: 2,
        flaggedCount: 1,
        scannedCount: 10,
        totalEvents: 12,
        flagDistribution: [],
      },
      learning: {
        windowHours: 24,
        candidates: {
          total: 5,
          byStatus: { pending: 3 },
          byType: {},
          pendingHighConfidence: 1,
          recentCreated: 2,
          avgPendingConfidence: 0.8,
        },
        vocabulary: { total: 0, approved: 0, activeApproved: 0, byType: {} },
        evaluation: {
          total: 10,
          active: 8,
          disabled: 0,
          failing: 4,
          passing: 4,
          neverRun: 0,
          byCategory: {},
        },
        funnel: {
          created: 5,
          recentCreated: 2,
          pending: 3,
          approved: 1,
          rejected: 0,
          promoted: 0,
          approvalRate: null,
          promotionRate: null,
        },
        highlights: {
          termDefinitions: 0,
          normalizationRules: 0,
          pendingHighConfidence: 1,
          learnedTermsActive: 0,
        },
      },
      evaluations: {
        total: 20,
        averageScore: 2.5,
        helpfulRate: 0.4,
        distribution: [],
        recent24h: 3,
      },
      metrics: {
        sessions: 100,
        messages: 400,
        knowledgeDocuments: 10,
        activeKnowledgeDocuments: 8,
        knowledgeChunks: 100,
        auditLogs: 50,
        recentToolCalls24h: 200,
        recentErrors24h: 30,
        errorRate24h: 0.2,
      },
    });

    expect(items[0]?.severity).toBe("critical");
    expect(items.map((item) => item.id)).toEqual(
      expect.arrayContaining([
        "tool:core",
        "tool:catalog",
        "security:blocked",
        "learning:pending",
        "learning:eval-failing",
        "metrics:error-rate",
        "evaluations:low-score",
      ]),
    );
    expect(items.find((item) => item.id === "learning:pending")?.nav).toEqual({
      section: "knowledge",
      subTab: "learning",
      page: "candidates",
    });
    expect(items.find((item) => item.id === "metrics:error-rate")?.severity).toBe(
      "critical",
    );
  });

  it("não cria item de taxa de erro abaixo do limiar", () => {
    const items = buildAttentionQueue({
      metrics: {
        sessions: 10,
        messages: 20,
        knowledgeDocuments: 0,
        activeKnowledgeDocuments: 0,
        knowledgeChunks: 0,
        auditLogs: 0,
        recentToolCalls24h: 5,
        recentErrors24h: 0,
        errorRate24h: 0.04,
      },
    });
    expect(items.some((item) => item.id === "metrics:error-rate")).toBe(false);
  });
});
