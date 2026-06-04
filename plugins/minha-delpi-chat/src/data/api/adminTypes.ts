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

export type AdminKnowledgeDocumentsSummary = {
  total: number;
  active: number;
  inactive: number;
  pendingIndex: number;
};

export type AdminKnowledgeDocumentsResponse = {
  items: AdminKnowledgeDocument[];
  summary?: AdminKnowledgeDocumentsSummary;
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
    agentId: string | null;
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

export type AdminDrawingAnalysisRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  productCode?: string | null;
  overallStatus?: string | null;
  criticalErrors?: number | null;
  reportExported?: boolean | null;
};

export type AdminIntentRoutingRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  intent?: string | null;
  subIntent?: string | null;
  decision?: string | null;
  ambiguous?: boolean | null;
};

export type AdminIntentRoutingSummary = {
  windowHours: number;
  since: string;
  routesCount: number;
  ambiguousCount: number;
  mixedTaskCount: number;
  webSearchCount: number;
  textSkipToolsCount: number;
  byIntent: Record<string, number>;
  byDecision: Record<string, number>;
  recent: AdminIntentRoutingRecentItem[];
};

export type AdminTextTaskRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  subtype?: string | null;
  type?: string | null;
  intent?: string | null;
  audience?: string | null;
  mixed?: boolean | null;
  qualityPassed?: boolean | null;
};

export type AdminTextTaskFeedbackRecentItem = {
  messageId?: string | null;
  rating?: number | null;
  reason?: string | null;
  textTaskSubtype?: string | null;
  textTaskIntent?: string | null;
  createdAt?: string | null;
};

export type AdminTextTaskFeedbackSummary = {
  feedbackTotal: number;
  feedbackPositive: number;
  feedbackNegative: number;
  feedbackByReason: Record<string, number>;
  feedbackBySubtype: Record<string, number>;
  feedbackRecent: AdminTextTaskFeedbackRecentItem[];
};

export type AdminSessionMemoryAssertivenessFlagCount = {
  key: string;
  count: number;
};

export type AdminSessionMemoryRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  assertivenessScore?: number | null;
  contextLossRisk?: boolean;
  followUpDetected?: boolean;
  entityCount?: number;
  flags?: string[];
};

export type AdminSessionMemoryFeedbackSummary = {
  feedbackTotal: number;
  feedbackPositive: number;
  feedbackNegative: number;
  memoryFeedbackCount: number;
  lostContextFeedbackCount: number;
  feedbackByReason: Record<string, number>;
  feedbackRecent: Record<string, unknown>[];
  alerts?: { code: string; message: string }[];
};

export type AdminSessionMemorySummary = {
  windowHours: number;
  since: string;
  memoryTurnsCount: number;
  entityActiveTurns: number;
  followUpTurns: number;
  followUpResolvedTurns: number;
  followUpResolutionRate?: number | null;
  contextLossRiskTurns: number;
  lowAssertivenessTurns: number;
  ambiguityTurns: number;
  memoryClearedTurns: number;
  assertivenessFlags: AdminSessionMemoryAssertivenessFlagCount[];
  recent: AdminSessionMemoryRecentItem[];
  feedback?: AdminSessionMemoryFeedbackSummary;
  alerts?: { code: string; message: string }[];
};

export type AdminTextTaskSummary = {
  windowHours: number;
  since: string;
  textTasksCount: number;
  mixedTurnCount: number;
  qualityFailedCount: number;
  canvasVersionedCount: number;
  deliverFinalOnlyCount?: number;
  technicalTermCount?: number;
  attachmentSourceCount?: number;
  bySubtype: Record<string, number>;
  byType: Record<string, number>;
  byIntent?: Record<string, number>;
  byAudience?: Record<string, number>;
  byFamily?: Record<string, number>;
  feedback?: AdminTextTaskFeedbackSummary;
  recent: AdminTextTaskRecentItem[];
};

export type AdminInteractivityLabelCount = {
  label: string;
  count: number;
};

export type AdminErrorHandlingTypeCount = {
  type: string;
  count: number;
};

