/**
 * Contratos da Pesquisa de Satisfação de Clientes (commercial-api `/satisfaction-surveys/*`).
 * Fonte de verdade: `commercial-api/.../satisfaction_survey_schemas.py` e
 * `manage_satisfaction_surveys.py` — o frontend só consome, nunca recalcula.
 */

/** Situação da janela, derivada pelo backend. */
export type SatisfactionCampaignStatus = "scheduled" | "open" | "closed";

export type SatisfactionCounts = {
  participants: number;
  responded: number;
  pending: number;
};

export type SatisfactionCampaign = {
  id: string;
  name: string;
  starts_at: string;
  ends_at: string;
  status: SatisfactionCampaignStatus;
  questionnaire_version: string;
  invite_subject: string;
  invite_body: string;
  created_by_user_id?: string | null;
  created_at: string;
  updated_at: string;
  /** Concorrência otimista — enviar de volta em PATCH. */
  version: number;
  counts: SatisfactionCounts;
};

export type SatisfactionCampaignList = {
  items: SatisfactionCampaign[];
};

export type SatisfactionCreateCampaignInput = {
  name: string;
  starts_at: string;
  ends_at: string;
  invite_subject?: string | null;
  invite_body?: string | null;
};

export type SatisfactionUpdateCampaignInput = {
  version: number;
  name?: string;
  starts_at?: string;
  ends_at?: string;
  invite_subject?: string;
  invite_body?: string;
};

export type SatisfactionRecipientStatus = "pending" | "responded";

export type SatisfactionRecipientInvite = {
  subject: string;
  body: string;
  link_url: string;
};

export type SatisfactionRecipient = {
  id: string;
  campaign_id: string;
  customer_code: string;
  customer_store: string;
  customer_name: string | null;
  contact_name: string | null;
  contact_email: string | null;
  status: SatisfactionRecipientStatus;
  response_id?: string | null;
  submitted_at?: string | null;
  created_at: string;
  updated_at: string;
  version: number;
  /** Só em GET do participante (null = não foi possível resolver). */
  invite?: SatisfactionRecipientInvite | null;
};

export type SatisfactionRecipientList = {
  campaign_id: string;
  counts: SatisfactionCounts;
  items: SatisfactionRecipient[];
};

export type SatisfactionAddRecipientItem = {
  customer_code: string;
  customer_store: string;
  customer_name?: string | null;
  contact_name?: string | null;
  contact_email?: string | null;
};

export type SatisfactionRecipientFailure = {
  customer_code: string;
  customer_store: string;
  reason: string;
  message: string;
};

export type SatisfactionAddRecipientsResult = {
  campaign_id: string;
  included: SatisfactionRecipient[];
  already_existing: SatisfactionRecipient[];
  failed: SatisfactionRecipientFailure[];
  counts: { included: number; already_existing: number; failed: number };
};

export type SatisfactionUpdateContactInput = {
  version: number;
  contact_name: string | null;
  contact_email: string | null;
};

export type SatisfactionRecipientLink = {
  recipient_id: string;
  campaign_id: string;
  url: string;
};

export type SatisfactionResolvedInvite = {
  recipient_id: string;
  campaign_id: string;
  company_name: string;
  subject: string;
  body: string;
  link_url: string;
};
