import type {
  DataQueryDiagnosticDto,
  DataTransformStep,
  DataTransformV2,
  MColumnSchemaDto,
} from "@delpi/tv-dashboard-presentation";

export type DataQueryCapabilities = {
  enabled: boolean;
  writeV2Enabled: boolean;
  advancedEditorEnabled: boolean;
  profile: "m-delpi-v1";
};

export type DataQueryCompiledStep = {
  name: string;
  operation: string;
  label: string;
  formula: string;
};

export type DataQueryCompileResult = {
  profile: string;
  canonicalScript: string | null;
  scriptHash: string;
  outputStepName: string | null;
  steps: DataQueryCompiledStep[];
  diagnostics: DataQueryDiagnosticDto[];
  referencedQueries: string[];
};

export type DataQueryPreview = {
  columns: MColumnSchemaDto[];
  rows: Array<Record<string, unknown>>;
  returnedRows: number;
  availableRows: number;
  truncated: boolean;
  isSample: boolean;
  selectedStepName: string | null;
  diagnostics: DataQueryDiagnosticDto[];
};

export type DataQueryDraft = {
  sourceId: string;
  queryName: string;
  persistedTransform?: DataTransformV2;
  legacySteps: DataTransformStep[];
  script: string;
  compiled: DataQueryCompileResult | null;
  selectedStepName: string | null;
  dirty: boolean;
};

export type DataQueryMutationAction =
  | {
      type: "convert_legacy";
      legacySteps: DataTransformStep[];
    }
  | {
      type: "insert_step";
      afterStepName?: string | null;
      stepName?: string;
      operation: string;
      arguments: Record<string, unknown>;
    }
  | { type: "replace_step_expression"; stepName: string; expression: string }
  | { type: "rename_step"; stepName: string; newName: string }
  | { type: "move_step"; stepName: string; targetIndex: number }
  | { type: "remove_step"; stepName: string }
  | { type: "rename_query"; from: string; to: string }
  | { type: "format_script" };

export type DataQueryFunction = {
  name: string;
  category: string;
  signature: string;
  description: string;
  examples: string[];
};
