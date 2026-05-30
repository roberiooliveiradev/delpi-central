export type ChatFeedbackReason = {
  id: string;
  label: string;
};

export const CHAT_FEEDBACK_REASONS: ChatFeedbackReason[] = [
  { id: "wrong_data", label: "Dado incorreto" },
  { id: "no_answer", label: "Não respondeu" },
  { id: "missing_source", label: "Faltou fonte" },
  { id: "bad_format", label: "Formato ruim" },
  { id: "too_long", label: "Muito longo" },
  { id: "too_short", label: "Muito curto" },
  { id: "wrong_query", label: "Consulta errada" },
];
