import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { DataTableSection } from "../../components/DataTableSection";
import { InstanciaReadView } from "../../components/instancia/InstanciaReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { useTransformometroEntityWatch } from "../../hooks/useTransformometroEntityWatch";
import { useScrollToRef } from "../../hooks/useScrollToRef";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { RevisaoComparativoSection } from "../../components/processo/RevisaoComparativoSection";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { FieldLabel } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { cenarioSelectLabel } from "../../content/cenarioLabels";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  createRevisao,
  createProcessoInstancia,
  deleteInstancia,
  deleteRevisao,
  duplicateInstancia,
  duplicateRevisao,
  fetchOptions,
  fetchProcesso,
  fetchProcessoComparativo,
  fetchProcessoInstancias,
  fetchRevisoes,
  updateInstancia,
  type OptionsData,
  type Processo,
  type ProcessoComparativoItem,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { optionalDateField, todayDateInput } from "../../utils/dateInputs";
import {
  buildComparativoColumns,
  buildRevisaoColumns,
} from "../../utils/processoDetailTables";
import { buildInstanciaPath, buildProcessoPath } from "../../utils/routeParser";
import { ProcessoInstanciasPanel } from "../processos/ProcessoInstanciasPanel";
import { processoEscopoFromEntity } from "../processos/processoEscopo";
import { ProcessoWorkspaceShell } from "../processos/ProcessoWorkspaceShell";
import { resolveActiveWorkspaceNodeId } from "../processos/processoWorkspaceNav";
import { useProcessoWorkspacePanelActions } from "../processos/processoWorkspacePanelActions";
import { InstanciaDiagramEscopoSection } from "../../components/diagram/InstanciaDiagramEscopoSection";
import { InstanciaDecompositionEscopoSection } from "../../components/decomposition/InstanciaDecompositionEscopoSection";
import { InstanciaContextoSection } from "../../components/decomposition/InstanciaContextoSection";
import { InstanciaMatrizRevisoesSection } from "../instancia/InstanciaMatrizRevisoesSection";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  embedded?: boolean;
  embeddedActive?: boolean;
};

