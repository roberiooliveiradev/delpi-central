/** DTOs do contrato M DELPI. Sem parser, análise semântica ou execução M. */

export type SourceRangeDto = {
  startLine: number;
  startColumn: number;
  endLine: number;
  endColumn: number;
  startOffset: number;
  endOffset: number;
};

export type DataQueryDiagnosticDto = {
  code: string;
  severity: "error" | "warning" | "info";
  message: string;
  range?: SourceRangeDto;
  hint?: string;
};

export type MTypeKind =
  | "any"
  | "null"
  | "text"
  | "number"
  | "logical"
  | "date"
  | "datetime"
  | "duration"
  | "table"
  | "list"
  | "record"
  | "error";

export type MColumnSchemaDto = {
  key: string;
  label: string;
  type: MTypeKind;
  nullable: boolean;
  typeSource: "declared" | "inferred" | "unknown";
};

export type TransformOperationDto =
  | "rename"
  | "select"
  | "filter"
  | "addColumn"
  | "replace"
  | "sort"
  | "keepRows"
  | "removeRows"
  | "changeType"
  | "fillDown"
  | "firstRowAsHeader"
  | "groupBy"
  | "pivot"
  | "unpivot"
  | "merge";

export type TransformPlanStepDto = {
  name: string;
  operation: TransformOperationDto;
  input: string;
};

export type TransformPlanDto = {
  version: 1;
  profile: "m-delpi-v1";
  steps: readonly TransformPlanStepDto[];
  output: string;
  referencedQueries: readonly string[];
};

export type DataTransformV2 = {
  version: 2;
  language: "m-delpi-v1";
  script: string;
};

export function isDataTransformV2(value: unknown): value is DataTransformV2 {
  if (!value || typeof value !== "object") return false;
  const record = value as Record<string, unknown>;
  return (
    record.version === 2 &&
    record.language === "m-delpi-v1" &&
    typeof record.script === "string"
  );
}
