import { describe, expect, it } from "vitest";

import {
  ATA_GENERATION_UNAVAILABLE_MESSAGE,
  requestAtaGenerationFromTranscript,
  resetMeetingMinuteGenerationPort,
} from "./meetingMinuteGenerationPort";

describe("meetingMinuteGenerationPort", () => {
  it("stub rejeita com mensagem estável", async () => {
    resetMeetingMinuteGenerationPort();
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
