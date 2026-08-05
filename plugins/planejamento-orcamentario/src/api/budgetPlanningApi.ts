import {
  downloadAuthenticatedBinary,
  downloadAuthenticatedFile,
  httpGetEnvelope,
  httpPostEnvelope,
  httpPostFormEnvelope,
  httpPutEnvelope,
  type UploadProgressCallback,
} from "./httpClient";
import type {
  AdminDocumentUploadInput,
  AdminExerciseInput,
  AdminExercisePatch,
  AdminGuidanceBundle,
  BudgetContext,
  BudgetExercise,
  BudgetResponsibility,
  BudgetResponsibilityCreateInput,
  BudgetResponsibilityListFilters,
  BudgetResponsibilityListResult,
  BudgetResponsibilityUpdateInput,
  CapexCategory,
  CapexCategoryCreateInput,
  CapexCategoryListResult,
  CapexCategoryUpdateInput,
  CapexConsolidationDetailsResult,
  CapexConsolidationExportResult,
  CapexConsolidationFilters,
  CapexConsolidationGroupingResult,
  CapexConsolidationSummaryResult,
  CapexInvestment,
  CapexInvestmentCreateInput,
  CapexInvestmentListFilters,
  CapexInvestmentListResult,
  CapexInvestmentUpdateInput,
  CapexInvestmentAttachment,
  CapexAttachmentUploadInput,
  CapexPlan,
  CapexPlanHistoryResult,
  CapexPlanListFilters,
  ErpCostCenter,
  CapexPlanListResult,
  GuidanceCurrent,
  GuidanceDocument,
  MyResponsibilitiesResult,
  OrgCatalog,
  OrgCostCenter,
  PagedItems,
  PersonnelPlan,
  PersonnelPlanHistoryResult,
  PersonnelPlanLine,
  PersonnelPlanLineCreateInput,
  PersonnelPlanLineUpdateInput,
  PersonnelPlanListFilters,
  PersonnelPlanListResult,
  PersonnelPlanResolveInput,
  UserScope,
  UserScopeInput,
} from "../types/budgetPlanning";

export async function fetchBudgetContext(signal?: AbortSignal): Promise<BudgetContext> {
  return httpGetEnvelope("/context", "Não foi possível carregar o contexto do exercício.", {
    signal,
  });
}

export async function fetchCurrentGuidance(signal?: AbortSignal): Promise<GuidanceCurrent> {
  return httpGetEnvelope(
    "/guidance/current",
    "Não foi possível carregar as orientações publicadas.",
    { signal },
  );
}

export async function acknowledgeCurrentGuidance(signal?: AbortSignal): Promise<{
  acknowledged: boolean;
  acknowledged_at?: string;
  idempotent_replay?: boolean;
  modules_unlocked?: boolean;
}> {
  return httpPostEnvelope(
    "/guidance/current/acknowledge",
    {},
    "Não foi possível registrar a confirmação de leitura.",
    { signal },
  );
}

export async function fetchCurrentGuidanceDocuments(
  signal?: AbortSignal,
): Promise<GuidanceDocument[]> {
  const data = await httpGetEnvelope<{ items: GuidanceDocument[] }>(
    "/guidance/current/documents",
    "Não foi possível carregar os documentos das orientações.",
    { signal },
  );
  return data.items ?? [];
}

export async function downloadGuidanceDocument(documentId: string): Promise<Blob> {
  return downloadAuthenticatedFile(`/documents/${documentId}/download`);
}

export async function listAdminExercises(signal?: AbortSignal): Promise<BudgetExercise[]> {
  const data = await httpGetEnvelope<PagedItems<BudgetExercise>>(
    "/admin/exercises",
    "Não foi possível listar os exercícios.",
    { signal },
  );
  return data.items ?? [];
}

export async function createAdminExercise(
  input: AdminExerciseInput,
  signal?: AbortSignal,
): Promise<BudgetExercise> {
  return httpPostEnvelope(
    "/admin/exercises",
    input,
    "Não foi possível criar o exercício.",
    { signal },
  );
}

