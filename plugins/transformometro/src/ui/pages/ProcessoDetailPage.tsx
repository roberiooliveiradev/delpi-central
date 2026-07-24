import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Copy, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { ProcessoFormProgress } from "../../components/processo/ProcessoFormProgress";
import { ProcessoTimeline } from "../../components/processo/ProcessoTimeline";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { ProcessoReadView } from "../../components/processo/ProcessoReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { useWorkspaceKeepAliveReload } from "../../hooks/useWorkspaceKeepAliveReload";
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
  duplicateProcesso,
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
import { fetchProcessoArquivos } from "../../data/api/transformometroProcessoArquivoApi";
import type { ProcessoAuditLogEntry } from "../../utils/processoTimeline";
import { computeProcessoSetupCompletion } from "../../utils/processoCompletion";
import { buildInstanciaPath, buildProcessoPath } from "../../utils/routeParser";
import { requestWorkspaceTreeRefresh } from "../../utils/navigation";
import { ProcessoFormFields } from "../processos/ProcessoFormFields";
import { ProcessoEscopoFields } from "../processos/ProcessoEscopoFields";
import { ProcessoInstanciasPanel } from "../processos/ProcessoInstanciasPanel";
import { ProcessoMatrizImpactoSection } from "../processos/ProcessoMatrizImpactoSection";
import { ProcessoDecompositionSection } from "../../components/decomposition/ProcessoDecompositionSection";
import { ProcessoDecompositionComposedSection } from "../../components/decomposition/ProcessoDecompositionComposedSection";
import { ProcessoDiagramSection } from "../../components/diagram/ProcessoDiagramSection";
import { ProcessoDiagramComposedSection } from "../../components/diagram/ProcessoDiagramComposedSection";
import { ProcessoArquivosSection } from "../processo/ProcessoArquivosSection";
import {
  masterPayloadFromProcessoForm,
  processoFormFromEntity,
  type ProcessoFormState,
} from "../processos/processoForm";
import { processoEscopoFromEntity } from "../processos/processoEscopo";
import {
  ProcessoWorkspaceShell,
  useProcessoWorkspaceSection,
} from "../processos/ProcessoWorkspaceShell";
import { resolveActiveWorkspaceNodeId } from "../processos/processoWorkspaceNav";
import type { ProcessoWorkspaceSectionId } from "../processos/processoWorkspaceNav";
import { ProcessoWorkspaceSectionPanel } from "../processos/ProcessoWorkspaceSectionPanel";
import { valuesEqual } from "@delpi/plugin-ui/index";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
  embedded?: boolean;
  embeddedActive?: boolean;
};