export type AdminErrorHandlingSummary = {
  windowHours: number;
  since: string;
  totalEvents: number;
  recoverableCount: number;
  apiFailedCount: number;
  autoRecoveryPlans?: number;
  recoveryClicksCount?: number;
  recoveryAttemptsCount?: number;
  recoverySuccessCount?: number;
  recoverySuccessRate?: number;
  byType: AdminErrorHandlingTypeCount[];
  recent: Record<string, unknown>[];
};

export type AdminWebSearchCountRow = {
  status?: string;
  mode?: string;
  confidence?: string;
  reason?: string;
  label?: string;
  count: number;
};

export type AdminFeedbackCountRow = {
  key: string;
  count: number;
};

export type AdminFeedbackAlert = {
  code: string;
  message: string;
};

export type AdminQualityUnifiedSummary = {
  windowHours: number;
  since: string;
  health: {
    csat?: number | null;
    errorRate?: number | null;
    toolUsageRate?: number | null;
    latencyAvgMs?: number | null;
    assertivenessRate?: number | null;
    lostContextCount?: number | null;
  };
  feedback: {
    total?: number;
    positive?: number;
    negative?: number;
    topReasons?: AdminFeedbackCountRow[];
    topIntents?: AdminFeedbackCountRow[];
    alerts?: AdminFeedbackAlert[];
  };
  adoption: {
    activeUsers?: number;
    activeSessions?: number;
    messagesSent?: number;
    interactivityClicks?: number;
    chipClickRate?: number | null;
    feedbackRate?: number | null;
  };
  efficiency: {
    latencyAvgMs?: number | null;
    messagesPerSession?: number | null;
    tokensUsed?: number | null;
    estimatedCost?: number | null;
  };
  security: {
    blockedCount?: number;
    flaggedCount?: number;
    scannedCount?: number;
    totalEvents?: number;
  };
};

export type AdminQualityReport = {
  id: number;
  reportType: string;
  periodStart: string;
  periodEnd: string;
  summary: Record<string, unknown>;
  markdown: string;
  createdAt: string;
};

export type AdminQualityIssue = {
  id: number;
  code: string;
  title: string;
  description: string;
  status: string;
  source: string;
  externalUrl?: string | null;
  createdAt?: string;
  metadata?: Record<string, unknown>;
};

export type AdminFeedbackSummary = {
  windowHours: number;
  since: string;
  totalFeedback: number;
  positiveCount: number;
  negativeCount: number;
  csat: number | null;
  lostContextCount: number;
  feedbackByReason: AdminFeedbackCountRow[];
  feedbackByIntent: AdminFeedbackCountRow[];
  feedbackByAgent: AdminFeedbackCountRow[];
  feedbackByToolPath: AdminFeedbackCountRow[];
  feedbackByPresentation: AdminFeedbackCountRow[];
  recentFeedback: Record<string, unknown>[];
  alerts: AdminFeedbackAlert[];
};

export type AdminWebSearchSummary = {
  windowHours: number;
  since: string;
  totalSearches: number;
  officialSourceRate: number;
  withOfficialSourceCount: number;
  lowConfidenceCount: number;
  noResultCount: number;
  redactedQueryCount: number;
  synthesizedCount: number;
  preferOfficialCount: number;
  blockedBySecurityCount: number;
  queryRedactedAuditCount: number;
  averageDurationMs?: number | null;
  followUpClicksCount: number;
  negativeFeedbackCount: number;
  byStatus: AdminWebSearchCountRow[];
  byMode: AdminWebSearchCountRow[];
  byConfidence: AdminWebSearchCountRow[];
  feedbackByReason: AdminWebSearchCountRow[];
  followUpByLabel: AdminWebSearchCountRow[];
  recent: Record<string, unknown>[];
  alerts: string[];
};

export type AdminPresentationLabelCount = {
  label: string;
  count: number;
};

