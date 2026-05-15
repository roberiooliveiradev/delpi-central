export type AdminFutureApiOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
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

export type AdminGuidelinePayload = {
  id?: string;
  title: string;
  description: string;
  content: string;
  category: "behavior" | "rag" | "tools" | "safety";
  status: "draft" | "active" | "archived";
};

export type AdminGuidelineVersion = {
  id: string;
  guidelineId: string;
  version: number;
  status: "draft" | "published" | "archived";
  createdAt: string;
  createdBy?: string | null;
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
