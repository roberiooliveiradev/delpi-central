import type { DisplayFormatCategory, DisplayFormatSpec } from "./types";

export type DisplayFormatValueSource =
  | "authoritative"
  | "representative"
  | "sample"
  | "none";

export type DisplayFormatPreviewOption = {
  formatId: string;
  category: DisplayFormatCategory | string;
  label: string;
  pattern?: string | null;
  compatibleTypes?: string[];
  spec: DisplayFormatSpec;
  preview: string | null;
  convertible: boolean;
  reasonCode?: string | null;
  reason?: string | null;
};

export type DisplayFormatPreviewResponse = {
  locale: string;
  timezone?: string | null;
  semanticType?: string | null;
  valueSource: DisplayFormatValueSource;
  value?: unknown;
  options: DisplayFormatPreviewOption[];
  custom: DisplayFormatPreviewOption;
  selected?: {
    formatId: string;
    preview: string | null;
    convertible: boolean;
    reasonCode?: string | null;
    reason?: string | null;
    category?: string;
    pattern?: string | null;
    spec?: DisplayFormatSpec;
  } | null;
  categories: Array<{ category: string; label: string }>;
};

export type DisplayFormatPreviewRequest = {
  value: unknown;
  semanticType?: string | null;
  locale?: string;
  timezone?: string | null;
  valueSource?: DisplayFormatValueSource;
  customPattern?: string | null;
  selectedSpec?: DisplayFormatSpec | null;
};

export type DisplayFormatPreviewLoader = (
  request: DisplayFormatPreviewRequest,
) => Promise<DisplayFormatPreviewResponse>;
