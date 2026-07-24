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
import { InlineErrorState } from "../../components/ErrorStateBox";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { FieldLabel, HelpTooltip, NativeCheckboxControl, NativeTextControl, valuesEqual } from "@delpi/plugin-ui/index";
import {
  DS_TABLE_CLASS_NAMES,
  DS_TABLE_SECTION_CLASS_NAMES,
} from "../../components/dataTableUi";
import { TableHeader } from "../../components/TableHeader";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { cenarioLabel } from "../../content/cenarioLabels";
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
import { RecursoWorkspaceSectionPanel } from "../configuracoes/RecursoWorkspaceSectionPanel";
import type { RecursoWorkspaceSectionId } from "../configuracoes/configuracoesWorkspaceNav";
import { defaultRecursoSection } from "../configuracoes/configuracoesWorkspaceNav";
import { RecursoCatalogFormFields } from "../recursos/RecursoCatalogFormFields";
import { RecursoCustosSection } from "../recursos/RecursoCustosSection";
import { DS_GHOST_BTN } from "../../components/ghostChrome";
import { DS_FILTERS_ROW, DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_WIDE } from "../../components/filterChrome";
import { EMPTY_STATE_CLASS } from "../../components/emptyStateUi";
import {
  emptyRecursoForm,
  payloadFromRecursoForm,
  recursoFormFromEntity,
  type RecursoCatalogFormState,
} from "../recursos/recursoCatalogForm";

const C = TM_HELP_TOOLTIPS.columns;
const R = TM_HELP_TOOLTIPS.recursos;
const tableCn = DS_TABLE_CLASS_NAMES;
const sectionCn = DS_TABLE_SECTION_CLASS_NAMES;

