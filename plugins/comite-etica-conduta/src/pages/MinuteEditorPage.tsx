import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, X } from "lucide-react";
import {
  ActionButton,
  BackLink,
  FieldLabel,
  FormSelectControl,
  IconButton,
  NativeCheckboxControl,
  NativeTextControl,
  RichTextEditor,
  UserDirectoryPicker,
} from "@delpi/plugin-ui/index";

import {
  createMinute,
  createVersion,
  getMinute,
  listComiteEticaMembers,
  searchDirectoryUsers,
  setSigners,
  updateMinute,
} from "../api/cecApi";
import {
  MEETING_TYPE_LABELS,
  PARTICIPANT_ROLE_LABELS,
  UNIT_LABELS,
} from "../constants/labels";
import { helpTooltips } from "../content/helpTooltips";
import { navigateCec } from "../hooks/useCecRouterPath";
import {
  ComiteEticaContentCard,
  ComiteEticaFormActions,
  ComiteEticaPageHeader,
  ComiteEticaPageNotices,
  ComiteEticaSectionCard,
  ComiteEticaStateBanner,
} from "../ui/cecUi";
import { mergeCompositionWithExternals } from "../utils/cecComposition";
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

function isSignerParticipant(item: ParticipantDraft): boolean {
  return !item.is_external && Boolean(item.user_id) && item.must_sign;
}

function statusRequiresNewVersion(status: string): boolean {
  return status !== "" && status !== "draft" && status !== "in_review";
}

function validateForm(values: {
  title: string;
  meetingDate: string;
  participants: ParticipantDraft[];
}): string | null {
  if (!values.title.trim()) return "Informe o título da ata.";
  if (!values.meetingDate) return "Informe a data da reunião.";
  if (!values.participants.some(isSignerParticipant)) {
    return "Marque ao menos um participante como signatário.";
  }
  return null;
}

