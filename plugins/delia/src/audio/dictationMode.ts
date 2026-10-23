/**
 * Dual-mode dictation selection (PO decision 2026-10-23, spec 123 §12).
 *
 * "batch" = Gravar e transcrever — dictation.transcription.v1, the
 * product default: record first, transcribe once, review, send.
 * "live" = Transcrição em tempo real — dictation.incremental.v1,
 * explicit opt-in only; incremental backend admission never selects it.
 *
 * Presentation state only — mount/session scoped, never persisted
 * (no web storage, Personal Memory or Core settings per the PO
 * decision).
 */
export type DictationMode = "batch" | "live";

export const DEFAULT_DICTATION_MODE: DictationMode = "batch";
