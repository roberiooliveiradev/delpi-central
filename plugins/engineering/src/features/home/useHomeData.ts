import { useCallback, useEffect, useRef, useState } from "react";

import { getEngineeringHome } from "../../api/engineeringHomeApi";
import { HomeApiError } from "../../api/httpClient";
import type { HomeResponse } from "../../types/home";

export type HomeDataState =
  | { phase: "loading" }
  | { phase: "error"; error: HomeApiError }
  | { phase: "ready"; home: HomeResponse };

/** Carrega a Home via engineering-api com AbortController + sequence
 * guard: desmontagem ou nova chamada invalida respostas obsoletas —
 * nenhuma resposta atrasada escreve estado de uma sessão encerrada. */
export function useHomeData() {
  const [state, setState] = useState<HomeDataState>({ phase: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const requestSeq = useRef(0);
  const controllerRef = useRef<AbortController | null>(null);

  const load = useCallback(async (isRefresh: boolean) => {
    const seq = ++requestSeq.current;
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    if (!isRefresh) setState({ phase: "loading" });
    setRefreshing(true);
    try {
      const home = await getEngineeringHome(controller.signal);
      if (seq !== requestSeq.current) return;
      setState({ phase: "ready", home });
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setState({
        phase: "error",
        error:
          error instanceof HomeApiError
            ? error
            : new HomeApiError(
                "network_error",
                "Falha ao carregar a área de trabalho.",
              ),
      });
    } finally {
      if (seq === requestSeq.current) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const pending = queueMicrotask(() => void load(false));
    return () => {
      void pending;
      requestSeq.current += 1;
      controllerRef.current?.abort();
      controllerRef.current = null;
    };
  }, [load]);

  return { state, refreshing, reload: () => void load(true) };
}