export async function updateAdminExercise(
  exerciseId: string,
  patch: AdminExercisePatch,
  signal?: AbortSignal,
): Promise<BudgetExercise> {
  return httpPutEnvelope(
    `/admin/exercises/${exerciseId}`,
    patch,
    "Não foi possível atualizar o exercício.",
    { signal },
  );
}

export async function transitionAdminExercise(
  exerciseId: string,
  action: string,
  signal?: AbortSignal,
): Promise<BudgetExercise> {
  return httpPostEnvelope(
    `/admin/exercises/${exerciseId}/transitions`,
    { action },
    "Não foi possível alterar o status do exercício.",
    { signal },
  );
}

export async function fetchAdminGuidance(
  exerciseId: string,
  signal?: AbortSignal,
): Promise<AdminGuidanceBundle> {
  return httpGetEnvelope(
    `/admin/exercises/${exerciseId}/guidance`,
    "Não foi possível carregar o rascunho das orientações.",
    { signal },
  );
}

export async function saveAdminGuidanceDraft(
  guidanceId: string,
  draft: Partial<GuidanceCurrent> & {
    premises?: GuidanceCurrent["premises"];
    schedule?: GuidanceCurrent["schedule"];
  },
  signal?: AbortSignal,
): Promise<GuidanceCurrent> {
  return httpPutEnvelope(
    `/admin/guidance/${guidanceId}`,
    draft,
    "Não foi possível salvar o rascunho das orientações.",
    { signal },
  );
}

export async function publishAdminGuidance(
  guidanceId: string,
  signal?: AbortSignal,
): Promise<GuidanceCurrent> {
  return httpPostEnvelope(
    `/admin/guidance/${guidanceId}/publish`,
    {},
    "Não foi possível publicar as orientações.",
    { signal },
  );
}

export async function listAdminGuidanceDocuments(
  guidanceId: string,
  signal?: AbortSignal,
): Promise<GuidanceDocument[]> {
  const data = await httpGetEnvelope<{ items: GuidanceDocument[] }>(
    `/admin/guidance/${guidanceId}/documents`,
    "Não foi possível listar os documentos.",
    { signal },
  );
  return data.items ?? [];
}

export async function uploadAdminGuidanceDocument(
  input: AdminDocumentUploadInput,
  options: { signal?: AbortSignal; onProgress?: UploadProgressCallback } = {},
): Promise<GuidanceDocument> {
  const formData = new FormData();
  formData.append("exercise_id", input.exerciseId);
  formData.append("display_name", input.displayName);
  formData.append("description", input.description ?? "");
  formData.append("display_order", String(input.displayOrder ?? 0));
  if (input.documentKind) {
    formData.append("document_kind", input.documentKind);
  }
  if (input.externalUrl?.trim()) {
    formData.append("external_url", input.externalUrl.trim());
  } else if (input.file) {
    formData.append("file", input.file, input.file.name);
  }
  return httpPostFormEnvelope(
    `/admin/guidance/${input.guidanceId}/documents`,
    formData,
    "Não foi possível enviar o documento.",
    options,
  );
}

export async function updateAdminDocument(
  documentId: string,
  patch: {
    display_name?: string;
    description?: string | null;
    display_order?: number;
  },
  signal?: AbortSignal,
): Promise<GuidanceDocument> {
  return httpPutEnvelope(
    `/admin/documents/${documentId}`,
    patch,
    "Não foi possível atualizar o documento.",
    { signal },
  );
}

export async function archiveAdminDocument(
  documentId: string,
  signal?: AbortSignal,
): Promise<GuidanceDocument> {
  return httpPostEnvelope(
    `/admin/documents/${documentId}/archive`,
    {},
    "Não foi possível arquivar o documento.",
    { signal },
  );
}

export async function listAdminScopes(signal?: AbortSignal): Promise<{
  items: UserScope[];
  catalog: OrgCatalog;
}> {
  return httpGetEnvelope(
    "/admin/scopes",
    "Não foi possível listar os escopos.",
    { signal },
  );
}

