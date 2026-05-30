export type ChatFeedbackReason = {
  id: string;
  label: string;
};

export const CHAT_FEEDBACK_REASONS: ChatFeedbackReason[] = [
  { id: "lost_context", label: "Perdeu o contexto" },
  { id: "wrong_product", label: "Usou produto errado" },
  { id: "bad_format", label: "Não seguiu o formato pedido" },
  { id: "forgot_previous", label: "Não lembrou a resposta anterior" },
  { id: "wrong_query", label: "Consulta errada" },
  { id: "too_long", label: "Resposta muito longa" },
  { id: "too_technical", label: "Resposta muito técnica" },
  { id: "wrong_data", label: "Dados incorretos" },
  { id: "missing_source", label: "Faltou fonte" },
  { id: "no_answer", label: "Não respondeu" },
  { id: "too_short", label: "Muito curto" },
  { id: "other", label: "Outro" },
];
