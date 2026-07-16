import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  BackLink,
  ConfirmModalPanel,
  DataTable,
  FieldLabel,
  FormSelectControl,
  ModalShell,
  NativeTextControl,
  StatusBadge,
  UserDirectoryPicker,
  type DataTableColumn,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";
import { Pencil, Plus, RefreshCw, UserMinus, Users } from "lucide-react";

import {
  createCipaMember,
  endCipaMember,
  listCipaMembers,
  searchDirectoryUsers,
  updateCipaMember,
  type CipaMember,
} from "../api/cipaApi";
import { MEMBER_ROLE_LABELS, MEMBER_ROLE_OPTIONS, UNIT_LABELS } from "../constants/labels";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import type { CipaUnitCode } from "../security/cipaAccess";
import {
  CipaContentCard,
  CipaFormActions,
  CipaLoadingState,
  CipaPageHeader,
  CipaSectionCard,
  CipaStateBanner,
  CipaStateBox,
} from "../ui/cipaUi";
import {
  cipaDataTableClassNames,
  cipaDataTableLabels,
  cipaStatusBadgeClassNames,
} from "../ui/cipaUiContracts";

type Props = {
  unitCode: CipaUnitCode;
};

type FormState = {
  user: DirectoryUserOption | null;
  role: string;
  mandate_start: string;
  mandate_end: string;
};

const EMPTY_FORM: FormState = {
  user: null,
  role: "titular_member",
  mandate_start: new Date().toISOString().slice(0, 10),
  mandate_end: "",
};

const MODAL_CLASSES = {
  overlay: "delpi-ui-modal-overlay",
  dialog: "delpi-ui-modal delpi-ui-modal--sm",
  header: "delpi-ui-modal__header",
  title: "delpi-ui-modal__title",
  closeButton: "delpi-ui-modal__close",
  body: "delpi-ui-modal__body",
  footer: "delpi-ui-modal__footer",
};

const CONFIRM_CLASSES = {
  message: "cipa-confirm-modal__message",
  actions: "cipa-form-actions cipa-form-actions--end",
  cancelButton: "delpi-ui-action-btn delpi-ui-action-btn--ghost",
  confirmButton: "delpi-ui-action-btn delpi-ui-action-btn--primary",
  confirmButtonDanger: "delpi-ui-action-btn cipa-action-btn--danger",
};

function formatMandate(member: CipaMember): string {
  const start = member.mandate_start || "—";
  const end = member.mandate_end || "em aberto";
  return `${start} → ${end}`;
}