export async function createAdminScope(
  input: UserScopeInput,
  signal?: AbortSignal,
): Promise<UserScope> {
  return httpPostEnvelope(
    "/admin/scopes",
    input,
    "Não foi possível criar o escopo.",
    { signal },
  );
}

export async function deactivateAdminScope(
  scopeId: string,
  signal?: AbortSignal,
): Promise<UserScope> {
  return httpPostEnvelope(
    `/admin/scopes/${scopeId}/deactivate`,
    {},
    "Não foi possível desativar o escopo.",
    { signal },
  );
}

export async function listOrgCostCenters(signal?: AbortSignal): Promise<OrgCostCenter[]> {
  const data = await listAdminScopes(signal);
  return data.catalog?.cost_centers ?? [];
}

export async function listErpCostCenters(
  branch: string,
  signal?: AbortSignal,
): Promise<{ items: ErpCostCenter[]; branch: string }> {
  const qs = new URLSearchParams({ branch });
  return httpGetEnvelope(
    `/org/erp-cost-centers?${qs.toString()}`,
    "Não foi possível consultar os centros de custo do ERP.",
    { signal },
  );
}

export async function createOrgCostCenterFromErp(
  input: { branch: string; code: string; unit_id: string; area_code?: string | null },
  signal?: AbortSignal,
): Promise<OrgCostCenter> {
  return httpPostEnvelope(
    "/admin/org/cost-centers/from-erp",
    input,
    "Não foi possível cadastrar o centro de custo a partir do ERP.",
    { signal },
  );
}

export async function upsertOrgCostCenter(
  input: {
    code: string;
    name: string;
    unit_code: string;
    branch?: string;
    area_code?: string | null;
  },
  signal?: AbortSignal,
): Promise<OrgCostCenter> {
  return httpPostEnvelope(
    "/admin/org/cost-centers",
    input,
    "Não foi possível salvar o centro de custo no catálogo.",
    { signal },
  );
}

export async function listAdminBudgetResponsibilities(
  filters: BudgetResponsibilityListFilters = {},
  signal?: AbortSignal,
): Promise<BudgetResponsibilityListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.module) qs.set("module", filters.module);
  if (filters.user_sub) qs.set("user_sub", filters.user_sub);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.area_id) qs.set("area_id", filters.area_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.responsibility_type) {
    qs.set("responsibility_type", filters.responsibility_type);
  }
  if (filters.is_active === true || filters.is_active === false) {
    qs.set("is_active", String(filters.is_active));
  }
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 20));
  const data = await httpGetEnvelope<BudgetResponsibilityListResult>(
    `/admin/budget-responsibilities?${qs.toString()}`,
    "Não foi possível listar as responsabilidades orçamentárias.",
    { signal },
  );
  return {
    items: data.items ?? [],
    pagination: data.pagination ?? {
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 20,
      total: (data.items ?? []).length,
      has_more: false,
    },
  };
}

export async function createAdminBudgetResponsibility(
  input: BudgetResponsibilityCreateInput,
  signal?: AbortSignal,
): Promise<BudgetResponsibility> {
  return httpPostEnvelope(
    "/admin/budget-responsibilities",
    { module: "capex", ...input },
    "Não foi possível criar a responsabilidade orçamentária.",
    { signal },
  );
}

export async function updateAdminBudgetResponsibility(
  responsibilityId: string,
  patch: BudgetResponsibilityUpdateInput,
  signal?: AbortSignal,
): Promise<BudgetResponsibility> {
  return httpPutEnvelope(
    `/admin/budget-responsibilities/${responsibilityId}`,
    patch,
    "Não foi possível atualizar a responsabilidade orçamentária.",
    { signal },
  );
}

export async function deactivateAdminBudgetResponsibility(
  responsibilityId: string,
  reason?: string,
  signal?: AbortSignal,
): Promise<BudgetResponsibility> {
  return httpPostEnvelope(
    `/admin/budget-responsibilities/${responsibilityId}/deactivate`,
    { reason: reason ?? null },
    "Não foi possível desativar a responsabilidade orçamentária.",
    { signal },
  );
}