export function ProcessoDetailPage({
  getAccessToken,
  processoId,
  pathname,
  onNavigate,
  onBack,
  embedded = false,
  embeddedActive = true,
}: Props) {
  const confirm = useConfirm();
  const [openInstanciaForm, setOpenInstanciaForm] = useState(false);
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>([]);
  const [instanciasComRevisao, setInstanciasComRevisao] = useState<string[]>([]);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [diagramNodeCount, setDiagramNodeCount] = useState(0);
  const [decompositionNodeCount, setDecompositionNodeCount] = useState(0);
  const [arquivosCount, setArquivosCount] = useState(0);
  const [comparativoItems, setComparativoItems] = useState<ProcessoComparativoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  /** Incrementado a cada load — invalida matriz keep-alive do processo. */
  const [dataEpoch, setDataEpoch] = useState(0);
  const [processoForm, setProcessoForm] = useState<ProcessoFormState | null>(null);
  const [processoFormBaseline, setProcessoFormBaseline] = useState<ProcessoFormState | null>(
    null
  );
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
      const [proc, revs, opts, inst, diagram, comparativo, decomposicao, arquivos] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
        fetchProcessoInstancias(processoId, getAccessToken),
        fetchProcessoDiagrama(processoId, getAccessToken).catch(() => null),
        fetchProcessoComparativo(processoId, getAccessToken).catch(() => ({ items: [] })),
        fetchProcessoDecomposicao(processoId, getAccessToken).catch(() => null),
        fetchProcessoArquivos(processoId, getAccessToken).catch(() => []),
      ]);
      setProcesso(proc);
      setOptions(opts);
      setInstancias(inst.items);
      setRevisoes(revs.items);
      setDiagramNodeCount(diagram?.conteudo?.nodes?.length ?? 0);
      setDecompositionNodeCount(decomposicao?.conteudo?.nodes?.length ?? 0);
      setArquivosCount(arquivos.length);
      setComparativoItems(comparativo.items ?? []);
      setInstanciasComRevisao(
        Array.from(
          new Set(
            revs.items.map((row) => row.instancia_id).filter((id): id is string => Boolean(id))
          )
        )
      );
      setDataEpoch((epoch) => epoch + 1);
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
    enabled: !embedded || embeddedActive,
    onResync: () => void load(),
  });
  /** WS remoto + load local (tree-refresh) — compostos/matriz não ficam stale. */
  const panelResyncVersion = sectionEdit.resyncVersion + dataEpoch;

  useEffect(() => {
    if (!sectionEdit.resyncVersion) return;
    void loadTimeline();
  }, [sectionEdit.resyncVersion, loadTimeline]);

  useEffect(() => {
    void load();
  }, [load]);

  useWorkspaceKeepAliveReload({
    embedded,
    embeddedActive,
    reload: () => void load(),
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (window.location.hash !== "#nova-instancia") return;
    setOpenInstanciaForm(true);
    window.history.replaceState(null, "", window.location.pathname);
  }, [processoId]);

  async function handleStartEditProcesso() {
    const acquired = await sectionEdit.startEdit("processo");
    if (acquired !== false) {
      const next = processoFormFromEntity(processo!);
      setProcessoForm(next);
      setProcessoFormBaseline(next);
    }
  }

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
      setProcessoFormBaseline(null);
      await loadTimeline();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar processo");
    } finally {
      setSavingProcesso(false);
    }
  }

  async function handleDuplicateProcesso() {
    if (!processo) return;
    const label = `${processo.codigo_processo} — ${processo.nome_processo}`;
    const confirmed = await confirm({
      title: "Duplicar processo",
      message: `Duplicar ${label}? Serão copiados diagrama, mapeamento WBS, melhorias, revisões, medições, investimentos, vínculos e evidências.`,
      confirmLabel: "Duplicar",
    });
    if (!confirmed) return;
    setError(null);
    try {
      const result = await duplicateProcesso(processoId, undefined, getAccessToken);
      onNavigate(buildProcessoPath(result.processo.processo_id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao duplicar processo");
    }
  }

  async function handleDeleteProcesso() {
    if (!processo) return;
    const label = `${processo.codigo_processo} — ${processo.nome_processo}`;
    const confirmed = await confirm({
      title: "Excluir processo",
      message: `Excluir o processo-mestre ${label} e todo o cadastro associado (melhorias, revisões, medições)? Esta ação é uma exclusão lógica. Você será redirecionado à lista.`,
      confirmLabel: "Excluir processo",
      variant: "danger",
    });
    if (!confirmed) {
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

  const activeSection = useProcessoWorkspaceSection();
  const activeNodeId = resolveActiveWorkspaceNodeId({ view: "processo", section: activeSection });
  const [mountedSections, setMountedSections] = useState<Set<ProcessoWorkspaceSectionId>>(
    () => new Set([activeSection])
  );

  useEffect(() => {
    setMountedSections((current) => {
      if (current.has(activeSection)) return current;
      const next = new Set(current);
      next.add(activeSection);
      return next;
    });
  }, [activeSection]);

  const visibleSections = useMemo(() => {
    const next = new Set(mountedSections);
    next.add(activeSection);
    return next;
  }, [activeSection, mountedSections]);

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
      hasMedicao: processo.setup_stats?.has_medicao,
    });
  }, [comparativoItems, decompositionNodeCount, diagramNodeCount, instancias.length, processo, revisoes]);

  const processFetchProgress = useTrackedSingleFetchProgress(loading && !processo);
  const processLoadingProgress = useLoadingProgress(loading && !processo, processFetchProgress);

  if (loading && !processo) {
    const loader = (
      <>
        {!embedded ? (
          <button type="button" className={DS_GHOST_BTN} onClick={onBack}>
            <ArrowLeft size={16} />
            Voltar
          </button>
        ) : null}
        <LoadingActivityCard
          title="Carregando processo"
          description="Buscando dados mestre e instâncias operacionais."
          progressPercent={processLoadingProgress}
        />
      </>
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  if (!processo || !options) {
    const errorView = (
      <>
        {!embedded ? (
          <button type="button" className={DS_GHOST_BTN} onClick={onBack}>
            <ArrowLeft size={16} />
            Voltar
          </button>
        ) : null}
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Processo não encontrado."}</p>
          <button type="button" className="ds-primary-btn" onClick={() => void load()}>
            Tentar novamente
          </button>
        </div>
      </>
    );
    if (embedded) return errorView;
    return <TransformometroShell>{errorView}</TransformometroShell>;
  }

  const sectionPanels = (
    <>
        {visibleSections.has("visao-geral") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "visao-geral"} sectionId="visao-geral">
          <section className="ds-card tm-processo-workspace-panel">
            <h2 className="ds-section-title">Visão geral</h2>
            <p className="ds-hint">
              Resumo do cadastro do processo-mestre. Use a árvore à esquerda para abrir cada tópico,
              melhoria ou revisão.
            </p>
            <ProcessoFormProgress completion={setupCompletion} title="Preenchimento do cadastro" />
            <div className="tm-processo-workspace-overview">
              <ProcessoReadView processo={processo} activeFilialCount={options.filiais.length} />
              <dl className="ds-dl-grid tm-processo-workspace-overview__stats">
                <div>
                  <dt>Melhorias</dt>
                  <dd>{instancias.length}</dd>
                </div>
                <div>
                  <dt>Revisões</dt>
                  <dd>{revisoes.length}</dd>
                </div>
                <div>
                  <dt>Arquivos</dt>
                  <dd>{arquivosCount}</dd>
                </div>
              </dl>
            </div>
          </section>
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("dados") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "dados"} sectionId="dados">
          <EditableSectionCard
            title="Dados do processo"
            hint={TM_HELP_TOOLTIPS.processos.nome}
            description="Informações mestre do processo. Melhorias e revisões ficam nos níveis abaixo."
            isEditing={sectionEdit.isEditing("processo")}
            onEdit={() => void handleStartEditProcesso()}
            onCancel={() => {
              if (processoFormBaseline) {
                setProcessoForm(processoFormBaseline);
              }
              sectionEdit.cancelEdit("processo");
              setProcessoForm(null);
              setProcessoFormBaseline(null);
            }}
            onSave={() => void handleSaveProcesso()}
            saving={savingProcesso}
            dirty={
              processoForm != null &&
              processoFormBaseline != null &&
              !valuesEqual(processoForm, processoFormBaseline)
            }
            readContent={<ProcessoReadView processo={processo} activeFilialCount={options.filiais.length} />}
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
                  <div className="tm-inst-form tm-inst-form--spaced">
                    <h3 className="ds-subsection-title">Unidades e departamentos do processo</h3>
                    <p className="ds-hint">
                      Escopo operacional do processo-mestre. Ao criar melhorias, você pode replicar esta
                      amarração ou definir outra.
                    </p>
                    <ProcessoEscopoFields
                      value={processoForm.escopo}
                      options={options}
                      onChange={(escopo) => setProcessoForm({ ...processoForm, escopo })}
                      activeFilialCount={options.filiais.length}
                    />
                  </div>
                </form>
              ) : null
            }
          />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("mapeamento") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "mapeamento"} sectionId="mapeamento">
          <div className="tm-processo-composed-card tm-processo-composed-card--first">
            <h3 className="ds-subsection-title">Macro composto (visão vigente)</h3>
            <p className="ds-hint">
              Base do processo + deltas das revisões vigentes na data escolhida. Conflitos de
              interseção aparecem em destaque.
            </p>
            <ProcessoDecompositionComposedSection
              embeddedInCard
              processoId={processoId}
              processoNome={processo.nome_processo}
              getAccessToken={getAccessToken}
              onError={setError}
              resyncVersion={panelResyncVersion}
            />
          </div>
          <EditableSectionCard
            title="Mapeamento base do processo"
            description="Árvore WBS cadastrada (fonte estrutural). Edite aqui a base; as revisões vigentes aparecem acima na visão composta."
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
                resyncVersion={panelResyncVersion}
                onEntityChanged={() => void loadTimeline()}
              />
            }
            editContent={
              <ProcessoDecompositionSection
                embeddedInCard
                processoId={processoId}
                processoNome={processo.nome_processo}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={panelResyncVersion}
                onEntityChanged={() => void loadTimeline()}
              />
            }
          />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("diagrama") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "diagrama"} sectionId="diagrama">
          <div className="tm-processo-composed-card tm-processo-composed-card--first">
            <h3 className="ds-subsection-title">Diagrama composto (visão vigente)</h3>
            <p className="ds-hint">
              Macro do fluxo + deltas das revisões vigentes na data escolhida. Conflitos de
              interseção aparecem em destaque.
            </p>
            <ProcessoDiagramComposedSection
              embeddedInCard
              processoId={processoId}
              getAccessToken={getAccessToken}
              onError={setError}
              resyncVersion={panelResyncVersion}
            />
          </div>
          <EditableSectionCard
            title="Diagrama macro base"
            description="Mapa canônico cadastrado. Edite aqui a base; as revisões vigentes aparecem acima na visão composta."
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
                resyncVersion={panelResyncVersion}
                onEntityChanged={() => void loadTimeline()}
              />
            }
            editContent={
              <ProcessoDiagramSection
                embeddedInCard
                processoId={processoId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={panelResyncVersion}
                onEntityChanged={() => void loadTimeline()}
              />
            }
          />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("arquivos") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "arquivos"} sectionId="arquivos">
          <EditableSectionCard
            title={`Arquivos do processo${arquivosCount ? ` (${arquivosCount})` : ""}`}
            description="Documentos de referência do processo-mestre — POP, instruções, planilhas e links."
            hint={TM_HELP_TOOLTIPS.processos.arquivos}
            isEditing={sectionEdit.isEditing("arquivos")}
            onEdit={() => void sectionEdit.startEdit("arquivos")}
            onCancel={() => sectionEdit.cancelEdit("arquivos")}
            readContent={
              <ProcessoArquivosSection
                embeddedInCard
                readOnly
                processoId={processoId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={panelResyncVersion}
              />
            }
            editContent={
              <ProcessoArquivosSection
                embeddedInCard
                processoId={processoId}
                getAccessToken={getAccessToken}
                onError={setError}
                resyncVersion={panelResyncVersion}
                onChanged={() => void load()}
              />
            }
          />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("melhorias") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "melhorias"} sectionId="melhorias">
          <ProcessoInstanciasPanel
            instancias={instancias}
            selectedInstanciaId={null}
            options={options}
            processoEscopo={processoEscopoFromEntity(processo)}
            busy={refreshing}
            initialShowForm={openInstanciaForm}
            instanciasComRevisao={instanciasComRevisao}
            navigateOnSelect
            onSelect={(instanciaId) => onNavigate(buildInstanciaPath(processoId, instanciaId))}
            onCreate={async (payload) => {
              await createProcessoInstancia(processoId, payload, getAccessToken);
              setOpenInstanciaForm(false);
              await load();
              requestWorkspaceTreeRefresh();
            }}
            onUpdate={async (instanciaId, payload) => {
              await updateInstancia(instanciaId, payload, getAccessToken);
              await load();
              requestWorkspaceTreeRefresh();
            }}
            onDelete={async (instanciaId) => {
              await deleteInstancia(instanciaId, getAccessToken);
              await load();
              requestWorkspaceTreeRefresh();
            }}
            onDuplicate={async ({ origemInstanciaId, ...payload }) => {
              await duplicateInstancia(origemInstanciaId, payload, getAccessToken);
              await load();
              requestWorkspaceTreeRefresh();
            }}
          />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("priorizacao") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "priorizacao"} sectionId="priorizacao">
            <ProcessoMatrizImpactoSection
              processoId={processoId}
              processoLabel={processo.nome_processo}
              getAccessToken={getAccessToken}
              onError={setError}
              onNavigate={onNavigate}
              resyncVersion={panelResyncVersion}
            />
          </ProcessoWorkspaceSectionPanel>
        ) : null}

        {visibleSections.has("timeline") ? (
          <ProcessoWorkspaceSectionPanel active={activeSection === "timeline"} sectionId="timeline">
          <ProcessoTimeline entries={timelineEntries} loading={timelineLoading} />
          </ProcessoWorkspaceSectionPanel>
        ) : null}
    </>
  );

  const pageBody = (
    <>
      {!embedded ? (
        <PageHeader
          title={`${processo.codigo_processo} — ${processo.nome_processo}`}
          subtitle={[processo.status_processo, processo.familia_processo ? `família ${processo.familia_processo}` : null]
            .filter(Boolean)
            .join(" · ")}
          currentPath={pathname ?? TRANSFORMOMETRO_ROUTES.processos}
          onNavigate={onNavigate}
          actions={
            <>
              <button type="button" className={DS_GHOST_BTN} onClick={onBack}>
                <ArrowLeft size={16} />
                Lista
              </button>
              <button
                type="button"
                className={DS_GHOST_BTN}
                disabled={refreshing}
                onClick={() => void handleDuplicateProcesso()}
              >
                <Copy size={16} />
                Duplicar processo
              </button>
              <button
                type="button"
                className={dsGhostBtn('danger')}
                disabled={refreshing}
                onClick={() => void handleDeleteProcesso()}
              >
                <Trash2 size={16} />
                Excluir processo
              </button>
            </>
          }
        />
      ) : null}

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      {embedded ? (
        sectionPanels
      ) : (
        <ProcessoWorkspaceShell
          processoId={processoId}
          activeNodeId={activeNodeId}
          getAccessToken={getAccessToken}
          onNavigate={onNavigate}
          processo={processo}
          instancias={instancias}
          revisoes={revisoes}
        >
          {sectionPanels}
        </ProcessoWorkspaceShell>
      )}
    </>
  );

  if (embedded) return pageBody;
  return <TransformometroShell>{pageBody}</TransformometroShell>;
}
