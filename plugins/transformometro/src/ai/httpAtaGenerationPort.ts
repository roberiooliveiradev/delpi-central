import type { AtaGenerationPort, AtaGenerationRequest } from "./ataGenerationPort";
import { generateAtaFromTranscript } from "../data/api/transformometroAtaApi";

/** Port HTTP real — POST /atas/generate-from-transcript via transformometroAtaApi. */
export function createHttpAtaGenerationPort(
  getAccessToken: () => string | undefined,
): AtaGenerationPort {
  return {
    generateFromTranscript(request: AtaGenerationRequest) {
      return generateAtaFromTranscript(request, getAccessToken);
    },
  };
}