export async function reactivateAdminBudgetResponsibility(
  responsibilityId: string,
  signal?: AbortSignal,
): Promise<BudgetResponsibility> {
  return httpPostEnvelope(
    `/admin/budget-responsibilities/${responsibilityId}/reactivate`,
    {},
    "Não foi possível reativar a responsabilidade orçamentária.",
    { signal },
  );
}

export async function fetchMyCapexResponsibilities(
  exerciseId?: string,
  signal?: AbortSignal,
): Promise<MyResponsibilitiesResult> {
  return fetchMyBudgetResponsibilities("capex", exerciseId, signal);
}

export async function fetchMyBudgetResponsibilities(
  module: "capex" | "personnel",
  exerciseId?: string,
  signal?: AbortSignal,
): Promise<MyResponsibilitiesResult> {
  const qs = new URLSearchParams({ module });
  if (exerciseId) qs.set("exercise_id", exerciseId);
  return httpGetEnvelope(
    `/capex/my-responsibilities?${qs.toString()}`,
    "Não foi possível carregar seus centros de custo.",
    { signal },
  );
}

export async function fetchMyPersonnelResponsibilities(
  exerciseId?: string,
  signal?: AbortSignal,
): Promise<MyResponsibilitiesResult> {
  return fetchMyBudgetResponsibilities("personnel", exerciseId, signal);
}

export async function listActiveCapexCategories(
  signal?: AbortSignal,
): Promise<CapexCategoryListResult> {
  return httpGetEnvelope(
    "/capex/categories",
    "Não foi possível listar as categorias CAPEX ativas.",
    { signal },
  );
}

export async function listAdminCapexCategories(
  filters: { is_active?: boolean | null; q?: string } = {},
  signal?: AbortSignal,
): Promise<CapexCategoryListResult> {
  const qs = new URLSearchParams();
  if (filters.is_active === true || filters.is_active === false) {
    qs.set("is_active", String(filters.is_active));
  }
  if (filters.q?.trim()) qs.set("q", filters.q.trim());
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  return httpGetEnvelope(
    `/admin/capex/categories${suffix}`,
    "Não foi possível listar as categorias CAPEX.",
    { signal },
  );
}

export async function createAdminCapexCategory(
  input: CapexCategoryCreateInput,
  signal?: AbortSignal,
): Promise<CapexCategory> {
  return httpPostEnvelope(
    "/admin/capex/categories",
    input,
    "Não foi possível criar a categoria CAPEX.",
    { signal },
  );
}

export async function updateAdminCapexCategory(
  categoryId: string,
  patch: CapexCategoryUpdateInput,
  signal?: AbortSignal,
): Promise<CapexCategory> {
  return httpPutEnvelope(
    `/admin/capex/categories/${categoryId}`,
    patch,
    "Não foi possível atualizar a categoria CAPEX.",
    { signal },
  );
}

export async function deactivateAdminCapexCategory(
  categoryId: string,
  reason?: string,
  signal?: AbortSignal,
): Promise<CapexCategory> {
  return httpPostEnvelope(
    `/admin/capex/categories/${categoryId}/deactivate`,
    { reason: reason ?? null },
    "Não foi possível desativar a categoria CAPEX.",
    { signal },
  );
}

export async function reactivateAdminCapexCategory(
  categoryId: string,
  signal?: AbortSignal,
): Promise<CapexCategory> {
  return httpPostEnvelope(
    `/admin/capex/categories/${categoryId}/reactivate`,
    {},
    "Não foi possível reativar a categoria CAPEX.",
    { signal },
  );
}

export async function listCapexInvestments(
  filters: CapexInvestmentListFilters = {},
  signal?: AbortSignal,
): Promise<CapexInvestmentListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.category_id) qs.set("category_id", filters.category_id);
  if (filters.priority) qs.set("priority", filters.priority);
  if (filters.origin) qs.set("origin", filters.origin);
  if (filters.status) qs.set("status", filters.status);
  if (filters.q?.trim()) qs.set("q", filters.q.trim());
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 20));
  const data = await httpGetEnvelope<CapexInvestmentListResult>(
    `/capex/investments?${qs.toString()}`,
    "Não foi possível listar os investimentos CAPEX.",
    { signal },
  );
  return {
    items: data.items ?? [],
    pagination: data.pagination ?? {
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 20,
      total: (data.items ?? []).length,
      has_more: false,
    },
  };
}

