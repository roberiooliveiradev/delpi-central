export type QualityLabelResult = "approved" | "rejected" | "conditional";

export type ExistingLabelBrief = {
  id: string;
  inspectedAt: string | null;
  inspectorName: string;
  result: QualityLabelResult;
  isActive: boolean;
};

export type OpLookup = {
  productionOrder: string;
  orderNumber: string | null;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  existingLabels: ExistingLabelBrief[];
  hasActiveInspection: boolean;
};

export type OpSuggestion = {
  productionOrder: string;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
};

export type QualityLabel = {
  id: string;
  publicToken: string;
  productionOrder: string;
  branch: string | null;
  branchName: string | null;
  productCode: string;
  productDescription: string;
  productUnit: string | null;
  orderNumber: string | null;
  inspectedAt: string | null;
  inspectorName: string;
  result: QualityLabelResult;
  notes: string | null;
  viewCount: number;
  isActive: boolean;
  createdAt: string | null;
  publicUrl: string;
};

export type CreateLabelPayload = {
  productionOrder: string;
  branch?: string | null;
  result?: QualityLabelResult;
  notes?: string | null;
};

export type LabelsPage = {
  items: QualityLabel[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    is_complete: boolean;
  };
};
