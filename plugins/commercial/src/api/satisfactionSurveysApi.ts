import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import type {
  SatisfactionAddRecipientItem,
  SatisfactionAddRecipientsResult,
  SatisfactionCampaign,
  SatisfactionCampaignList,
  SatisfactionCreateCampaignInput,
  SatisfactionRecipient,
  SatisfactionRecipientLink,
  SatisfactionRecipientList,
  SatisfactionResolvedInvite,
  SatisfactionUpdateCampaignInput,
  SatisfactionUpdateContactInput,
} from "../types/satisfactionSurvey";
import { commercialApiUrl, httpGet, httpPatch, httpPost } from "./httpClient";

/** Máximo aceito pelo backend por lote (`AddRecipientsBody.items`). */
export const SATISFACTION_ADD_RECIPIENTS_MAX_BATCH = 100;

const BASE = "/satisfaction-surveys";

function campaignUrl(campaignId: string): string {
  return commercialApiUrl(`${BASE}/campaigns/${encodeURIComponent(campaignId)}`);
}

function recipientUrl(campaignId: string, recipientId: string): string {
  return `${campaignUrl(campaignId)}/recipients/${encodeURIComponent(recipientId)}`;
}

export async function listSatisfactionCampaigns(
  signal?: AbortSignal,
): Promise<SatisfactionCampaign[]> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionCampaignList>>(
    commercialApiUrl(`${BASE}/campaigns`),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar campanhas.").items ?? [];
}

export async function getSatisfactionCampaign(
  campaignId: string,
  signal?: AbortSignal,
): Promise<SatisfactionCampaign> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionCampaign>>(
    campaignUrl(campaignId),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar campanha.");
}

export async function createSatisfactionCampaign(
  input: SatisfactionCreateCampaignInput,
): Promise<SatisfactionCampaign> {
  const response = await httpPost<ApiSuccessResponse<SatisfactionCampaign>>(
    commercialApiUrl(`${BASE}/campaigns`),
    input,
  );
  return unwrapEnvelope(response, "Erro ao criar campanha.");
}

export async function updateSatisfactionCampaign(
  campaignId: string,
  input: SatisfactionUpdateCampaignInput,
): Promise<SatisfactionCampaign> {
  const response = await httpPatch<ApiSuccessResponse<SatisfactionCampaign>>(
    campaignUrl(campaignId),
    input,
  );
  return unwrapEnvelope(response, "Erro ao atualizar campanha.");
}

export async function listSatisfactionRecipients(
  campaignId: string,
  signal?: AbortSignal,
): Promise<SatisfactionRecipientList> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionRecipientList>>(
    `${campaignUrl(campaignId)}/recipients`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar participantes.");
}

export async function addSatisfactionRecipients(
  campaignId: string,
  items: SatisfactionAddRecipientItem[],
): Promise<SatisfactionAddRecipientsResult> {
  const response = await httpPost<ApiSuccessResponse<SatisfactionAddRecipientsResult>>(
    `${campaignUrl(campaignId)}/recipients`,
    { items },
  );
  return unwrapEnvelope(response, "Erro ao incluir participantes.");
}

export async function getSatisfactionRecipient(
  campaignId: string,
  recipientId: string,
  signal?: AbortSignal,
): Promise<SatisfactionRecipient> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionRecipient>>(
    recipientUrl(campaignId, recipientId),
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao carregar participante.");
}

export async function updateSatisfactionRecipientContact(
  campaignId: string,
  recipientId: string,
  input: SatisfactionUpdateContactInput,
): Promise<SatisfactionRecipient> {
  const response = await httpPatch<ApiSuccessResponse<SatisfactionRecipient>>(
    recipientUrl(campaignId, recipientId),
    input,
  );
  return unwrapEnvelope(response, "Erro ao atualizar contato.");
}

export async function getSatisfactionRecipientLink(
  campaignId: string,
  recipientId: string,
  signal?: AbortSignal,
): Promise<SatisfactionRecipientLink> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionRecipientLink>>(
    `${recipientUrl(campaignId, recipientId)}/link`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao recuperar link.");
}

export async function getSatisfactionRecipientInvite(
  campaignId: string,
  recipientId: string,
  signal?: AbortSignal,
): Promise<SatisfactionResolvedInvite> {
  const response = await httpGet<ApiSuccessResponse<SatisfactionResolvedInvite>>(
    `${recipientUrl(campaignId, recipientId)}/invite`,
    { signal },
  );
  return unwrapEnvelope(response, "Erro ao resolver convite.");
}
