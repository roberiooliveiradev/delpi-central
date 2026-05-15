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

export type AdminMetricsSummary = {
  sessions: number;
  messages: number;
  knowledgeDocuments: number;
  activeKnowledgeDocuments: number;
  knowledgeChunks: number;
  auditLogs: number;
  recentToolCalls24h: number;
  recentErrors24h: number;
};


export type AdminGuidelineStatus = "draft" | "active" | "archived";

export type AdminGuidelineCategory = "behavior" | "rag" | "tools" | "safety";

export type AdminGuideline = {
  id: string;
  title: string;
  description: string;
  content: string;
  category: AdminGuidelineCategory;
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
