import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { DataTableSection } from "../../components/DataTableSection";
import { InstanciaReadView } from "../../components/instancia/InstanciaReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { RevisaoComparativoSection } from "../../components/processo/RevisaoComparativoSection";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { FieldLabel } from "../../components/HelpTooltip";
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
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancia, setInstancia] = useState<ProcessoInstancia | null>(null);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [comparativo, setComparativo] = useState<ProcessoComparativoItem[]>([]);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [showRevisaoForm, setShowRevisaoForm] = useState(false);
  const [revForm, setRevForm] = useState({
    versao_revisao: "1.0.0",
    cenario_tipo: "baseline",
    data_inicio_vigencia: todayDateInput(),
    data_implantacao: "",
    data_fim_vigencia: "",
    revisao_ativa: true,
  });

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

  async function handleDeleteRevisao(revisao: Revisao) {
    const label = `v${revisao.versao_revisao} (${revisao.cenario_tipo})`;
    if (!window.confirm(`Excluir a revisão ${label}?`)) return;
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
        onOpen: (revisaoId) =>
          onNavigate(buildProcessoPath(processoId, revisaoId, instanciaId)),
        onDelete: (revisao) => void handleDeleteRevisao(revisao),
      }),
    [instanciaId, onNavigate, processoId]
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
            <button type="button" className="ds-primary-btn" onClick={() => setShowRevisaoForm((v) => !v)}>
              <Plus size={16} />
              {showRevisaoForm ? "Cancelar revisão" : "Nova revisão"}
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              onClick={() => {
                if (!window.confirm("Excluir esta instância operacional?")) return;
                void deleteInstancia(instanciaId, getAccessToken).then(() =>
                  onNavigate(buildProcessoPath(processoId))
                );
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

      {showRevisaoForm ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">Nova revisão</h2>
          <form onSubmit={handleCreateRevisao}>
            <div className="ds-filters-row">
              <div className="ds-filter-box">
                <FieldLabel label="Versão" hint={TM_HELP_TOOLTIPS.revisao.versao} />
                <input
                  id="tm-rev-versao"
                  required
                  value={revForm.versao_revisao}
                  onChange={(e) => setRevForm({ ...revForm, versao_revisao: e.target.value })}
                />
              </div>
              <div className="ds-filter-box">
                <FieldLabel label="Cenário" hint={TM_HELP_TOOLTIPS.revisao.cenario} />
                <select
                  id="tm-rev-cenario"
                  value={revForm.cenario_tipo}
                  onChange={(e) => setRevForm({ ...revForm, cenario_tipo: e.target.value })}
                >
                  {options.cenario_tipo.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div className="ds-filter-box">
                <FieldLabel label="Início vigência" hint={TM_HELP_TOOLTIPS.revisao.inicioVigencia} />
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
        footer={
          <p className="ds-hint">
            Abra uma revisão para cadastrar medição, investimentos, recursos compartilhados e evidências.
          </p>
        }
      />
    </TransformometroShell>
  );
}
