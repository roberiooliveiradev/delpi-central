import type {
  DataQueryDiagnosticDto,
  DataTransformStep,
  DataTransformV2,
  ComunicadoDataSourceBlock,
  MColumnSchemaDto,
} from "@delpi/tv-dashboard-presentation";

export type DataQueryCapabilities = {
  enabled: boolean;
  writeV2Enabled: boolean;
  advancedEditorEnabled: boolean;
  profilingEnabled: boolean;
  explainPlanEnabled: boolean;
  compileCacheEnabled: boolean;
  previewCacheEnabled: boolean;
  phase7TelemetryEnabled: boolean;
  limits?: {
    previewRows: number;
    profileSampleRows: number;
    profileTimeoutMs: number;
    previewDeadlineMaxMs: number;
  };
  profile: "m-delpi-v1";
};

export type DataQueryExplainStep = {
  index: number;
  name: string;
  input: string;
  operation: string;
  cost: "bounded" | "potentially_expensive";
  cancelable: boolean;
};

export type DataQueryExplainPlan = {
  version: number;
  profile?: string;
  output: string | null;
  referencedQueries?: string[];
  steps: DataQueryExplainStep[];
  warnings: Array<{ code: string; stepName: string; operation: string }>;
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
  completionContext: {
    steps: string[];
    columns: string[];
    queries: string[];
    items: Array<{
      label: string;
      insertText: string;
      kind: "step" | "column" | "query";
    }>;
  };
  syntaxTokens: Array<{
    kind: "keyword" | "literal" | "number" | "string" | "identifier" | "function" | "operator";
    startOffset: number;
    endOffset: number;
  }>;
  explainPlan?: DataQueryExplainPlan | null;
  compileMetrics?: { durationMs: number; cache: string };
};

export type DataQueryColumnProfile = {
  sampled: boolean;
  sampleRows: number;
  availableRows: number;
  columns: Array<{
    key: string;
    quality: { valid: number; empty: number; error: number };
    distribution: { distinct: number; repeated: number; distinctRatio: number };
    min: unknown;
    max: unknown;
    minMaxAvailable: boolean;
  }>;
};

export type DataQueryRuntimeError = {
  stepName: string;
  code: string;
  message: string;
  rowIndex?: number;
  column?: string;
};

export type DataQueryRuntimeErrors = {
  count: number;
  sample: DataQueryRuntimeError[];
};

export type DataQueryPreview = {
  /** Schema imutável da Fonte, antes de qualquer etapa M. */
  sourceColumns: MColumnSchemaDto[];
  /** Schema da saída da etapa selecionada. */
  columns: MColumnSchemaDto[];
  rows: Array<Record<string, unknown>>;
  returnedRows: number;
  availableRows: number;
  truncated: boolean;
  isSample: boolean;
  selectedStepName: string | null;
  diagnostics: DataQueryDiagnosticDto[];
  runtimeErrors: DataQueryRuntimeErrors;
  columnProfile?: DataQueryColumnProfile | null;
  executionMs?: number;
  stepMetrics?: Array<{
    stepName: string;
    operation: string;
    durationMs: number;
    inputRows: number;
    outputRows: number;
    inputColumns: number;
    outputColumns: number;
    runtimeErrors: number;
  }>;
  explainPlan?: DataQueryExplainPlan | null;
  profilingStatus?: "idle" | "completed" | "timeout";
};

export type DataQueryDraft = {
  sourceId: string;
  queryName: string;
  persistedTransform?: DataTransformV2;
  persistedBinding?: ComunicadoDataSourceBlock["dataBinding"];
  legacySteps: DataTransformStep[];
  script: string;
  compiled: DataQueryCompileResult | null;
  selectedStepName: string | null;
  dirty: boolean;
  queryNameDirty: boolean;
  undoStack: string[];
  redoStack: string[];
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
