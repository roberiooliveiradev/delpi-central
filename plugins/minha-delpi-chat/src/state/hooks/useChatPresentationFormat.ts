import { useCallback, useEffect, useMemo, useState } from "react";

import { setChatSessionResponseFormat } from "../../data/api/chatApi";
import type { ChatPresentationFormatId } from "../../data/api/chatTypes";

type SessionFormatChip = { label: string; kind: string; value: string };

const STORAGE_KEY = "minha-delpi-chat.presentation-format";

export type ChatPresentationFormatOption = {
  id: ChatPresentationFormatId;
  label: string;
  description: string;
};

export const PRESENTATION_FORMAT_OPTIONS: ChatPresentationFormatOption[] = [
  {
    id: "auto",
    label: "Automático",
    description: "O chat escolhe texto, tabela, árvore ou gráfico conforme os dados.",
  },
  {
    id: "text",
    label: "Texto",
    description: "Prioriza narrativa e insights em texto.",
  },
  {
    id: "table",
    label: "Tabela",
    description: "Prioriza listagens e comparações em tabela.",
  },
  {
    id: "tree",
    label: "Árvore",
    description: "Prioriza hierarquias (estrutura, BOM).",
  },
  {
    id: "chart",
    label: "Gráfico",
    description: "Prioriza gráficos quando os dados forem visuais.",
  },
];

function normalizeFormat(value: string | null | undefined): ChatPresentationFormatId {
  const raw = String(value ?? "").trim().toLowerCase();

  if (raw === "text" || raw === "table" || raw === "tree" || raw === "chart") {
    return raw;
  }

  return "auto";
}

function readStoredFormat(): ChatPresentationFormatId | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return null;
    }

    return normalizeFormat(stored);
  } catch {
    return null;
  }
}

type UseChatPresentationFormatOptions = {
  sessionId?: string | null;
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatPresentationFormat(options: UseChatPresentationFormatOptions = {}) {
  const [presentationFormat, setPresentationFormatState] = useState<ChatPresentationFormatId>(
    () => readStoredFormat() ?? "auto",
  );
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    const stored = readStoredFormat();

    if (stored) {
      setPresentationFormatState(stored);
    }
  }, []);

  const syncFromSessionChips = useCallback((chips: SessionFormatChip[] | undefined) => {
    const formatChip = (chips ?? []).find((chip) => chip.kind === "format");
    const value = String(formatChip?.value ?? "").trim().toLowerCase();

    if (!formatChip) {
      return;
    }

    setPresentationFormatState(normalizeFormat(value || "auto"));
  }, []);

  const setPresentationFormat = useCallback(
    (format: ChatPresentationFormatId) => {
      const normalized = normalizeFormat(format);
      setPresentationFormatState(normalized);

      try {
        localStorage.setItem(STORAGE_KEY, normalized);
      } catch {
        /* ignore */
      }

      const sessionId = String(options.sessionId ?? "").trim();

      if (!sessionId) {
        return;
      }

      setSyncing(true);

      void setChatSessionResponseFormat(sessionId, normalized, {
        getAccessToken: options.getAccessToken,
      })
        .catch(() => {
          /* preferência local ainda vale no próximo turno via overlay após sync */
        })
        .finally(() => {
          setSyncing(false);
        });
    },
    [options.getAccessToken, options.sessionId],
  );

  const activeOption = useMemo(
    () =>
      PRESENTATION_FORMAT_OPTIONS.find((item) => item.id === presentationFormat) ??
      PRESENTATION_FORMAT_OPTIONS[0],
    [presentationFormat],
  );

  return {
    presentationFormat,
    activeOption,
    setPresentationFormat,
    syncFromSessionChips,
    syncing,
    options: PRESENTATION_FORMAT_OPTIONS,
  };
}
