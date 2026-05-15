import type { AdminRagTestResponse } from "../../../../data/api/adminTypes";
import type { AdminGuideline } from "../../../../data/api/adminTypes";
import type { SaveAdminGuidelinePayload } from "../../../../data/api/adminApi";

export type { AdminGuideline };

export type GuidelineBackendPlaceholders = {
  guidelines: AdminGuideline[];
  saveGuideline: (payload: SaveAdminGuidelinePayload) => Promise<void>;
  publishGuideline: (guidelineId: string) => Promise<void>;
  archiveGuideline: (guidelineId: string) => Promise<void>;
  reloadAdminData?: () => Promise<void>;
  testGuidelines?: (question: string) => Promise<AdminRagTestResponse>;
};