type Props = Pick<AppProps, "getAccessToken"> & {
  recursoId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
  embedded?: boolean;
  activeSection?: RecursoWorkspaceSectionId;
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
  embedded = false,
  activeSection = defaultRecursoSection(),
}: Props) {
  const confirm = useConfirm();
  const isCreate = isCatalogCreateId("recurso", recursoId);
  const [recurso, setRecurso] = useState<RecursoCompartilhado | null>(null);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [form, setForm] = useState<RecursoCatalogFormState>(() => emptyRecursoForm());
  const [formBaseline, setFormBaseline] = useState<RecursoCatalogFormState>(() => emptyRecursoForm());
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
      const empty = emptyRecursoForm();
      setForm(empty);
      setFormBaseline(empty);
      setLoading(false);
      return;
    }

    setRefreshing(true);
    try {
      const [recursoData, vinculosData, opts] = await Promise.all([
        fetchRecurso(recursoId, getAccessToken),
        fetchRecursoVinculos(recursoId, getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setRecurso(recursoData);
      setVinculos(vinculosData.items);
      setOptions(opts);
      const next = recursoFormFromEntity(recursoData);
      setForm(next);
      setFormBaseline(next);
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

  const editingRecurso = sectionEdit.isEditing("recurso");

  useEffect(() => {
    if (isCreate) {
      sectionEdit.startEdit("recurso");
    }
  }, [isCreate, sectionEdit.startEdit]);

  useEffect(() => {
    if (!recurso || editingRecurso) return;
    const next = recursoFormFromEntity(recurso);
    setForm(next);
    setFormBaseline(next);
  }, [recurso, editingRecurso]);

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
    setForm(formBaseline);
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
    const loader = (
      <LoadingActivityCard
        title="Carregando detalhe do recurso"
        description="Buscando cadastro, custos e processos vinculados."
      />
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  if (!isCreate && !recurso && !loading) {
    const errorView = (
      <InlineErrorState
        title={error ? "Não foi possível carregar o recurso" : "Recurso não encontrado"}
        message={
          error ??
          "Este recurso pode ter sido excluído ou você não tem acesso."
        }
        actionLabel="Voltar à lista"
        onAction={onBack}
      />
    );
    if (embedded) return errorView;
    return <TransformometroShell>{errorView}</TransformometroShell>;
  }

  const title = isCreate
    ? "Novo recurso"
    : `${recurso?.codigo_recurso ?? ""} — ${recurso?.nome_recurso ?? ""}`;

  const showSection = (sectionId: RecursoWorkspaceSectionId) =>
    !embedded || isCreate || activeSection === sectionId;

  const pageBody = (
    <>
      {embedded ? (
        <div className="tm-cadastro-detail-toolbar">
          <div>
            <h2 className="ds-section-title">{title}</h2>
            <p className="ds-hint">
              {isCreate
                ? "Cadastre licenças e ferramentas compartilhadas do catálogo global"
                : "Detalhes, histórico de custos e processos vinculados"}
            </p>
          </div>
          {!isCreate ? (
            <button type="button" className={DS_GHOST_BTN} onClick={() => void handleDeleteRecurso()}>
              <Trash2 size={16} />
              Excluir
            </button>
          ) : null}
        </div>
      ) : null}

      <StatusAlerts
        error={error}
        loading={loading}
        hasData={Boolean(recurso) || isCreate}
        onDismissError={() => setError(null)}
        onRetry={() => {
          setError(null);
          void load();
        }}
      />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      <div className={`ds-cadastro-panel ds-cadastro-panel--cards${embedded ? " ds-cadastro-panel--workspace" : ""}`}>
        {options && showSection("identificacao") ? (
          <RecursoWorkspaceSectionPanel
            active={!embedded || isCreate || activeSection === "identificacao"}
            sectionId="identificacao"
          >
            <EditableSectionCard
              title="Dados do recurso"
              description="Cadastro principal — rateio, escopo e vigência."
              isEditing={isCreate || sectionEdit.isEditing("recurso")}
              onEdit={() => void sectionEdit.startEdit("recurso")}
              onCancel={cancelRecursoEdit}
              onSave={() => void handleSaveRecurso()}
              saving={saving}
              dirty={!valuesEqual(form, formBaseline)}
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
          </RecursoWorkspaceSectionPanel>
        ) : null}

        {!isCreate && showSection("custos") ? (
          <RecursoWorkspaceSectionPanel active={!embedded || activeSection === "custos"} sectionId="custos">
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
          </RecursoWorkspaceSectionPanel>
        ) : null}

        {!isCreate && showSection("vinculos") ? (
          <RecursoWorkspaceSectionPanel active={!embedded || activeSection === "vinculos"} sectionId="vinculos">
            <section className={sectionCn.section} aria-busy={loading || refreshing}>
              <div className={sectionCn.header}>
                <h2 className={sectionCn.title}>Processos vinculados</h2>
                <div className={sectionCn.metaGroup}>
                  <span className={sectionCn.meta}>
                    Vínculos ativos entram no rateio das revisões
                  </span>
                  <span className={sectionCn.meta}>{filteredVinculos.length} registro(s)</span>
                </div>
              </div>

              <div className={sectionCn.toolbar}>
                <div className={sectionCn.search} role="search">
                  <Search size={16} aria-hidden="true" className={sectionCn.searchIcon} />
                  <NativeTextControl
                    type="search"
                    className={sectionCn.searchInput}
                    value={search}
                    placeholder="Código, processo, unidade, departamento…"
                    onChange={setSearch}
                    aria-label="Filtrar processos vinculados"
                  />
                </div>
              </div>

              {filteredVinculos.length === 0 ? (
                <p className={EMPTY_STATE_CLASS}>Nenhum processo vinculado a este recurso.</p>
              ) : (
                <div className={`${tableCn.wrap} ds-cadastro-section__table`}>
                  <table className={tableCn.compactTable}>
                    <thead>
                      <tr>
                        <th className={tableCn.colWide}>
                          <TableHeader label="Processo" hint={C.processo} />
                        </th>
                        <th><TableHeader label="Unidade" hint={C.unidade} /></th>
                        <th><TableHeader label="Departamento" hint={C.setor} /></th>
                        <th><TableHeader label="Revisão" hint={C.revisao} /></th>
                        <th><TableHeader label="Uso no processo" hint={C.usoRevisao} /></th>
                        <th className={tableCn.colNumeric}>
                          <TableHeader label="Peso" hint={C.peso} />
                        </th>
                        <th><TableHeader label="Ativo" hint={C.ativoVinculo} /></th>
                        <th className={tableCn.colActions}>
                          <TableHeader label="Ações" hint={C.acoes} />
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredVinculos.map((row) =>
                        editingVinculoId === row.vinculo_id && editVinculoForm ? (
                          <tr key={row.vinculo_id} className={tableCn.rowEditing}>
                            <td colSpan={8}>
                              <form className="ds-cadastro-subsection" onSubmit={saveEditVinculo}>
                                <h4 className="ds-cadastro-subsection__title">
                                  Editar vínculo — {row.codigo_processo ?? "—"} · {row.nome_processo ?? "—"}
                                </h4>
                                <div className={DS_FILTERS_ROW}>
                                  <label className={DS_FILTER_BOX_PLAIN}>
                                    <FieldLabel className="tm-field__label" label="Início do uso" hint={R.vinculoInicio} />
                                    <NativeTextControl
                                      type="date"
                                      value={editVinculoForm.data_inicio_uso}
                                      onChange={(data_inicio_uso) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          data_inicio_uso,
                                        })
                                      }
                                    />
                                  </label>
                                  <label className={DS_FILTER_BOX_PLAIN}>
                                    <FieldLabel className="tm-field__label" label="Fim do uso" hint={R.vinculoFim} />
                                    <NativeTextControl
                                      type="date"
                                      value={editVinculoForm.data_fim_uso}
                                      onChange={(data_fim_uso) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          data_fim_uso,
                                        })
                                      }
                                    />
                                  </label>
                                  <label className={DS_FILTER_BOX_PLAIN}>
                                    <FieldLabel className="tm-field__label" label="Peso do rateio" hint={R.peso} />
                                    <NativeTextControl
                                      type="number"
                                      min={0}
                                      step="any"
                                      value={editVinculoForm.peso_rateio}
                                      onChange={(peso_rateio) =>
                                        setEditVinculoForm({
                                          ...editVinculoForm,
                                          peso_rateio,
                                        })
                                      }
                                    />
                                  </label>
                                  <NativeCheckboxControl
                                    className="ds-check-label"
                                    checked={editVinculoForm.ativo}
                                    onChange={(ativo) => setEditVinculoForm({ ...editVinculoForm, ativo })}
                                    label={<span className="tm-field__label">Vínculo ativo <HelpTooltip content={R.vinculoAtivo} ariaLabel="Ajuda: Vínculo ativo" /></span>}
                                  />
                                </div>
                                <label className={DS_FILTER_BOX_WIDE}>
                                  <FieldLabel className="tm-field__label" label="Observações" hint={R.vinculoObservacoes} />
                                  <NativeTextControl
                                    value={editVinculoForm.observacoes}
                                    onChange={(observacoes) =>
                                      setEditVinculoForm({
                                        ...editVinculoForm,
                                        observacoes,
                                      })
                                    }
                                  />
                                </label>
                                <div className="ds-cadastro-form__actions">
                                  <button type="submit" className="ds-primary-btn">
                                    Salvar vínculo
                                  </button>
                                  <button type="button" className={DS_GHOST_BTN} onClick={cancelEditVinculo}>
                                    Cancelar
                                  </button>
                                </div>
                              </form>
                            </td>
                          </tr>
                        ) : (
                          <tr key={row.vinculo_id}>
                            <td className={tableCn.colWide}>
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
                              {row.versao_revisao ?? "—"} · {cenarioLabel(row.cenario_tipo)}
                            </td>
                            <td>
                              {toDateInputValue(row.data_inicio_uso) || "…"} →{" "}
                              {toDateInputValue(row.data_fim_uso) || "…"}
                            </td>
                            <td className={tableCn.colNumeric}>{row.peso_rateio ?? "—"}</td>
                            <td>{row.ativo ? "Sim" : "Não"}</td>
                            <td className={tableCn.colActions}>
                              <TableRowActions>
                                <button
                                  type="button"
                                  className={DS_GHOST_BTN}
                                  onClick={() => startEditVinculo(row)}
                                >
                                  Editar
                                </button>
                                <button
                                  type="button"
                                  className={DS_GHOST_BTN}
                                  onClick={() => void handleDeleteVinculo(row)}
                                >
                                  Desvincular
                                </button>
                              </TableRowActions>
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </RecursoWorkspaceSectionPanel>
        ) : null}
      </div>
    </>
  );

  if (embedded) return pageBody;

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
            <button type="button" className={DS_GHOST_BTN} onClick={onBack}>
              <ArrowLeft size={16} />
              Lista
            </button>
            {!isCreate ? (
              <button type="button" className={DS_GHOST_BTN} onClick={() => void handleDeleteRecurso()}>
                <Trash2 size={16} />
                Excluir
              </button>
            ) : null}
          </>
        }
      />
      {pageBody}
    </TransformometroShell>
  );
}
