import { useEffect, useMemo, useState } from "react";
import {
  ActionButton,
  DataTable,
  FieldLabel,
  FormSelectControl,
  NativeTextControl,
  StatusBadge,
  UserDirectoryPicker,
  type DataTableColumn,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";
import { Pencil, Plus, UserMinus, Users } from "lucide-react";

import {
  createComiteEticaMember,
  endComiteEticaMember,
  listComiteEticaMembers,
  searchDirectoryUsers,
  updateComiteEticaMember,
  type ComiteEticaMember,
} from "../api/cecApi";
import { MEMBER_ROLE_LABELS, MEMBER_ROLE_OPTIONS } from "../constants/labels";
import type { ComiteEticaUnitCode } from "../security/cecAccess";
import {
  ComiteEticaContentCard,
  ComiteEticaFormActions,
  ComiteEticaLoadingState,
  ComiteEticaPageNotices,
  ComiteEticaSectionCard,
  ComiteEticaStateBanner,
  ComiteEticaStateBox,
} from "../ui/cecUi";
import {
  cecDataTableClassNames,
  cecDataTableLabels,
  cecStatusBadgeClassNames,
} from "../ui/cecUiContracts";
import { CecConfirmModal } from "../ui/CecConfirmModal";

type Props = {
  unitCode: ComiteEticaUnitCode;
  refreshToken?: number;
};

type FormState = {
  user: DirectoryUserOption | null;
  role: string;
  mandate_start: string;
  mandate_end: string;
};

const EMPTY_FORM: FormState = {
  user: null,
  role: "member",
  mandate_start: new Date().toISOString().slice(0, 10),
  mandate_end: "",
};

function formatMandate(member: ComiteEticaMember): string {
  const start = member.mandate_start || "—";
  const end = member.mandate_end || "em aberto";
  return `${start} → ${end}`;
}

export function CecMembersPage({ unitCode, refreshToken = 0 }: Props) {
  const [members, setMembers] = useState<ComiteEticaMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [editing, setEditing] = useState<ComiteEticaMember | null>(null);
  const [ending, setEnding] = useState<ComiteEticaMember | null>(null);

  const load = () => {
    const controller = new AbortController();
    setLoading(true);
    listComiteEticaMembers(unitCode, { includeInactive: true, signal: controller.signal })
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

  useEffect(() => load(), [unitCode, refreshToken]);

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

  function startEdit(member: ComiteEticaMember) {
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
        await updateComiteEticaMember(editing.id, {
          display_name: form.user?.name || editing.display_name,
          role: form.role,
          mandate_start: form.mandate_start,
          mandate_end: form.mandate_end || null,
          is_active: true,
        });
        setSuccess("Membro atualizado.");
      } else {
        await createComiteEticaMember({
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
      await endComiteEticaMember(ending.id);
      setSuccess(`Particomite-etica-condutação de ${ending.display_name} encerrada.`);
      setEnding(null);
      if (editing?.id === ending.id) resetForm();
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao encerrar participação.");
    } finally {
      setSaving(false);
    }
  }

  const columns = useMemo<DataTableColumn<ComiteEticaMember>[]>(
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
            classNames={cecStatusBadgeClassNames}
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
          <div className="cec-members-actions">
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
    <div className="cec-page-stack">
      <ComiteEticaPageNotices
        error={error}
        success={success}
        onDismissError={() => setError(null)}
        onDismissSuccess={() => setSuccess(null)}
      />

      <ComiteEticaSectionCard
        title={editing ? "Editar membro" : "Incluir membro"}
        className="cec-compose__section"
      >
        <div className="cec-compose__panel">
          {editing ? (
            <p className="cec-compose__hint">
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

          <div className="cec-compose__meta-fields">
            <div className="cec-field comite-etica-conduta-field--grow">
              <FieldLabel label="Cargo" htmlFor="comite-etica-conduta-member-role" />
              <FormSelectControl
                id="comite-etica-conduta-member-role"
                value={form.role}
                onChange={(role) => setForm((prev) => ({ ...prev, role }))}
                options={MEMBER_ROLE_OPTIONS}
                portalScopeClassName="dashboard-comite-etica-conduta"
                ariaLabel="Cargo no Comitê de Ética"
              />
            </div>
            <div className="cec-field">
              <FieldLabel label="Início do mandato" htmlFor="comite-etica-conduta-member-start" />
              <NativeTextControl
                id="comite-etica-conduta-member-start"
                type="date"
                value={form.mandate_start}
                onChange={(mandate_start) => setForm((prev) => ({ ...prev, mandate_start }))}
              />
            </div>
            <div className="cec-field">
              <FieldLabel label="Fim do mandato" htmlFor="comite-etica-conduta-member-end" />
              <NativeTextControl
                id="comite-etica-conduta-member-end"
                type="date"
                value={form.mandate_end}
                onChange={(mandate_end) => setForm((prev) => ({ ...prev, mandate_end }))}
              />
            </div>
          </div>

          <ComiteEticaFormActions>
            {editing ? (
              <ActionButton variant="ghost" onClick={() => resetForm()} disabled={saving}>
                Cancelar edição
              </ActionButton>
            ) : null}
            <ActionButton variant="primary" onClick={() => void handleSave()} disabled={saving}>
              <Plus size={16} /> {editing ? "Salvar alterações" : "Adicionar membro"}
            </ActionButton>
          </ComiteEticaFormActions>
        </div>
      </ComiteEticaSectionCard>

      <ComiteEticaContentCard title="Composição ativa">
        {loading ? (
          <ComiteEticaLoadingState />
        ) : activeMembers.length === 0 ? (
          <ComiteEticaStateBox
            variant="empty"
            title="Nenhum membro ativo"
            message="Cadastre a composição do Comitê de Ética para pré-carregar participantes nas novas atas."
          />
        ) : (
          <DataTable
            columns={columns}
            rows={activeMembers}
            rowKey={(item) => item.id}
            layout="embedded"
            classNames={cecDataTableClassNames}
            labels={cecDataTableLabels}
          />
        )}
      </ComiteEticaContentCard>

      <ComiteEticaSectionCard title="Histórico">
        {loading ? null : historicalMembers.length === 0 ? (
          <ComiteEticaStateBanner>
            <Users size={16} /> Ainda não há mandatos encerrados no comitê.
          </ComiteEticaStateBanner>
        ) : (
          <DataTable
            columns={columns}
            rows={historicalMembers}
            rowKey={(item) => item.id}
            layout="embedded"
            classNames={cecDataTableClassNames}
            labels={cecDataTableLabels}
          />
        )}
      </ComiteEticaSectionCard>

      <CecConfirmModal
        open={Boolean(ending)}
        title="Encerrar participação"
        message={
          ending
            ? `Encerrar o mandato ativo de ${ending.display_name}? O histórico será preservado.`
            : ""
        }
        confirmLabel="Encerrar"
        busy={saving}
        variant="danger"
        onConfirm={() => void confirmEnd()}
        onCancel={() => setEnding(null)}
      />
    </div>
  );
}
