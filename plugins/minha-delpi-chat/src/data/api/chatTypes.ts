export type ChatSession = {
  id: string;
  title: string | null;
  context: string | null;
  project_id: string | null;
  agent_id: string | null;
  is_pinned: boolean;
  pinned_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ChatSource = {
  id?: string;
  documentId?: string;
  title?: string | null;
  sourceType?: string | null;
  sourceRef?: string | null;
  qualityScore?: number | null;
  isOfficial?: boolean | null;
  chunkIndex?: number | null;
  score?: number | null;
  scope?: string | null;
  agentId?: string | null;
  projectId?: string | null;
  sessionId?: string | null;
  attachmentId?: string | null;
};

export type ChatKpiCard = {
  label: string;
  value: string | number;
  unit?: string;
  dataType?: "text" | "number" | "currency" | "date" | "percent" | "quantity" | "days";
  key?: string;
  trend?: "up" | "down" | "stable";
  delta?: string;
  color?: string;
};

export type ChatTreeNode = {
  id: string;
  label: string;
  subtitle?: string;
  badge?: string;
  meta?: Record<string, string | number>;
  /** Legenda humanizada gerada pela API (estoque, etc.). */
  metaCaption?: string;
  children?: ChatTreeNode[];
};

export type ChatPresentation =
  | {
      type: "table";
      title: string;
      /** Papel no stack humanizado — emitido pela API (Playbook 12 R1). */
      role?: string;
      columns: {
        key: string;
        label: string;
        dataType?: "text" | "number" | "currency" | "date" | "percent" | "quantity" | "days";
      }[];
      rows: Record<string, unknown>[];
    }
  | {
      type: "chart";
      title: string;
      chartType:
        | "bar"
        | "line"
        | "pie"
        | "area"
        | "horizontal_bar"
        | "donut"
        | "grouped_bar"
        | "stacked_bar"
        | "multi_line"
        | "combo"
        | "scatter"
        | "histogram"
        | "gauge"
        | "heatmap";
      data: Record<string, unknown>[];
      config?: {
        xAxis?: string;
        yAxis?: string | string[];
        valueKey?: string;
        numericColumns?: string[];
        categoryColumns?: string[];
        recommendedChartType?: string;
        colors?: string[];
        legend?: boolean;
        comboBarKey?: string;
        comboLineKey?: string;
        gaugeValueKey?: string;
        gaugeTargetKey?: string | null;
        fieldLabels?: Record<string, string>;
        fieldFormats?: Record<string, string>;
      };
      chartExplanation?: string;
    }
  | {
      type: "kpi";
      title: string;
      cards: ChatKpiCard[];
    }
  | {
      type: "dashboard";
      title: string;
      panels: {
        id: string;
        title?: string;
        presentation: Extract<
          ChatPresentation,
          { type: "kpi" } | { type: "chart" } | { type: "table" }
        >;
        /** Gráfico alternativo para o painel de itens (toggle no MFE). */
        chartPresentation?: Extract<ChatPresentation, { type: "chart" }>;
      }[];
    }
  | {
      type: "tree";
      title: string;
      root: ChatTreeNode;
    }
  | {
      type: "json";
      title: string;
      data: unknown;
    }
  | {
      type: "markdown";
      title: string;
      markdown: string;
    };

export type ChatStoryBlockKind =
  | "verdict"
  | "fact"
  | "analysis"
  | "hypothesis"
  | "recommendation"
  | "limitation";

export type ChatStoryBlock = {
  kind: ChatStoryBlockKind;
  title?: string | null;
  text: string;
  status?: "ok" | "attention" | "critical" | "unknown" | null;
  confirmed?: boolean | null;
  query?: string | null;
};

export type ChatStoryPresentation = {
  type: "story";
  title?: string | null;
  blocks: ChatStoryBlock[];
};

export type ChatDataAnswerSummary = {
  answer?: string | null;
  meaning?: string | null;
  riskLevel?: "ok" | "attention" | "critical" | "undefined" | null;
  nextAction?: string | null;
  attention?: string[] | null;
};

export type ChatDataAnswer = {
  summary?: ChatDataAnswerSummary | null;
  facts?: Array<{ text?: string }> | null;
  analysis?: string[] | null;
  hypotheses?: Array<{ text?: string; confirmed?: boolean }> | null;
  recommendations?: Array<{
    label?: string;
    query?: string;
    reason?: string;
  }> | null;
  limitations?: string[] | null;
  profileKey?: string | null;
};

export type ChatDataCoverageNotice = {
  kind?: "pagination" | "depth" | "preview" | "partial" | string;
  message: string;
  messages?: string[];
  details?: Record<string, unknown>;
  page?: number;
  pageSize?: number;
  totalPages?: number;
  total?: number;
  maxDepth?: number;
};

export type ChatPaginationState = {
  page: number;
  pageSize: number;
  totalPages?: number;
  total?: number;
  hasPrevious: boolean;
  hasNext: boolean;
};

export type ChatDepthState = {
  maxDepth: number;
  canIncrease: boolean;
};

export type ChatStreamActivityEntry = {
  id: string;
  at?: number;
  level?: "info" | "success" | "warning" | "error" | string;
  phase?: string;
  group?: string;
  verb?: string;
  target?: string;
  state?: "active" | "done" | "failed" | string;
  message: string;
  detail?: string;
  path?: string;
  statusCode?: number;
  actionId?: string;
};

export type ChatWebSearchSourceQuality = {
  hostname?: string;
  type?: string | null;
  confidence?: "high" | "medium" | "low" | string | null;
};

export type ChatWebSearchResearchSite = {
  hostname: string;
  url: string;
  title?: string;
  sourceType?: string | null;
  qualityScore?: number | null;
  isOfficial?: boolean | null;
  sourceQuality?: ChatWebSearchSourceQuality | null;
};

export type ChatWebSearchResearchStep = {
  id: string;
  type: "search" | "synthesis" | "organize" | string;
  message: string;
  query?: string;
  state?: "active" | "done" | string;
  sites?: ChatWebSearchResearchSite[];
};

export type ChatWebSearchResearch = {
  sourceCount: number;
  durationMs?: number;
  provider?: string | null;
  query?: string | null;
  attemptedQueries?: string[] | null;
  searchStatus?: string | null;
  searchMode?: "quick" | "deep" | string | null;
  searchIntent?: string | null;
  preferOfficial?: boolean | null;
  querySecurity?: {
    redacted?: boolean;
    warnings?: string[];
  } | null;
  confidence?: "high" | "medium" | "low" | string | null;
  sourceTypes?: string[] | null;
  warnings?: string[] | null;
  excludedSources?: Array<{ hostname?: string; url?: string; reason?: string }> | null;
  integrationMode?: string | null;
  integrationProductCode?: string | null;
  integrationAttachment?: string | null;
  synthesized?: boolean;
  steps?: ChatWebSearchResearchStep[];
  sites?: ChatWebSearchResearchSite[];
};

export type ChatPresentationReadingLayers = {
  quick?: string[];
  diagnostic?: string[];
  evidence?: string[];
};

export type ChatPresentationDecision = {
  selected?: string | null;
  fallback?: string | null;
  reason?: string | null;
  purpose?: string | null;
  message?: string | null;
  layoutMode?: "stack" | "single" | null;
  visualOrder?: string[] | null;
  insight?: string | null;
  chartExplanation?: string | null;
  dashboardExplanation?: string | null;
  recommendations?: Array<{
    view?: string;
    label: string;
    reason?: string;
    query: string;
  }> | null;
  policyNotice?: string | null;
  availableViews?: string[] | null;
  scores?: Record<string, number> | null;
  readingLayers?: ChatPresentationReadingLayers | null;
  presentationProfileKey?: string | null;
  stackPresentationPlan?: Record<string, unknown> | null;
  dataShape?: {
    rows?: number;
    columns?: number;
    hasDate?: boolean;
    hasNumeric?: boolean;
    hasCategory?: boolean;
    hasHierarchy?: boolean;
    recommended?: string | null;
  } | null;
  intent?: string | null;
};

export type ChatToolCall = {
  name?: string;
  arguments?: Record<string, unknown>;
  reason?: string | null;
  metadata?: (Record<string, unknown> & {
    presentationDecision?: ChatPresentationDecision | null;
    storyPresentation?: ChatStoryPresentation | null;
    dataAnswer?: ChatDataAnswer | null;
    presentation?: ChatPresentation | null;
    responsePreview?: string | null;
    actionId?: string | null;
    provider?: string | null;
    method?: string | null;
    path?: string | null;
    statusCode?: number | null;
    ok?: boolean | null;
  }) | null;
};

export type ChatCanvasOpenPayload = {
  title: string;
  markdown: string;
  messageId?: string | null;
  sourceMessageId?: string | null;
  version?: number | null;
  documentType?: string | null;
};

export type ChatMessageBranch = {
  currentIndex: number;
  total: number;
  siblingIds: string[];
};

export type ChatFollowUpSuggestion = {
  id?: string;
  label: string;
  query: string;
  icon?: string;
  group?: string;
  kind?: "primary" | "secondary" | "ghost" | "danger";
  tooltip?: string;
  requiresConfirmation?: boolean;
  confirmationMessage?: string;
  disabledReason?: string;
  /** Ação no cliente sem novo turno (ex.: explain_chart). */
  inlineAction?: string;
};

export type ChatGuidedFlowStep = {
  order: number;
  text: string;
  suggestion?: ChatFollowUpSuggestion | null;
};

export type ChatGuidedFlow = {
  id: string;
  title: string;
  intro?: string | null;
  steps: ChatGuidedFlowStep[];
};

export type ChatGuidedFlowCard = {
  title: string;
  description?: string | null;
  flowId?: string | null;
  suggestions: ChatFollowUpSuggestion[];
};

export type AssistantCatalogFeature = {
  id: string;
  title: string;
  category: string;
  status?: string;
  summary?: string;
  requiresAgent?: boolean;
  helpTopicId?: string | null;
  examples?: string[];
  howToUse?: string[];
  relatedFeatures?: string[];
};

export type AssistantCatalogQuickPrompt = {
  id: string;
  label: string;
  query: string;
};

export type AssistantCatalogCategory = {
  id: string;
  label: string;
  features: AssistantCatalogFeature[];
};

export type AssistantCatalogAvailability = {
  availableNow: AssistantCatalogFeature[];
  requiresAgent: AssistantCatalogFeature[];
  requiresPermission: AssistantCatalogFeature[];
  requiresProfilePermission?: AssistantCatalogFeature[];
  disabled: AssistantCatalogFeature[];
};

export type AssistantCatalogUserContext = {
  canUseTools: boolean;
  isSuperadmin: boolean;
  canOpenAdmin?: boolean | null;
};

export type AssistantContextualHighlight = {
  featureId?: string | null;
  title: string;
  description?: string;
  exampleQuery?: string | null;
  releaseVersion?: string | null;
};

export type AssistantOnboardingStarterCard = {
  id: string;
  label: string;
  description?: string;
  query: string;
};

export type AssistantOnboardingTourStep = {
  id: string;
  title: string;
  body?: string;
  /** Alvo do spotlight (`data-tour` no DOM). */
  target?: string;
  /** Texto digitado em tempo real no composer. */
  demoQuery?: string;
  /** Abre o menu + do composer neste passo. */
  openPlusMenu?: boolean;
  /** Chips de demonstração (passo «próximos passos»). */
  demoSuggestions?: { label: string; query: string }[];
};

export type AssistantOnboardingProfile = {
  id: string;
  label: string;
  subtitle?: string;
};

export type AssistantOnboardingPayload = {
  welcome: {
    title: string;
    subtitle?: string;
  };
  profiles?: AssistantOnboardingProfile[];
  selectedProfileId?: string | null;
  starterCards: AssistantOnboardingStarterCard[];
  tourSteps: AssistantOnboardingTourStep[];
  idleHints?: string[];
};

export type AssistantCatalogResponse = {
  version: string;
  query?: string | null;
  webSearchEnabled: boolean;
  agentId?: string | null;
  agentName?: string | null;
  features: AssistantCatalogFeature[];
  categories: AssistantCatalogCategory[];
  availability: AssistantCatalogAvailability;
  quickPrompts: AssistantCatalogQuickPrompt[];
  categoryLabels: Record<string, string>;
  releaseNotesPreview?: string | null;
  releaseVersion?: string | null;
  contextualHighlights?: AssistantContextualHighlight[];
  onboarding?: AssistantOnboardingPayload;
  userContext?: AssistantCatalogUserContext;
};

export type ChatMessageMetadata = {
  sources?: ChatSource[];
  toolCalls?: ChatToolCall[];
  canvasOpen?: ChatCanvasOpenPayload | null;
  canvas?: {
    active?: boolean;
    title?: string;
    documentType?: string;
    version?: number;
    lastOperation?: string;
  } | null;
  canvasFollowUpSuggestions?: ChatFollowUpSuggestion[];
  attachmentSourceCitation?: {
    filenames?: string[];
    note?: string;
  } | null;
  errorHandling?: {
    type?: string;
    severity?: string;
    recoverable?: boolean;
    title?: string;
    userMessage?: string;
    reasons?: string[];
    alternativesIntro?: string;
    apiFailed?: boolean;
    affirmsNonExistence?: boolean;
    suggestions?: string[];
    action?: string;
    params?: Record<string, unknown>;
    attempted?: string;
    records?: number;
    durationMs?: number;
  } | null;
  errorRecoveryFollowUpSuggestions?: ChatFollowUpSuggestion[];
  errorHandlingEnrichedAnswer?: string | null;
  interactivity?: {
    consolidated?: boolean;
    maxPrimary?: number;
    suggestions?: ChatFollowUpSuggestion[];
    moreSuggestions?: Record<string, ChatFollowUpSuggestion[]>;
    contextBar?: {
      items?: { label: string; kind: string; value: string }[];
      summary?: string | null;
    } | null;
    sourceIntent?: string | null;
    suggestionsShown?: string[];
  } | null;
  presentationFollowUpSuggestions?: ChatFollowUpSuggestion[];
  attachmentFollowUpSuggestions?: ChatFollowUpSuggestion[];
  routingDisambiguationSuggestions?: ChatFollowUpSuggestion[];
  webSearchResearch?: ChatWebSearchResearch | null;
  followUpSuggestions?: ChatFollowUpSuggestion[];
  webSearchFollowUpSuggestions?: ChatFollowUpSuggestion[];
  helpFollowUpSuggestions?: ChatFollowUpSuggestion[];
  helpSelfHelp?: {
    topic?: string;
    resolved?: boolean;
    source?: string;
    agentId?: string | null;
    agentName?: string | null;
  };
  onboardingFollowUpSuggestions?: ChatFollowUpSuggestion[];
  milestoneCelebrations?: { id: string; label?: string; message: string }[];
  onboardingMilestonesAchieved?: string[];
  helpErrorFollowUpSuggestions?: ChatFollowUpSuggestion[];
  drawingFollowUpSuggestions?: ChatFollowUpSuggestion[];
  emailFollowUpSuggestions?: ChatFollowUpSuggestion[];
  textCorrectionFollowUpSuggestions?: ChatFollowUpSuggestion[];
  textTaskFollowUpSuggestions?: ChatFollowUpSuggestion[];
  textTaskQuality?: {
    passed?: boolean;
    checks?: { code?: string; message?: string }[];
    subtype?: string;
  };
  textTaskMetrics?: {
    type?: string;
    subtype?: string;
    intent?: string;
    tone?: string;
    audience?: string;
    source?: string;
    deliverFinalOnly?: boolean;
    containsTechnicalTerms?: boolean;
  };
  textAssistant?: {
    intent?: string;
    source?: string;
    audience?: string;
    tone?: string;
    format?: string;
    preserveMeaning?: boolean;
    containsTechnicalTerms?: boolean;
    criticalDataPreserved?: boolean;
    suggestions?: string[];
  };
  textCanvasSuggested?: boolean;
  textCorrectionPreferences?: {
    active?: Record<string, boolean>;
    labels?: string[];
    persisted?: boolean;
  };
  textCorrectionMetrics?: {
    subtype?: string;
    source?: string;
    followUpCount?: number;
    qualityPassed?: boolean;
    preferenceLabels?: string[];
  };
  textCorrectionQuality?: {
    passed?: boolean;
    checks?: { criterion: string; ok: boolean; detail?: string }[];
    warnings?: string[];
  };
  textTask?: {
    type?: string;
    subtype?: string;
    recipient?: string;
    tone?: string;
    audience?: string;
    subject?: string;
    missingFields?: string[];
    inventedFieldsPrevented?: boolean;
    suggestions?: string[];
  };
  emailQuality?: {
    passed?: boolean;
    checks?: { criterion: string; ok: boolean; detail?: string }[];
    warnings?: string[];
  };
  emailDataSource?: {
    title?: string;
    path?: string | null;
    productCode?: string | null;
    lineCount?: number;
  };
  emailPreferences?: {
    active?: Record<string, boolean>;
    labels?: string[];
    persisted?: boolean;
  };
  drawingAnalysisMode?: boolean;
  drawingAnalysis?: Record<string, unknown>;
  drawingAnalysisExport?: {
    filename: string;
    pdfFilename?: string;
    mimeType: string;
    markdown: string;
    csv?: string;
    csvFilename?: string;
    spreadsheetRows?: {
      section: string;
      item: string;
      status: string;
      pdfEvidence: string;
      apiEvidence: string;
      recommendation: string;
    }[];
  };
  guidedFlow?: ChatGuidedFlow | null;
  guidedFlowCards?: ChatGuidedFlowCard[];
  guidedFlowSuggestions?: ChatFollowUpSuggestion[];
  helpContext?: string;
  followUpOutcome?: string;
  personality?: {
    tone?: string;
    humorLevel?: number;
    emojiLevel?: number;
    proactivity?: boolean;
    suggestFollowUps?: boolean;
    riskLevel?: number;
  };
  rag?: {
    enabled?: boolean;
    sourceCount?: number;
    sources?: ChatSource[];
  };
  [key: string]: unknown;
};

export type ChatMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system" | string;
  content: string;
  metadata: ChatMessageMetadata | null;
  created_at: string;
  user_feedback?: -1 | 1 | null;
  user_feedback_reason?: string | null;
  parent_message_id?: string | null;
  branch?: ChatMessageBranch | null;
};