export function MinuteEditorPage({ unitCode, minuteId }: Props) {
  const [title, setTitle] = useState("");
  const [meetingType, setMeetingType] = useState("ordinary");
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().slice(0, 10));
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [location, setLocation] = useState("");
  const [contentHtml, setContentHtml] = useState("<p></p>");
  const [participants, setParticipants] = useState<ParticipantDraft[]>([]);
  const [externalName, setExternalName] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentId, setCurrentId] = useState<string | undefined>(minuteId);
  const [minuteStatus, setMinuteStatus] = useState("");
  const [participantsTouched, setParticipantsTouched] = useState(false);
  const [compositionLoading, setCompositionLoading] = useState(false);
  const [compositionNotice, setCompositionNotice] = useState<string | null>(null);

  const listPath = `/apps/comite-etica-conduta/minutes`;
  const unitLabel = UNIT_LABELS[unitCode] || `Unidade ${unitCode}`;
  const isNewMinute = !minuteId;

  const applyComposition = useCallback(
    async (date: string, { force = false }: { force?: boolean } = {}) => {
      if (!isNewMinute) return;
      if (!date) return;
      setCompositionLoading(true);
      try {
        const members = await listComiteEticaMembers(unitCode, { activeOn: date });
        setParticipants((prev) => mergeCompositionWithExternals(members, prev));
        setParticipantsTouched(false);
        setCompositionNotice(
          members.length === 0
            ? "Nenhum membro ativo na data da reunião. Cadastre a composição em Membros e cargos."
            : null,
        );
        if (force) {
          setError(null);
        }
      } catch (err) {
        setCompositionNotice(
          err instanceof Error
            ? err.message
            : "Não foi possível carregar a composição do Comitê de Ética.",
        );
      } finally {
        setCompositionLoading(false);
      }
    },
    [isNewMinute, unitCode],
  );

  useEffect(() => {
    if (!isNewMinute || participantsTouched) return;
    void applyComposition(meetingDate);
  }, [applyComposition, isNewMinute, meetingDate, participantsTouched]);

  useEffect(() => {
    if (!minuteId) return;
    getMinute(minuteId)
      .then((detail) => {
        const m = detail.minute;
        setMinuteStatus(String(m.status || ""));
        setTitle(String(m.title || ""));
        setMeetingType(String(m.meeting_type || "ordinary"));
        setMeetingDate(String(m.meeting_date || "").slice(0, 10));
        setStartTime(String(m.start_time || "").slice(0, 5));
        setEndTime(String(m.end_time || "").slice(0, 5));
        setLocation(String(m.location || ""));
        setContentHtml(mergeMinuteContentHtml(detail.version));
        const signerIds = new Set(
          (detail.signers || []).map((item) => String(item.user_id)),
        );
        const loadedParticipants = (detail.participants || []).map((item) => {
          const userId = item.user_id ? String(item.user_id) : undefined;
          return {
            user_id: userId,
            display_name: String(item.display_name || ""),
            role_in_meeting: String(item.role_in_meeting || "other"),
            presence: String(item.presence || "present"),
            is_external: Boolean(item.is_external),
            must_sign: Boolean(item.must_sign) || Boolean(userId && signerIds.has(userId)),
          };
        });
        const participantUserIds = new Set(
          loadedParticipants.filter((item) => item.user_id).map((item) => item.user_id),
        );
        const signerOnly = (detail.signers || [])
          .filter((item) => !participantUserIds.has(String(item.user_id)))
          .map((item) => ({
            user_id: String(item.user_id),
            display_name: String(item.display_name),
            role_in_meeting: "member",
            presence: "present",
            is_external: false,
            must_sign: true,
          }));
        setParticipants([...loadedParticipants, ...signerOnly]);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Erro ao carregar"));
  }, [minuteId]);

  function markParticipantsTouched() {
    if (isNewMinute) setParticipantsTouched(true);
  }

  function addExternalParticipant() {
    const value = externalName.trim();
    if (!value) return;
    markParticipantsTouched();
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
    markParticipantsTouched();
    setParticipants((prev) => prev.filter((_, i) => i !== index));
  }

  function toggleSigner(index: number, checked: boolean) {
    markParticipantsTouched();
    setParticipants((prev) =>
      prev.map((item, i) => (i === index ? { ...item, must_sign: checked } : item)),
    );
  }

  function updateParticipantRole(index: number, role: string) {
    markParticipantsTouched();
    setParticipants((prev) =>
      prev.map((item, i) => (i === index ? { ...item, role_in_meeting: role } : item)),
    );
  }

  async function saveDraft() {
    const validationError = validateForm({ title, meetingDate, participants });
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
        start_time: startTime || null,
        end_time: endTime || null,
        location,
        ...contentFields,
        participants,
      };
      if (currentId && statusRequiresNewVersion(minuteStatus)) {
        // Ata já enviada/assinada: reabrir criando nova versão apenas no salvar
        // (invalida assinaturas somente quando a alteração é confirmada).
        await createVersion(currentId, {
          change_reason: "Ata reaberta para edição pelo gestor.",
        });
        setMinuteStatus("in_review");
      }
      const detail = currentId
        ? await updateMinute(currentId, payload)
        : await createMinute(payload);
      const id = String(detail.minute.id);
      setCurrentId(id);
      await setSigners(
        id,
        participants.filter(isSignerParticipant).map((item, index) => ({
          user_id: item.user_id!,
          display_name: item.display_name,
          sign_order: index + 1,
        })),
      );
      navigateCec(`/apps/comite-etica-conduta/minutes/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar");
    } finally {
      setSaving(false);
    }
  }

  const directoryParticipants = participants
    .filter((item) => item.user_id && !item.is_external)
    .map((item) => ({
      id: item.user_id!,
      name: item.display_name,
      email: "",
    }));

  const signerParticipants = participants.filter(isSignerParticipant);

  return (
    <div className="cec-page-stack comite-etica-conduta-editor-page">
      <ComiteEticaPageHeader
        nav={
          <BackLink variant="prominent" onClick={() => navigateCec(listPath)}>
            Voltar para atas
          </BackLink>
        }
        title={currentId ? "Editar ata" : "Nova ata"}
        subtitle={unitLabel}
        actions={
          <ActionButton
            variant="primary"
            disabled={saving || !title.trim()}
            onClick={() => void saveDraft()}
          >
            {saving ? "Salvando…" : "Salvar ata"}
          </ActionButton>
        }
      />

      <ComiteEticaPageNotices error={error} onDismissError={() => setError(null)} />

      {statusRequiresNewVersion(minuteStatus) ? (
        <ComiteEticaStateBanner>
          Esta ata já está em processo de assinatura. Nada muda enquanto você não
          salvar; ao salvar, uma nova versão será criada e as assinaturas
          existentes serão invalidadas, exigindo nova rodada de assinaturas.
        </ComiteEticaStateBanner>
      ) : null}

      <form
        className="cec-compose"
        onSubmit={(event) => {
          event.preventDefault();
          void saveDraft();
        }}
      >
        <ComiteEticaContentCard className="cec-compose__section">
          <div className="cec-compose__row">
            <FieldLabel
              label="Título"
              htmlFor="comite-etica-conduta-minute-title"
              className="cec-compose__label"
            />
            <NativeTextControl
              id="comite-etica-conduta-minute-title"
              className="cec-compose__input--title"
              value={title}
              onChange={setTitle}
              placeholder="Ex.: Reunião ordinária — março/2026"
              required
            />
          </div>

          <div className="cec-compose__row comite-etica-conduta-compose__row--meta">
            <span className="cec-compose__label">Configurações</span>
            <div className="cec-compose__meta-fields">
              <div className="cec-field">
                <FieldLabel label="Tipo" htmlFor="comite-etica-conduta-minute-type" />
                <FormSelectControl
                  id="comite-etica-conduta-minute-type"
                  value={meetingType}
                  onChange={setMeetingType}
                  portalScopeClassName="dashboard-comite-etica-conduta"
                  options={Object.entries(MEETING_TYPE_LABELS).map(([value, label]) => ({
                    value,
                    label,
                  }))}
                />
              </div>
              <div className="cec-field">
                <FieldLabel label="Data" htmlFor="comite-etica-conduta-minute-date" />
                <NativeTextControl
                  id="comite-etica-conduta-minute-date"
                  type="date"
                  value={meetingDate}
                  onChange={setMeetingDate}
                />
              </div>
              <div className="cec-field">
                <FieldLabel label="Início" htmlFor="comite-etica-conduta-minute-start-time" />
                <NativeTextControl
                  id="comite-etica-conduta-minute-start-time"
                  type="time"
                  value={startTime}
                  onChange={setStartTime}
                />
              </div>
              <div className="cec-field">
                <FieldLabel label="Término" htmlFor="comite-etica-conduta-minute-end-time" />
                <NativeTextControl
                  id="comite-etica-conduta-minute-end-time"
                  type="time"
                  value={endTime}
                  onChange={setEndTime}
                />
              </div>
              <div className="cec-field comite-etica-conduta-field--grow">
                <FieldLabel label="Local" htmlFor="comite-etica-conduta-minute-location" />
                <NativeTextControl
                  id="comite-etica-conduta-minute-location"
                  value={location}
                  onChange={setLocation}
                  placeholder="Sala, auditório ou link da reunião"
                />
              </div>
            </div>
          </div>
        </ComiteEticaContentCard>

        <ComiteEticaSectionCard title="Participantes" className="cec-compose__section">
          <div className="cec-compose__panel">
            {isNewMinute ? (
              <div className="cec-composition-toolbar">
                <p className="cec-compose__hint">
                  Nova ata carrega a composição ativa do Comitê de Ética na data da reunião. Após editar
                  participantes manualmente, use «Recarregar composição Comitê de Ética» para atualizar.
                </p>
                <ActionButton
                  variant="ghost"
                  disabled={compositionLoading || !meetingDate}
                  onClick={() => void applyComposition(meetingDate, { force: true })}
                >
                  <RefreshCw size={16} />
                  {compositionLoading ? "Carregando…" : "Recarregar composição Comitê de Ética"}
                </ActionButton>
              </div>
            ) : (
              <p className="cec-compose__hint">
                Participantes desta ata são um snapshot histórico e não são sobrescritos pelo
                cadastro de membros.
              </p>
            )}
            {compositionNotice ? (
              <ComiteEticaStateBanner>{compositionNotice}</ComiteEticaStateBanner>
            ) : null}

            <UserDirectoryPicker
              value={directoryParticipants}
              onChange={(users) => {
                markParticipantsTouched();
                const externals = participants.filter((item) => item.is_external);
                const previousById = new Map(
                  participants
                    .filter((item) => item.user_id && !item.is_external)
                    .map((item) => [item.user_id!, item]),
                );
                setParticipants([
                  ...users.map((user) => {
                    const previous = previousById.get(user.id);
                    return {
                      user_id: user.id,
                      display_name: user.name || user.email,
                      role_in_meeting: previous?.role_in_meeting ?? "member",
                      presence: previous?.presence ?? "present",
                      is_external: false,
                      // Interno adicionado já entra como signatário; desmarcar é a exceção.
                      must_sign: previous?.must_sign ?? true,
                    };
                  }),
                  ...externals,
                ]);
              }}
              searchUsers={searchDirectoryUsers}
              showSelectedList={false}
              labels={{ title: "Usuários do diretório" }}
            />

            <div className="cec-external-row">
              <div className="cec-field comite-etica-conduta-field--grow">
                <FieldLabel label="Participante externo" htmlFor="comite-etica-conduta-external-name" />
                <NativeTextControl
                  id="comite-etica-conduta-external-name"
                  value={externalName}
                  onChange={setExternalName}
                  placeholder="Nome completo"
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      addExternalParticipant();
                    }
                  }}
                />
              </div>
              <ActionButton
                onClick={() => addExternalParticipant()}
                disabled={!externalName.trim()}
              >
                <Plus size={16} /> Adicionar
              </ActionButton>
            </div>

            {participants.length > 0 ? (
              <ul className="cec-chip-list">
                {participants.map((item, index) => (
                  <li key={`${item.display_name}-${index}`}>
                    <span className="cec-chip-list__name">
                      <span className="cec-chip-list__name-main">
                        {item.display_name}
                        {item.is_external ? (
                          <span className="cec-chip-list__tag">externo</span>
                        ) : null}
                      </span>
                      <span className="cec-chip-list__role">
                        {PARTICIPANT_ROLE_LABELS[item.role_in_meeting] ||
                          item.role_in_meeting}
                      </span>
                    </span>
                    <div className="cec-chip-list__actions">
                      <FormSelectControl
                        value={item.role_in_meeting}
                        onChange={(role) => updateParticipantRole(index, role)}
                        options={Object.entries(PARTICIPANT_ROLE_LABELS).map(
                          ([value, label]) => ({ value, label }),
                        )}
                        className="cec-participant-role-select"
                        portalScopeClassName="dashboard-comite-etica-conduta"
                        ariaLabel={`Papel de ${item.display_name}`}
                      />
                      {item.is_external ? (
                        <span className="cec-chip-list__note">não assina</span>
                      ) : (
                        <NativeCheckboxControl
                          checked={item.must_sign}
                          onChange={(checked) => toggleSigner(index, checked)}
                          label="Deve assinar"
                          aria-label={`${item.display_name} deve assinar`}
                        />
                      )}
                      <IconButton
                        tone="danger"
                        aria-label={`Remover ${item.display_name}`}
                        onClick={() => removeParticipant(index)}
                      >
                        <X size={16} />
                      </IconButton>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <ComiteEticaStateBanner>Nenhum participante adicionado.</ComiteEticaStateBanner>
            )}

            <div className="cec-signers-summary">
              <h3 className="cec-signers-summary__title">Signatários</h3>
              <p className="cec-compose__hint">
                Marque «Deve assinar» nos participantes internos. É obrigatório selecionar
                ao menos um signatário antes do envio para assinatura.
              </p>
              {signerParticipants.length > 0 ? (
                <ol className="cec-signer-list">
                  {signerParticipants.map((item, index) => (
                    <li key={item.user_id || `signer-${index}`}>{item.display_name}</li>
                  ))}
                </ol>
              ) : (
                <ComiteEticaStateBanner variant="error">
                  Nenhum signatário selecionado. Marque ao menos um participante.
                </ComiteEticaStateBanner>
              )}
            </div>
          </div>
        </ComiteEticaSectionCard>

        <ComiteEticaSectionCard
          title="Conteúdo da ata"
          hint={helpTooltips.richText}
          className="cec-compose__section comite-etica-conduta-compose__section--body"
        >
          <RichTextEditor
            value={contentHtml}
            onChange={setContentHtml}
            mode="edit"
            portalScopeClassName="dashboard-comite-etica-conduta"
            minHeight={360}
            ariaLabel="Conteúdo da ata"
          />
        </ComiteEticaSectionCard>

        <ComiteEticaFormActions align="end" className="cec-compose__footer">
          <ActionButton onClick={() => navigateCec(listPath)}>Cancelar</ActionButton>
          <ActionButton type="submit" variant="primary" disabled={saving || !title.trim()}>
            {saving ? "Salvando…" : "Salvar ata"}
          </ActionButton>
        </ComiteEticaFormActions>
      </form>
    </div>
  );
}
