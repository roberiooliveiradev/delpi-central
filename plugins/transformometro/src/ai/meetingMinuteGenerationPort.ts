/**
 * Port de geração de ata a partir de transcrição (Kimi via API Transformômetro).
 *
 * Troque o port ativo com setMeetingMinuteGenerationPort (ex.: HTTP no editor).
 * Endpoint: POST /transformometro/atas/generate-from-transcript
 */

export type AtaGenerationSource = "docx" | "manual";

export type AtaGenerationRequest = {
  unitCode: string;
  meetingDate: string;
  title?: string;
  transcriptHtml: string;
  source: AtaGenerationSource;
};

export type AtaGenerationResult = {
  agendaHtml: string;
  bodyHtml: string;
  decisionsHtml: string;
  pendingHtml: string;
  observationsHtml: string;
  title?: string;
};

export type MeetingMinuteGenerationPort = {
  generateFromTranscript(request: AtaGenerationRequest): Promise<AtaGenerationResult>;
};

export const ATA_GENERATION_UNAVAILABLE_MESSAGE =
  "Geração por IA ainda não disponível. Em breve com Kimi K3.";

export const stubMeetingMinuteGenerationPort: MeetingMinuteGenerationPort = {
  async generateFromTranscript() {
    throw new Error(ATA_GENERATION_UNAVAILABLE_MESSAGE);
  },
};

/** Ponto único de chamada do MFE — trocar o stub pelo client HTTP quando a API existir. */
let activePort: MeetingMinuteGenerationPort = stubMeetingMinuteGenerationPort;

export function setMeetingMinuteGenerationPort(port: MeetingMinuteGenerationPort): void {
  activePort = port;
}

export function resetMeetingMinuteGenerationPort(): void {
  activePort = stubMeetingMinuteGenerationPort;
}

export function requestAtaGenerationFromTranscript(
  request: AtaGenerationRequest,
): Promise<AtaGenerationResult> {
  return activePort.generateFromTranscript(request);
}