export type AdminPresentationSummary = {
  windowHours: number;
  since: string;
  responsesWithRichPresentation: number;
  eventsCount: number;
  viewSwitchCount: number;
  chartTypeSwitchCount: number;
  axisChangeCount: number;
  exportPngCount: number;
  categoryFilterCount: number;
  switchToTableCount: number;
  engagementRate: number;
  viewSwitchRate: number;
  axisChangeRate: number;
  switchToTableRate: number;
  bySelected: Record<string, number>;
  byPresentationType: Record<string, number>;
  byChartType: Record<string, number>;
  byEvent: Record<string, number>;
  byViewTarget: Record<string, number>;
  byAxisColumn: Record<string, number>;
  byFilterKey: Record<string, number>;
  topSelected: AdminPresentationLabelCount[];
  topEvents: AdminPresentationLabelCount[];
  topViewTargets: AdminPresentationLabelCount[];
  topAxisColumns: AdminPresentationLabelCount[];
  topFilterKeys: AdminPresentationLabelCount[];
  recentImpressions: Record<string, unknown>[];
  recentEvents: Record<string, unknown>[];
  alerts: string[];
};

export type AdminInteractivitySummary = {
  windowHours: number;
  since: string;
  responsesWithChips: number;
  clicksCount: number;
  suggestionsShownTotal: number;
  moreOptionsResponses: number;
  clickThroughRate: number;
  byIntent: Record<string, number>;
  byLabelShown: Record<string, number>;
  byLabelClicked: Record<string, number>;
  byGroupClicked: Record<string, number>;
  ctrByLabel: Record<string, number>;
  topShown: AdminInteractivityLabelCount[];
  topClicked: AdminInteractivityLabelCount[];
  recentImpressions: Record<string, unknown>[];
  recentClicks: Record<string, unknown>[];
};

export type AdminDrawingAnalysisSummary = {
  windowHours: number;
  since: string;
  analysesCount: number;
  uniqueProductCodes: number;
  byStatus: Record<string, number>;
  totalCriticalErrors: number;
  totalErrors: number;
  reportExportedCount: number;
  analyserOkCount: number;
  withPdfCount: number;
  recent: AdminDrawingAnalysisRecentItem[];
};

export type AdminDocumentVisionRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  engine?: string | null;
  context?: string | null;
  legible?: boolean | null;
  durationMs?: number | null;
};

export type AdminDocumentVisionSummary = {
  windowHours: number;
  since: string;
  runsCount: number;
  byEngine: Record<string, number>;
  byContext: Record<string, number>;
  byStage?: Record<string, number>;
  legibleCount: number;
  legibilityRate: number | null;
  avgDurationMs: number | null;
  recent: AdminDocumentVisionRecentItem[];
};

export type AdminSqlAdvancedRecentItem = {
  loggedAt?: string | null;
  action?: string | null;
  mode?: string | null;
  dialect?: string | null;
  blocked?: boolean | null;
};

export type AdminSqlAdvancedSummary = {
  windowHours: number;
  since: string;
  runsCount: number;
  blockedCount: number;
  cteUsageCount: number;
  windowFunctionUsageCount: number;
  incrementalEditCount: number;
  schemaPrefetchCount: number;
  emptyResultCount: number;
  executedWithRowCount: number;
  byMode: Record<string, number>;
  byDialect: Record<string, number>;
  byChartType: Record<string, number>;
  recent: AdminSqlAdvancedRecentItem[];
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
  documentId?: string;
  sessionId?: string;
  generateAnswer?: boolean;
  executeToolsInSandbox?: boolean;
};

