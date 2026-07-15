import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { FilialReadView } from "../../components/filial/FilialReadView";
import { EditableSectionCard } from "../../components/ui/EditableSectionCard";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { LoadingActivityCard } from "../../components/LoadingActivityCard";
import {
  useLoadingProgress,
  useTrackedSingleFetchProgress,
} from "../../hooks/useSimulatedLoadingProgress";
import { useCollaborativeSectionEdit } from "../../hooks/useCollaborativeSectionEdit";
import { CollaborativePresenceBanner } from "../../components/collaboration/CollaborativePresenceBanner";
import { PageHeader } from "../../components/PageHeader";
import { StatusAlerts } from "../../components/StatusAlerts";
import { TransformometroShell } from "../../components/TransformometroShell";
import { CATALOG_CREATE, isCatalogCreateId } from "../../constants/catalogRoutes";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  createFilial,
  deleteFilial,
  fetchFilial,
  fetchOptions,
  updateFilial,
  type Filial,
  type OptionsData,
} from "../../data/api/transformometroApi";
import { buildFilialPath } from "../../utils/routeParser";
import { FilialFormFields } from "../filiais/FilialFormFields";
import {
  emptyFilialForm,
  filialFormFromEntity,
  payloadFromFilialForm,
  type FilialFormState,
} from "../filiais/filialCatalogForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  filialId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
  embedded?: boolean;
};

export function FilialDetailPage({
  getAccessToken,
  filialId,
  pathname,
  onNavigate,
  onBack,
  embedded = false,
}: Props) {
  const confirm = useConfirm();
  const isCreate = isCatalogCreateId("filial", filialId);
  const [filial, setFilial] = useState<Filial | null>(null);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [form, setForm] = useState<FilialFormState>(() => emptyFilialForm());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isCreate);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    if (isCreate) {
      const opts = await fetchOptions(getAccessToken);
      setOptions(opts);
      setForm(emptyFilialForm());
      setLoading(false);
      return;
    }

    setError(null);
    try {
      const [row, opts] = await Promise.all([
        fetchFilial(filialId, getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      setFilial(row);
      setOptions(opts);
      setForm(filialFormFromEntity(row));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar unidade");
    } finally {
      setLoading(false);
    }
  }, [filialId, getAccessToken, isCreate]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "filial",
    entityId: filialId,
    getAccessToken,
    enabled: !isCreate,
    onResync: () => void load(),
  });

  useEffect(() => {
    void load();
  }, [load]);

  const editingFilial = sectionEdit.isEditing("filial");

  useEffect(() => {
    if (isCreate) {
      sectionEdit.startEdit("filial");
    }
  }, [isCreate, sectionEdit.startEdit]);

  useEffect(() => {
    if (!filial || editingFilial) return;
    setForm(filialFormFromEntity(filial));
  }, [filial, editingFilial]);

  async function handleSave() {
    setSaving(true);
    setError(null);
    const payload = payloadFromFilialForm(form, !isCreate);
    try {
      if (isCreate) {
        const created = await createFilial(
          {
            codigo_filial: form.codigo_filial.trim(),
            nome_filial: payload.nome_filial,
            status_filial: payload.status_filial,
          },
          getAccessToken
        );
        onNavigate(buildFilialPath(created.filial_id));
        return;
      }
      const updated = await updateFilial(filialId, payload, getAccessToken);
      setFilial(updated);
      sectionEdit.stopEdit("filial");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar unidade");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!filial) return;
    const label = `${filial.codigo_filial ?? filial.filial_id} — ${filial.nome_filial}`;
    const confirmed = await confirm({
      title: "Excluir unidade",
      message: `Excluir unidade ${label}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteFilial(filial.filial_id, getAccessToken);
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir unidade");
    }
  }

  function cancelEdit() {
    if (isCreate) {
      onBack();
      return;
    }
    if (filial) setForm(filialFormFromEntity(filial));
    sectionEdit.cancelEdit("filial");
  }

  const fetchProgress = useTrackedSingleFetchProgress(loading && !isCreate && !filial);
  const loadingProgress = useLoadingProgress(loading && !isCreate && !filial, fetchProgress);

  if (loading && !isCreate && !filial) {
    const loader = (
      <LoadingActivityCard
        title="Carregando unidade"
        description="Dados da unidade operacional."
        progressPercent={loadingProgress}
      />
    );
    if (embedded) return loader;
    return <TransformometroShell>{loader}</TransformometroShell>;
  }

  if (!isCreate && !filial && !loading) {
    const errorView = (
      <div className="ds-state ds-state--error" role="alert">
        <p>{error ?? "Unidade não encontrada."}</p>
        <button type="button" className="ds-ghost-btn" onClick={onBack}>
          Voltar à lista
        </button>
      </div>
    );
    if (embedded) return errorView;
    return <TransformometroShell>{errorView}</TransformometroShell>;
  }

  const title = isCreate
    ? "Nova unidade"
    : `${filial?.codigo_filial ?? filialId} — ${filial?.nome_filial ?? ""}`;

  const pageBody = (
    <>
      {!embedded ? null : (
        <div className="tm-cadastro-detail-toolbar">
          <div>
            <h2 className="ds-section-title">{title}</h2>
            {!isCreate ? (
              <p className="ds-hint">Status: {filial?.status_filial ?? "ativo"}</p>
            ) : (
              <p className="ds-hint">Cadastre uma unidade para instâncias, departamentos e escopo do dashboard</p>
            )}
          </div>
          {!isCreate ? (
            <button type="button" className="ds-ghost-btn" onClick={() => void handleDelete()}>
              <Trash2 size={16} />
              Excluir
            </button>
          ) : null}
        </div>
      )}

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      {options ? (
        <EditableSectionCard
          title="Dados da unidade"
          hint={TM_HELP_TOOLTIPS.filiais.nome}
          description="Código TOTVS, nome e status usados em departamentos e processos."
          isEditing={isCreate || sectionEdit.isEditing("filial")}
          onEdit={() => void sectionEdit.startEdit("filial")}
          onCancel={cancelEdit}
          onSave={() => void handleSave()}
          saving={saving}
          editable={!isCreate}
          readContent={filial ? <FilialReadView filial={filial} /> : null}
          editContent={
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleSave();
              }}
            >
              <FilialFormFields
                form={form}
                options={options}
                editing={!isCreate}
                onChange={setForm}
              />
            </form>
          }
        />
      ) : null}
    </>
  );

  if (embedded) return pageBody;

  return (
    <TransformometroShell>
      <PageHeader
        title={title}
        subtitle={
          isCreate
            ? "Cadastre uma unidade para instâncias, departamentos e escopo do dashboard"
            : `Status: ${filial?.status_filial ?? "ativo"}`
        }
        currentPath={pathname ?? (isCreate ? buildFilialPath(CATALOG_CREATE.filial) : buildFilialPath(filialId))}
        onNavigate={onNavigate}
        actions={
          <>
            <button type="button" className="ds-ghost-btn" onClick={onBack}>
              <ArrowLeft size={16} />
              Lista
            </button>
            {!isCreate ? (
              <button type="button" className="ds-ghost-btn" onClick={() => void handleDelete()}>
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