export function InstanciaDetailPage({
  getAccessToken,
  processoId,
  instanciaId,
  pathname,
  onNavigate,
  embedded = false,
  embeddedActive = true,
}: Props) {
  const confirm = useConfirm();
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancia, setInstancia] = useState<ProcessoInstancia | null>(null);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [allRevisoes, setAllRevisoes] = useState<Revisao[]>([]);
  const [allInstancias, setAllInstancias] = useState<ProcessoInstancia[]>([]);
  const [comparativo, setComparativo] = useState<ProcessoComparativoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRevisaoForm, setShowRevisaoForm] = useState(false);
  const pendingRevisaoScroll = useRef(false);
  const consumedNovaRevisaoHash = useRef(false);
  const { ref: revisoesSectionRef, scrollToRef: scrollToRevisoes } = useScrollToRef<HTMLElement>();
  const [revForm, setRevForm] = useState({
    versao_revisao: "1.0.0",
    cenario_tipo: "baseline",
    revisao_referencia_id: "",
    data_inicio_vigencia: todayDateInput(),
    data_implantacao: "",
    data_fim_vigencia: "",
    revisao_ativa: true,
  });

  const revisoesById = useMemo(
    () => new Map(revisoes.map((item) => [item.revisao_id, item])),
    [revisoes]
  );

  const referenciaOptions = useMemo(
    () =>
      revisoes.map((item) => ({
        value: item.revisao_id,
        label: revisaoDisplayLabel(item),
      })),
    [revisoes]
  );

  const defaultReferenciaId = useMemo(() => {
    const active = revisoes.find((item) => item.revisao_ativa);
    if (active) return active.revisao_id;
    return revisoes[revisoes.length - 1]?.revisao_id ?? "";
  }, [revisoes]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [proc, revs, opts, comp, inst] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
        fetchOptions(getAccessToken),
        fetchProcessoComparativo(processoId, getAccessToken),
        fetchProcessoInstancias(processoId, getAccessToken),
      ]);
      const row = inst.items.find((item) => item.instancia_id === instanciaId) ?? null;
      setProcesso(proc);
      setInstancia(row);
      setAllInstancias(inst.items);
      setAllRevisoes(revs.items);
      setRevisoes(revs.items.filter((item) => item.instancia_id === instanciaId));
      const revisaoIds = new Set(
        revs.items.filter((item) => item.instancia_id === instanciaId).map((item) => item.revisao_id)
      );
      setComparativo(comp.items.filter((item) => revisaoIds.has(item.revisao_id)));
      setOptions(opts);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, processoId]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "processo_instancia",
    entityId: instanciaId,
    getAccessToken,
    enabled: !embedded || embeddedActive,
    onResync: () => void load(),
  });

  useTransformometroEntityWatch({
    entities: [{ entityType: "processo", entityId: processoId }],
    getAccessToken,
    enabled: (!embedded || embeddedActive) && Boolean(processoId),
    onEntityUpdated: sectionEdit.handleRemoteEntityUpdate,
  });

  useEffect(() => {
    void load();
  }, [load]);

  function buildNovaRevisaoFormState() {
    return {
      versao_revisao: revisoes.length ? "2.0.0" : "1.0.0",
      cenario_tipo: revisoes.length ? "melhoria" : "baseline",
      revisao_referencia_id: defaultReferenciaId,
      data_inicio_vigencia: todayDateInput(),
      data_implantacao: "",
      data_fim_vigencia: "",
      revisao_ativa: revisoes.length > 0,
    };
  }

  function openNovaRevisaoForm() {
    setRevForm(buildNovaRevisaoFormState());
    if (showRevisaoForm) {
      scrollToRevisoes();
      return;
    }
    pendingRevisaoScroll.current = true;
    setShowRevisaoForm(true);
  }

  const closeNovaRevisaoForm = useCallback(() => {
    setShowRevisaoForm(false);
  }, []);

  useEffect(() => {
    if (!showRevisaoForm || !pendingRevisaoScroll.current) return;
    pendingRevisaoScroll.current = false;
    scrollToRevisoes();
  }, [showRevisaoForm, scrollToRevisoes]);

  useEffect(() => {
    if (loading || !instancia || consumedNovaRevisaoHash.current) return;
    if (typeof window === "undefined") return;
    if (window.location.hash !== "#nova-revisao") return;
    consumedNovaRevisaoHash.current = true;
    window.history.replaceState(null, "", window.location.pathname);
    openNovaRevisaoForm();
  }, [loading, instancia, revisoes.length, defaultReferenciaId]);

  async function handleDeleteRevisao(revisao: Revisao) {
    const label = revisaoDisplayLabel(revisao);
    const confirmed = await confirm({
      title: "Excluir revisão",
      message: `Excluir a revisão ${label}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteRevisao(revisao.revisao_id, getAccessToken);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir revisão");
    }
  }

  async function handleDuplicateRevisao(revisao: Revisao) {
    const label = revisaoDisplayLabel(revisao);
    const confirmed = await confirm({
      title: "Duplicar revisão",
      message: `Duplicar ${label}? Serão copiados medição, investimentos, vínculos, mapeamento, diagrama, evidências e matriz impacto × esforço. A nova revisão ficará inativa.`,
      confirmLabel: "Duplicar",
    });
    if (!confirmed) return;
    setError(null);
    try {
      const result = await duplicateRevisao(revisao.revisao_id, undefined, getAccessToken);
      await load();
      onNavigate(buildProcessoPath(processoId, result.revisao.revisao_id, instanciaId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao duplicar revisão");
    }
  }

  const comparativoColumns = useMemo(() => buildComparativoColumns(), []);
  const revisaoColumns = useMemo(
    () =>
      buildRevisaoColumns({
        revisoesById,
        onOpen: (revisaoId) =>
          onNavigate(buildProcessoPath(processoId, revisaoId, instanciaId)),
        onDuplicate: (revisao) => void handleDuplicateRevisao(revisao),
        onDelete: (revisao) => void handleDeleteRevisao(revisao),
      }),
    [instanciaId, onNavigate, processoId, revisoesById]
  );

  async function handleCreateRevisao(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await createRevisao(
        {
          processo_id: processoId,
          instancia_id: instanciaId,
          versao_revisao: revForm.versao_revisao,
          cenario_tipo: revForm.cenario_tipo,
          revisao_referencia_id:
            revForm.cenario_tipo === "baseline" ? undefined : revForm.revisao_referencia_id,
          data_inicio_vigencia: revForm.data_inicio_vigencia,
          revisao_ativa: revForm.revisao_ativa,
          data_implantacao: optionalDateField(revForm.data_implantacao),
          data_fim_vigencia: optionalDateField(revForm.data_fim_vigencia),
        },
        getAccessToken
      );
      setShowRevisaoForm(false);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar revisão");
    }
  }

  const fetchProgress = useTrackedSingleFetchProgress(loading && !instancia);
  const loadingProgress = useLoadingProgress(loading && !instancia, fetchProgress);

  const panelSidebarActions = useMemo(
    () =>
      embedded && instancia ? (
        <>
          {showRevisaoForm ? (
            <button
              type="button"
              className="ds-ghost-btn tm-processo-workspace-sidebar__action-btn"
              onClick={closeNovaRevisaoForm}
            >
              Cancelar revisão
            </button>
          ) : (
            <button
              type="button"
              className="ds-primary-btn tm-processo-workspace-sidebar__action-btn"
              onClick={openNovaRevisaoForm}
            >
              <Plus size={16} />
              Nova revisão
            </button>
          )}
          <button
            type="button"
            className="ds-ghost-btn ds-ghost-btn--danger tm-processo-workspace-sidebar__action-btn"
            onClick={() => {
              void (async () => {
                const confirmed = await confirm({
                  title: "Excluir melhoria",
                  message: "Excluir esta instância operacional?",
                  confirmLabel: "Excluir",
                  variant: "danger",
                });
                if (!confirmed) return;
                await deleteInstancia(instanciaId, getAccessToken);
                onNavigate(buildProcessoPath(processoId));
              })();
            }}
          >
            <Trash2 size={16} />
            Excluir instância
          </button>
        </>
      ) : null,
    [
      closeNovaRevisaoForm,
      confirm,
      embedded,
      getAccessToken,
      instancia,
      instanciaId,
      onNavigate,
      openNovaRevisaoForm,
      processoId,
      showRevisaoForm,
    ]
  );

  useProcessoWorkspacePanelActions(panelSidebarActions, embedded && embeddedActive);

  if (loading && !instancia) {
    const loader = (
      <LoadingActivityCard
        title="Carregando instância"
        description="Buscando dados operacionais e revisões."
        progressPercent={loadingProgress}
      />
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  if (!processo || !instancia || !options) {
    const errorView = (
      <div className="ds-state ds-state--error" role="alert">
        <p>{error ?? "Instância não encontrada."}</p>
        <button type="button" className="ds-ghost-btn" onClick={() => onNavigate(buildProcessoPath(processoId))}>
          Voltar ao processo
        </button>
      </div>
    );
    if (embedded) return errorView;
    return <TransformometroShell>{errorView}</TransformometroShell>;
  }

  const instanciaLabel = instancia.todas_filiais_ativas
    ? "Todas as unidades ativas"
    : `${instancia.codigo_filial ?? instancia.filial_id} · ${instancia.setores?.[0]?.codigo_setor ?? instancia.codigo_setor ?? ""}`;

  const instanciaMain = (
    <>
        <EditableSectionCard
          title="Instância operacional"
        hint={TM_HELP_TOOLTIPS.instancias.escopo}
        isEditing={sectionEdit.isEditing("instancia")}
        onEdit={() => void sectionEdit.startEdit("instancia")}
        onCancel={() => sectionEdit.cancelEdit("instancia")}
        readContent={<InstanciaReadView instancia={instancia} options={options} />}
        editContent={
          <ProcessoInstanciasPanel
            hideTable
            initialEditInstanciaId={instanciaId}
            onCancelEdit={() => sectionEdit.cancelEdit("instancia")}
            instancias={[instancia]}
            selectedInstanciaId={instanciaId}
            options={options}
            processoEscopo={processo ? processoEscopoFromEntity(processo) : null}
            instanciasComRevisao={revisoes.length > 0 ? [instanciaId] : []}
            onSelect={() => undefined}
            onCreate={async (payload) => {
              await createProcessoInstancia(processoId, payload, getAccessToken);
              await load();
            }}
            onUpdate={async (id, payload) => {
              await updateInstancia(id, payload, getAccessToken);
              sectionEdit.cancelEdit("instancia");
              await load();
            }}
            onDelete={async () => undefined}
            onDuplicate={async ({ origemInstanciaId, ...payload }) => {
              await duplicateInstancia(origemInstanciaId, payload, getAccessToken);
              await load();
            }}
          />
        }
      />

      <EditableSectionCard
        title="Escopo no mapeamento"
        description="Quais processos-chave deste macroprocesso esta instância trata."
        hint={TM_HELP_TOOLTIPS.decomposition.escopoInstancia}
        isEditing={sectionEdit.isEditing("decomposicao_escopo")}
        onEdit={() => void sectionEdit.startEdit("decomposicao_escopo")}
        onCancel={() => sectionEdit.cancelEdit("decomposicao_escopo")}
        readContent={
          <InstanciaDecompositionEscopoSection
            embeddedInCard
            readOnly
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
        editContent={
          <InstanciaDecompositionEscopoSection
            embeddedInCard
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
      />

      <EditableSectionCard
        title="Contexto operacional"
        description="Metadados locais da instância — rollout, responsáveis e observações."
        hint={TM_HELP_TOOLTIPS.decomposition.contextoInstancia}
        isEditing={sectionEdit.isEditing("instancia_contexto")}
        onEdit={() => void sectionEdit.startEdit("instancia_contexto")}
        onCancel={() => sectionEdit.cancelEdit("instancia_contexto")}
        readContent={
          <InstanciaContextoSection
            embeddedInCard
            readOnly
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
        editContent={
          <InstanciaContextoSection
            embeddedInCard
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
            onSaved={() => sectionEdit.stopEdit("instancia_contexto")}
          />
        }
      />

      <EditableSectionCard
        title="Escopo no diagrama"
        description="Subset de nós do diagrama macro relevante para esta instância."
        hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopo}
        isEditing={sectionEdit.isEditing("diagrama_escopo")}
        onEdit={() => void sectionEdit.startEdit("diagrama_escopo")}
        onCancel={() => sectionEdit.cancelEdit("diagrama_escopo")}
        readContent={
          <InstanciaDiagramEscopoSection
            embeddedInCard
            readOnly
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
        editContent={
          <InstanciaDiagramEscopoSection
            embeddedInCard
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
            resyncVersion={sectionEdit.resyncVersion}
          />
        }
      />

      <section ref={revisoesSectionRef} id="tm-instancia-revisoes" className="tm-panel-stack">
      {showRevisaoForm ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Nova revisão</h2>
          <form onSubmit={handleCreateRevisao}>
            <div className="ds-filters-row">
              <div className="ds-filter-box">
                <FieldLabel className="tm-field__label" label="Versão" hint={TM_HELP_TOOLTIPS.revisao.versao} />
                <input
                  id="tm-rev-versao"
                  required
                  value={revForm.versao_revisao}
                  onChange={(e) => setRevForm({ ...revForm, versao_revisao: e.target.value })}
                />
              </div>
              <SelectField
                id="tm-rev-cenario"
                label="Cenário"
                hint={TM_HELP_TOOLTIPS.revisao.cenario}
                value={revForm.cenario_tipo}
                onChange={(cenario) =>
                  setRevForm((current) => ({
                    ...current,
                    cenario_tipo: cenario,
                    revisao_referencia_id:
                      cenario === "baseline"
                        ? ""
                        : current.revisao_referencia_id || defaultReferenciaId,
                    revisao_ativa: cenario === "baseline" ? false : current.revisao_ativa,
                  }))
                }
                options={mapSelectOptions(options.cenario_tipo, cenarioSelectLabel)}
              />
              {revForm.cenario_tipo !== "baseline" ? (
                <SelectField
                  id="tm-rev-referencia"
                  label="Compara com"
                  hint={TM_HELP_TOOLTIPS.revisao.referenciaComparacao}
                  required
                  value={revForm.revisao_referencia_id || defaultReferenciaId}
                  onChange={(revisaoReferenciaId) =>
                    setRevForm({ ...revForm, revisao_referencia_id: revisaoReferenciaId })
                  }
                  options={referenciaOptions}
                />
              ) : null}
              <div className="ds-filter-box">
                <FieldLabel className="tm-field__label" label="Início vigência" hint={TM_HELP_TOOLTIPS.revisao.inicioVigencia} />
                <input
                  id="tm-rev-inicio"
                  type="date"
                  required
                  value={revForm.data_inicio_vigencia}
                  onChange={(e) => setRevForm({ ...revForm, data_inicio_vigencia: e.target.value })}
                />
              </div>
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn">Salvar revisão</button>
              <button type="button" className="ds-ghost-btn" onClick={closeNovaRevisaoForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}

      {revisoes.length > 0 ? (
        <InstanciaMatrizRevisoesSection
          instanciaId={instanciaId}
          instanciaLabel={instanciaLabel}
          getAccessToken={getAccessToken}
          onError={setError}
          onNavigateToRevisao={(revisaoId) =>
            onNavigate(buildProcessoPath(processoId, revisaoId, instanciaId))
          }
        />
      ) : null}

      {comparativo.length > 0 ? (
        <RevisaoComparativoSection items={comparativo} columns={comparativoColumns} />
      ) : null}

      <DataTableSection
        title={`Revisões (${revisoes.length})`}
        columns={revisaoColumns}
        rows={revisoes}
        rowKey={(r) => r.revisao_id}
        hideSearch
        pageSize={10}
        emptyMessage="Nenhuma revisão nesta instância. Cadastre baseline e melhoria para mensurar economia."
        onRowClick={(r) => onNavigate(buildProcessoPath(processoId, r.revisao_id, instanciaId))}
        headerActions={
          showRevisaoForm ? (
            <button type="button" className="ds-ghost-btn" onClick={closeNovaRevisaoForm}>
              Cancelar revisão
            </button>
          ) : (
            <button type="button" className="ds-primary-btn" onClick={openNovaRevisaoForm}>
              <Plus size={16} />
              Nova revisão
            </button>
          )
        }
        footer={
          <p className="ds-hint">
            Abra uma revisão para cadastrar medição, investimentos, recursos compartilhados e evidências.
          </p>
        }
      />
      </section>
    </>
  );

  const pageBody = (
    <>
      {!embedded ? (
        <PageHeader
          title={instanciaLabel}
          subtitle={`${processo.codigo_processo} — ${processo.nome_processo} · ${instancia.status_instancia ?? "ativo"}`}
          currentPath={pathname ?? buildInstanciaPath(processoId, instanciaId)}
          onNavigate={onNavigate}
          actions={
            <>
              <button type="button" className="ds-ghost-btn" onClick={() => onNavigate(buildProcessoPath(processoId))}>
                <ArrowLeft size={16} />
                Processo
              </button>
              <button type="button" className="ds-primary-btn" onClick={openNovaRevisaoForm}>
                <Plus size={16} />
                Nova revisão
              </button>
              <button
                type="button"
                className="ds-ghost-btn"
                onClick={() => {
                  void (async () => {
                    const confirmed = await confirm({
                      title: "Excluir melhoria",
                      message: "Excluir esta instância operacional?",
                      confirmLabel: "Excluir",
                      variant: "danger",
                    });
                    if (!confirmed) return;
                    await deleteInstancia(instanciaId, getAccessToken);
                    onNavigate(buildProcessoPath(processoId));
                  })();
                }}
              >
                <Trash2 size={16} />
                Excluir instância
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

      {instancia.todas_filiais_ativas && options.filiais.length > 1 ? (
        <p className="tm-instancia-multi-banner">
          {TM_HELP_TOOLTIPS.instancias.multiplicadorConsolidado}{" "}
          Unidades ativas hoje: {options.filiais.length} (fator ×{options.filiais.length} no Consolidado).
        </p>
      ) : null}

      {embedded ? (
        instanciaMain
      ) : (
        <ProcessoWorkspaceShell
          processoId={processoId}
          activeNodeId={resolveActiveWorkspaceNodeId({ view: "instancia", instanciaId })}
          getAccessToken={getAccessToken}
          onNavigate={onNavigate}
          processo={processo}
          instancias={allInstancias}
          revisoes={allRevisoes}
        >
          {instanciaMain}
        </ProcessoWorkspaceShell>
      )}
    </>
  );

  if (embedded) return pageBody;
  return <TransformometroShell>{pageBody}</TransformometroShell>;
}