export type AdminAgentSimulateResponse = AdminRagTestResponse & {
  agent?: {
    id: string;
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

export type AdminPaginatedResponse<T> = {
  items: T[];
  pagination: {
    limit: number;
    offset: number;
    total: number;
    hasNext: boolean;
    hasPrevious: boolean;
  };
};

export type AdminLearningCandidate = {
  id: number;
  candidateType: string;
  inputText: string;
  term: string | null;
  proposedRule: string | null;
  proposedMeaning: string | null;
  confidence: number | null;
  evidenceCount: number;
  riskLevel: string;
  scope: string;
  projectId: string | null;
  status: string;
  source: string;
  createdBy: string | null;
  reviewerId: string | null;
  promotedTermId: number | null;
  evidence?: Record<string, unknown>;
  createdAt: string | null;
  updatedAt: string | null;
  reviewedAt: string | null;
};

export type AdminVocabularyTerm = {
  id: number;
  term: string;
  normalizedTerm: string;
  meaning: string | null;
  type: string;
  scope: string;
  projectId: string | null;
  source: string;
  confidence: number | null;
  evidenceCount: number;
  approved: boolean;
  active: boolean;
  createdBy: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ReviewLearningCandidatePayload = {
  action: "approve" | "reject" | "promote";
  term?: string;
  normalizedTerm?: string;
  meaning?: string;
};

export type UpsertVocabularyTermPayload = {
  term: string;
  normalizedTerm?: string;
  meaning?: string;
  type?: string;
  scope?: string;
  approved?: boolean;
  active?: boolean;
};

export type AdminMemoryItem = {
  id: number;
  userId: string | null;
  projectId: string | null;
  sessionId: string | null;
  scope: string;
  type: string;
  content: string;
  confidence: number | null;
  evidenceCount: number;
  source: string;
  status: string;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ReviewMemoryItemPayload = {
  action: "forget" | "restore";
};

export type AdminEvaluationCase = {
  id: number;
  category: string;
  input: string;
  expectedIntent: string | null;
  expectedAnswer: string | null;
  expectedNormalized: string | null;
  mustNotUseTools: boolean;
  mustNotUseRag: boolean;
  sourceFeedbackId: number | null;
  linkedCandidateId: number | null;
  status: string;
  lastRunAt: string | null;
  lastPassed: boolean | null;
  lastFailureReason: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type AdminFineTuningSample = {
  id: number;
  datasetId: number | null;
  category: string;
  source: string;
  sourceRef: string | null;
  status: string;
  messages: Array<{ role: string; content: string }>;
  intentLabel: string | null;
  qualityScore: number | null;
  anonymized: boolean;
  riskLevel: string | null;
  createdAt: string | null;
};

export type AdminFineTuningDataset = {
  id: number;
  name: string;
  description: string | null;
  status: string;
  targetModel: string;
  createdAt: string | null;
};

export type CreateEvaluationCasePayload = {
  category?: string;
  input: string;
  expectedIntent?: string;
  expectedAnswer?: string;
  expectedNormalized?: string;
  mustNotUseTools?: boolean;
  mustNotUseRag?: boolean;
};

export type AdminLearningSummary = {
  windowHours: number;
  candidates: {
    total: number;
    byStatus: Record<string, number>;
    byType: Record<string, number>;
    pendingHighConfidence: number;
    recentCreated: number;
    avgPendingConfidence: number | null;
  };
  vocabulary: {
    total: number;
    approved: number;
    activeApproved: number;
    byType: Record<string, number>;
  };
  memory?: {
    total: number;
    active: number;
    forgotten: number;
    byStatus: Record<string, number>;
    byType: Record<string, number>;
  };
  evaluation?: {
    total: number;
    active: number;
    disabled: number;
    failing: number;
    passing: number;
    neverRun: number;
    byCategory: Record<string, number>;
  };
  funnel: {
    created: number;
    recentCreated: number;
    pending: number;
    approved: number;
    rejected: number;
    promoted: number;
    approvalRate: number | null;
    promotionRate: number | null;
  };
  highlights: {
    termDefinitions: number;
    normalizationRules: number;
    pendingHighConfidence: number;
    learnedTermsActive: number;
    memoryItemsActive?: number;
    evaluationCasesFailing?: number;
    evaluationCasesActive?: number;
    fineTuningSamplesApproved?: number;
    fineTuningDatasetsApproved?: number;
    ragGlossaryIndexed?: number;
    ragUserMemoryIndexed?: number;
  };
  fineTuning?: {
    samplesTotal: number;
    samplesApproved: number;
    samplesCaptured: number;
    datasetsApproved: number;
  };
  ragIndex?: {
    glossaryDocuments: number;
    userMemoryDocuments: number;
  };
  dashboard?: {
    topTypoRules: Array<{
      term: string;
      normalizedTerm: string;
      evidenceCount: number;
    }>;
  };
};
