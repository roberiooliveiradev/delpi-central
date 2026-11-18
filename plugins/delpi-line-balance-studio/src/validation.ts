export type IssueCode =
  | "REQUIRED"
  | "INVALID_NUMBER"
  | "INVALID_CLOCK_TIME"
  | "AMBIGUOUS_SHIFT"
  | "EMPTY_BREAK"
  | "BREAK_OUTSIDE_SHIFT"
  | "BREAK_OVERLAP"
  | "NO_PRODUCTIVE_TIME"
  | "DUPLICATE_ID"
  | "UNKNOWN_OPERATION"
  | "UNKNOWN_STATION"
  | "DUPLICATE_ASSIGNMENT";

export type ValidationIssue = Readonly<{ path: string; code: IssueCode }>;

export type ValidationResult<T> =
  | Readonly<{ ok: true; value: T }>
  | Readonly<{ ok: false; issues: readonly ValidationIssue[] }>;