export async function getCapexInvestment(
  investmentId: string,
  signal?: AbortSignal,
): Promise<CapexInvestment> {
  return httpGetEnvelope(
    `/capex/investments/${investmentId}`,
    "Não foi possível carregar o investimento CAPEX.",
    { signal },
  );
}

export async function createCapexInvestment(
  input: CapexInvestmentCreateInput,
  signal?: AbortSignal,
): Promise<CapexInvestment> {
  return httpPostEnvelope(
    "/capex/investments",
    input,
    "Não foi possível criar o rascunho do investimento.",
    { signal },
  );
}

export async function updateCapexInvestment(
  investmentId: string,
  patch: CapexInvestmentUpdateInput,
  signal?: AbortSignal,
): Promise<CapexInvestment> {
  return httpPutEnvelope(
    `/capex/investments/${investmentId}`,
    patch,
    "Não foi possível salvar o investimento CAPEX.",
    { signal },
  );
}

export async function archiveCapexInvestment(
  investmentId: string,
  reason?: string,
  signal?: AbortSignal,
): Promise<CapexInvestment> {
  return httpPostEnvelope(
    `/capex/investments/${investmentId}/archive`,
    { reason: reason ?? null },
    "Não foi possível arquivar o investimento CAPEX.",
    { signal },
  );
}

export async function listCapexInvestmentAttachments(
  investmentId: string,
  signal?: AbortSignal,
): Promise<CapexInvestmentAttachment[]> {
  const data = await httpGetEnvelope<{ items: CapexInvestmentAttachment[] }>(
    `/capex/investments/${investmentId}/attachments`,
    "Não foi possível listar os anexos do investimento.",
    { signal },
  );
  return data.items ?? [];
}

export async function uploadCapexInvestmentAttachment(
  input: CapexAttachmentUploadInput,
  options: { signal?: AbortSignal; onProgress?: UploadProgressCallback } = {},
): Promise<CapexInvestmentAttachment> {
  const formData = new FormData();
  formData.append("file", input.file, input.file.name);
  formData.append("attachment_type", input.attachmentType);
  formData.append("display_name", input.displayName);
  formData.append("description", input.description ?? "");
  formData.append("idempotency_key", input.idempotencyKey);
  return httpPostFormEnvelope(
    `/capex/investments/${input.investmentId}/attachments`,
    formData,
    "Não foi possível enviar o anexo CAPEX.",
    options,
  );
}

export async function downloadCapexAttachment(attachmentId: string): Promise<Blob> {
  return downloadAuthenticatedFile(`/capex/attachments/${attachmentId}/download`);
}

export async function archiveCapexAttachment(
  attachmentId: string,
  signal?: AbortSignal,
): Promise<CapexInvestmentAttachment> {
  return httpPostEnvelope(
    `/capex/attachments/${attachmentId}/archive`,
    {},
    "Não foi possível arquivar o anexo CAPEX.",
    { signal },
  );
}

function normalizePlanList(
  data: CapexPlanListResult,
  filters: CapexPlanListFilters,
): CapexPlanListResult {
  return {
    items: data.items ?? [],
    pagination: data.pagination ?? {
      page: filters.page ?? 1,
      page_size: filters.page_size ?? 50,
      total: (data.items ?? []).length,
      has_more: false,
    },
  };
}

export async function resolveCapexPlan(
  input: { exercise_id: string; cost_center_id: string; unit_id?: string | null },
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpPostEnvelope(
    "/capex/plans/resolve",
    input,
    "Não foi possível obter o planejamento CAPEX do centro de custo.",
    { signal },
  );
}

export async function getCapexPlan(
  planId: string,
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpGetEnvelope(
    `/capex/plans/${planId}`,
    "Não foi possível carregar o planejamento CAPEX.",
    { signal },
  );
}

