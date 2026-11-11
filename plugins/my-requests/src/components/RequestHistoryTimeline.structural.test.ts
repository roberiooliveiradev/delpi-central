import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { RequestHistoryTimeline } from "./RequestHistoryTimeline";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

describe("RequestHistoryTimeline — renderer único de histórico", () => {
  it("é um componente funcional render-only (não consulta APIs)", () => {
    expect(typeof RequestHistoryTimeline).toBe("function");
    const src = read("components/RequestHistoryTimeline.tsx");
    expect(src).not.toMatch(/requestsApi|engineeringApi|prcApi|fetch\(/);
    // Recebe itens normalizados e renderiza sobre a timeline oficial.
    expect(src).toMatch(/MyRequestsTimeline/);
    expect(src).toMatch(/PersonIdentity/);
    expect(src).toMatch(/MyRequestsEmptyState/);
    expect(src).toMatch(/MyRequestsStateBanner/);
  });

  it("preserva a mesma estrutura visual do histórico tradicional", () => {
    const src = read("components/RequestHistoryTimeline.tsx");
    expect(src).toMatch(/my-requests-timeline-detail/);
    expect(src).toMatch(/my-requests-timeline-detail__reason/);
    // título + data/hora + identidade + transição + justificativa + meta
    expect(src).toMatch(/item\.title/);
    expect(src).toMatch(/item\.timeLabel/);
    expect(src).toMatch(/item\.transition/);
    expect(src).toMatch(/item\.detailText/);
    expect(src).toMatch(/item\.metaText/);
    expect(src).toMatch(/item\.actorUserId/);
    expect(src).toMatch(/avatarByUserId/);
  });

  it("timeline tradicional consome o renderer compartilhado", () => {
    const panel = read("components/TimelinePanel.tsx");
    expect(panel).toMatch(/RequestHistoryTimeline/);
    expect(panel).not.toMatch(/<MyRequestsTimeline/);
    // normalização da Requests API permanece no container tradicional
    expect(panel).toMatch(/timelineEventTitle/);
    expect(panel).toMatch(/timelineEventJustification/);
    expect(panel).toMatch(/formatDateTimePtBr/);
  });

  it("histórico PRC consome o MESMO renderer — sem timeline própria", () => {
    const prc = read("features/product-registration/PrcCasePage.tsx");
    expect(prc).toMatch(/RequestHistoryTimeline/);
    expect(prc).not.toMatch(/<MyRequestsTimeline/);
    // normalização PRC continua no mapper compartilhado do kit
    expect(prc).toMatch(/prcTimelineItemViews/);
    // identidade e avatar seguem o mecanismo oficial
    expect(prc).toMatch(/useParticipantAvatarUrls/);
    expect(prc).toMatch(/actorUserId/);
    expect(prc).toMatch(/actorLabel/);
    // transição, motivo e detalhes secundários preservados
    expect(prc).toMatch(/transition: v\.transition/);
    expect(prc).toMatch(/detailText: v\.reasonText/);
    expect(prc).toMatch(/metaText: v\.metaText/);
  });
});
