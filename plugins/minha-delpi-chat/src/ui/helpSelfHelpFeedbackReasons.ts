export type HelpSelfHelpFeedbackReason = {
  id: string;
  label: string;
};

/** Playbook 04 §32 — motivos quando a ajuda não foi útil. */
export const HELP_SELF_HELP_FEEDBACK_REASONS: HelpSelfHelpFeedbackReason[] = [
  { id: "help_not_found", label: "Não encontrei o que queria" },
  { id: "help_confusing", label: "Explicação confusa" },
  { id: "help_example_failed", label: "Exemplo não funcionou" },
  { id: "help_unavailable", label: "Funcionalidade indisponível" },
  { id: "help_missing_steps", label: "Faltou passo a passo" },
  { id: "help_outdated", label: "Informação desatualizada" },
];
