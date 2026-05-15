export type AdminLlmStatus = {
  provider: string;
  model: string;
  temperature: number;
  maxTokens: number;
};

export type AdminKnowledgeDocument = {
  id: string;
  title: string;
  sourceType: string;
  sourceRef: string | null;
  active: boolean;
  chunkCount: number;
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
};

export type AdminKnowledgeDocumentsResponse = {
  items: AdminKnowledgeDocument[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  filters: {
    search: string;
    active: boolean | null;
  };
};

export type AdminAuditLog = {
  id: number;
  userId: string | null;
  action: string;
  promptHash: string | null;
  context: string | null;
  toolCalls: unknown[] | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
};

export type AdminMetricsDistributionItem = {
  key: string;
  count: number;
};

export type AdminMetricsSummary = {
  sessions: number;
  messages: number;
  knowledgeDocuments: number;
  activeKnowledgeDocuments: number;
  knowledgeChunks: number;
  auditLogs: number;
  recentToolCalls24h: number;
  recentErrors24h: number;
  recentAuditLogs24h?: number;
  toolUsageRate24h?: number;
  errorRate24h?: number;
  actionDistribution24h?: AdminMetricsDistributionItem[];
  contextDistribution24h?: AdminMetricsDistributionItem[];
  errorDistribution24h?: AdminMetricsDistributionItem[];
  advanced?: {
    latencyAvgMs?: number | null;
    tokensUsed?: number | null;
    estimatedCost?: number | null;
    ragFailures?: number | null;
    assertivenessRate?: number | null;
    agentMetrics?: AdminMetricsDistributionItem[];
    userProfileMetrics?: AdminMetricsDistributionItem[];
    notes?: string[];
  };
};


export type AdminGuidelineStatus = "draft" | "active" | "archived";

export type AdminGuidelineCategory = "behavior" | "rag" | "tools" | "safety";
export type AdminGuidelineEnvironment = "global" | "dev" | "homolog" | "prod";

export type AdminGuideline = {
  id: string;
  title: string;
  description: string;
  content: string;
  category: AdminGuidelineCategory;
  environment?: AdminGuidelineEnvironment;
  status: AdminGuidelineStatus;
  metadata?: Record<string, unknown>;
  createdBy?: string | null;
  updatedBy?: string | null;
  publishedAt?: string | null;
  archivedAt?: string | null;
  createdAt?: string | null;
  updatedAt?: string | null;
};


export type AdminGuidelineVersion = {
  id: string;
  guidelineId: string;
  version: number;
  title: string;
  description: string;
  content: string;
  category: AdminGuidelineCategory;
  environment?: AdminGuidelineEnvironment;
  status: AdminGuidelineStatus;
  event: "saved" | "published" | "archived" | string;
  metadata?: Record<string, unknown>;
  createdBy?: string | null;
  createdAt?: string | null;
};


export type AdminGuidelineVersionComparison = {
  guidelineId: string;
  fromVersion: AdminGuidelineVersion;
  toVersion: AdminGuidelineVersion;
  changes: Array<{
    field: string;
    from: string | null;
    to: string | null;
  }>;
};

export type AdminRagTestRequest = {
  question: string;
  documentId?: string;
  guidelineId?: string;
};

export type AdminRagTestResponse = {
  answerPreview: string;
  score: number;
  matchedDocuments: Array<{
    id: string;
    title: string;
    score: number;
    sourceType?: string | null;
    sourceRef?: string | null;
  }>;
  triggeredGuidelines: Array<{
    id: string;
    title: string;
    category?: string;
    status?: string;
    description?: string | null;
  }>;
  appliedGuidelines?: Array<{
    id: string;
    title: string;
    category?: string;
    status?: string;
    description?: string | null;
  }>;
  chunks?: Array<{
    id: string;
    documentId: string;
    title: string;
    sourceType?: string | null;
    sourceRef?: string | null;
    chunkIndex?: number | null;
    score: number;
    preview: string;
  }>;
  debugContext?: {
    question: string;
    guidelineCount: number;
    documentCount: number;
    chunkCount: number;
    hasActiveGuidelines: boolean;
    hasRagContext: boolean;
    limit: number;
    filters: {
      includeGlobal: boolean;
      documentId?: string | null;
    };
    safeContextPreview: string;
  };
  comparison?: {
    withGuidelines: {
      enabled: boolean;
      guidelineCount: number;
      summary: string;
    };
    withoutGuidelines: {
      enabled: boolean;
      guidelineCount: number;
      summary: string;
    };
    withRag: {
      enabled: boolean;
      chunkCount: number;
      documentCount: number;
      summary: string;
    };
    withoutRag: {
      enabled: boolean;
      chunkCount: number;
      documentCount: number;
      summary: string;
    };
  };
};

export type AdminExternalActionCatalogItem = {
  id: string;
  name: string;
  provider: string;
  status: "ok" | "warning" | "error" | "unknown";
  calls24h: number;
  lastRunAt?: string | null;
};

export type AdminToolHealthResponse = {
  items: Array<{
    id: string;
    label: string;
    status: "ok" | "warning" | "error" | "unknown";
    description: string;
  }>;
};

export type AdminAuditQuery = {
  search?: string;
  context?: string;
  action?: string;
  userId?: string;
  limit?: number;
  offset?: number;
};

export type AdminAuditExportResponse = {
  downloadUrl: string;
};


export type AdminRbacSummary = {
  userId?: string | null;
  isSuperadmin: boolean;
  roles: string[];
  permissions: string[];
  capabilities: {
    canCreateGuidelines: boolean;
    canPublishGuidelines: boolean;
    canArchiveGuidelines: boolean;
    canDeleteKnowledgeDocuments: boolean;
    canReindexKnowledgeDocuments: boolean;
    canViewAudit: boolean;
    canExportAudit: boolean;
    canManageTools: boolean;
    canUseTools: boolean;
    canViewAdmin: boolean;
  };
  matrix: Array<{
    key: string;
    label: string;
    allowed: boolean;
    requiredPermission: string;
  }>;
};