export async function listCapexPlans(
  filters: CapexPlanListFilters = {},
  signal?: AbortSignal,
): Promise<CapexPlanListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.area_id) qs.set("area_id", filters.area_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.status) qs.set("status", filters.status);
  if (filters.submitted_by) qs.set("submitted_by", filters.submitted_by);
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 50));
  const data = await httpGetEnvelope<CapexPlanListResult>(
    `/capex/plans?${qs.toString()}`,
    "Não foi possível listar os planejamentos CAPEX.",
    { signal },
  );
  return normalizePlanList(data, filters);
}

export async function submitCapexPlan(
  planId: string,
  input: { version: number; comment?: string | null },
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpPostEnvelope(
    `/capex/plans/${planId}/submit`,
    input,
    "Não foi possível enviar o planejamento CAPEX para aprovação.",
    { signal },
  );
}

export async function listCapexPlanHistory(
  planId: string,
  signal?: AbortSignal,
): Promise<CapexPlanHistoryResult> {
  const data = await httpGetEnvelope<CapexPlanHistoryResult>(
    `/capex/plans/${planId}/history`,
    "Não foi possível carregar o histórico do planejamento CAPEX.",
    { signal },
  );
  return { items: data.items ?? [] };
}

export async function listCapexReviewQueue(
  filters: CapexPlanListFilters = {},
  signal?: AbortSignal,
): Promise<CapexPlanListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.area_id) qs.set("area_id", filters.area_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.status) qs.set("status", filters.status);
  if (filters.submitted_by) qs.set("submitted_by", filters.submitted_by);
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 20));
  const data = await httpGetEnvelope<CapexPlanListResult>(
    `/capex/review-queue?${qs.toString()}`,
    "Não foi possível carregar a fila de aprovação CAPEX.",
    { signal },
  );
  return normalizePlanList(data, filters);
}

export async function getCapexReviewDetail(
  planId: string,
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpGetEnvelope(
    `/capex/review/${planId}`,
    "Não foi possível carregar a análise do planejamento CAPEX.",
    { signal },
  );
}

export async function requestCapexPlanChanges(
  planId: string,
  input: { version: number; comment: string },
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpPostEnvelope(
    `/capex/review/${planId}/request-changes`,
    input,
    "Não foi possível solicitar ajustes no planejamento CAPEX.",
    { signal },
  );
}

export async function rejectCapexPlan(
  planId: string,
  input: { version: number; comment: string },
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpPostEnvelope(
    `/capex/review/${planId}/reject`,
    input,
    "Não foi possível reprovar o planejamento CAPEX.",
    { signal },
  );
}

export async function approveCapexPlan(
  planId: string,
  input: { version: number; comment?: string | null },
  signal?: AbortSignal,
): Promise<CapexPlan> {
  return httpPostEnvelope(
    `/capex/review/${planId}/approve`,
    input,
    "Não foi possível aprovar o planejamento CAPEX.",
    { signal },
  );
}

function appendConsolidationFilters(
  qs: URLSearchParams,
  filters: CapexConsolidationFilters,
): void {
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.year != null) qs.set("year", String(filters.year));
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.area_id) qs.set("area_id", filters.area_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.category_id) qs.set("category_id", filters.category_id);
  if (filters.priority) qs.set("priority", filters.priority);
  if (filters.origin) qs.set("origin", filters.origin);
  if (filters.plan_status) qs.set("plan_status", filters.plan_status);
  if (filters.required_date_from) qs.set("required_date_from", filters.required_date_from);
  if (filters.required_date_to) qs.set("required_date_to", filters.required_date_to);
}

export function buildCapexConsolidationQuery(filters: CapexConsolidationFilters): string {
  const qs = new URLSearchParams();
  appendConsolidationFilters(qs, filters);
  const raw = qs.toString();
  return raw ? `?${raw}` : "";
}

export async function fetchCapexConsolidationSummary(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
): Promise<CapexConsolidationSummaryResult> {
  return httpGetEnvelope(
    `/capex/consolidation/summary${buildCapexConsolidationQuery(filters)}`,
    "Não foi possível carregar o resumo consolidado CAPEX.",
    { signal },
  );
}

