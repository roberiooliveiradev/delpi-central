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
      operation: DataQueryInsertOperation;
      arguments: Record<string, unknown>;
    }
  | { type: "replace_step_expression"; stepName: string; expression: string }
  | { type: "rename_step"; stepName: string; newName: string }
  | { type: "move_step"; stepName: string; targetIndex: number }
  | { type: "remove_step"; stepName: string }
  | { type: "rename_query"; from: string; to: string }
  | { type: "format_script" };

export type DataQueryInsertOperation =
  | "rename"
  | "select"
  | "remove_columns"
  | "reorder_columns"
  | "filter"
  | "sort"
  | "replace"
  | "keepRows"
  | "removeRows"
  | "range_rows"
  | "distinct_rows"
  | "remove_errors"
  | "replace_errors"
  | "changeType"
  | "fillDown"
  | "fill_up"
  | "firstRowAsHeader"
  | "transpose"
  | "reverse_rows"
  | "duplicate_column"
  | "split_column"
  | "add_index"
  | "add_custom_column"
  | "add_conditional_column"
  | "transform_column"
  | "group_rows"
  | "pivot"
  | "unpivot"
  | "append_queries"
  | "nested_join"
  | "expand_table_column";

export type DataQueryFunction = {
  name: string;
  kind: "transform" | "scalar";
  category: string;
  signature: string;
  description: string;
  parameters: string[];
  examples: string[];
  introducedIn: string;
  availability: {
    ribbon: boolean;
    formulaBar: boolean;
    advancedEditor: boolean;
  };
};
