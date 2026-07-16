import { useEffect, useState } from "react";
import { Plus, X } from "lucide-react";
import {
  HelpTooltip,
  RichTextEditor,
  UserDirectoryPicker,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";

import {
  createMinute,
  getMinute,
  searchDirectoryUsers,
  setSigners,
  updateMinute,
} from "../api/cipaApi";
import { MEETING_TYPE_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import { mergeMinuteContentHtml, splitMinuteContentForSave } from "../utils/minuteContent";

type Props = {
  unitCode: "01" | "02";
  minuteId?: string;
};

type ParticipantDraft = {
  user_id?: string;
  display_name: string;
  role_in_meeting: string;
  presence: string;
  is_external: boolean;
  must_sign: boolean;
};

function validateForm(values: {
  title: string;
  meetingDate: string;
  selectedUsers: DirectoryUserOption[];
}): string | null {
  if (!values.title.trim()) return "Informe o título da ata.";
  if (!values.meetingDate) return "Informe a data da reunião.";
  if (values.selectedUsers.length === 0) return "Selecione ao menos um signatário obrigatório.";
  return null;
}

export function MinuteEditorPage({ unitCode, minuteId }: Props) {
  const [title, setTitle] = useState("");
  const [meetingType, setMeetingType] = useState("ordinary");
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().slice(0, 10));
  const [location, setLocation] = useState("");
  const [contentHtml, setContentHtml] = useState("<p></p>");
  const [participants, setParticipants] = useState<ParticipantDraft[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<DirectoryUserOption[]>([]);
  const [externalName, setExternalName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentId, setCurrentId] = useState<string | undefined>(minuteId);

  const listPath = `/apps/cipa/filial-${unitCode}/minutes`;
  const unitLabel = UNIT_LABELS[unitCode] || `Unidade ${unitCode}`;

  useEffect(() => {
    if (!minuteId) return;
    getMinute(minuteId)
      .then((detail) => {
        const m = detail.minute;
        setTitle(String(m.title || ""));
        setMeetingType(String(m.meeting_type || "ordinary"));
        setMeetingDate(String(m.meeting_date || "").slice(0, 10));
        setLocation(String(m.location || ""));
        setContentHtml(mergeMinuteContentHtml(detail.version));
        setParticipants(
          (detail.participants || []).map((item) => ({
            user_id: item.user_id ? String(item.user_id) : undefined,
            display_name: String(item.display_name || ""),
            role_in_meeting: String(item.role_in_meeting || "other"),
            presence: String(item.presence || "present"),
            is_external: Boolean(item.is_external),
            must_sign: Boolean(item.must_sign),
          })),
        );
        setSelectedUsers(
          (detail.signers || []).map((item) => ({
            id: String(item.user_id),
            name: String(item.display_name),
            email: "",
          })),
        );
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar"));
  }, [minuteId]);

  function addExternalParticipant() {
    const value = externalName.trim();
    if (!value) return;
    setParticipants((prev) => [
      ...prev,
      {
        display_name: value,
        role_in_meeting: "guest",
        presence: "present",
        is_external: true,
        must_sign: false,
      },
    ]);
    setExternalName("");
  }

  function removeParticipant(index: number) {
    setParticipants((prev) => prev.filter((_, i) => i !== index));
  }

  async function saveDraft() {
    const validationError = validateForm({ title, meetingDate, selectedUsers });
    if (validationError) {
      setError(validationError);
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const contentFields = splitMinuteContentForSave(contentHtml);
      const payload = {
        unit_code: unitCode,
        title,
        meeting_type: meetingType,
        meeting_date: meetingDate,
        location,
        ...contentFields,
        participants,
      };
      const detail = currentId
        ? await updateMinute(currentId, payload)
        : await createMinute(payload);
      const id = String(detail.minute.id);
      setCurrentId(id);
      await setSigners(
        id,
        selectedUsers.map((user, index) => ({
          user_id: user.id,
          display_name: user.name || user.email,
          sign_order: index + 1,
        })),
      );
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  const directoryParticipants = participants
    .filter((item) => item.user_id)
    .map((item) => ({
      id: item.user_id!,
      name: item.display_name,
      email: "",
    }));

  return (
    <div className="cipa-page-stack cipa-editor-page">
      <header className="cipa-header">
        <div>
          <button type="button" className="cipa-link" onClick={() => navigateCipa(listPath)}>
            ← Voltar para atas
          </button>
          <h1>{currentId ? "Editar ata" : "Nova ata"}</h1>
          <p>{unitLabel}</p>
        </div>
        <div className="cipa-header__actions">
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            disabled={saving || !title.trim()}
            onClick={() => void saveDraft()}
          >
            {saving ? "Salvando…" : "Salvar ata"}
          </button>
        </div>
      </header>

      {error ? (
        <p className="cipa-error" role="alert">
          {error}
        </p>
      ) : null}

      <form
        className="cipa-compose"
        onSubmit={(event) => {
          event.preventDefault();
          void saveDraft();
        }}
      >
        <section className="cipa-card cipa-compose__section">
          <div className="cipa-compose__row">
            <span className="cipa-compose__label">Título</span>
            <input
              className="cipa-compose__input cipa-compose__input--title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex.: Reunião ordinária — março/2026"
              required
            />
          </div>

          <div className="cipa-compose__row cipa-compose__row--meta">
            <span className="cipa-compose__label">Configurações</span>
            <div className="cipa-compose__meta-fields">
              <label className="cipa-field">
                <span className="cipa-field__label">Tipo</span>
                <select value={meetingType} onChange={(e) => setMeetingType(e.target.value)}>
                  {Object.entries(MEETING_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="cipa-field">
                <span className="cipa-field__label">Data</span>
                <input
                  type="date"
                  value={meetingDate}
                  onChange={(e) => setMeetingDate(e.target.value)}
                />
              </label>
              <label className="cipa-field cipa-field--grow">
                <span className="cipa-field__label">Local</span>
                <input
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Sala, auditório ou link da reunião"
                />
              </label>
            </div>
          </div>
        </section>

        <section className="cipa-card cipa-compose__section">
          <h2 className="cipa-compose__section-title">Participantes</h2>
          <div className="cipa-compose__panel">
            <UserDirectoryPicker
              value={directoryParticipants}
              onChange={(users) => {
                const externals = participants.filter((item) => item.is_external);
                setParticipants([
                  ...users.map((user) => ({
                    user_id: user.id,
                    display_name: user.name || user.email,
                    role_in_meeting: "titular_member",
                    presence: "present",
                    is_external: false,
                    must_sign: false,
                  })),
                  ...externals,
                ]);
              }}
              searchUsers={searchDirectoryUsers}
              labels={{ title: "Usuários do diretório" }}
            />

            <div className="cipa-external-row">
              <label className="cipa-field cipa-field--grow">
                <span className="cipa-field__label">Participante externo</span>
                <input
                  value={externalName}
                  onChange={(e) => setExternalName(e.target.value)}
                  placeholder="Nome completo"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addExternalParticipant();
                    }
                  }}
                />
              </label>
              <button
                type="button"
                className="cipa-btn"
                onClick={() => addExternalParticipant()}
                disabled={!externalName.trim()}
              >
                <Plus size={16} /> Adicionar
              </button>
            </div>

            {participants.length > 0 ? (
              <ul className="cipa-chip-list">
                {participants.map((item, index) => (
                  <li key={`${item.display_name}-${index}`}>
                    <span>
                      {item.display_name}
                      {item.is_external ? (
                        <span className="cipa-chip-list__tag">externo</span>
                      ) : null}
                    </span>
                    <button
                      type="button"
                      className="cipa-icon-btn"
                      aria-label={`Remover ${item.display_name}`}
                      onClick={() => removeParticipant(index)}
                    >
                      <X size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="cipa-review-empty">Nenhum participante adicionado.</p>
            )}
          </div>
        </section>

        <section className="cipa-card cipa-compose__section">
          <h2 className="cipa-compose__section-title">Signatários</h2>
          <div className="cipa-compose__panel">
            <UserDirectoryPicker
              value={selectedUsers}
              onChange={setSelectedUsers}
              searchUsers={searchDirectoryUsers}
              labels={{
                title: "Quem deve assinar",
                hint: "Obrigatório antes do envio para assinatura.",
              }}
            />
          </div>
        </section>

        <section className="cipa-card cipa-compose__section cipa-compose__section--body">
          <h2 className="cipa-compose__section-title">
            Conteúdo da ata <HelpTooltip content={helpTooltips.richText} />
          </h2>
          <RichTextEditor
            value={contentHtml}
            onChange={setContentHtml}
            mode="edit"
            portalScopeClassName="dashboard-cipa"
            minHeight={360}
            ariaLabel="Conteúdo da ata"
          />
        </section>

        <div className="cipa-compose__footer">
          <button type="button" className="cipa-btn" onClick={() => navigateCipa(listPath)}>
            Cancelar
          </button>
          <button
            type="submit"
            className="cipa-btn cipa-btn--primary"
            disabled={saving || !title.trim()}
          >
            {saving ? "Salvando…" : "Salvar ata"}
          </button>
        </div>
      </form>
    </div>
  );
}