async function fetchCapexConsolidationGrouping(
  pathSuffix: string,
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
): Promise<CapexConsolidationGroupingResult> {
  return httpGetEnvelope(
    `/capex/consolidation/${pathSuffix}${buildCapexConsolidationQuery(filters)}`,
    "Não foi possível carregar o agrupamento consolidado CAPEX.",
    { signal },
  );
}

export function fetchCapexConsolidationByUnit(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-unit", filters, signal);
}

export function fetchCapexConsolidationByArea(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-area", filters, signal);
}

export function fetchCapexConsolidationByCostCenter(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-cost-center", filters, signal);
}

export function fetchCapexConsolidationByCategory(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-category", filters, signal);
}

export function fetchCapexConsolidationByPriority(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-priority", filters, signal);
}

export function fetchCapexConsolidationByOrigin(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-origin", filters, signal);
}

export function fetchCapexConsolidationByMonth(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-month", filters, signal);
}

export function fetchCapexConsolidationByPlanStatus(
  filters: CapexConsolidationFilters,
  signal?: AbortSignal,
) {
  return fetchCapexConsolidationGrouping("by-plan-status", filters, signal);
}

export async function listCapexConsolidationDetails(
  filters: CapexConsolidationFilters & {
    page?: number;
    page_size?: number;
    sort_by?: string;
    sort_dir?: "asc" | "desc";
  },
  signal?: AbortSignal,
): Promise<CapexConsolidationDetailsResult> {
  const qs = new URLSearchParams();
  appendConsolidationFilters(qs, filters);
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 20));
  if (filters.sort_by) qs.set("sort_by", filters.sort_by);
  if (filters.sort_dir) qs.set("sort_dir", filters.sort_dir);
  return httpGetEnvelope(
    `/capex/consolidation/details?${qs.toString()}`,
    "Não foi possível carregar o detalhamento consolidado CAPEX.",
    { signal },
  );
}

export async function exportCapexConsolidationXlsx(
  filters: CapexConsolidationFilters,
): Promise<CapexConsolidationExportResult> {
  const path = `/capex/consolidation/export.xlsx${buildCapexConsolidationQuery(filters)}`;
  const result = await downloadAuthenticatedBinary(path);
  const fallbackYear = filters.year ?? new Date().getFullYear();
  const fallbackDate = new Date().toISOString().slice(0, 10);
  return {
    blob: result.blob,
    filename:
      result.filename ||
      `planejamento-capex-${fallbackYear}-${fallbackDate}.xlsx`,
  };
}

// -------- Orçamento de Pessoal (Fase 3B.2) --------

export async function resolvePersonnelPlan(
  input: PersonnelPlanResolveInput,
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpPostEnvelope(
    "/personnel/plans/resolve",
    input,
    "Não foi possível resolver o planejamento de Pessoal.",
    { signal },
  );
}

export async function listPersonnelPlans(
  filters: {
    exercise_id?: string;
    unit_id?: string;
    cost_center_id?: string;
    page?: number;
    page_size?: number;
  } = {},
  signal?: AbortSignal,
): Promise<PersonnelPlanListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 50));
  return httpGetEnvelope(
    `/personnel/plans?${qs.toString()}`,
    "Não foi possível listar os planejamentos de Pessoal.",
    { signal },
  );
}

export async function getPersonnelPlan(
  planId: string,
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpGetEnvelope(
    `/personnel/plans/${encodeURIComponent(planId)}`,
    "Não foi possível carregar o planejamento de Pessoal.",
    { signal },
  );
}

export async function createPersonnelPlanLine(
  planId: string,
  input: PersonnelPlanLineCreateInput,
  signal?: AbortSignal,
): Promise<PersonnelPlanLine> {
  return httpPostEnvelope(
    `/personnel/plans/${encodeURIComponent(planId)}/lines`,
    input,
    "Não foi possível criar a linha de Pessoal.",
    { signal },
  );
}

export async function updatePersonnelPlanLine(
  lineId: string,
  input: PersonnelPlanLineUpdateInput,
  signal?: AbortSignal,
): Promise<PersonnelPlanLine> {
  return httpPutEnvelope(
    `/personnel/lines/${encodeURIComponent(lineId)}`,
    input,
    "Não foi possível atualizar a linha de Pessoal.",
    { signal },
  );
}

