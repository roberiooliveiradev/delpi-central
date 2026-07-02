export type QualityLabelResult = "approved" | "rejected" | "conditional";

export type AuditSource = {
  operationId: string;
  params?: Record<string, unknown>;
  ok?: boolean;
};

export type AuditError = {
  operationId: string;
  message: string;
};

export type AuditMetadata = {
  snapshotVersion?: number;
  capturedAt?: string;
  productionOrder?: {
    order?: Record<string, unknown> | null;
    linkSummary?: Record<string, unknown> | null;
    linkedOrders?: Array<Record<string, unknown>>;
    linkedOrdersTruncated?: boolean;
  } | null;
  product?: {
    code?: string | null;
    structure?: Record<string, unknown> | null;
    routing?: Record<string, unknown> | null;
    inspection?: Record<string, unknown> | null;
  } | null;
  sources?: AuditSource[];
  errors?: AuditError[];
};

export type ExistingLabelBrief = {
  id: string;
  inspectedAt: string | null;
  inspectorName: string;
  result: QualityLabelResult;
  isActive: boolean;
};

export type OpLookup = {
  productionOrder: string;
  orderNumber: string | null;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  existingLabels: ExistingLabelBrief[];
  hasActiveInspection: boolean;
};

export type OpSuggestion = {
  productionOrder: string;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
};

export type QualityLabel = {
  id: string;
  publicToken: string;
  productionOrder: string;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  orderNumber: string | null;
  inspectedAt: string | null;
  inspectorName: string;
  result: QualityLabelResult;
  notes: string | null;
  viewCount: number;
  isActive: boolean;
  createdAt: string | null;
  publicUrl: string;
  /** Snapshot TOTVS no registro — presente em create/get detalhe. */
  auditMetadata?: AuditMetadata;
  hasAuditMetadata?: boolean;
};

export type CreateLabelPayload = {
  productionOrder: string;
  branch?: string | null;
  result?: QualityLabelResult;
  notes?: string | null;
};

export type LabelsPage = {
  items: QualityLabel[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    is_complete: boolean;
  };
};
