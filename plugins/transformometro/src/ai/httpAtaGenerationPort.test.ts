import { describe, expect, it, vi } from "vitest";

import { createHttpAtaGenerationPort } from "./httpAtaGenerationPort";
import * as ataApi from "../data/api/transformometroAtaApi";

describe("createHttpAtaGenerationPort", () => {
  it("delega para generateAtaFromTranscript com o getAccessToken", async () => {
    const getAccessToken = () => "token-test";
    const spy = vi.spyOn(ataApi, "generateAtaFromTranscript").mockResolvedValue({
      agendaHtml: "<p>pauta</p>",
      bodyHtml: "<p>corpo</p>",
      decisionsHtml: "<p>dec</p>",
      pendingHtml: "<p>pend</p>",
      observationsHtml: "<p>obs</p>",
      title: "Título",
    });

    const port = createHttpAtaGenerationPort(getAccessToken);
    const request = {
      unitCode: "01",
      meetingDate: "2026-07-28",
      transcriptHtml: "<p>x</p>",
      source: "docx" as const,
    };
    const result = await port.generateFromTranscript(request);

    expect(spy).toHaveBeenCalledWith(request, getAccessToken);
    expect(result.bodyHtml).toBe("<p>corpo</p>");
    spy.mockRestore();
  });
});
