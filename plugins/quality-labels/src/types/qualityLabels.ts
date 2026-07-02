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
  inspectedQuantity: number | null;
  viewCount: number;
  isActive: boolean;
  createdAt: string | null;
  publicUrl: string;
  /** Snapshot TOTVS no registro — presente em create/get detalhe. */
  auditMetadata?: AuditMetadata;
  hasAuditMetadata?: boolean;
};

export type AuditEventType =
  | "label_created"
  | "label_activated"
  | "label_deactivated"
  | "label_deleted"
  | "label_viewed"
  | "certificate_saved"
  | "certificate_issued";

export type AuditEvent = {
  id: string;
  eventType: AuditEventType | string;
  labelId: string | null;
  productionOrder: string | null;
  productCode: string | null;
  branch: string | null;
  branchName: string | null;
  result: QualityLabelResult | string | null;
  actorUserId: string | null;
  actorName: string | null;
  detail: Record<string, unknown>;
  createdAt: string | null;
};

export type AuditEventsPage = {
  items: AuditEvent[];
  summary: Record<string, number>;
  pagination: {
    total: number;
    limit: number;
    offset: number;
    is_complete: boolean;
  };
};

export type CreateLabelPayload = {
  productionOrder: string;
  branch?: string | null;
  result?: QualityLabelResult;
  notes?: string | null;
  inspectedQuantity?: number | null;
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

export type CertificateSampleType = "amostra" | "lote_piloto" | "fornecimento";

export type CertificateItemStatus = "A" | "R" | "NA";

export type CertificateItem = {
  position: number;
  description: string;
  status: CertificateItemStatus;
  isCustom: boolean;
};

export type Certificate = {
  id: string | null;
  labelId: string;
  docRef: string;
  sampleType: CertificateSampleType;
  quantity: string | null;
  sampleQuantity: string | null;
  customerCode: string | null;
  customerStore: string | null;
  customerName: string | null;
  customerItem: string | null;
  customerItemRev: string | null;
  customerSource: "totvs" | "manual";
  delpiNotes: string | null;
  customerNotes: string | null;
  inspectorName: string | null;
  status: "draft" | "issued";
  hasPdf: boolean;
  issuedAt: string | null;
  updatedAt: string | null;
  items: CertificateItem[];
  // contexto da etiqueta
  productionOrder: string;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  branch: string | null;
  branchName: string | null;
};

export type CertificateSavePayload = {
  sampleType: CertificateSampleType;
  quantity?: string | null;
  sampleQuantity?: string | null;
  customerCode?: string | null;
  customerStore?: string | null;
  customerName?: string | null;
  customerItem?: string | null;
  customerItemRev?: string | null;
  customerSource?: "totvs" | "manual";
  delpiNotes?: string | null;
  customerNotes?: string | null;
  items: Array<{
    position?: number;
    description: string;
    status: CertificateItemStatus;
    isCustom?: boolean;
  }>;
  issue: boolean;
};

export type CustomerHit = {
  code: string;
  store: string;
  name: string;
};

export type Inspector = {
  id?: string;
  userId: string;
  displayName: string;
  roleTitle: string | null;
  hasSignature: boolean;
  signatureUpdatedAt: string | null;
};