export type ChatFeedbackReasonsPayload = {
  reasons: Array<{ id: string; label: string }>;
  primaryReasonIds: string[];
  downPrompt?: string | null;
  correctiveActions?: Array<Record<string, unknown>>;
};

export type ChatMessageFeedbackResponse = {
  messageId: string;
  userId: string;
  rating: -1 | 1;
  reason?: string;
  comment?: string;
  contextMetadata?: Record<string, unknown>;
  correctiveActions?: Array<{
    id: string;
    label: string;
    action: string;
    query?: string;
  }>;
  thanksMessage?: string;
  createdAt: string;
  updatedAt: string;
} | {
  removed: boolean;
};

export type CreateChatSessionPayload = {
  title?: string;
  context?: string;
  projectId?: string | null;
  agentId?: string | null;
  forkFromSessionId?: string | null;
  forkUntilMessageId?: string | null;
  /** Ao continuar de uma pergunta user: não copia a resposta antiga e reexecuta no cliente. */
  forkResendUserMessage?: boolean;
};

export type ChatAttachment = {
  id: string;
  session_id: string;
  message_id: string | null;
  project_id: string | null;
  agent_id: string | null;
  filename: string;
  original_filename: string;
  content_type: string | null;
  size_bytes: number;
  status: "uploaded" | "indexing" | "indexed" | "unsupported" | "index_failed" | string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type ChatPresentationFormatId =
  | "auto"
  | "text"
  | "table"
  | "tree"
  | "chart"
  | "canvas"
  | "dashboard";

export type ChatResponseModeId = "fast" | "normal" | "thinker";

export type ChatResponseModeOption = {
  id: ChatResponseModeId;
  label: string;
  description: string;
  default?: boolean;
  model?: string;
  maxTokens?: number;
  numCtx?: number;
};

export type ChatResponseModesResponse = {
  enabled: boolean;
  defaultMode: ChatResponseModeId;
  provider: string;
  modes: ChatResponseModeOption[];
};

export type SendChatMessagePayload = {
  message: string;
  context?: string;
  attachmentIds?: string[];
  agentId?: string | null;
  agentIds?: string[];
  projectId?: string | null;
  projectIds?: string[];
  /** Modo explícito: common limpa agente legado na sessão; agent persiste agentId. */
  chatMode?: "common" | "agent";
  responseMode?: ChatResponseModeId;
  /** Preferência de apresentação do turno (table, text, tree, chart, canvas). */
  responseFormat?: ChatPresentationFormatId;
};

export type SendChatMessageResponse = {
  messageId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  playback?: boolean;
  canvasOpen?: ChatCanvasOpenPayload | null;
  adminDebug?: Record<string, unknown> | null;
  metadata?: ChatMessageMetadata | null;
};

export type ChatPlaybackEvent = {
  messageId: string;
  answer: string;
  sources: ChatSource[];
  toolCalls: ChatToolCall[];
  adminDebug?: Record<string, unknown> | null;
  metadata?: ChatMessageMetadata | null;
};

export type ChatArtifact = {
  id: string;
  session_id: string;
  message_id: string | null;
  user_id: string;
  type: "markdown" | "table" | "json" | "report" | string;
  title: string;
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type CreateChatArtifactPayload = {
  type: "markdown" | "table" | "json" | "report" | string;
  title: string;
  content: string;
  messageId?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type UpdateChatArtifactPayload = {
  title?: string;
  content?: string;
  metadata?: Record<string, unknown> | null;
};

export type ChatAgent = {
  id: string;
  name: string;
  description: string | null;
  enabled: boolean;
  metadata: Record<string, unknown> | null;
  owner_user_id: string | null;
  visibility: "system" | "private" | "public" | string;
  category: string | null;
  icon: string | null;
  response_style: string | null;
  max_tool_calls: number;
  requires_confirmation_for_write: boolean;
  access_role: "system" | "owner" | "editor" | "viewer" | string;
  system_prompt?: string | null;
  created_at: string;
  updated_at: string;
  sessions_in_window?: number | null;
  total_sessions?: number | null;
  published_version?: number;
  published_at?: string | null;
  has_unpublished_changes?: boolean;
};

export type ChatAgentVersion = {
  id: string;
  version: number;
  event: string;
  createdAt: string | null;
  createdBy: string | null;
};

export type ChatAgentPreviewDraft = {
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  responseStyle?: string | null;
  category?: string | null;
  icon?: string | null;
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
  metadata?: Record<string, unknown> | null;
};

export type ChatProject = {
  id: string;
  name: string;
  description: string | null;
  instructions: string | null;
  default_agent_id: string | null;
  visibility: "private" | "public" | string;
  icon: string | null;
  color: string | null;
  archived_at: string | null;
  metadata: Record<string, unknown> | null;
  share_conversation_context?: boolean;
  shareConversationContext?: boolean;
  access_role: "owner" | "editor" | "viewer" | string;
  created_at: string;
  updated_at: string;
};

export type CreateChatProjectPayload = {
  name: string;
  description?: string | null;
  instructions?: string | null;
  defaultAgentId?: string | null;
  visibility?: "private" | "public" | string;
  icon?: string | null;
  color?: string | null;
  metadata?: Record<string, unknown> | null;
  shareConversationContext?: boolean;
};

export type UpdateChatProjectPayload = {
  name?: string;
  description?: string | null;
  instructions?: string | null;
  defaultAgentId?: string | null;
  visibility?: "private" | "public" | string;
  icon?: string | null;
  color?: string | null;
  metadata?: Record<string, unknown> | null;
  shareConversationContext?: boolean;
  archived?: boolean;
};

export type CreateChatAgentPayload = {
  name: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: "private" | "public" | string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
};

export type UpdateChatAgentPayload = {
  name?: string;
  description?: string | null;
  systemPrompt?: string | null;
  visibility?: "private" | "public" | string;
  category?: string | null;
  icon?: string | null;
  responseStyle?: string | null;
  metadata?: Record<string, unknown> | null;
  enabled?: boolean;
  maxToolCalls?: number;
  requiresConfirmationForWrite?: boolean;
};

export type ShareChatAgentPayload = {
  targetUserId: string;
  role: "viewer" | "editor" | string;
};

export type ChatAgentExportBundle = {
  exportVersion: number;
  exportedAt: string;
  suggestedKey?: string;
  agent: {
    name: string;
    description?: string | null;
    systemPrompt?: string | null;
    category?: string | null;
    icon?: string | null;
    responseStyle?: string | null;
    visibility?: string;
    enabled?: boolean;
    maxToolCalls?: number;
    requiresConfirmationForWrite?: boolean;
    metadata?: Record<string, unknown> | null;
  };
  actionProviders: Array<{
    providerKey: string;
    enabled: boolean;
    allowRead: boolean;
    allowWrite: boolean;
    allowAdmin: boolean;
    requiresConfirmationForWrite: boolean;
  }>;
  actions: Array<{
    providerKey: string;
    actionId: string;
    enabled: boolean;
    sensitivity: string;
    requiresConfirmation: boolean;
  }>;
};

export type ChatAgentStats = {
  agentId: string;
  windowHours: number;
  sessionsInWindow: number;
  messagesInWindow: number;
  totalSessions: number;
  actionProvidersCount: number;
  sharesCount: number;
  miniDashboard?: Extract<ChatPresentation, { type: "dashboard" }>;
  recommendations?: string[];
};

export type ChatDirectoryUser = {
  id: string;
  name: string;
  email: string;
};

export type ChatAgentShare = {
  id: string;
  target_user_id: string;
  target_user_name?: string | null;
  target_user_email?: string | null;
  role: "viewer" | "editor" | string;
  created_at: string | null;
};

export type ChatProjectShare = ChatAgentShare;

export type ChatAgentPreviewResponse = {
  answer?: string | null;
  answerPreview?: string | null;
  rag?: Record<string, unknown>;
  toolCalls?: ChatToolCall[];
  plannedToolCalls?: ChatToolCall[];
  [key: string]: unknown;
};

export type UpsertChatAgentActionPayload = {
  providerKey: string;
  actionId: string;
  sensitivity?: "read" | "write" | "admin" | string;
  requiresConfirmation?: boolean;
  enabled?: boolean;
};


export type ShareChatProjectPayload = {
  targetUserId: string;
  role: "viewer" | "editor" | string;
};


export type ChatWorkspaceSource = {
  id: string;
  title: string;
  source_type: string;
  source_ref: string | null;
  scope: string | null;
  project_id: string | null;
  agent_id: string | null;
  attachment_id: string | null;
  original_filename: string | null;
  content_type: string | null;
  active: boolean;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
  chunk_count: number | null;
  duplicate?: boolean;
};

export type ChatActionCatalogItem = {
  id: string;
  actionId: string;
  operationId?: string | null;
  method?: string | null;
  path?: string | null;
  summary?: string | null;
  description?: string | null;
  tags?: string[];
  parametersSchema?: Array<Record<string, unknown>>;
  requestBodySchema?: Record<string, unknown> | null;
  responseSchema?: Record<string, unknown> | null;
  sensitivity?: "read" | "write" | "admin" | string;
  enabled?: boolean;
  deprecated?: boolean;
};

export type ChatAgentAction = {
  id: string;
  agentId: string;
  providerKey: string;
  actionId: string;
  enabled: boolean;
  sensitivity: "read" | "write" | "admin" | string;
  requiresConfirmation: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ChatSkillCatalogItem = {
  skillKey: string;
  label: string;
  description: string;
  policyFile: string;
  metadataFlag: string;
  executionHint?: string | null;
};

export type ChatAgentSkillBinding = {
  skillKey: string;
  label: string;
  description: string;
  policyFile: string;
  enabled: boolean;
  executionHint?: string | null;
  derived?: {
    sqlExecutionAvailable?: boolean;
  };
};

export type UpsertChatAgentSkillPayload = {
  skillKey: string;
  enabled: boolean;
};

export type ChatActionProvider = {
  id: string;
  providerKey: string;
  name: string;
  type: string;
  baseUrl: string;
  openApiUrl: string | null;
  privacyPolicyUrl?: string | null;
  authMode: string;
  authConfig?: Record<string, unknown> | null;
  latestSchema?: Record<string, unknown> | null;
  latestSchemaHash?: string | null;
  latestSchemaImportedAt?: string | null;
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
};

export type ChatAgentActionProvider = {
  id: string;
  agentId: string;
  providerKey: string;
  providerName: string;
  providerType: string | null;
  baseUrl: string | null;
  openApiUrl: string | null;
  privacyPolicyUrl?: string | null;
  enabled: boolean;
  allowRead: boolean;
  allowWrite: boolean;
  allowAdmin: boolean;
  requiresConfirmationForWrite: boolean;
  actionCount: number;
  createdAt: string;
  updatedAt: string;
};

export type ChatActionTestResult = {
  ok: boolean;
  statusCode: number | null;
  durationMs: number;
  url: string;
  responsePreview: string | null;
  errorMessage: string | null;
};

export type ChatActionTestLog = ChatActionTestResult & {
  id: string;
  providerKey: string;
  actionId: string;
  method: string;
  requestPayload: Record<string, unknown> | null;
  createdAt: string | null;
};


export type ChatCapabilities = {
  permissions: string[];
  isSuperadmin: boolean;
  canOpenAdmin: boolean;
  canManageAgents: boolean;
  canManageOwnAgents: boolean;
  canManageOfficialAgents: boolean;
  canManageTools: boolean;
  canUseTools: boolean;
};
