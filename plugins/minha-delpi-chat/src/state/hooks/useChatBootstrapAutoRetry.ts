import { useEffect, useRef, useState } from "react";

import { BOOTSTRAP_UI_AUTO_RETRY_DELAYS_MS } from "../../data/api/chatApiFetch";

type UseChatBootstrapAutoRetryOptions = {
  bootstrapLoadError: boolean;
  isLoadingSessions: boolean;
  isLoadingAgents: boolean;
  isLoadingProjects: boolean;
  reloadBootstrapData: () => void;
};

/**
 * Após esgotar o retry HTTP do bootstrap, reagenda recargas silenciosas
 * enquanto o stack sobe (ex.: docker compose up --build).
 */
export function useChatBootstrapAutoRetry({
  bootstrapLoadError,
  isLoadingSessions,
  isLoadingAgents,
  isLoadingProjects,
  reloadBootstrapData,
}: UseChatBootstrapAutoRetryOptions): boolean {
  const attemptRef = useRef(0);
  const [isAutoRetrying, setIsAutoRetrying] = useState(false);
  const isBootstrapLoading =
    isLoadingSessions || isLoadingAgents || isLoadingProjects;

  useEffect(() => {
    if (!bootstrapLoadError && !isBootstrapLoading) {
      attemptRef.current = 0;
      setIsAutoRetrying(false);
      return;
    }

    if (!bootstrapLoadError || isBootstrapLoading) {
      return;
    }

    const attempt = attemptRef.current;

    if (attempt >= BOOTSTRAP_UI_AUTO_RETRY_DELAYS_MS.length) {
      setIsAutoRetrying(false);
      return;
    }

    setIsAutoRetrying(true);

    const delayMs = BOOTSTRAP_UI_AUTO_RETRY_DELAYS_MS[attempt] ?? 48000;
    const timer = window.setTimeout(() => {
      attemptRef.current += 1;
      reloadBootstrapData();
    }, delayMs);

    return () => {
      window.clearTimeout(timer);
    };
  }, [
    bootstrapLoadError,
    isBootstrapLoading,
    isLoadingAgents,
    isLoadingProjects,
    isLoadingSessions,
    reloadBootstrapData,
  ]);

  return isAutoRetrying;
}
