import { useCallback, useEffect, useState } from "react";

import {
  fetchInspecoesEntradaPendentes,
  fetchInspecoesEntradaPendentesFornecedor,
  fetchInspecoesEntradaRejeitadasProduto,
  fetchInspecoesEntradaResumo,
} from "../api/inspecoesEntradaApi";
import type {
  InspecoesEntradaPendentesFornecedorResponse,
  InspecoesEntradaPendentesResponse,
  InspecoesEntradaRejeitadasProdutoResponse,
  InspecoesEntradaResumo,
} from "../types/inspecoesEntradaDashboard";

const PENDING_DASHBOARD_PAGE_SIZE = 200;
const REJECTED_DASHBOARD_LIMIT = 50;

type BlockState<T> = {
  data: T | null;
  loading: boolean;
  error: string | null;
};

function emptyBlock<T>(): BlockState<T> {
  return { data: null, loading: true, error: null };
}

type UseInspecoesEntradaDashboardResult = {
  resumo: BlockState<InspecoesEntradaResumo>;
  pendentes: BlockState<InspecoesEntradaPendentesResponse>;
  fornecedores: BlockState<InspecoesEntradaPendentesFornecedorResponse>;
  rejeitadas: BlockState<InspecoesEntradaRejeitadasProdutoResponse>;
  loading: boolean;
  reload: () => void;
};

async function loadBlock<T>(
  loader: (signal: AbortSignal) => Promise<T>,
  signal: AbortSignal,
): Promise<{ data?: T; error?: string }> {
  try {
    const data = await loader(signal);
    return { data };
  } catch (err) {
    if (signal.aborted) return {};
    const message = err instanceof Error ? err.message : "Erro ao carregar dados.";
    return { error: message };
  }
}

export function useInspecoesEntradaDashboard(
  branch: string,
  refreshToken = 0,
): UseInspecoesEntradaDashboardResult {
  const [resumo, setResumo] = useState<BlockState<InspecoesEntradaResumo>>(emptyBlock());
  const [pendentes, setPendentes] =
    useState<BlockState<InspecoesEntradaPendentesResponse>>(emptyBlock());
  const [fornecedores, setFornecedores] =
    useState<BlockState<InspecoesEntradaPendentesFornecedorResponse>>(emptyBlock());
  const [rejeitadas, setRejeitadas] =
    useState<BlockState<InspecoesEntradaRejeitadasProdutoResponse>>(emptyBlock());
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((value) => value + 1);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      setResumo({ data: null, loading: true, error: null });
      setPendentes({ data: null, loading: true, error: null });
      setFornecedores({ data: null, loading: true, error: null });
      setRejeitadas({ data: null, loading: true, error: null });

      const [resumoResult, pendentesResult, fornecedoresResult, rejeitadasResult] =
        await Promise.all([
          loadBlock((signal) => fetchInspecoesEntradaResumo(branch, signal), controller.signal),
          loadBlock(
            (signal) => fetchInspecoesEntradaPendentes(branch, 1, PENDING_DASHBOARD_PAGE_SIZE, signal),
            controller.signal,
          ),
          loadBlock(
            (signal) => fetchInspecoesEntradaPendentesFornecedor(branch, signal),
            controller.signal,
          ),
          loadBlock(
            (signal) =>
              fetchInspecoesEntradaRejeitadasProduto(branch, REJECTED_DASHBOARD_LIMIT, signal),
            controller.signal,
          ),
        ]);

      if (controller.signal.aborted) return;

      setResumo({
        data: resumoResult.data ?? null,
        loading: false,
        error: resumoResult.error ?? null,
      });
      setPendentes({
        data: pendentesResult.data ?? null,
        loading: false,
        error: pendentesResult.error ?? null,
      });
      setFornecedores({
        data: fornecedoresResult.data ?? null,
        loading: false,
        error: fornecedoresResult.error ?? null,
      });
      setRejeitadas({
        data: rejeitadasResult.data ?? null,
        loading: false,
        error: rejeitadasResult.error ?? null,
      });
    }

    void run();
    return () => controller.abort();
  }, [branch, reloadKey, refreshToken]);

  const loading =
    resumo.loading || pendentes.loading || fornecedores.loading || rejeitadas.loading;

  return {
    resumo,
    pendentes,
    fornecedores,
    rejeitadas,
    loading,
    reload,
  };
}
