export type AdminLlmStatus = {
  provider: string;
  model: string;
  temperature: number;
  maxTokens: number;
};

export type AdminKnowledgeCuratorialFacets = {
  categories: string[];
  namespaces: string[];
  domains: string[];
  tags: string[];
  sourceTypes: string[];
};

export type AdminKnowledgeDocument = {
  id: string;
  title: string;
  sourceType: string;
  sourceRef: string | null;
  active: boolean;
  chunkCount: number;
  metadata: Record<string, unknown> | null;
  category?: string | null;
  tags?: string[];
  namespace?: string | null;
  domain?: string | null;
  priority?: number | null;
  qualityScore?: number | null;
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
    category: string;
    namespace: string;
    domain: string;
    tag: string;
    sourceType: string;
  };
  facets: AdminKnowledgeCuratorialFacets;
};

export type AdminKnowledgeIngestionPipelineStats = {
  version: string;
  enabled: boolean;
  chunkStrategy: string;
  originalChars: number;
  cleanedChars: number;
  charsRemoved: number;
  wordCount: number;
  contentHash: string;
  chunksBeforeDedup: number;
  chunksAfterDedup: number;
  duplicatesRemoved: number;
};

export type AdminKnowledgeIngestionPreviewChunk = {
  index: number;
  charCount: number;
  wordCount: number;
  preview: string;
  metadata: Record<string, unknown>;
};

export type AdminKnowledgeSemanticDuplicate = {
  documentId?: string;
  chunkId?: string;
  title?: string | null;
  sourceType?: string | null;
  similarity: number;
  preview: string;
};

export type AdminKnowledgeIngestionPreviewResponse = {
  title: string;
  sourceType: string;
  sourceRef: string | null;
  contentHash: string;
  wordCount: number;
  cleanedPreview: string;
  chunks: AdminKnowledgeIngestionPreviewChunk[];
  pipeline: AdminKnowledgeIngestionPipelineStats;
  semanticDuplicates?: AdminKnowledgeSemanticDuplicate[];
};

export type UpdateKnowledgeDocumentMetadataPayload = {
  category?: string;
  tags?: string[] | string;
  namespace?: string;
  domain?: string;
  priority?: number;
  qualityScore?: number;
};

export type AdminResponseEvaluationSummary = {
  total: number;
  averageScore: number | null;
  helpfulRate: number | null;
  distribution: Array<{ verdict: string; count: number }>;
  recent24h: number;
};

export type AdminResponseEvaluation = {
  id: number;
  messageId: string;
  sessionId: string;
  evaluatorUserId: string;
  score: number;
  verdict: string;
  comment: string | null;
  suggestions: AdminResponseEvaluationSuggestions;
  metadata: Record<string, unknown>;
  createdAt: string;
  updatedAt: string;
  messagePreview?: string;
  messageCreatedAt?: string;
};

export type AdminResponseEvaluationSuggestionItem = {
  type: string;
  priority?: string;
  reason?: string;
  suggestedAction?: string;
  suggestedTitle?: string;
  suggestedTopic?: string;
  title?: string;
  documentId?: string;
  guidelineId?: string;
};

export type AdminResponseEvaluationSuggestions = {
  documents: AdminResponseEvaluationSuggestionItem[];
  guidelines: AdminResponseEvaluationSuggestionItem[];
  notes: AdminResponseEvaluationSuggestionItem[];
};

export type AdminResponseCandidate = {
  messageId: string;
  sessionId: string;
  contentPreview: string;
  createdAt: string;
  sourceCount: number;
  guidelineCount: number;
  evaluation: AdminResponseEvaluation | null;
};

