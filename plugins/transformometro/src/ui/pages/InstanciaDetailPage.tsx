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
import { useScrollToRef } from "../../hooks/useScrollToRef";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { RevisaoComparativoSection } from "../../components/processo/RevisaoComparativoSection";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { FieldLabel } from "@delpi/plugin-ui";
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
import { InstanciaDiagramEscopoSection } from "../../components/diagram/InstanciaDiagramEscopoSection";
import { InstanciaDecompositionEscopoSection } from "../../components/decomposition/InstanciaDecompositionEscopoSection";
import { InstanciaContextoSection } from "../../components/decomposition/InstanciaContextoSection";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
};

export function InstanciaDetailPage({
  getAccessToken,
  processoId,
  instanciaId,
  pathname,
  onNavigate,
}: Props) {
  const confirm = useConfirm();
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancia, setInstancia] = useState<ProcessoInstancia | null>(null);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
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
    onResync: () => void load(),
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

  function closeNovaRevisaoForm() {
    setShowRevisaoForm(false);
  }

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

  const comparativoColumns = useMemo(() => buildComparativoColumns(), []);
  const revisaoColumns = useMemo(
    () =>
      buildRevisaoColumns({
        revisoesById,
        onOpen: (revisaoId) =>
          onNavigate(buildProcessoPath(processoId, revisaoId, instanciaId)),
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

  if (loading && !instancia) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando instância"
          description="Buscando dados operacionais e revisões."
          progressPercent={loadingProgress}
        />
      </TransformometroShell>
    );
  }

  if (!processo || !instancia || !options) {
    return (
      <TransformometroShell>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Instância não encontrada."}</p>
          <button type="button" className="ds-ghost-btn" onClick={() => onNavigate(buildProcessoPath(processoId))}>
            Voltar ao processo
          </button>
        </div>
      </TransformometroShell>
    );
  }

  const instanciaLabel = instancia.todas_filiais_ativas
    ? "Todas as unidades ativas"
    : `${instancia.codigo_filial ?? instancia.filial_id} · ${instancia.setores?.[0]?.codigo_setor ?? instancia.codigo_setor ?? ""}`;

  return (
    <TransformometroShell>
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
          />
        }
        editContent={
          <InstanciaDecompositionEscopoSection
            embeddedInCard
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
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
          />
        }
        editContent={
          <InstanciaContextoSection
            embeddedInCard
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
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
          />
        }
        editContent={
          <InstanciaDiagramEscopoSection
            embeddedInCard
            processoId={processoId}
            instanciaId={instanciaId}
            getAccessToken={getAccessToken}
            onError={setError}
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
    </TransformometroShell>
  );
}
