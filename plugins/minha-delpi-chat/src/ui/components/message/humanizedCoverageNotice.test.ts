import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import { resolveHumanizedCoverageNotice } from "./humanizedCoverageNotice";

function fixtureToolCalls(calls: unknown[]): ChatToolCall[] {
  return calls as ChatToolCall[];
}

describe("resolveHumanizedCoverageNotice", () => {
  it("usa limitações de dataAnswer quando não há aviso técnico", () => {
    const notice = resolveHumanizedCoverageNotice(
      fixtureToolCalls([
        {
          metadata: {
            dataAnswer: {
              limitations: ["Esta análise considera apenas os registros desta página."],
            },
          },
        },
      ]),
    );

    expect(notice?.message).toContain("registros desta página");
    expect(notice?.messages).toContain(
      "Esta análise considera apenas os registros desta página.",
    );
  });

  it("mescla aviso técnico com limitações humanizadas sem duplicar", () => {
    const notice = resolveHumanizedCoverageNotice(
      fixtureToolCalls([
        {
          metadata: {
            dataCoverageNotice: {
              kind: "pagination",
              message: "Parcial · 25 de 265 registros.",
            },
            dataAnswer: {
              limitations: ["Esta análise considera apenas os registros desta página."],
            },
          },
        },
      ]),
    );

    expect(notice?.message).toContain("Parcial");
    expect(notice?.message).toContain("registros desta página");
    expect(notice?.messages?.length).toBeGreaterThanOrEqual(2);
  });
});
