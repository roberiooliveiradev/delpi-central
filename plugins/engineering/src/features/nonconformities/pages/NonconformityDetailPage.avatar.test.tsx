/** PRC-AUDIT — avatar canônico do Portal no detalhe NC: histórico
 * usa actor_user_id real do ledger; identificação deriva o id dos
 * eventos (created→criador, updated mais recente→atualizador);
 * campos sem id (executado/liberado por — labels livres) seguem em
 * iniciais honestas. */

import { readFileSync } from "fs";
import { resolve } from "path";
import { describe, expect, it } from "vitest";

const SRC = readFileSync(
  resolve(__dirname, "NonconformityDetailPage.tsx"),
  "utf8",
);

describe("NonconformityDetailPage — avatar canônico (Core via BFF)", () => {
  it("histórico resolve fotos por actor_user_id via hook BFF", () => {
    expect(SRC).toMatch(/useParticipantAvatarUrls/);
    expect(SRC).toMatch(/map\(\(e\) => e\.actor_user_id\)/);
    expect(SRC).toMatch(/toTimelineItem\(event, avatarByUserId\)/);
    expect(SRC).toMatch(/src=\{avatarByUserId\?\.get\(event\.actor_user_id\)\}/);
  });

  it("identificação deriva user_id dos eventos de auditoria", () => {
    expect(SRC).toMatch(/event_type === "created"/);
    expect(SRC).toMatch(/event_type === "updated"/);
    expect(SRC).toMatch(
      /detailFields\(record, avatarByUserId, history\)/,
    );
  });

  it("campos sem id auditável permanecem em iniciais (sem foto errada)", () => {
    // executed_by/released_by são labels livres do registro — não
    // recebem src derivado (avatarFor só aparece em created/updated).
    const executed = SRC.indexOf('label: "Executado por"');
    const created = SRC.indexOf('label: "Criado por"');
    const executedBlock = SRC.slice(executed, created);
    expect(executedBlock).not.toMatch(/avatarFor/);
    const released = SRC.indexOf('label: "Liberado por"');
    const releasedBlock = SRC.slice(released, created);
    expect(releasedBlock).not.toMatch(/avatarFor/);
  });
});
