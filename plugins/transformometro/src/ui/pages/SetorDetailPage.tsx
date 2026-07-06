import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { SetorReadView } from "../../components/setor/SetorReadView";
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
  createSetor,
  deleteSetor,
  fetchOptions,
  fetchSetores,
  updateSetor,
  type OptionsData,
  type Setor,
} from "../../data/api/transformometroApi";
import { buildSetorPath } from "../../utils/routeParser";
import { SetorFormFields } from "../setores/SetorFormFields";
import {
  emptySetorForm,
  payloadFromSetorForm,
  setorFormFromEntity,
  type SetorFormState,
} from "../setores/setorCatalogForm";

type Props = Pick<AppProps, "getAccessToken"> & {
  setorId: string;
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

export function SetorDetailPage({
  getAccessToken,
  setorId,
  pathname,
  onNavigate,
  onBack,
}: Props) {
  const confirm = useConfirm();
  const isCreate = isCatalogCreateId("setor", setorId);
  const [setor, setSetor] = useState<Setor | null>(null);
  const [options, setOptions] = useState<OptionsData | null>(null);
  const [form, setForm] = useState<SetorFormState>(() => emptySetorForm());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!isCreate);
  const [saving, setSaving] = useState(false);

  const filialLabels = useMemo(
    () => new Map((options?.filiais ?? []).map((filial) => [filial.id, filial.label])),
    [options?.filiais]
  );

  const load = useCallback(async () => {
    if (isCreate) {
      const opts = await fetchOptions(getAccessToken);
      setOptions(opts);
      setForm(emptySetorForm());
      setLoading(false);
      return;
    }

    setError(null);
    try {
      const [list, opts] = await Promise.all([
        fetchSetores(getAccessToken),
        fetchOptions(getAccessToken),
      ]);
      const row = list.items.find((item) => item.setor_id === setorId) ?? null;
      setSetor(row);
      setOptions(opts);
      if (row) setForm(setorFormFromEntity(row));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar departamento");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, isCreate, setorId]);

  const sectionEdit = useCollaborativeSectionEdit({
    entityType: "setor",
    entityId: setorId,
    getAccessToken,
    enabled: !isCreate,
    onResync: () => void load(),
  });

  useEffect(() => {
    void load();
  }, [load]);

  const editingSetor = sectionEdit.isEditing("setor");

  useEffect(() => {
    if (isCreate) {
      sectionEdit.startEdit("setor");
    }
  }, [isCreate, sectionEdit.startEdit]);

  useEffect(() => {
    if (!setor || editingSetor) return;
    setForm(setorFormFromEntity(setor));
  }, [setor, editingSetor]);

  async function handleSave() {
    if (form.filiais.length === 0) {
      setError("Selecione ao menos uma unidade para o departamento.");
      return;
    }
    setSaving(true);
    setError(null);
    const payload = payloadFromSetorForm(form, !isCreate);
    try {
      if (isCreate) {
        const created = await createSetor(
          {
            setor_id: form.codigo_setor.trim(),
            nome_setor: payload.nome_setor,
            filiais: payload.filiais,
            status_setor: payload.status_setor,
          },
          getAccessToken
        );
        onNavigate(buildSetorPath(created.setor_id));
        return;
      }
      const updated = await updateSetor(setorId, payload, getAccessToken);
      setSetor(updated);
      sectionEdit.stopEdit("setor");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar departamento");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!setor) return;
    const label = `${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor}`;
    const confirmed = await confirm({
      title: "Excluir departamento",
      message: `Excluir departamento ${label}?`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) return;
    setError(null);
    try {
      await deleteSetor(setor.setor_id, getAccessToken);
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir departamento");
    }
  }

  function cancelEdit() {
    if (isCreate) {
      onBack();
      return;
    }
    if (setor) setForm(setorFormFromEntity(setor));
    sectionEdit.cancelEdit("setor");
  }

  const fetchProgress = useTrackedSingleFetchProgress(loading && !isCreate && !setor);
  const loadingProgress = useLoadingProgress(loading && !isCreate && !setor, fetchProgress);

  if (loading && !isCreate && !setor) {
    return (
      <TransformometroShell>
        <LoadingActivityCard
          title="Carregando departamento"
          description="Dados do departamento e unidades vinculadas."
          progressPercent={loadingProgress}
        />
      </TransformometroShell>
    );
  }

  if (!isCreate && !setor && !loading) {
    return (
      <TransformometroShell>
        <div className="ds-state ds-state--error" role="alert">
          <p>{error ?? "Departamento não encontrado."}</p>
          <button type="button" className="ds-ghost-btn" onClick={onBack}>
            Voltar à lista
          </button>
        </div>
      </TransformometroShell>
    );
  }

  const title = isCreate
    ? "Novo departamento"
    : `${setor?.codigo_setor ?? setorId} — ${setor?.nome_setor ?? ""}`;

  return (
    <TransformometroShell>
      <PageHeader
        title={title}
        subtitle={
          isCreate
            ? "Cadastre departamento e vínculo com unidades"
            : `Status: ${setor?.status_setor ?? "ativo"}`
        }
        currentPath={pathname ?? (isCreate ? buildSetorPath(CATALOG_CREATE.setor) : buildSetorPath(setorId))}
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

      <StatusAlerts error={error} loading={false} hasData onRetry={() => void load()} />

      <CollaborativePresenceBanner
        presence={sectionEdit.presence}
        lockError={sectionEdit.lockError}
        realtimeNotice={sectionEdit.realtimeNotice}
        onDismissRealtimeNotice={sectionEdit.clearRealtimeNotice}
      />

      {options ? (
        <EditableSectionCard
          title="Dados do departamento"
          hint={TM_HELP_TOOLTIPS.setores.nome}
          description="Código, nome, status e unidades onde o departamento aparece nos processos."
          isEditing={isCreate || sectionEdit.isEditing("setor")}
          onEdit={() => void sectionEdit.startEdit("setor")}
          onCancel={cancelEdit}
          onSave={() => void handleSave()}
          saving={saving}
          editable={!isCreate}
          readContent={
            setor ? <SetorReadView setor={setor} filialLabels={filialLabels} /> : null
          }
          editContent={
            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleSave();
              }}
            >
              <SetorFormFields
                form={form}
                options={options}
                editing={!isCreate}
                onChange={setForm}
              />
            </form>
          }
        />
      ) : null}
    </TransformometroShell>
  );
}
