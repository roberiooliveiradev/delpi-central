import { describe, expect, it } from "vitest";

import type { ChatToolCall } from "../../../data/api/chatTypes";

import {
  getProseDeliveryModeFromToolCalls,
  getTemplateProseArchiveFromToolCalls,
  resolveRenderableHumanizedDetailLines,
  resolveRenderableHumanizedLines,
  resolveRenderableTemplateMarkdown,
  shouldBlockTemplateProseMetadata,
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

  it("ignora humanizedSummary.linhas quando proseDeliveryMode é llm", () => {
    const metadata = {
      proseDeliveryMode: "llm",
      humanizedSummary: { titulo: "Status", linhas: ["- linha legada"] },
    };

    expect(resolveRenderableHumanizedLines(metadata)).toEqual([]);
  });

  it("bloqueia linhas quando dataOnlyPresentation", () => {
    const metadata = {
      dataOnlyPresentation: true,
      humanizedSummary: { linhas: ["- legado"], linhas_detalhe: ["detalhe"] },
      textPresentation: { markdown: "### Template" },
    };

    expect(shouldBlockTemplateProseMetadata(metadata)).toBe(true);
    expect(resolveRenderableHumanizedLines(metadata)).toEqual([]);
    expect(resolveRenderableHumanizedDetailLines(metadata)).toEqual([]);
    expect(resolveRenderableTemplateMarkdown(metadata)).toBe("");
  });
});
