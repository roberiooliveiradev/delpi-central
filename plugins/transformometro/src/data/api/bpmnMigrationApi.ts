import {
  TRANSFORMOMETRO_API_BASE,
  buildAuthHeaders,
} from "./transformometroApiBase";

type GetToken = (() => string | undefined) | undefined;

const GPT_ACTIONS_BASE = "/gpt-actions/v1";

export class BpmnMigrationError extends Error {
  readonly status: number;
  readonly errorCode?: string;

  constructor(message: string, status: number, errorCode?: string) {
    super(message);
    this.name = "BpmnMigrationError";
    this.status = status;
    this.errorCode = errorCode;
  }
}

export type MigrationAmbiguity = {
  ambiguity_id: string;
  legacy_object_ids: string[];
  description: string;
  options: Array<{ id: string; label: string; requires_values?: boolean }>;
  recommended_option?: string | null;
  confidence: string;
  blocking: boolean;
};

export type MigrationLoss = {
  loss_id: string;
  legacy_object_ids: string[];
  classification: "NON_BLOCKING" | "BLOCKING";
  description: string;
};

export type MigrationReportItem = {
  mapping_id: string;
  legacy_id: string;
  legacy_kind: string;
  legacy_type?: string;
  target_element_id?: string;
  target_bpmn_tag?: string;
  classification: string;
  notes?: string[];
};

export type MigrationReport = {
  status: "READY" | "AMBIGUOUS" | "BLOCKED";
  candidate_sha256?: string;
  mapping_report: MigrationReportItem[];
  losses: MigrationLoss[];
  ambiguities: MigrationAmbiguity[];
  warnings: string[];
  statistics: {
    legacy_nodes?: number;
    legacy_edges?: number;
    legacy_lanes?: number;
    by_classification?: Record<string, number>;
    unresolved_ambiguities?: number;
    warnings?: number;
  };
  source_format?: string;
};

export type BpmnValidationSummary = {
  evaluated_stages?: string[];
  issues?: Array<{
    rule_id: string;
    stage: string;
    severity: string;
    message: string;
  }>;
  blocking_issues?: number;
  passed?: boolean;
  error?: string;
};

export type MigrationProposal = {
  proposal_handle: string;
  ready: boolean;
  act_allowed: boolean;
  execution_policy: string;
  validation_result: {
    ready: boolean;
    migration_report: MigrationReport;
    bpmn_validation: BpmnValidationSummary;
  };
  exact_change: {
    processo_id: string;
    candidate_xml: string;
    candidate_sha256: string;
    legacy_source_fingerprint: string;
    source_summary?: Record<string, unknown>;
  };
  consequential_impact: {
    persists: boolean;
    creates_native_bpmn_document: boolean;
    creates_bpmn_revision: number;
    revision_origin: string;
    mutates_legacy: boolean;
    writes_to_bpmn_modeler: boolean;
  };
  confirmation_requirement: {
    explicit_user_confirmation: boolean;
    message?: string;
  };
};

export type MigrationResolutions = Record<
  string,
  { option: string; values?: Record<string, string> }
>;

type Envelope = {
  success?: boolean;
  message?: string;
  data?: Record<string, unknown> | null;
};

async function governedRequest<T>(
  path: string,
  getAccessToken: GetToken,
  body: Record<string, unknown>,
): Promise<T> {
  const response = await fetch(
    `${TRANSFORMOMETRO_API_BASE}${path}`,
    {
      method: "POST",
      headers: {
        ...buildAuthHeaders(getAccessToken),
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    },
  );
  const parsed = (await response.json().catch(() => null)) as Envelope | null;
  if (!response.ok || parsed?.success === false) {
    const data = (parsed?.data ?? {}) as Record<string, unknown>;
    const code =
      typeof data.error_code === "string"
        ? data.error_code
        : typeof data.error_kind === "string"
          ? data.error_kind
          : undefined;
    throw new BpmnMigrationError(
      parsed?.message ?? `HTTP ${response.status}`,
      response.status,
      code,
    );
  }
  return parsed?.data as T;
}

/**
 * PREPARE da migração governada — nunca persiste. Retorna a proposta selada
 * (handle opaco + relatório completo de mapeamento + XML candidato).
 * Re-preparar com `resolutions` após resolução humana de ambiguidades.
 */
export function prepareBpmnMigration(
  processoId: string,
  getAccessToken: GetToken,
  resolutions?: MigrationResolutions,
): Promise<MigrationProposal> {
  return governedRequest(
    `${GPT_ACTIONS_BASE}/governed-operations/prepare`,
    getAccessToken,
    {
      action: "migrate_legacy_diagram_to_native_bpmn",
      processo_id: processoId,
      ...(resolutions ? { resolutions } : {}),
    },
  );
}

/**
 * ACT — único caminho de escrita canônica (commit_proposal). Exige
 * confirmação explícita do usuário (confirm_before_act).
 */
export function commitBpmnMigration(
  proposalHandle: string,
  getAccessToken: GetToken,
): Promise<{
  verified: boolean;
  capability: string;
  proposal_id: string;
  data: {
    document_id?: string;
    version?: number;
    working_copy_sha256?: string;
    migration?: Record<string, unknown> | null;
    write_result?: Record<string, unknown>;
  };
}> {
  return governedRequest(
    `${GPT_ACTIONS_BASE}/proposals/commit`,
    getAccessToken,
    { proposal_handle: proposalHandle, confirmation: true },
  );
}
