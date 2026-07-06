import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Search, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { RecursoReadView } from "../../components/recurso/RecursoReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { FieldLabel, HelpTooltip, TableHeader } from "../../components/HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { CATALOG_CREATE, isCatalogCreateId } from "../../constants/catalogRoutes";
import {
  createRecurso,
  deleteRecurso,
  deleteVinculo,
  fetchOptions,
  fetchRecurso,
  fetchRecursoVinculos,
  updateRecurso,
  updateVinculo,
  type OptionsData,
  type RecursoCompartilhado,
  type VinculoRecurso,
} from "../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../utils/dateInputs";
import { buildProcessoPath, buildRecursoPath } from "../../utils/routeParser";
import { RecursoCatalogFormFields } from "../recursos/RecursoCatalogFormFields";
import { RecursoCustosSection } from "../recursos/RecursoCustosSection";
import {
  emptyRecursoForm,
  payloadFromRecursoForm,
  recursoFormFromEntity,
  type RecursoCatalogFormState,
} from "../recursos/recursoCatalogForm";

const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;

type Props = Pick<AppProps, "getAccessToken"> & {
  recursoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

type VinculoEditForm = {
  ativo: boolean;
  data_inicio_uso: string;
  data_fim_uso: string;
  peso_rateio: string;
  observacoes: string;
};

function formFromVinculo(vinculo: VinculoRecurso): VinculoEditForm {
  return {
    ativo: Boolean(vinculo.ativo),
    data_inicio_uso: toDateInputValue(vinculo.data_inicio_uso),
    data_fim_uso: toDateInputValue(vinculo.data_fim_uso),
    peso_rateio: vinculo.peso_rateio == null ? "" : String(vinculo.peso_rateio),
    observacoes: vinculo.observacoes ?? "",
  };
}

export function RecursoDetailPage({
  recursoId,
  pathname,
  getAccessToken,
  onNavigate,
  onBack,
}: Props) {
  const confirm = useConfirm();
  const isCreate = isCatalogCreateId("recurso", recursoId);
  const [recurso, setRecurso] = useState<RecursoCompartilhado | null>(null);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [form, setForm] = useState<RecursoCatalogFormState>(() => emptyRecursoForm());
  const [vinculos, setVinculos] = useState<VinculoRecurso[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isCreate);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editingVinculoId, setEditingVinculoId] = useState<string | null>(null);
  const [editVinculoForm, setEditVinculoForm] = useState<VinculoEditForm | null>(null);
  const [search, setSearch] = useState("");

  const load = useCallback(async () => {
    if (isCreate) {
      const opts = await fetchOptions(getAccessToken);
      setOptions(opts);
      setForm(emptyRecursoForm());
      setLoading(false);
      return;
    }

    setRefreshing(true);
    setError(null);
    try {
      const [recursoData, vinculosData, opts] = await Promise.all([
        fetchRecurso(recursoId, getAccessToken),
        fetchRecursoVinculos(recursoId, getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setRecurso(recursoData);
      setVinculos(vinculosData.items);
      setOptions(opts);
      setForm(recursoFormFromEntity(recursoData));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar recurso");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [getAccessToken, isCreate, recursoId]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "recurso",
    entityId: recursoId,
    getAccessToken,
    enabled: !isCreate,
    onResync: () => void load(),
  });

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (isCreate) {
      sectionEdit.startEdit("recurso");
    }
  }, [isCreate, sectionEdit]);

  useEffect(() => {
    if (!recurso || sectionEdit.isEditing("recurso")) return;
    setForm(recursoFormFromEntity(recurso));
  }, [recurso, sectionEdit]);

  const ativos = useMemo(() => vinculos.filter((v) => v.ativo).length, [vinculos]);

  const filteredVinculos = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return vinculos;
    return vinculos.filter((row) =>
      [
        row.codigo_processo,
        row.nome_processo,
        row.filial_id,
        row.setor_id,
        row.familia_processo,
        row.versao_revisao,
        row.cenario_tipo,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [search, vinculos]);

  async function handleSaveRecurso() {
    setSaving(true);
    setError(null);
    const payload = payloadFromRecursoForm(form);
    try {
      if (isCreate) {
        const created = await createRecurso(payload, getAccessToken);
        onNavigate(buildRecursoPath(created.recurso_compartilhado_id));
        return;
      }
      const updated = await updateRecurso(recursoId, payload, getAccessToken);
      setRecurso(updated);
      sectionEdit.stopEdit("recurso");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar recurso");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteRecurso() {
    if (!recurso) return;
    const confirmed = await confirm({
      title: "Excluir recurso",
      message: `Excluir ${recurso.codigo_recurso} — ${recurso.nome_recurso}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteRecurso(recurso.recurso_compartilhado_id, getAccessToken);
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir recurso");
    }
  }

  function cancelRecursoEdit() {
    if (isCreate) {
      onBack();
      return;
    }
    if (recurso) setForm(recursoFormFromEntity(recurso));
    sectionEdit.cancelEdit("recurso");
  }

  function startEditVinculo(vinculo: VinculoRecurso) {
    setEditingVinculoId(vinculo.vinculo_id);
    setEditVinculoForm(formFromVinculo(vinculo));
  }

  function cancelEditVinculo() {
    setEditingVinculoId(null);
    setEditVinculoForm(null);
  }

  async function saveEditVinculo(event: React.FormEvent) {
    event.preventDefault();
    if (!editingVinculoId || !editVinculoForm) return;

    const peso = editVinculoForm.peso_rateio.trim()
      ? Number.parseFloat(editVinculoForm.peso_rateio)
      : undefined;
    if (peso != null && (!Number.isFinite(peso) || peso < 0)) {
      setError("Informe um peso de rateio válido.");
      return;
    }

    setError(null);
    try {
      await updateVinculo(
        editingVinculoId,
        {
          ativo: editVinculoForm.ativo,
          data_inicio_uso: optionalDateField(editVinculoForm.data_inicio_uso) ?? undefined,
          data_fim_uso: optionalDateField(editVinculoForm.data_fim_uso) ?? undefined,
          peso_rateio: peso,
          observacoes: editVinculoForm.observacoes.trim() || undefined,
        },
        getAccessToken
      );
      cancelEditVinculo();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar vínculo");
    }
  }

  async function handleDeleteVinculo(vinculo: VinculoRecurso) {
    const label = `${vinculo.codigo_processo ?? "processo"} — ${vinculo.nome_processo ?? ""}`;
    const confirmed = await confirm({
      title: "Desvincular recurso",
      message: `Desvincular este recurso de ${label}?`,
      confirmLabel: "Desvincular",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteVinculo(vinculo.vinculo_id, getAccessToken);
      if (editingVinculoId === vinculo.vinculo_id) cancelEditVinculo();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao desvincular recurso");
    }
  }

  if (loading && !isCreate && !recurso) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando detalhe do recurso"
          description="Buscando cadastro, custos e processos vinculados."
        />
      </TransformometroShell>
    );
  }

  if (!isCreate && !recurso && !loading) {
    return (
      <TransformometroShell>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Recurso não encontrado."}</p>
          <button type="button" className="ds-ghost-btn" onClick={onBack}>
            Voltar à lista
          </button>
        </div>
      </TransformometroShell>
    );
  }

  const title = isCreate
    ? "Novo recurso"
    : `${recurso?.codigo_recurso ?? ""} — ${recurso?.nome_recurso ?? ""}`;

  return (
    <TransformometroShell>
      <PageHeader
        title={title}
        subtitle={
          isCreate
            ? "Cadastre licenças e ferramentas compartilhadas do catálogo global"
            : "Detalhes, histórico de custos e processos vinculados"
        }
        currentPath={
          pathname ?? (isCreate ? buildRecursoPath(CATALOG_CREATE.recurso) : buildRecursoPath(recursoId))
        }
        onNavigate={onNavigate}
        actions={
          <>
            <button type="button" className="ds-ghost-btn" onClick={onBack}>
              <ArrowLeft size={16} />
              Lista
            </button>
            {!isCreate ? (
              <button type="button" className="ds-ghost-btn" onClick={() => void handleDeleteRecurso()}>
                <Trash2 size={16} />
                Excluir
              </button>
            ) : null}
          </>
        }
      />

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={Boolean(recurso) || isCreate}
        onRetry={() => void load()}
      />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      <div className="ds-cadastro-panel ds-cadastro-panel--cards">
        {options ? (
          <EditableSectionCard
            title="Dados do recurso"
            description="Cadastro principal — rateio, escopo e vigência."
            isEditing={isCreate || sectionEdit.isEditing("recurso")}
            onEdit={() => void sectionEdit.startEdit("recurso")}
            onCancel={cancelRecursoEdit}
            onSave={() => void handleSaveRecurso()}
            saving={saving}
            editable={!isCreate}
            readContent={
              recurso ? <RecursoReadView recurso={recurso} vinculosAtivos={ativos} /> : null
            }
            editContent={
              <form
                onSubmit={(event) => {
                  event.preventDefault();
                  void handleSaveRecurso();
                }}
              >
                <RecursoCatalogFormFields
                  form={form}
                  options={options}
                  onChange={setForm}
                  submitLabel="Salvar alterações"
                  hideSubmit
                />
              </form>
            }
          />
        ) : null}

        {!isCreate ? (
          <>
            <EditableSectionCard
              title="Custos ao longo do tempo"
              description="Histórico de vigências de custo mensal usado no dashboard."
              isEditing={sectionEdit.isEditing("custos")}
              onEdit={() => void sectionEdit.startEdit("custos")}
              onCancel={() => sectionEdit.cancelEdit("custos")}
              readContent={
                <RecursoCustosSection
                  embeddedInCard
                  readOnly
                  recursoId={recursoId}
                  getAccessToken={getAccessToken}
                  onError={setError}
                  onRecursoSynced={() => void load()}
                />
              }
              editContent={
                <RecursoCustosSection
                  embeddedInCard
                  recursoId={recursoId}
                  getAccessToken={getAccessToken}
                  onError={setError}
                  onRecursoSynced={() => void load()}
                />
              }
            />

            <section className="ds-card ds-table-section" aria-busy={loading || refreshing}>
              <div className="ds-table-section__header">
                <h2 className="ds-section-title">Processos vinculados</h2>
                <div className="ds-table-section__meta-group">
                  <span className="ds-table-section__meta">
                    Vínculos ativos entram no rateio das revisões
                  </span>
                  <span className="ds-table-section__meta">{filteredVinculos.length} registro(s)</span>
                </div>
              </div>

              <div className="ds-table-toolbar">
                <div className="ds-table-search" role="search">
                  <Search size={16} aria-hidden="true" className="ds-table-search__icon" />
                  <input
                    type="search"
                    className="ds-table-search__input"
                    value={search}
                    placeholder="Código, processo, unidade, departamento…"
                    onChange={(event) => setSearch(event.target.value)}
                    aria-label="Filtrar processos vinculados"
                  />
                </div>
              </div>

              {filteredVinculos.length === 0 ? (
                <p className="ds-state-box">Nenhum processo vinculado a este recurso.</p>
              ) : (
                <div className="ds-table-wrap ds-cadastro-section__table">
                  <table className="ds-table ds-table--compact">
                    <thead>
                      <tr>
                        <th><TableHeader label="Processo" hint={C.processo} /></th>
                        <th><TableHeader label="Unidade" hint={C.unidade} /></th>
                        <th><TableHeader label="Departamento" hint={C.setor} /></th>
                        <th><TableHeader label="Revisão" hint={C.revisao} /></th>
                        <th><TableHeader label="Uso no processo" hint={C.usoRevisao} /></th>
                        <th><TableHeader label="Peso" hint={C.peso} /></th>
                        <th><TableHeader label="Ativo" hint={C.ativoVinculo} /></th>
                        <th className="ds-table__actions-col">
                          <TableHeader label="Ações" hint={C.acoes} />
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredVinculos.map((row) =>
                        editingVinculoId === row.vinculo_id && editVinculoForm ? (
                          <tr key={row.vinculo_id} className="ds-table__row--editing">
                            <td colSpan={8}>
                              <form className="ds-cadastro-subsection" onSubmit={saveEditVinculo}>
                                <h4 className="ds-cadastro-subsection__title">
                                  Editar vínculo — {row.codigo_processo ?? "—"} · {row.nome_processo ?? "—"}
                                </h4>
                                <div className="ds-filters-row">
                                  <label className="ds-filter-box">
                                    <FieldLabel label="Início do uso" hint={R.vinculoInicio} />
                                    <input
                                      type="date"
                                      value={editVinculoForm.data_inicio_uso}
                                      onChange={(event) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          data_inicio_uso: event.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label className="ds-filter-box">
                                    <FieldLabel label="Fim do uso" hint={R.vinculoFim} />
                                    <input
                                      type="date"
                                      value={editVinculoForm.data_fim_uso}
                                      onChange={(event) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          data_fim_uso: event.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label className="ds-filter-box">
                                    <FieldLabel label="Peso do rateio" hint={R.peso} />
                                    <input
                                      type="number"
                                      min={0}
                                      step="any"
                                      value={editVinculoForm.peso_rateio}
                                      onChange={(event) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          peso_rateio: event.target.value,
                                        })
                                      }
                                    />
                                  </label>
                                  <label className="ds-check-label">
                                    <input
                                      type="checkbox"
                                      checked={editVinculoForm.ativo}
                                      onChange={(event) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          ativo: event.target.checked,
                                        })
                                      }
                                    />
                                    <span className="tm-field__label">
                                      Vínculo ativo
                                      <HelpTooltip content={R.vinculoAtivo} ariaLabel="Ajuda: Vínculo ativo" />
                                    </span>
                                  </label>
                                </div>
                                <label className="ds-filter-box ds-filter-box--wide">
                                  <FieldLabel label="Observações" hint={R.vinculoObservacoes} />
                                  <input
                                    value={editVinculoForm.observacoes}
                                    onChange={(event) =>
                                      setEditVinculoForm({
                                        ...editVinculoForm,
                                        observacoes: event.target.value,
                                      })
                                    }
                                  />
                                </label>
                                <div className="ds-cadastro-form__actions">
                                  <button type="submit" className="ds-primary-btn">
                                    Salvar vínculo
                                  </button>
                                  <button type="button" className="ds-ghost-btn" onClick={cancelEditVinculo}>
                                    Cancelar
                                  </button>
                                </div>
                              </form>
                            </td>
                          </tr>
                        ) : (
                          <tr key={row.vinculo_id}>
                            <td className="ds-table__col--wide">
                              <button
                                type="button"
                                className="ds-link-btn"
                                onClick={() => {
                                  if (row.processo_id) {
                                    onNavigate(buildProcessoPath(row.processo_id, row.revisao_id));
                                  }
                                }}
                              >
                                {row.codigo_processo ?? "—"} — {row.nome_processo ?? "—"}
                              </button>
                            </td>
                            <td>{row.filial_id ?? "—"}</td>
                            <td>{row.setor_id ?? "—"}</td>
                            <td>
                              {row.versao_revisao ?? "—"} · {row.cenario_tipo ?? "—"}
                            </td>
                            <td>
                              {toDateInputValue(row.data_inicio_uso) || "…"} →{" "}
                              {toDateInputValue(row.data_fim_uso) || "…"}
                            </td>
                            <td className="ds-table__col--numeric">{row.peso_rateio ?? "—"}</td>
                            <td>{row.ativo ? "Sim" : "Não"}</td>
                            <td className="ds-table__actions-col">
                              <button
                                type="button"
                                className="ds-ghost-btn"
                                onClick={() => startEditVinculo(row)}
                              >
                                Editar
                              </button>
                              <button
                                type="button"
                                className="ds-ghost-btn"
                                onClick={() => void handleDeleteVinculo(row)}
                              >
                                Desvincular
                              </button>
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        ) : null}
      </div>
    </TransformometroShell>
  );
}
