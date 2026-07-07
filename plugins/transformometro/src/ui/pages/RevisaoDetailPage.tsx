import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import {
  fetchOptions,
  fetchProcesso,
  fetchProcessoInstancias,
  fetchRevisoes,
  type OptionsData,
  type Processo,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { buildInstanciaPath, buildProcessoPath } from "../../utils/routeParser";
import { cenarioLabel } from "../../content/cenarioLabels";
import { RevisaoCadastroPanel } from "./RevisaoCadastroPanel";
import { ProcessoWorkspaceShell } from "../processos/ProcessoWorkspaceShell";
import { resolveActiveWorkspaceNodeId } from "../processos/processoWorkspaceNav";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  revisaoId: string;
  legacyRevisaoPath?: boolean;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function RevisaoDetailPage({
  getAccessToken,
  processoId,
  instanciaId,
  revisaoId,
  legacyRevisaoPath = false,
  pathname,
  onNavigate,
}: Props) {
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [revisao, setRevisao] = useState<Revisao | null>(null);
  const [revisoesInstancia, setRevisoesInstancia] = useState<Revisao[]>([]);
  const [allInstancias, setAllInstancias] = useState<ProcessoInstancia[]>([]);
  const [allRevisoes, setAllRevisoes] = useState<Revisao[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [proc, revs, opts, inst] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
        fetchProcessoInstancias(processoId, getAccessToken),
      ]);
      const rev = revs.items.find((row) => row.revisao_id === revisaoId) ?? null;
      setProcesso(proc);
      setRevisao(rev);
      setAllInstancias(inst.items);
      setAllRevisoes(revs.items);
      setRevisoesInstancia(
        revs.items.filter((row) => row.instancia_id === (rev?.instancia_id ?? instanciaId))
      );
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, processoId, revisaoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!legacyRevisaoPath || !revisao?.instancia_id) return;
    onNavigate(buildProcessoPath(processoId, revisaoId, revisao.instancia_id));
  }, [legacyRevisaoPath, onNavigate, processoId, revisao, revisaoId]);

  const fetchProgress = useTrackedSingleFetchProgress(loading && !revisao);
  const loadingProgress = useLoadingProgress(loading && !revisao, fetchProgress);

  if (loading && !revisao) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando revisão"
          description="Medição, investimentos, recursos e evidências."
          progressPercent={loadingProgress}
        />
      </TransformometroShell>
    );
  }

  if (!processo || !revisao || !options) {
    return (
      <TransformometroShell>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Revisão não encontrada."}</p>
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => onNavigate(buildInstanciaPath(processoId, instanciaId))}
          >
            Voltar à instância
          </button>
        </div>
      </TransformometroShell>
    );
  }

  const resolvedInstanciaId = revisao.instancia_id ?? instanciaId;

  return (
    <TransformometroShell>
      <PageHeader
        title={`Revisão v${revisao.versao_revisao} · ${cenarioLabel(revisao.cenario_tipo)}`}
        subtitle={`${processo.codigo_processo} — ${processo.nome_processo}${revisao.revisao_ativa ? " · ativa" : ""}`}
        currentPath={pathname ?? buildProcessoPath(processoId, revisaoId, resolvedInstanciaId)}
        onNavigate={onNavigate}
        actions={
          <button
            type="button"
            className="ds-ghost-btn"
            onClick={() => onNavigate(buildInstanciaPath(processoId, resolvedInstanciaId))}
          >
            <ArrowLeft size={16} />
            Instância
          </button>
        }
      />

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      <ProcessoWorkspaceShell
        processoId={processoId}
        activeNodeId={resolveActiveWorkspaceNodeId({
          view: "revisao",
          revisaoId,
          instanciaId: resolvedInstanciaId,
        })}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
        processo={processo}
        instancias={allInstancias}
        revisoes={allRevisoes}
      >
        <RevisaoCadastroPanel
          revisao={revisao}
          revisoesReferencia={revisoesInstancia}
          options={options}
          getAccessToken={getAccessToken}
          onError={setError}
          onRevisaoUpdated={load}
          onRevisaoDeleted={() => onNavigate(buildInstanciaPath(processoId, resolvedInstanciaId))}
        />
      </ProcessoWorkspaceShell>
    </TransformometroShell>
  );
}
