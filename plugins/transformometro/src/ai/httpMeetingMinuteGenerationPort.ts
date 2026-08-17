import type { MeetingMinuteGenerationPort, AtaGenerationRequest } from "./meetingMinuteGenerationPort";
import { generateAtaFromTranscript } from "../data/api/transformometroMeetingMinutesApi";

/** Port HTTP real — POST /atas/generate-from-transcript via transformometroMeetingMinutesApi. */
export function createHttpMeetingMinuteGenerationPort(
  getAccessToken: () => string | undefined,
): MeetingMinuteGenerationPort {
  return {
    generateFromTranscript(request: AtaGenerationRequest) {
      return generateAtaFromTranscript(request, getAccessToken);
    },
  };
}
