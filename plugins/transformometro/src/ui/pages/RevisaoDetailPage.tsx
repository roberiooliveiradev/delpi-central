import { useCallback, useEffect, useRef, useState } from "react";
import { ArrowLeft } from "lucide-react";

import type { AppProps } from "../../App";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useWorkspaceKeepAliveReload } from "../../hooks/useWorkspaceKeepAliveReload";
import { PageHeader } from "../../components/PageHeader";
import { InlineErrorState } from "../../components/ErrorStateBox";
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
import { requestWorkspaceTreeRefresh } from "../../utils/navigation";
import { createCoalescedAsyncRunner } from "../../utils/coalescedAsync";
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
  const [errorTitle, setErrorTitle] = useState("Não foi possível carregar");
  const [loading, setLoading] = useState(true);
  /** Incrementado no keep-alive/tree-refresh — Cadastro refetcha medição/inv/rateio. */
  const [cadastroResyncToken, setCadastroResyncToken] = useState(0);

  const reportError = useCallback((message: string | null, title = "Não foi possível carregar") => {
    setError(message);
    setErrorTitle(title);
  }, []);

  const scheduleLoad = useRef(createCoalescedAsyncRunner()).current;
  const revisaoUpdatedTimerRef = useRef<number | null>(null);

  const load = useCallback(async () => {
    await scheduleLoad(async () => {
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
        setCadastroResyncToken((token) => token + 1);
      } catch (err) {
        reportError(
          err instanceof Error ? err.message : "Falha ao carregar a revisão.",
          "Não foi possível carregar a revisão",
        );
      } finally {
        setLoading(false);
      }
    });
  }, [getAccessToken, instanciaId, processoId, reportError, revisaoId, scheduleLoad]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    return () => {
      if (revisaoUpdatedTimerRef.current != null) {
        window.clearTimeout(revisaoUpdatedTimerRef.current);
      }
    };
  }, []);

  const handleRevisaoUpdated = useCallback(() => {
    if (revisaoUpdatedTimerRef.current != null) {
      window.clearTimeout(revisaoUpdatedTimerRef.current);
    }
    revisaoUpdatedTimerRef.current = window.setTimeout(() => {
      revisaoUpdatedTimerRef.current = null;
      void load();
      requestWorkspaceTreeRefresh();
    }, 400);
  }, [load]);

  useWorkspaceKeepAliveReload({
    embedded,
    embeddedActive,
    reload: () => void load(),
  });

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
      <InlineErrorState
        title={error ? errorTitle : "Revisão não encontrada"}
        message={
          error ??
          "Esta revisão pode ter sido excluída ou você não tem acesso. Volte à melhoria e abra novamente."
        }
        actionLabel="Voltar à melhoria"
        onAction={() => onNavigate(buildInstanciaPath(processoId, instanciaId))}
      />
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
      externalResyncVersion={cadastroResyncToken}
      onError={(message) =>
        reportError(message, message ? "Não foi possível salvar" : "Não foi possível carregar")
      }
      onRevisaoUpdated={handleRevisaoUpdated}
      onRevisaoDeleted={() => {
        requestWorkspaceTreeRefresh();
        onNavigate(buildInstanciaPath(processoId, resolvedInstanciaId));
      }}
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

      <StatusAlerts
        error={error}
        errorTitle={errorTitle}
        loading={false}
        hasData
        onRetry={() => {
          reportError(null);
          void load();
        }}
        onDismissError={() => reportError(null)}
      />

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
