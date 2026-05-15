import type { AdminRagTestResponse } from "../../../../data/api/adminFutureTypes";

export type AdminGuidelineStatus = "active" | "draft" | "review";

export type AdminGuideline = {
  id: string;
  title: string;
  description: string;
  status: AdminGuidelineStatus;
  category: "behavior" | "rag" | "tools" | "safety";
};

export type GuidelineBackendPlaceholders = {
  loadGuidelines?: () => Promise<void>;
  saveGuideline?: (guideline: AdminGuideline) => Promise<void>;
  publishGuideline?: (guidelineId: string) => Promise<void>;
  archiveGuideline?: (guidelineId: string) => Promise<void>;
  testGuidelines?: (question: string) => Promise<AdminRagTestResponse>;
};
