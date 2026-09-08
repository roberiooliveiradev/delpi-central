export const WIZARD_STEPS = [
  { id: "recipient", label: "Destinatário" },
  { id: "invoiceType", label: "Tipo de NF" },
  { id: "items", label: "Itens" },
  { id: "freight", label: "Transporte" },
  { id: "extras", label: "Adicionais" },
  { id: "review", label: "Conferência" },
] as const;

export type WizardStepDefinition = (typeof WIZARD_STEPS)[number];
