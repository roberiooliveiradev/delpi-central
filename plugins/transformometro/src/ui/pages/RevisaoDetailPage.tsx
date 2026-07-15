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
import { ProcessoWorkspaceShell, useRevisaoWorkspaceSection } from "../processos/ProcessoWorkspaceShell";
import { resolveActiveWorkspaceNodeId, type RevisaoWorkspaceSectionId } from "../processos/processoWorkspaceNav";
import { DS_GHOST_BTN } from "../../components/ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  revisaoId: string;
  legacyRevisaoPath?: boolean;
  pathname?: string;
  onNavigate: (path: string) => void;
  embedded?: boolean;
  embeddedActive?: boolean;
  activeSection?: RevisaoWorkspaceSectionId;
};

export function RevisaoDetailPage({
  getAccessToken,
  processoId,
  instanciaId,
  revisaoId,
  legacyRevisaoPath = false,
  pathname,
  onNavigate,
  embedded = false,
  embeddedActive = true,
  activeSection: activeSectionProp,
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
  const fallbackSection = useRevisaoWorkspaceSection(revisao?.cenario_tipo);
  const activeSection = activeSectionProp ?? fallbackSection;

  if (loading && !revisao) {
    const loader = (
      <LoadingActivityCard
        title="Carregando revisão"
        description="Medição, investimentos, recursos e evidências."
        progressPercent={loadingProgress}
      />
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  if (!processo || !revisao || !options) {
    const errorView = (
      <div className="ds-state ds-state--error" role="alert">
        <p>{error ?? "Revisão não encontrada."}</p>
        <button
          type="button"
          className={DS_GHOST_BTN}
          onClick={() => onNavigate(buildInstanciaPath(processoId, instanciaId))}
        >
          Voltar à instância
        </button>
      </div>
    );
    if (embedded) return errorView;
    return <TransformometroShell>{errorView}</TransformometroShell>;
  }

  const resolvedInstanciaId = revisao.instancia_id ?? instanciaId;

  const revisaoMain = (
    <RevisaoCadastroPanel
      revisao={revisao}
      revisoesReferencia={revisoesInstancia}
      options={options}
      getAccessToken={getAccessToken}
      collaborationActive={!embedded || embeddedActive}
      activeSection={activeSection}
      onError={setError}
      onRevisaoUpdated={load}
      onRevisaoDeleted={() => onNavigate(buildInstanciaPath(processoId, resolvedInstanciaId))}
      onNavigate={onNavigate}
    />
  );

  const pageBody = (
    <>
      {!embedded ? (
        <PageHeader
          title={`Revisão v${revisao.versao_revisao} · ${cenarioLabel(revisao.cenario_tipo)}`}
          subtitle={`${processo.codigo_processo} — ${processo.nome_processo}${revisao.revisao_ativa ? " · ativa" : ""}`}
          currentPath={pathname ?? buildProcessoPath(processoId, revisaoId, resolvedInstanciaId)}
          onNavigate={onNavigate}
          actions={
            <button
              type="button"
              className={DS_GHOST_BTN}
              onClick={() => onNavigate(buildInstanciaPath(processoId, resolvedInstanciaId))}
            >
              <ArrowLeft size={16} />
              Instância
            </button>
          }
        />
      ) : null}

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      {embedded ? (
        revisaoMain
      ) : (
        <ProcessoWorkspaceShell
          processoId={processoId}
          activeNodeId={resolveActiveWorkspaceNodeId({
            view: "revisao",
            revisaoId,
            instanciaId: resolvedInstanciaId,
            revisaoSection: activeSection,
          })}
          getAccessToken={getAccessToken}
          onNavigate={onNavigate}
          processo={processo}
          instancias={allInstancias}
          revisoes={allRevisoes}
        >
          {revisaoMain}
        </ProcessoWorkspaceShell>
      )}
    </>
  );

  if (embedded) return pageBody;
  return <TransformometroShell>{pageBody}</TransformometroShell>;
}
