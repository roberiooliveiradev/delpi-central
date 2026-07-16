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
import { HtmlPreview } from "../components/HtmlPreview";
import { MEETING_TYPE_LABELS, UNIT_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import { formatDateBr } from "../utils/htmlContent";

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

const STEPS = [
  "Dados da reunião",
  "Participantes",
  "Conteúdo",
  "Decisões",
  "Signatários",
  "Revisão",
] as const;

function validateStep(
  step: number,
  values: {
    title: string;
    meetingDate: string;
    selectedUsers: DirectoryUserOption[];
  },
): string | null {
  if (step === 0) {
    if (!values.title.trim()) return "Informe o título da ata.";
    if (!values.meetingDate) return "Informe a data da reunião.";
  }
  if (step === 4 && values.selectedUsers.length === 0) {
    return "Selecione ao menos um signatário obrigatório.";
  }
  return null;
}

export function MinuteEditorPage({ unitCode, minuteId }: Props) {
  const [step, setStep] = useState(0);
  const [title, setTitle] = useState("");
  const [meetingType, setMeetingType] = useState("ordinary");
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().slice(0, 10));
  const [location, setLocation] = useState("");
  const [bodyHtml, setBodyHtml] = useState("<p></p>");
  const [agendaHtml, setAgendaHtml] = useState("<p></p>");
  const [decisionsHtml, setDecisionsHtml] = useState("<p></p>");
  const [pendingHtml, setPendingHtml] = useState("<p></p>");
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
        setBodyHtml(String(detail.version?.body_html || "<p></p>"));
        setAgendaHtml(String(detail.version?.agenda_html || "<p></p>"));
        setDecisionsHtml(String(detail.version?.decisions_html || "<p></p>"));
        setPendingHtml(String(detail.version?.pending_html || "<p></p>"));
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

  function goToStep(next: number) {
    if (next > step) {
      const validationError = validateStep(step, { title, meetingDate, selectedUsers });
      if (validationError) {
        setError(validationError);
        return;
      }
    }
    setError(null);
    setStep(next);
  }

  async function saveDraft() {
    const validationError = validateStep(0, { title, meetingDate, selectedUsers });
    if (validationError) {
      setError(validationError);
      setStep(0);
      return;
    }
    if (selectedUsers.length === 0) {
      setError("Selecione ao menos um signatário obrigatório.");
      setStep(4);
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const payload = {
        unit_code: unitCode,
        title,
        meeting_type: meetingType,
        meeting_date: meetingDate,
        location,
        agenda_html: agendaHtml,
        body_html: bodyHtml,
        decisions_html: decisionsHtml,
        pending_html: pendingHtml,
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
      </header>

      <nav className="cipa-steps" aria-label="Etapas">
        {STEPS.map((label, index) => (
          <button
            key={label}
            type="button"
            className={`cipa-steps__item${step === index ? " is-active" : ""}${
              index < step ? " is-done" : ""
            }`}
            onClick={() => goToStep(index)}
          >
            {index + 1}. {label}
          </button>
        ))}
      </nav>

      {error && <p className="cipa-error" role="alert">{error}</p>}

      <section className="cipa-card cipa-editor-card">
        {step === 0 && (
          <div className="cipa-form-grid">
            <label className="cipa-field cipa-field--span-2">
              <span className="cipa-field__label">Título</span>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Ex.: Reunião ordinária — março/2026"
                required
              />
            </label>
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
            <label className="cipa-field cipa-field--span-2">
              <span className="cipa-field__label">Local</span>
              <input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="Sala, auditório ou link da reunião"
              />
            </label>
          </div>
        )}

        {step === 1 && (
          <div className="cipa-form-stack">
            <div className="cipa-field">
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
                labels={{ title: "Participantes (usuários)" }}
              />
            </div>

            <div className="cipa-external-row">
              <label className="cipa-field cipa-field--grow">
                <span className="cipa-field__label">Participante externo (nome)</span>
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
              <div className="cipa-participant-list">
                <p className="cipa-section-title">Lista de participantes ({participants.length})</p>
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
              </div>
            ) : (
              <p className="cipa-review-empty">Nenhum participante adicionado ainda.</p>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="cipa-form-stack">
            <div className="cipa-rich-section">
              <p className="cipa-section-title">
                Conteúdo da ata <HelpTooltip content={helpTooltips.richText} />
              </p>
              <RichTextEditor
                value={bodyHtml}
                onChange={setBodyHtml}
                mode="edit"
                portalScopeClassName="dashboard-cipa"
              />
            </div>
            <div className="cipa-rich-section">
              <p className="cipa-section-title">Pauta</p>
              <RichTextEditor
                value={agendaHtml}
                onChange={setAgendaHtml}
                mode="edit"
                portalScopeClassName="dashboard-cipa"
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="cipa-form-stack">
            <div className="cipa-rich-section">
              <p className="cipa-section-title">Decisões</p>
              <RichTextEditor
                value={decisionsHtml}
                onChange={setDecisionsHtml}
                mode="edit"
                portalScopeClassName="dashboard-cipa"
              />
            </div>
            <div className="cipa-rich-section">
              <p className="cipa-section-title">Pendências</p>
              <RichTextEditor
                value={pendingHtml}
                onChange={setPendingHtml}
                mode="edit"
                portalScopeClassName="dashboard-cipa"
              />
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="cipa-field">
            <UserDirectoryPicker
              value={selectedUsers}
              onChange={setSelectedUsers}
              searchUsers={searchDirectoryUsers}
              labels={{
                title: "Signatários obrigatórios",
                hint: "Selecione quem deve assinar a ata antes do envio.",
              }}
            />
          </div>
        )}

        {step === 5 && (
          <div className="cipa-review">
            <header className="cipa-review__header">
              <h2>Revisão</h2>
              <p className="cipa-review__meta">
                <strong>{title || "Sem título"}</strong>
                {" · "}
                {MEETING_TYPE_LABELS[meetingType] || meetingType}
                {" · "}
                {formatDateBr(meetingDate)}
                {location ? ` · ${location}` : ""}
              </p>
            </header>

            <div className="cipa-review-grid">
              <section className="cipa-review-block">
                <h3>Participantes</h3>
                {participants.length > 0 ? (
                  <ul className="cipa-review-list">
                    {participants.map((item, index) => (
                      <li key={`${item.display_name}-${index}`}>
                        {item.display_name}
                        {item.is_external ? " (externo)" : ""}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="cipa-review-empty">Nenhum participante informado.</p>
                )}
              </section>

              <section className="cipa-review-block">
                <h3>Signatários</h3>
                {selectedUsers.length > 0 ? (
                  <ul className="cipa-review-list">
                    {selectedUsers.map((user) => (
                      <li key={user.id}>{user.name || user.email}</li>
                    ))}
                  </ul>
                ) : (
                  <p className="cipa-review-empty">Nenhum signatário selecionado.</p>
                )}
              </section>

              <section className="cipa-review-block cipa-review-block--wide">
                <h3>Conteúdo da ata</h3>
                <HtmlPreview html={bodyHtml} emptyLabel="Conteúdo não preenchido." />
              </section>

              <section className="cipa-review-block cipa-review-block--wide">
                <h3>Pauta</h3>
                <HtmlPreview html={agendaHtml} emptyLabel="Pauta não preenchida." />
              </section>

              <section className="cipa-review-block cipa-review-block--wide">
                <h3>Decisões</h3>
                <HtmlPreview html={decisionsHtml} emptyLabel="Decisões não preenchidas." />
              </section>

              <section className="cipa-review-block cipa-review-block--wide">
                <h3>Pendências</h3>
                <HtmlPreview html={pendingHtml} emptyLabel="Pendências não preenchidas." />
              </section>
            </div>
          </div>
        )}
      </section>

      <div className="cipa-footer-actions">
        <button
          type="button"
          className="cipa-btn"
          disabled={step === 0}
          onClick={() => goToStep(Math.max(0, step - 1))}
        >
          Anterior
        </button>
        {step < STEPS.length - 1 ? (
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            onClick={() => goToStep(Math.min(STEPS.length - 1, step + 1))}
          >
            Próximo
          </button>
        ) : (
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            disabled={saving || !title.trim()}
            onClick={() => void saveDraft()}
          >
            {saving ? "Salvando…" : "Salvar ata"}
          </button>
        )}
      </div>
    </div>
  );
}