export type AdminResponseCandidatesResponse = {
  items: AdminResponseCandidate[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
};

export type AdminAgentSpecialization = {
  enabled: boolean;
  presetKey?: string;
  label?: string;
  domain?: string;
  knowledgeDomains?: string[];
  knowledgeNamespaces?: string[];
  knowledgeCategories?: string[];
  knowledgeTags?: string[];
  guidelineCategories?: string[];
  allowedTools?: string[];
  includeGlobalKnowledge?: boolean;
};

export type AdminAgentSpecializationPreset = AdminAgentSpecialization & {
  key: string;
};

export type AdminSpecializedAgent = {
  id: string;
  key: string;
  name: string;
  description: string | null;
  category: string | null;
  visibility: string;
  enabled: boolean;
  hasSpecialization: boolean;
  specialization: AdminAgentSpecialization | null;
};

export type AdminSpecializedAgentsResponse = {
  items: AdminSpecializedAgent[];
};

export type AdminAgentSpecializationPresetsResponse = {
  presets: AdminAgentSpecializationPreset[];
};

export type AdminAgentSpecializationResponse = {
  agentId: string;
  agentKey: string;
  agentName: string;
  enabled: boolean;
  specialization: AdminAgentSpecialization | null;
};

export type AdminResponseEvaluationContext = {
  message: {
    id: string;
    sessionId: string;
    role: string;
    content: string;
    metadata: Record<string, unknown>;
    createdAt: string;
    sourceCount: number;
    guidelineCount: number;
    toolCallCount: number;
  };
  session: {
    id: string | null;
    title: string | null;
    agentKey: string | null;
  };
  userQuestion: string | null;
  evaluation: AdminResponseEvaluation | null;
  suggestedScore: number;
  suggestedVerdict: string;
  suggestions: AdminResponseEvaluationSuggestions;
};

export type AdminAuditLog = {
  id: number;
  userId: string | null;
  action: string;
  promptHash: string | null;
  traceId: string | null;
  context: string | null;
  toolCalls: unknown[] | null;
  metadata: Record<string, unknown> | null;
  createdAt: string;
};

export type AdminAuditTimelineDay = {
  date: string;
  total: number;
  actions: Array<{ action: string; count: number }>;
  recent: AdminAuditLog[];
};

export type AdminAuditTimelineResponse = {
  days: AdminAuditTimelineDay[];
  totalEvents: number;
  dayCount: number;
  filters: AdminAuditLogsResponse["filters"];
};

export type AdminMetricsDistributionItem = {
  key: string;
  count: number;
};

export type AdminLlmCostTableEntry = {
  provider: string;
  model: string;
  promptCostPer1k: number;
  completionCostPer1k: number;
  currency: string;
  source?: string;
};

export type AdminLlmCostBreakdownItem = {
  provider: string;
  model: string;
  messages: number;
  tokensUsed: number;
  estimatedCost: number | null;
};

export type AdminLlmCostTableResponse = {
  entries: AdminLlmCostTableEntry[];
  source: "database" | "env" | string;
};

export type AdminChatIntelligenceSettings = {
  ragContextMinScore: number;
  externalActionSemanticMinScore: number;
  externalActionSemanticRankEnabled: boolean;
  chatToolRouterEnabled: boolean;
  chatHistorySummaryEnabled: boolean;
  ragHybridEnabled: boolean;
  ragRerankEnabled: boolean;
  ragFtsEnabled: boolean;
  nativeToolCallingEnabled: boolean;
  agenticLoopEnabled: boolean;
  agenticLoopMaxSteps: number;
  defaults: {
    ragContextMinScore: number;
    externalActionSemanticMinScore: number;
    externalActionSemanticRankEnabled: boolean;
    chatToolRouterEnabled: boolean;
    chatHistorySummaryEnabled: boolean;
    ragHybridEnabled: boolean;
    ragRerankEnabled: boolean;
    ragFtsEnabled: boolean;
    nativeToolCallingEnabled: boolean;
    agenticLoopEnabled: boolean;
    agenticLoopMaxSteps: number;
  };
};

export type AdminMetricsTimeseriesBucket = {
  start: string;
  end: string;
  auditLogs: number;
  messagesInstrumented: number;
  tokensUsed: number | null;
  estimatedCost: number | null;
  latencyAvgMs: number | null;
};

export type AdminMetricsTimeseriesResponse = {
  windowHours: number;
  bucketHours: number;
  buckets: AdminMetricsTimeseriesBucket[];
};

export type AdminMetricsSummary = {
  windowHours?: number;
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
    instrumentedMessages?: number | null;
    ragFailures?: number | null;
    assertivenessRate?: number | null;
    ragTests24h?: number | null;
    ragTestsAssertive24h?: number | null;
    agentMetrics?: AdminMetricsDistributionItem[];
    userProfileMetrics?: AdminMetricsDistributionItem[];
    costTable?: AdminLlmCostTableEntry[];
    costBreakdown24h?: AdminLlmCostBreakdownItem[];
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

export type AdminAgentSimulateRequest = {
  question: string;
  agentId?: string;
  agentKey?: string;
  documentId?: string;
  sessionId?: string;
  generateAnswer?: boolean;
  executeToolsInSandbox?: boolean;
};

export type AdminAgentSimulateResponse = AdminRagTestResponse & {
  agent?: {
    id: string;
    key: string;
    name: string;
  } | null;
  plannedToolCalls?: Array<{
    name?: string;
    arguments?: Record<string, unknown>;
    reason?: string;
    status?: "planned" | "executed" | string;
    metadata?: Record<string, unknown>;
  }>;
  finalPrompt?: {
    systemPrompt: string;
    messages: Array<{ role: string; content: string }>;
    preview: string;
  };
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
  status?: "ok" | "warning" | "error";
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
  traceId?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
  offset?: number;
  maxDays?: number;
};

export type AdminAuditLogsResponse = {
  items: AdminAuditLog[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
  filters: {
    action: string;
    context: string;
    userId: string;
    traceId: string;
    search: string;
    dateFrom: string;
    dateTo: string;
  };
};

export type AdminAuditExportResponse = {
  items: AdminAuditLog[];
  total: number;
  exportedAt: string;
  filters: AdminAuditLogsResponse["filters"];
};

export type AdminAuditLogDetailResponse = {
  log: AdminAuditLog;
  relatedLogs: AdminAuditLog[];
  traceRelatedLogs: AdminAuditLog[];
};


export type AdminSecurityConfig = {
  enabled: boolean;
  mode: string;
  messageMaxChars: number;
  blockThreshold: number;
  flagThreshold: number;
  rateLimitEnabled: boolean;
  rateLimits: {
    chatMessagesPerWindow: number;
    toolCallsPerWindow: number;
    knowledgeWritesPerWindow: number;
    adminActionsPerWindow: number;
    windowSeconds: number;
  };
  injectionRuleCount: number;
};

export type AdminSecuritySummary = {
  windowHours: number;
  since: string;
  blockedCount: number;
  flaggedCount: number;
  scannedCount: number;
  totalEvents: number;
  flagDistribution: Array<{ flag: string; count: number }>;
};

export type AdminSecurityEvent = {
  id: number;
  userId: string | null;
  action: string;
  promptHash: string | null;
  context: string | null;
  toolCalls: unknown;
  metadata: Record<string, unknown> | null;
  createdAt: string;
};

export type AdminSecurityEventsResponse = {
  items: AdminSecurityEvent[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
};

export type AdminSecurityScanAnalysis = {
  sanitizedPreview: string;
  originalLength: number;
  sanitizedLength: number;
  riskScore: number;
  riskLevel: string;
  flags: string[];
  blocked: boolean;
  flagged: boolean;
  blockReason: string | null;
};

export type AdminSecurityScanResponse = {
  source: string;
  analysis: AdminSecurityScanAnalysis;
  wouldBlock: boolean;
  wouldFlag: boolean;
  config: AdminSecurityConfig;
};

export type AdminChatSkill = {
  id: string;
  skillKey: string;
  label: string;
  description: string;
  policyContent?: string | null;
  policyFile?: string | null;
  metadataFlag: string;
  legacyMetadataFlag?: string | null;
  executionPathHint?: string | null;
  executionDerivedKey?: string | null;
  isActive: boolean;
  sortOrder: number;
  createdAt?: string | null;
  updatedAt?: string | null;
};

export type UpsertAdminChatSkillPayload = {
  skillKey?: string;
  label?: string;
  description?: string;
  policyContent?: string | null;
  policyFile?: string | null;
  metadataFlag?: string;
  legacyMetadataFlag?: string | null;
  executionPathHint?: string | null;
  executionDerivedKey?: string | null;
  isActive?: boolean;
  sortOrder?: number;
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
