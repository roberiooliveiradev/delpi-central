import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { ProcessoTimeline } from "../../components/processo/ProcessoTimeline";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { ProcessoReadView } from "../../components/processo/ProcessoReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  createProcessoInstancia,
  deleteInstancia,
  deleteProcesso,
  duplicateInstancia,
  fetchOptions,
  fetchProcesso,
  fetchProcessoComparativo,
  fetchProcessoInstancias,
  fetchProcessoTimeline,
  fetchRevisoes,
  updateProcesso,
  updateInstancia,
  type OptionsData,
  type Processo,
  type ProcessoComparativoItem,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { fetchProcessoDiagrama } from "../../data/api/transformometroDiagramApi";
import { fetchProcessoDecomposicao } from "../../data/api/transformometroDecompositionApi";
import type { ProcessoAuditLogEntry } from "../../utils/processoTimeline";
import { computeProcessoSetupCompletion } from "../../utils/processoCompletion";
import { buildInstanciaPath } from "../../utils/routeParser";
import { ProcessoFormFields } from "../processos/ProcessoFormFields";
import { ProcessoInstanciasPanel } from "../processos/ProcessoInstanciasPanel";
import { ProcessoDecompositionSection } from "../../components/decomposition/ProcessoDecompositionSection";
import { ProcessoDiagramSection } from "../../components/diagram/ProcessoDiagramSection";
import {
  masterPayloadFromProcessoForm,
  processoFormFromEntity,
  type ProcessoFormState,
} from "../processos/processoForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

