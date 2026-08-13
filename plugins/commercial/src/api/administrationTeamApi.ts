import { unwrapEnvelope, type ApiSuccessResponse } from "../types/api";
import { commercialApiUrl, httpGet } from "./httpClient";

export type TeamRosterGroupDto = {
  id: string;
  kind: string;
  name: string;
  active: boolean;
  sort_order?: number;
};

export type TeamRosterPortfolioDto = {
  id: string;
  name: string;
  active: boolean;
  user_id?: string;
  owner_user_id?: string | null;
  role?: "owner" | "member" | string;
  customer_count?: number | null;
  member_count?: number | null;
};

export type TeamRosterPersonDto = {
  user_id: string;
  name: string;
  email: string;
  groups: TeamRosterGroupDto[];
  portfolios: TeamRosterPortfolioDto[];
};

export type ListTeamRosterOptions = {
  groupId?: string | null;
  portfolioId?: string | null;
  q?: string | null;
  signal?: AbortSignal;
};

export async function listTeamRoster(
  options?: ListTeamRosterOptions,
): Promise<TeamRosterPersonDto[]> {
  const params = new URLSearchParams();
  const groupId = (options?.groupId || "").trim();
  const portfolioId = (options?.portfolioId || "").trim();
  const q = (options?.q || "").trim();
  if (groupId) params.set("group_id", groupId);
  if (portfolioId) params.set("portfolio_id", portfolioId);
  if (q) params.set("q", q);
  const qs = params.toString();
  const response = await httpGet<ApiSuccessResponse<{ items: TeamRosterPersonDto[] }>>(
    `${commercialApiUrl("/administration/team-roster")}${qs ? `?${qs}` : ""}`,
    { signal: options?.signal },
  );
  const data = unwrapEnvelope(response, "Erro ao carregar a equipe.");
  return data.items ?? [];
}
