import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import {
  getProseDeliveryModeFromToolCalls,
  getTemplateProseArchiveFromToolCalls,
  resolveRenderableHumanizedLines,
  resolveRenderableTemplateMarkdown,
} from "./presentationProseDeliveryReaders";

const decoupledToolCall: ChatToolCall = {
  name: "execute_external_action",
  metadata: {
    ok: true,
    llmProseDecoupled: true,
    proseDeliveryMode: "llm",
    textPresentation: { type: "markdown", markdown: "" },
    templateProseArchive: {
      textPresentationMarkdown: "### Arquivado",
      humanizedSummary: { linhas: ["- linha template"] },
    },
    humanizedSummary: { titulo: "Status", linhas: [] },
  },
};

describe("presentationProseDeliveryReaders", () => {
  it("reads proseDeliveryMode from toolCalls", () => {
    expect(getProseDeliveryModeFromToolCalls([decoupledToolCall])).toBe("llm");
  });

  it("exposes archive without using it for render", () => {
    const archive = getTemplateProseArchiveFromToolCalls([decoupledToolCall]);

    expect(archive?.textPresentationMarkdown).toContain("Arquivado");
    expect(
      resolveRenderableTemplateMarkdown(decoupledToolCall.metadata as Record<string, unknown>),
    ).toBe("");
    expect(
      resolveRenderableHumanizedLines(decoupledToolCall.metadata as Record<string, unknown>),
    ).toEqual([]);
  });
});
