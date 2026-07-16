import { useEffect, useState } from "react";
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
import { MEETING_TYPE_LABELS } from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCipa } from "../hooks/useCipaRouterPath";

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
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentId, setCurrentId] = useState<string | undefined>(minuteId);

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

  async function saveDraft() {
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
      if (selectedUsers.length > 0) {
        await setSigners(
          id,
          selectedUsers.map((user, index) => ({
            user_id: user.id,
            display_name: user.name || user.email,
            sign_order: index + 1,
          })),
        );
      }
      navigateCipa(`/apps/cipa/filial-${unitCode}/minutes/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  const steps = [
    "Dados da reunião",
    "Participantes",
    "Conteúdo",
    "Decisões",
    "Signatários",
    "Revisão",
  ];

  return (
    <div className="cipa-page-stack">
      <header className="cipa-header">
        <div>
          <h1>{currentId ? "Editar ata" : "Nova ata"}</h1>
          <p>Unidade {unitCode}</p>
        </div>
      </header>

      <nav className="cipa-steps" aria-label="Etapas">
        {steps.map((label, index) => (
          <button
            key={label}
            type="button"
            className={`cipa-steps__item${step === index ? " is-active" : ""}`}
            onClick={() => setStep(index)}
          >
            {index + 1}. {label}
          </button>
        ))}
      </nav>

      {error && <p className="cipa-error">{error}</p>}

      <section className="cipa-card">
        {step === 0 && (
          <div className="cipa-form-grid">
            <label>
              Título
              <input value={title} onChange={(e) => setTitle(e.target.value)} required />
            </label>
            <label>
              Tipo
              <select value={meetingType} onChange={(e) => setMeetingType(e.target.value)}>
                {Object.entries(MEETING_TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Data
              <input
                type="date"
                value={meetingDate}
                onChange={(e) => setMeetingDate(e.target.value)}
              />
            </label>
            <label>
              Local
              <input value={location} onChange={(e) => setLocation(e.target.value)} />
            </label>
          </div>
        )}

        {step === 1 && (
          <div className="cipa-form-grid">
            <UserDirectoryPicker
              value={participants
                .filter((item) => item.user_id)
                .map((item) => ({
                  id: item.user_id!,
                  name: item.display_name,
                  email: "",
                }))}
              onChange={(users) => {
                setParticipants(
                  users.map((user) => ({
                    user_id: user.id,
                    display_name: user.name || user.email,
                    role_in_meeting: "titular_member",
                    presence: "present",
                    is_external: false,
                    must_sign: false,
                  })),
                );
              }}
              searchUsers={searchDirectoryUsers}
              labels={{ title: "Participantes (usuários)" }}
            />
            <label>
              Participante externo (nome)
              <input
                placeholder="Nome completo"
                onKeyDown={(e) => {
                  if (e.key !== "Enter") return;
                  const value = (e.target as HTMLInputElement).value.trim();
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
                  (e.target as HTMLInputElement).value = "";
                }}
              />
            </label>
            <ul className="cipa-list">
              {participants.map((item, index) => (
                <li key={`${item.display_name}-${index}`}>
                  {item.display_name}
                  {item.is_external ? " (externo)" : ""}
                </li>
              ))}
            </ul>
          </div>
        )}

        {step === 2 && (
          <div>
            <p>
              Conteúdo da ata <HelpTooltip content={helpTooltips.richText} />
            </p>
            <RichTextEditor value={bodyHtml} onChange={setBodyHtml} mode="edit" />
            <p>Pauta</p>
            <RichTextEditor value={agendaHtml} onChange={setAgendaHtml} mode="edit" />
          </div>
        )}

        {step === 3 && (
          <div>
            <p>Decisões</p>
            <RichTextEditor value={decisionsHtml} onChange={setDecisionsHtml} mode="edit" />
            <p>Pendências</p>
            <RichTextEditor value={pendingHtml} onChange={setPendingHtml} mode="edit" />
          </div>
        )}

        {step === 4 && (
          <UserDirectoryPicker
            value={selectedUsers}
            onChange={setSelectedUsers}
            searchUsers={searchDirectoryUsers}
            labels={{ title: "Signatários obrigatórios" }}
          />
        )}

        {step === 5 && (
          <div>
            <h2>Revisão</h2>
            <p>
              <strong>{title}</strong> · {MEETING_TYPE_LABELS[meetingType]} · {meetingDate}
            </p>
            <RichTextEditor value={bodyHtml} mode="preview" onChange={() => undefined} />
          </div>
        )}
      </section>

      <div className="cipa-footer-actions">
        <button
          type="button"
          className="cipa-btn"
          disabled={step === 0}
          onClick={() => setStep((value) => Math.max(0, value - 1))}
        >
          Anterior
        </button>
        {step < steps.length - 1 ? (
          <button
            type="button"
            className="cipa-btn cipa-btn--primary"
            onClick={() => setStep((value) => Math.min(steps.length - 1, value + 1))}
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
