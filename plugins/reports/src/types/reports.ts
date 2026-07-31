export type ReportDefinition = {
  id: string;
  name: string;
  providerKey: string;
  params: Record<string, unknown>;
  active: boolean;
  createdByUserId: string | null;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ReportDefinitionsList = {
  items: ReportDefinition[];
  total: number;
};

export type ReportRecipient = {
  id: string;
  definitionId: string;
  userId: string;
  email: string;
  active: boolean;
};

export type ReportSchedule = {
  id: string;
  definitionId: string;
  scheduleKind: "daily" | "weekly" | "weekdays" | string;
  cronExpression: string | null;
  timezone: string;
  nextRunAt: string | null;
  enabled: boolean;
  hour: number | null;
  minute: number | null;
  weekday: number | null;
};

export type ReportDelivery = {
  id: string;
  runId: string;
  recipientEmail: string;
  status: string;
  error: string | null;
  sentAt: string | null;
};

export type ReportRun = {
  id: string;
  definitionId: string;
  trigger: string;
  status: string;
  startedAt: string | null;
  finishedAt: string | null;
  summary: Record<string, unknown>;
  error: string | null;
  createdAt: string | null;
  deliveries?: ReportDelivery[];
};

export type DirectoryUser = {
  id: string;
  name: string;
  email: string;
};

export type ShortageItemNote = {
  id: string;
  definitionId: string;
  branch: string;
  productCode: string;
  noteText: string;
  expectedReceiptDate: string | null;
  authorUserId: string;
  authorDisplayName: string;
  createdAt: string | null;
  updatedAt: string | null;
};

export type ShortageItemNotesList = {
  items: ShortageItemNote[];
  total: number;
  definitionId: string;
  branch: string;
};

export type ShortagePreviewItem = {
  product_code: string;
  product_description?: string;
  observation?: string;
};
