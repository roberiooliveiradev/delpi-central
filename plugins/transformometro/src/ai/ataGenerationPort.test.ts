import { describe, expect, it } from "vitest";

import {
  ATA_GENERATION_UNAVAILABLE_MESSAGE,
  requestAtaGenerationFromTranscript,
  resetAtaGenerationPort,
} from "./ataGenerationPort";

describe("ataGenerationPort", () => {
  it("stub rejeita com mensagem estável", async () => {
    resetAtaGenerationPort();
    await expect(
      requestAtaGenerationFromTranscript({
        unitCode: "01",
        meetingDate: "2026-07-28",
        transcriptHtml: "<p>Transcrição</p>",
        source: "docx",
      }),
    ).rejects.toThrow(ATA_GENERATION_UNAVAILABLE_MESSAGE);
  });
});
