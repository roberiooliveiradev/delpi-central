/** Modelos rápidos no menu + (Fase 3 — textos administrativos). */
export type ChatTextTemplate = {
  label: string;
  /** Texto inserido no composer (usuário completa o restante). */
  draft: string;
};

export const CHAT_TEXT_TEMPLATES: ChatTextTemplate[] = [
  {
    label: "Corrigir",
    draft: "Corrija o texto abaixo mantendo o sentido:\n\n",
  },
  {
    label: "Tom formal",
    draft: "Deixe mais formal e profissional:\n\n",
  },
  {
    label: "Resumir",
    draft: "Resuma em tópicos objetivos:\n\n",
  },
  {
    label: "Traduzir (EN)",
    draft: "Traduza para inglês:\n\n",
  },
  {
    label: "E-mail",
    draft:
      "Escreva um e-mail profissional para [destinatário] sobre [assunto]. Tom cordial e objetivo.",
  },
  {
    label: "Comunicado",
    draft:
      "Escreva um comunicado interno sobre [assunto]. Inclua contexto, impacto e próximos passos.",
  },
];
