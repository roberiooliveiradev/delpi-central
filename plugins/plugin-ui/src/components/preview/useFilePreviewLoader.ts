import { useEffect, useRef, useState } from "react";

import { parseDocxPreview } from "./docxPreviewModel";
import { parseSpreadsheetPreview } from "./spreadsheetPreviewModel";
import type { FilePreviewContentState, FilePreviewKind, FilePreviewSource } from "./filePreviewTypes";
import { resolveFilePreviewKind } from "./resolveFilePreviewKind";

const LOCAL_TEXT_MAX_CHARS = 80_000;

export type UseFilePreviewLoaderOptions = {
  source: FilePreviewSource | null | undefined;
  mimeType?: string | null;
  fileName?: string | null;
  declaredType?: string | null;
  /** Texto já extraído (API remota) — evita fetch de blob. */
  remoteText?: string | null;
  remoteTextTruncated?: boolean;
  enabled?: boolean;
};

const EMPTY_STATE: FilePreviewContentState = {
  kind: "none",
  loading: false,
  error: null,
  previewUrl: null,
  textContent: null,
  textTruncated: false,
  spreadsheetData: null,
  docxData: null,
};

async function resolveBlob(source: FilePreviewSource): Promise<Blob> {
  if (typeof source === "function") {
    const result = await source();
    if (typeof result === "string") {
      return new Blob([result], { type: "text/plain;charset=utf-8" });
    }
    return result;
  }
  return source;
}

export function useFilePreviewLoader({
  source,
  mimeType,
  fileName,
  declaredType,
  remoteText,
  remoteTextTruncated = false,
  enabled = true,
}: UseFilePreviewLoaderOptions): FilePreviewContentState {
  const kind = resolveFilePreviewKind({ mimeType, fileName, declaredType });
  const [state, setState] = useState<FilePreviewContentState>({
    ...EMPTY_STATE,
    kind,
    loading: Boolean(enabled && source && kind !== "none"),
  });
  const objectUrlRef = useRef<string | null>(null);

  useEffect(() => {
    if (!enabled || !source || kind === "none") {
      setState({ ...EMPTY_STATE, kind });
      return;
    }

    if (kind === "text" && remoteText != null) {
      setState({
        kind,
        loading: false,
        error: remoteText.trim() ? null : "empty",
        previewUrl: null,
        textContent: remoteText.trim() || null,
        textTruncated: remoteTextTruncated,
        spreadsheetData: null,
        docxData: null,
      });
      return;
    }

    let cancelled = false;

    const activeSource = source;

    async function load() {
      setState((current) => ({
        ...current,
        kind,
        loading: true,
        error: null,
        previewUrl: null,
        textContent: null,
        textTruncated: false,
        spreadsheetData: null,
        docxData: null,
      }));

      try {
        const blob = await resolveBlob(activeSource);

        if (kind === "image" || kind === "pdf") {
          const url = URL.createObjectURL(blob);
          if (cancelled) {
            URL.revokeObjectURL(url);
            return;
          }
          if (objectUrlRef.current) URL.revokeObjectURL(objectUrlRef.current);
          objectUrlRef.current = url;
          setState({
            kind,
            loading: false,
            error: null,
            previewUrl: url,
            textContent: null,
            textTruncated: false,
            spreadsheetData: null,
            docxData: null,
          });
          return;
        }

        if (kind === "spreadsheet") {
          const data = await parseSpreadsheetPreview(blob, { fileName: fileName ?? undefined });
          if (cancelled) return;
          setState({
            kind,
            loading: false,
            error: null,
            previewUrl: null,
            textContent: null,
            textTruncated: false,
            spreadsheetData: data,
            docxData: null,
          });
          return;
        }

        if (kind === "docx") {
          const data = await parseDocxPreview(blob);
          if (cancelled) return;
          setState({
            kind,
            loading: false,
            error: null,
            previewUrl: null,
            textContent: null,
            textTruncated: false,
            spreadsheetData: null,
            docxData: data,
          });
          return;
        }

        if (kind === "text") {
          const content = await blob.text();
          if (cancelled) return;
          const trimmed = content.trim();
          if (!trimmed) {
            setState({
              kind,
              loading: false,
              error: "empty",
              previewUrl: null,
              textContent: null,
              textTruncated: false,
              spreadsheetData: null,
              docxData: null,
            });
            return;
          }
          const truncated = trimmed.length > LOCAL_TEXT_MAX_CHARS;
          setState({
            kind,
            loading: false,
            error: null,
            previewUrl: null,
            textContent: truncated
              ? `${trimmed.slice(0, LOCAL_TEXT_MAX_CHARS)}\n… (conteúdo truncado)`
              : trimmed,
            textTruncated: truncated,
            spreadsheetData: null,
            docxData: null,
          });
          return;
        }

        setState({
          kind,
          loading: false,
          error: "unsupported",
          previewUrl: null,
          textContent: null,
          textTruncated: false,
          spreadsheetData: null,
          docxData: null,
        });
      } catch (err) {
        if (cancelled) return;
        setState({
          kind,
          loading: false,
          error: err instanceof Error ? err.message : "load_failed",
          previewUrl: null,
          textContent: null,
          textTruncated: false,
          spreadsheetData: null,
          docxData: null,
        });
      }
    }

    void load();

    return () => {
      cancelled = true;
      if (objectUrlRef.current) {
        URL.revokeObjectURL(objectUrlRef.current);
        objectUrlRef.current = null;
      }
    };
  }, [source, kind, enabled, fileName, remoteText, remoteTextTruncated]);

  return state;
}

export function filePreviewKindFromState(state: FilePreviewContentState): FilePreviewKind {
  return state.kind;
}