export async function archivePersonnelPlanLine(
  lineId: string,
  signal?: AbortSignal,
): Promise<PersonnelPlanLine> {
  return httpPostEnvelope(
    `/personnel/lines/${encodeURIComponent(lineId)}/archive`,
    {},
    "Não foi possível arquivar a linha de Pessoal.",
    { signal },
  );
}

function normalizePersonnelPlanList(
  data: PersonnelPlanListResult,
  filters: PersonnelPlanListFilters,
): PersonnelPlanListResult {
  return {
    items: data.items ?? [],
    pagination: {
      page: data.pagination?.page ?? filters.page ?? 1,
      page_size: data.pagination?.page_size ?? filters.page_size ?? 50,
      total: data.pagination?.total ?? (data.items ?? []).length,
      has_more: Boolean(data.pagination?.has_more),
    },
  };
}

export async function submitPersonnelPlan(
  planId: string,
  input: { version: number; comment?: string | null },
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpPostEnvelope(
    `/personnel/plans/${encodeURIComponent(planId)}/submit`,
    input,
    "Não foi possível enviar o Orçamento de Pessoal para aprovação.",
    { signal },
  );
}

export async function listPersonnelPlanHistory(
  planId: string,
  signal?: AbortSignal,
): Promise<PersonnelPlanHistoryResult> {
  const data = await httpGetEnvelope<PersonnelPlanHistoryResult>(
    `/personnel/plans/${encodeURIComponent(planId)}/history`,
    "Não foi possível carregar o histórico do Orçamento de Pessoal.",
    { signal },
  );
  return { items: data.items ?? [] };
}

export async function listPersonnelReviewQueue(
  filters: PersonnelPlanListFilters = {},
  signal?: AbortSignal,
): Promise<PersonnelPlanListResult> {
  const qs = new URLSearchParams();
  if (filters.exercise_id) qs.set("exercise_id", filters.exercise_id);
  if (filters.unit_id) qs.set("unit_id", filters.unit_id);
  if (filters.area_id) qs.set("area_id", filters.area_id);
  if (filters.cost_center_id) qs.set("cost_center_id", filters.cost_center_id);
  if (filters.status) qs.set("status", filters.status);
  if (filters.submitted_by) qs.set("submitted_by", filters.submitted_by);
  qs.set("page", String(filters.page ?? 1));
  qs.set("page_size", String(filters.page_size ?? 20));
  const data = await httpGetEnvelope<PersonnelPlanListResult>(
    `/personnel/review-queue?${qs.toString()}`,
    "Não foi possível carregar a fila de aprovação de Pessoal.",
    { signal },
  );
  return normalizePersonnelPlanList(data, filters);
}

export async function getPersonnelReviewDetail(
  planId: string,
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpGetEnvelope(
    `/personnel/review/${encodeURIComponent(planId)}`,
    "Não foi possível carregar a análise do Orçamento de Pessoal.",
    { signal },
  );
}

export async function requestPersonnelPlanChanges(
  planId: string,
  input: { version: number; comment: string },
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpPostEnvelope(
    `/personnel/review/${encodeURIComponent(planId)}/request-changes`,
    input,
    "Não foi possível solicitar ajustes no Orçamento de Pessoal.",
    { signal },
  );
}

export async function rejectPersonnelPlan(
  planId: string,
  input: { version: number; comment: string },
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpPostEnvelope(
    `/personnel/review/${encodeURIComponent(planId)}/reject`,
    input,
    "Não foi possível reprovar o Orçamento de Pessoal.",
    { signal },
  );
}

export async function approvePersonnelPlan(
  planId: string,
  input: { version: number; comment?: string | null },
  signal?: AbortSignal,
): Promise<PersonnelPlan> {
  return httpPostEnvelope(
    `/personnel/review/${encodeURIComponent(planId)}/approve`,
    input,
    "Não foi possível aprovar o Orçamento de Pessoal.",
    { signal },
  );
}
