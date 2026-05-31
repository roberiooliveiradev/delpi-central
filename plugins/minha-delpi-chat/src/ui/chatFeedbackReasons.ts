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
  { id: "wrong_intent", label: "Entendeu a intenção errada" },
  { id: "routing_wrong_intent", label: "Interpretou errado o pedido" },
  { id: "routing_wrong_api", label: "Chamou consulta errada" },
  { id: "routing_should_api", label: "Deveria ter usado API/dados" },
  { id: "routing_should_not_api", label: "Não deveria ter usado API" },
  { id: "routing_should_web", label: "Deveria ter pesquisado na web" },
  { id: "routing_unneeded_web", label: "Pesquisou na web sem necessidade" },
  { id: "routing_lost_context", label: "Perdeu contexto no roteamento" },
  { id: "routing_repeated_question", label: "Perguntou algo que já informei" },
  { id: "routing_wrong_format", label: "Usou formato errado (tabela/gráfico)" },
  { id: "routing_missed_text_task", label: "Não entendeu que era tarefa de texto" },
  { id: "too_long", label: "Resposta muito longa" },
  { id: "too_technical", label: "Resposta muito técnica" },
  { id: "wrong_data", label: "Dados incorretos" },
  { id: "missing_source", label: "Faltou fonte" },
  { id: "no_answer", label: "Não respondeu" },
  { id: "too_short", label: "Muito curto" },
  { id: "other", label: "Outro" },
];
