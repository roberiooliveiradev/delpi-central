import { useCallback, useEffect, useMemo, useState } from "react";

import { getChatResponseModes } from "../../data/api/chatApi";
import type { ChatResponseModeId, ChatResponseModeOption } from "../../data/api/chatTypes";

const STORAGE_KEY = "minha-delpi-chat.response-mode";

const FALLBACK_MODES: ChatResponseModeOption[] = [
  {
    id: "fast",
    label: "Rápida",
    description: "Respostas mais curtas e ágeis.",
  },
  {
    id: "normal",
    label: "Normal",
    description: "Equilíbrio entre qualidade e velocidade.",
    default: true,
  },
  {
    id: "thinker",
    label: "Pensador",
    description: "Respostas mais elaboradas (pode demorar mais).",
  },
];

function normalizeMode(value: string | null | undefined): ChatResponseModeId {
  const raw = String(value ?? "").trim().toLowerCase();

  if (raw === "fast" || raw === "rapida" || raw === "rápida") {
    return "fast";
  }

  if (raw === "thinker" || raw === "pensador") {
    return "thinker";
  }

  return "normal";
}

function readStoredMode(): ChatResponseModeId | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);

    if (!stored) {
      return null;
    }

    return normalizeMode(stored);
  } catch {
    return null;
  }
}

type UseChatResponseModeOptions = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function useChatResponseMode(options: UseChatResponseModeOptions = {}) {
  const [modes, setModes] = useState<ChatResponseModeOption[]>(FALLBACK_MODES);
  const [enabled, setEnabled] = useState(true);
  const [responseMode, setResponseModeState] = useState<ChatResponseModeId>(
    () => readStoredMode() ?? "normal",
  );

  useEffect(() => {
    let cancelled = false;

    void getChatResponseModes({ getAccessToken: options.getAccessToken })
      .then((payload) => {
        if (cancelled) {
          return;
        }

        setEnabled(payload.enabled !== false);

        if (payload.modes?.length) {
          setModes(payload.modes);
        }

        const defaultMode = normalizeMode(payload.defaultMode);
        const stored = readStoredMode();
        const hasStored = stored && payload.modes.some((item) => item.id === stored);

        setResponseModeState(hasStored ? stored! : defaultMode);
      })
      .catch(() => {
        if (!cancelled) {
          setModes(FALLBACK_MODES);
          setEnabled(true);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [options.getAccessToken]);

  const setResponseMode = useCallback((mode: ChatResponseModeId) => {
    const normalized = normalizeMode(mode);
    setResponseModeState(normalized);

    try {
      localStorage.setItem(STORAGE_KEY, normalized);
    } catch {
      /* ignore quota / private mode */
    }
  }, []);

  const activeMode = useMemo(
    () => modes.find((item) => item.id === responseMode) ?? modes[0],
    [modes, responseMode],
  );

  return {
    enabled,
    modes,
    responseMode,
    activeMode,
    setResponseMode,
  };
}
