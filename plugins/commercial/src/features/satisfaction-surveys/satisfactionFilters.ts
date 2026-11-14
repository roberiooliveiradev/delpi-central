import type {
  SatisfactionCampaign,
  SatisfactionCampaignStatus,
  SatisfactionRecipient,
  SatisfactionRecipientStatus,
} from "../../types/satisfactionSurvey";
import { customerKey } from "../../shared/format";
import { surveyYearOf } from "./satisfactionDates";

export type CampaignFilters = {
  year: string;
  status: "" | SatisfactionCampaignStatus;
  search: string;
};

export const EMPTY_CAMPAIGN_FILTERS: CampaignFilters = { year: "", status: "", search: "" };

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .toLowerCase()
    .trim();
}

export function hasActiveCampaignFilters(filters: CampaignFilters): boolean {
  return Boolean(filters.year || filters.status || filters.search.trim());
}

/** Anos (desc) em que há campanhas, segundo a data de início. */
export function campaignYearOptions(campaigns: readonly SatisfactionCampaign[]): string[] {
  const years = new Set<number>();
  for (const campaign of campaigns) {
    const year = surveyYearOf(campaign.starts_at);
    if (year != null) years.add(year);
  }
  return [...years].sort((a, b) => b - a).map(String);
}

/**
 * Filtros de apresentação sobre a lista já carregada. A situação NÃO é recalculada:
 * usa `status` devolvido pela API.
 */
export function filterCampaigns(
  campaigns: readonly SatisfactionCampaign[],
  filters: CampaignFilters,
): SatisfactionCampaign[] {
  const term = normalize(filters.search);
  return campaigns
    .filter((campaign) => {
      if (filters.status && campaign.status !== filters.status) return false;
      if (filters.year && String(surveyYearOf(campaign.starts_at)) !== filters.year) return false;
      if (term && !normalize(campaign.name).includes(term)) return false;
      return true;
    })
    .slice()
    .sort((a, b) => Date.parse(b.starts_at) - Date.parse(a.starts_at));
}

export type RecipientFilters = {
  status: "" | SatisfactionRecipientStatus;
  search: string;
};

export const EMPTY_RECIPIENT_FILTERS: RecipientFilters = { status: "", search: "" };

export function filterRecipients(
  recipients: readonly SatisfactionRecipient[],
  filters: RecipientFilters,
): SatisfactionRecipient[] {
  const term = normalize(filters.search);
  return recipients.filter((recipient) => {
    if (filters.status && recipient.status !== filters.status) return false;
    if (!term) return true;
    const haystack = normalize(
      [
        recipient.customer_name ?? "",
        `${recipient.customer_code}/${recipient.customer_store}`,
        recipient.contact_name ?? "",
        recipient.contact_email ?? "",
      ].join(" "),
    );
    return haystack.includes(term);
  });
}

export function recipientCompanyLabel(recipient: Pick<
  SatisfactionRecipient,
  "customer_name" | "customer_code" | "customer_store"
>): string {
  const codeStore = `${recipient.customer_code}/${recipient.customer_store}`;
  const name = (recipient.customer_name ?? "").trim();
  return name ? `${name} · ${codeStore}` : codeStore;
}

/** Chaves canônicas (`customerKey`) dos participantes (para excluir do seletor de clientes). */
export function recipientKeys(recipients: readonly SatisfactionRecipient[]): Set<string> {
  return new Set(recipients.map((item) => customerKey(item.customer_code, item.customer_store)));
}