export function CipaMembersPage({ unitCode }: Props) {
  const [members, setMembers] = useState<CipaMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editing, setEditing] = useState<CipaMember | null>(null);
  const [ending, setEnding] = useState<CipaMember | null>(null);

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    listCipaMembers(unitCode, { includeInactive: true, signal: controller.signal })
      .then((items) => {
        setMembers(items);
        setError(null);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Erro ao listar membros.");
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  };

  useEffect(() => load(), [unitCode]);

  const activeMembers = useMemo(
    () => members.filter((item) => item.is_active && !item.deleted_at),
    [members],
  );
  const historicalMembers = useMemo(
    () => members.filter((item) => !item.is_active || item.deleted_at),
    [members],
  );

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditing(null);
  }

  function startEdit(member: CipaMember) {
    setEditing(member);
    setForm({
      user: {
        id: member.user_id,
        name: member.display_name,
        email: "",
      },
      role: member.role,
      mandate_start: member.mandate_start?.slice(0, 10) || "",
      mandate_end: member.mandate_end?.slice(0, 10) || "",
    });
    setSuccess(null);
    setError(null);
  }

  async function handleSave() {
    if (!form.user?.id && !editing) {
      setError("Selecione um usuário do diretório.");
      return;
    }
    if (!form.mandate_start) {
      setError("Informe o início do mandato.");
      return;
    }
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      if (editing) {
        await updateCipaMember(editing.id, {
          display_name: form.user?.name || editing.display_name,
          role: form.role,
          mandate_start: form.mandate_start,
          mandate_end: form.mandate_end || null,
          is_active: true,
        });
        setSuccess("Membro atualizado.");
      } else {
        await createCipaMember({
          unit_code: unitCode,
          user_id: form.user!.id,
          display_name: form.user!.name || form.user!.email,
          role: form.role,
          mandate_start: form.mandate_start,
          mandate_end: form.mandate_end || null,
        });
        setSuccess("Membro cadastrado.");
      }
      resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar membro.");
    } finally {
      setSaving(false);
    }
  }

  async function confirmEnd() {
    if (!ending) return;
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      await endCipaMember(ending.id);
      setSuccess(`Participação de ${ending.display_name} encerrada.`);
      setEnding(null);
      if (editing?.id === ending.id) resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao encerrar participação.");
    } finally {
      setSaving(false);
    }
  }

  const columns = useMemo<DataTableColumn<CipaMember>[]>(
    () => [
      {
        key: "display_name",
        header: "Nome",
        mobileLabel: "Nome",
        render: (item) => item.display_name,
      },
      {
        key: "role",
        header: "Cargo",
        mobileLabel: "Cargo",
        render: (item) => MEMBER_ROLE_LABELS[item.role] || item.role,
      },
      {
        key: "mandate",
        header: "Mandato",
        mobileLabel: "Mandato",
        render: (item) => formatMandate(item),
      },
      {
        key: "status",
        header: "Status",
        mobileLabel: "Status",
        render: (item) => (
          <StatusBadge
            classNames={cipaStatusBadgeClassNames}
            label={item.is_active ? "Ativo" : "Encerrado"}
            variant={item.is_active ? "success" : "neutral"}
          />
        ),
      },
      {
        key: "actions",
        header: "Ações",
        mobileLabel: "Ações",
        render: (item) => (
          <div className="cipa-members-actions">
            <ActionButton variant="ghost" onClick={() => startEdit(item)}>
              <Pencil size={14} /> Editar
            </ActionButton>
            {item.is_active ? (
              <ActionButton variant="ghost" onClick={() => setEnding(item)}>
                <UserMinus size={14} /> Encerrar
              </ActionButton>
            ) : null}
          </div>
        ),
      },
    ],
    [],
  );

  return (
    <div className="cipa-page-stack">
      <CipaPageHeader
        nav={
          <BackLink onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}`)}>
            Atas da unidade
          </BackLink>
        }
        title={`Membros e cargos — ${UNIT_LABELS[unitCode]}`}
        subtitle="Cadastro permanente da composição da CIPA. Novas atas pré-carregam a composição vigente na data da reunião."
        actions={
          <ActionButton variant="ghost" onClick={() => load()}>
            <RefreshCw size={16} /> Atualizar
          </ActionButton>
        }
      />

      {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}
      {success ? <CipaStateBanner>{success}</CipaStateBanner> : null}

      <CipaSectionCard
        title={editing ? "Editar membro" : "Incluir membro"}
        className="cipa-compose__section"
      >
        <div className="cipa-compose__panel">
          {editing ? (
            <p className="cipa-compose__hint">
              Editando <strong>{editing.display_name}</strong>. Alterações não mudam atas já
              gravadas (snapshot histórico).
            </p>
          ) : (
            <UserDirectoryPicker
              value={form.user ? [form.user] : []}
              onChange={(users) => {
                const selected = users[users.length - 1] ?? null;
                setForm((prev) => ({
                  ...prev,
                  user: selected,
                }));
              }}
              searchUsers={searchDirectoryUsers}
              showSelectedList
              labels={{
                title: "Usuário do diretório",
                hint: "Busque pelo nome ou e-mail. Apenas um usuário por inclusão.",
              }}
            />
          )}

          <div className="cipa-compose__meta-fields">
            <div className="cipa-field cipa-field--grow">
              <FieldLabel label="Cargo" htmlFor="cipa-member-role" />
              <FormSelectControl
                id="cipa-member-role"
                value={form.role}
                onChange={(role) => setForm((prev) => ({ ...prev, role }))}
                options={MEMBER_ROLE_OPTIONS}
                portalScopeClassName="dashboard-cipa"
                ariaLabel="Cargo na CIPA"
              />
            </div>
            <div className="cipa-field">
              <FieldLabel label="Início do mandato" htmlFor="cipa-member-start" />
              <NativeTextControl
                id="cipa-member-start"
                type="date"
                value={form.mandate_start}
                onChange={(mandate_start) => setForm((prev) => ({ ...prev, mandate_start }))}
              />
            </div>
            <div className="cipa-field">
              <FieldLabel label="Fim do mandato" htmlFor="cipa-member-end" />
              <NativeTextControl
                id="cipa-member-end"
                type="date"
                value={form.mandate_end}
                onChange={(mandate_end) => setForm((prev) => ({ ...prev, mandate_end }))}
              />
            </div>
          </div>

          <CipaFormActions>
            {editing ? (
              <ActionButton variant="ghost" onClick={() => resetForm()} disabled={saving}>
                Cancelar edição
              </ActionButton>
            ) : null}
            <ActionButton variant="primary" onClick={() => void handleSave()} disabled={saving}>
              <Plus size={16} /> {editing ? "Salvar alterações" : "Adicionar membro"}
            </ActionButton>
          </CipaFormActions>
        </div>
      </CipaSectionCard>

      <CipaContentCard title="Composição ativa">
        {loading ? (
          <CipaLoadingState />
        ) : activeMembers.length === 0 ? (
          <CipaStateBox
            variant="empty"
            title="Nenhum membro ativo"
            message="Cadastre a composição da CIPA para pré-carregar participantes nas novas atas."
          />
        ) : (
          <DataTable
            columns={columns}
            rows={activeMembers}
            rowKey={(item) => item.id}
            layout="embedded"
            classNames={cipaDataTableClassNames}
            labels={cipaDataTableLabels}
          />
        )}
      </CipaContentCard>

      <CipaSectionCard title="Histórico">
        {loading ? null : historicalMembers.length === 0 ? (
          <CipaStateBanner>
            <Users size={16} /> Ainda não há mandatos encerrados nesta filial.
          </CipaStateBanner>
        ) : (
          <DataTable
            columns={columns}
            rows={historicalMembers}
            rowKey={(item) => item.id}
            layout="embedded"
            classNames={cipaDataTableClassNames}
            labels={cipaDataTableLabels}
          />
        )}
      </CipaSectionCard>

      <ModalShell
        open={Boolean(ending)}
        title="Encerrar participação"
        onClose={() => {
          if (!saving) setEnding(null);
        }}
        classNames={MODAL_CLASSES}
        portalScopeClassName="dashboard-cipa"
      >
        <ConfirmModalPanel
          message={
            ending
              ? `Encerrar o mandato ativo de ${ending.display_name}? O histórico será preservado.`
              : ""
          }
          confirmLabel="Encerrar"
          cancelLabel="Cancelar"
          confirmBusy={saving}
          variant="danger"
          onConfirm={() => void confirmEnd()}
          onCancel={() => setEnding(null)}
          classNames={CONFIRM_CLASSES}
        />
      </ModalShell>
    </div>
  );
}