export function ProcessoDetailPage({
  getAccessToken,
  processoId,
  pathname,
  onNavigate,
  onBack,
}: Props) {
  const [openInstanciaForm, setOpenInstanciaForm] = useState(false);
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>([]);
  const [instanciasComRevisao, setInstanciasComRevisao] = useState<string[]>([]);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [diagramNodeCount, setDiagramNodeCount] = useState(0);
  const [decompositionNodeCount, setDecompositionNodeCount] = useState(0);
  const [comparativoItems, setComparativoItems] = useState<ProcessoComparativoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processoForm, setProcessoForm] = useState<ProcessoFormState | null>(null);
  const [savingProcesso, setSavingProcesso] = useState(false);
  const [timelineEntries, setTimelineEntries] = useState<ProcessoAuditLogEntry[]>([]);
  const [timelineLoading, setTimelineLoading] = useState(true);

  const loadTimeline = useCallback(async () => {
    setTimelineLoading(true);
    try {
      const data = await fetchProcessoTimeline(processoId, getAccessToken, { page_size: 500 });
      setTimelineEntries(data.items);
    } catch {
      setTimelineEntries([]);
    } finally {
      setTimelineLoading(false);
    }
  }, [getAccessToken, processoId]);

  const load = useCallback(async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [proc, revs, opts, inst, diagram, comparativo, decomposicao] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
        fetchProcessoInstancias(processoId, getAccessToken),
        fetchProcessoDiagrama(processoId, getAccessToken).catch(() => null),
        fetchProcessoComparativo(processoId, getAccessToken).catch(() => ({ items: [] })),
        fetchProcessoDecomposicao(processoId, getAccessToken).catch(() => null),
      ]);
      setProcesso(proc);
      setOptions(opts);
      setInstancias(inst.items);
      setRevisoes(revs.items);
      setDiagramNodeCount(diagram?.conteudo?.nodes?.length ?? 0);
      setDecompositionNodeCount(decomposicao?.conteudo?.nodes?.length ?? 0);
      setComparativoItems(comparativo.items ?? []);
      setInstanciasComRevisao(
        Array.from(
          new Set(
            revs.items.map((row) => row.instancia_id).filter((id): id is string => Boolean(id))
          )
        )
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
    void loadTimeline();
  }, [getAccessToken, processoId, loadTimeline]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "processo",
    entityId: processoId,
    getAccessToken,
    onResync: () => void load(),
  });

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.hash !== "#nova-instancia") return;
    setOpenInstanciaForm(true);
    window.history.replaceState(null, "", window.location.pathname);
  }, [processoId]);

  useEffect(() => {
    if (!processo || !sectionEdit.isEditing("processo")) return;
    setProcessoForm(processoFormFromEntity(processo));
  }, [processo, sectionEdit]);

  async function handleSaveProcesso() {
    if (!processoForm) return;
    setSavingProcesso(true);
    setError(null);
    try {
      const updated = await updateProcesso(
        processoId,
        masterPayloadFromProcessoForm(processoForm),
        getAccessToken
      );
      setProcesso(updated);
      sectionEdit.stopEdit("processo");
      setProcessoForm(null);
      await loadTimeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar processo");
    } finally {
      setSavingProcesso(false);
    }
  }

  async function handleDeleteProcesso() {
    if (!processo) return;
    const label = `${processo.codigo_processo} — ${processo.nome_processo}`;
    if (!window.confirm(`Excluir o processo ${label}? Você será redirecionado à lista.`)) {
      return;
    }
    setError(null);
    try {
      await deleteProcesso(processoId, getAccessToken);
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir processo");
    }
  }

  const setupCompletion = useMemo(() => {
    if (!processo) {
      return { percent: 0, done: 0, total: 0, items: [] };
    }
    return computeProcessoSetupCompletion({
      processo,
      instanciaCount: instancias.length,
      diagramNodeCount,
      decompositionNodeCount,
      revisoes,
      comparativoItems,
    });
  }, [comparativoItems, decompositionNodeCount, diagramNodeCount, instancias.length, processo, revisoes]);

  const processFetchProgress = useTrackedSingleFetchProgress(loading && !processo);
  const processLoadingProgress = useLoadingProgress(loading && !processo, processFetchProgress);

  if (loading && !processo) {
    return (
      <TransformometroShell>
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <LoadingActivityCard
          title="Carregando processo"
          description="Buscando dados mestre e instâncias operacionais."
          progressPercent={processLoadingProgress}
        />
      </TransformometroShell>
    );
  }

  if (!processo || !options) {
    return (
      <TransformometroShell>
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          <ArrowLeft size={16} />
          Voltar
        </button>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Processo não encontrado."}</p>
          <button type="button" className="ds-primary-btn" onClick={() => void load()}>
            Tentar novamente
          </button>
        </div>
      </TransformometroShell>
    );
  }

  return (
    <TransformometroShell>
      <PageHeader
        title={`${processo.codigo_processo} — ${processo.nome_processo}`}
        subtitle={[processo.status_processo, processo.familia_processo ? `família ${processo.familia_processo}` : null]
          .filter(Boolean)
          .join(" · ")}
        currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
        onNavigate={onNavigate}
        actions={
          <>
            <button type="button" className="ds-ghost-btn" onClick={onBack}>
              <ArrowLeft size={16} />
              Lista
            </button>
            <button type="button" className="ds-ghost-btn" disabled={refreshing} onClick={() => void handleDeleteProcesso()}>
              <Trash2 size={16} />
              Excluir processo
            </button>
          </>
        }
      />

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      <ProcessoFormProgress
        completion={setupCompletion}
        title="Preenchimento do cadastro"
      />

      <EditableSectionCard
        title="Dados do processo"
        hint={TM_HELP_TOOLTIPS.processos.nome}
        description="Informações mestre do processo. Instâncias operacionais e revisões ficam nos níveis abaixo."
        isEditing={sectionEdit.isEditing("processo")}
        onEdit={() => void sectionEdit.startEdit("processo")}
        onCancel={() => {
          sectionEdit.cancelEdit("processo");
          setProcessoForm(null);
        }}
        onSave={() => void handleSaveProcesso()}
        saving={savingProcesso}
        readContent={<ProcessoReadView processo={processo} />}
        editContent={
          processoForm ? (
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleSaveProcesso();
              }}
            >
              <ProcessoFormFields
                form={processoForm}
                options={options}
                codigoProcesso={processo.codigo_processo}
                showInstanciaFields={false}
                onChange={setProcessoForm}
              />
            </form>
          ) : null
        }
      />

      <EditableSectionCard
        title="Mapeamento do processo"
        description="Árvore WBS — processos-chave, tarefas e sub-tarefas. Fonte da planilha de mapeamento."
        hint={TM_HELP_TOOLTIPS.decomposition.mapeamento}
        isEditing={sectionEdit.isEditing("decomposicao")}
        onEdit={() => void sectionEdit.startEdit("decomposicao")}
        onCancel={() => sectionEdit.cancelEdit("decomposicao")}
        readContent={
          <ProcessoDecompositionSection
            embeddedInCard
            readOnly
            processoId={processoId}
            processoNome={processo.nome_processo}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
        editContent={
          <ProcessoDecompositionSection
            embeddedInCard
            processoId={processoId}
            processoNome={processo.nome_processo}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
      />

      <EditableSectionCard
        title="Diagrama macro"
        description="Mapa canônico do fluxo end-to-end deste processo-mestre."
        hint={TM_HELP_TOOLTIPS.processos.diagramaMacro}
        isEditing={sectionEdit.isEditing("diagrama_macro")}
        onEdit={() => void sectionEdit.startEdit("diagrama_macro")}
        onCancel={() => sectionEdit.cancelEdit("diagrama_macro")}
        readContent={
          <ProcessoDiagramSection
            embeddedInCard
            readOnly
            processoId={processoId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
        editContent={
          <ProcessoDiagramSection
            embeddedInCard
            processoId={processoId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
      />

      <ProcessoInstanciasPanel
        instancias={instancias}
        selectedInstanciaId={null}
        options={options}
        busy={refreshing}
        initialShowForm={openInstanciaForm}
        instanciasComRevisao={instanciasComRevisao}
        navigateOnSelect
        onSelect={(instanciaId) => onNavigate(buildInstanciaPath(processoId, instanciaId))}
        onCreate={async (payload) => {
          await createProcessoInstancia(processoId, payload, getAccessToken);
          setOpenInstanciaForm(false);
          await load();
        }}
        onUpdate={async (instanciaId, payload) => {
          await updateInstancia(instanciaId, payload, getAccessToken);
          await load();
        }}
        onDelete={async (instanciaId) => {
          await deleteInstancia(instanciaId, getAccessToken);
          await load();
        }}
        onDuplicate={async ({ origemInstanciaId, ...payload }) => {
          await duplicateInstancia(origemInstanciaId, payload, getAccessToken);
          await load();
        }}
      />

      <ProcessoTimeline entries={timelineEntries} loading={timelineLoading} />
    </TransformometroShell>
  );
}
