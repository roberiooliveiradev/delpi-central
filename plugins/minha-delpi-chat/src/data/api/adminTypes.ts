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
  metadata: Record<string, unknown> | null;
  createdAt: string;
  updatedAt: string;
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
