import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  ActionButton,
  FieldLabel,
  NativeCheckboxControl,
  NativeSelectControl,
  NativeTextControl,
  parseDocxPreview,
  RichTextEditor,
  UserDirectoryPicker,
  type DirectoryUserOption,
} from "@delpi/plugin-ui/index";
import {
  ArrowLeft,
  Clock3,
  FileUp,
  PenLine,
  Save,
  Send,
  Sparkles,
  UserPlus,
  Users,
} from "lucide-react";

import type { AppProps } from "../../App";
import { PageHeader } from "../../components/PageHeader";
import { TransformometroShell } from "../../components/TransformometroShell";
import { buildAtaPath, TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  createAta,
  getAta,
  searchDirectoryUsers,
  sendAta,
  updateAta,
} from "../../data/api/transformometroAtaApi";
import {
  ATA_GENERATION_UNAVAILABLE_MESSAGE,
  requestAtaGenerationFromTranscript,
  resetAtaGenerationPort,
  setAtaGenerationPort,
} from "../../ai/ataGenerationPort";
import { createHttpAtaGenerationPort } from "../../ai/httpAtaGenerationPort";
import { mergeAtaContentHtml, splitAtaContentForSave } from "../atas/ataContent";
import { ATA_MEETING_TYPE_LABELS } from "../atas/ataLabels";

type Props = Pick<AppProps, "getAccessToken"> & {
  ataId?: string;
  onNavigate: (path: string) => void;
};

type ParticipantDraft = {
  user_id?: string;
  display_name: string;
  role_in_meeting: string;
  must_sign: boolean;
  is_external: boolean;
};

type EditorMode = "fill" | "import";
type PostSaveState = { id: string } | null;

function isSigner(item: ParticipantDraft): boolean {
  return !item.is_external && Boolean(item.user_id) && item.must_sign;
}

export function AtaEditorPage({ getAccessToken, ataId, onNavigate }: Props) {
  const [mode, setMode] = useState<EditorMode>("fill");
  const [title, setTitle] = useState("");
  const [unitCode, setUnitCode] = useState("01");
  const [meetingType, setMeetingType] = useState("ordinary");
  const [meetingDate, setMeetingDate] = useState(new Date().toISOString().slice(0, 10));
  const [showTimes, setShowTimes] = useState(false);
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");
  const [location, setLocation] = useState("");
  const [contentHtml, setContentHtml] = useState("<p></p>");
  const [participants, setParticipants] = useState<ParticipantDraft[]>([]);
  const [externalName, setExternalName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [sending, setSending] = useState(false);
  const [importing, setImporting] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [docxTruncated, setDocxTruncated] = useState(false);
  const [currentId, setCurrentId] = useState<string | undefined>(ataId);
  const [postSave, setPostSave] = useState<PostSaveState>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    setAtaGenerationPort(createHttpAtaGenerationPort(() => getAccessToken?.()));
    return () => resetAtaGenerationPort();
  }, [getAccessToken]);

  useEffect(() => {
    if (!ataId) return;
    void getAta(ataId, getAccessToken)
      .then((detail) => {
        const m = detail.minute;
        const v = detail.version ?? {};
        setTitle(String(m.title ?? ""));
        setUnitCode(String(m.unit_code ?? "01"));
        setMeetingType(String(m.meeting_type ?? "ordinary"));
        setMeetingDate(String(m.meeting_date ?? "").slice(0, 10));
        setStartTime(String(m.start_time ?? "").slice(0, 5));
        setEndTime(String(m.end_time ?? "").slice(0, 5));
        setShowTimes(Boolean(m.start_time || m.end_time));
        setLocation(String(m.location ?? ""));
        setContentHtml(mergeAtaContentHtml(v as Parameters<typeof mergeAtaContentHtml>[0]));
        setParticipants(
          detail.participants.map((item) => ({
            user_id: item.user_id ? String(item.user_id) : undefined,
            display_name: String(item.display_name ?? ""),
            role_in_meeting: String(item.role_in_meeting ?? "participant"),
            must_sign: Boolean(item.must_sign),
            is_external: Boolean(item.is_external),
          })),
        );
        setCurrentId(String(detail.minute.id));
      })
      .catch((reason) =>
        setError(reason instanceof Error ? reason.message : "Erro ao carregar ata."),
      );
  }, [ataId, getAccessToken]);

  const searchUsers = useCallback(
    (search: string, limit = 10, signal?: AbortSignal) =>
      searchDirectoryUsers(search, limit, signal, getAccessToken),
    [getAccessToken],
  );

  const directoryUsers: DirectoryUserOption[] = participants
    .filter((item) => item.user_id && !item.is_external)
    .map((item) => ({
      id: item.user_id!,
      name: item.display_name,
      email: "",
    }));

  const internalPeople = useMemo(
    () => participants.filter((item) => !item.is_external),
    [participants],
  );
  const externalPeople = useMemo(
    () => participants.filter((item) => item.is_external),
    [participants],
  );
  const signerCount = useMemo(() => participants.filter(isSigner).length, [participants]);

  function onDirectoryChange(users: DirectoryUserOption[]) {
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
          role_in_meeting: previous?.role_in_meeting ?? "participant",
          must_sign: previous?.must_sign ?? true,
          is_external: false,
        };
      }),
      ...externals,
    ]);
    setError(null);
  }

  function addExternal() {
    if (!externalName.trim()) return;
    setParticipants((prev) => [
      ...prev,
      {
        display_name: externalName.trim(),
        role_in_meeting: "guest",
        must_sign: false,
        is_external: true,
      },
    ]);
    setExternalName("");
  }

  async function onDocxSelected(file: File | null) {
    if (!file) return;
    setImporting(true);
    setError(null);
    setNotice(null);
    try {
      const preview = await parseDocxPreview(file);
      setContentHtml(preview.html || "<p></p>");
      setDocxTruncated(Boolean(preview.truncated));
      setMode("import");
      setNotice(
        preview.truncated
          ? "Transcrição importada (texto truncado por tamanho). Revise antes de salvar."
          : "Transcrição importada. Revise o texto e selecione os signatários.",
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Não foi possível ler o DOCX.");
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function onGenerateAi() {
    setGenerating(true);
    setError(null);
    setNotice(null);
    try {
      const result = await requestAtaGenerationFromTranscript({
        unitCode,
        meetingDate,
        title: title.trim() || undefined,
        transcriptHtml: contentHtml,
        source: mode === "import" ? "docx" : "manual",
      });
      setContentHtml(
        mergeAtaContentHtml({
          agenda_html: result.agendaHtml,
          body_html: result.bodyHtml,
          decisions_html: result.decisionsHtml,
          pending_html: result.pendingHtml,
          observations_html: result.observationsHtml,
        }),
      );
      if (result.title) setTitle(result.title);
      setNotice("Ata gerada pela IA. Revise antes de salvar.");
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : ATA_GENERATION_UNAVAILABLE_MESSAGE,
      );
    } finally {
      setGenerating(false);
    }
  }

  async function save(): Promise<string | null> {
    if (!title.trim() || !meetingDate) {
      setError("Informe título e data da reunião.");
      return null;
    }
    const signers = participants.filter(isSigner);
    if (!signers.length) {
      setError("Selecione ao menos um signatário no diretório do Minha Delpi.");
      return null;
    }
    setSaving(true);
    setError(null);
    try {
      const payload = {
        unit_code: unitCode,
        title: title.trim(),
        meeting_type: meetingType,
        meeting_date: meetingDate,
        start_time: startTime || null,
        end_time: endTime || null,
        location: location.trim() || null,
        ...splitAtaContentForSave(contentHtml),
        participants,
        signers: signers.map((item, index) => ({
          user_id: item.user_id,
          display_name: item.display_name,
          sign_order: index + 1,
        })),
      };
      const detail = currentId
        ? await updateAta(currentId, payload, getAccessToken)
        : await createAta(payload, getAccessToken);
      const id = String(detail.minute.id);
      setCurrentId(id);
      setPostSave({ id });
      setNotice("Rascunho salvo.");
      return id;
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erro ao salvar ata.");
      return null;
    } finally {
      setSaving(false);
    }
  }

  async function saveAndSend() {
    const id = postSave?.id ?? (await save());
    if (!id) return;
    setSending(true);
    try {
      await sendAta(id, getAccessToken);
      onNavigate(buildAtaPath(id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Erro ao enviar para assinatura.");
    } finally {
      setSending(false);
    }
  }

  const pageTitle = currentId ? "Editar ata" : "Nova ata";

  return (
    <TransformometroShell>
      <PageHeader
        title={pageTitle}
        subtitle="Transforma+ · preencha o registro ou gere a partir da transcrição."
        currentPath={TRANSFORMOMETRO_ROUTES.atas}
        onNavigate={onNavigate}
        actions={
          <>
            <ActionButton variant="link" onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atas)}>
              <ArrowLeft size={16} aria-hidden />
              Voltar
            </ActionButton>
            <ActionButton variant="primary" disabled={saving} onClick={() => void save()}>
              <Save size={16} aria-hidden />
              {saving ? "Salvando…" : "Salvar rascunho"}
            </ActionButton>
          </>
        }
      />

      <div className="tm-ata-editor" aria-busy={saving || generating || importing}>
        <section className="tm-ata-editor__mode ds-card" aria-label="Modo de criação">
          <div className="tm-ata-editor__mode-copy">
            <h2>Como deseja criar?</h2>
            <p className="ds-muted">
              Escreva o conteúdo manualmente ou importe um .docx e use IA para estruturar a ata.
            </p>
          </div>
          <div className="tm-ata-editor__segment" role="tablist" aria-label="Modo de inclusão">
            <button
              type="button"
              role="tab"
              aria-selected={mode === "fill"}
              className={`tm-ata-editor__segment-btn${mode === "fill" ? " is-active" : ""}`}
              onClick={() => setMode("fill")}
            >
              <PenLine size={16} aria-hidden />
              Preencher
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={mode === "import"}
              className={`tm-ata-editor__segment-btn${mode === "import" ? " is-active" : ""}`}
              onClick={() => setMode("import")}
            >
              <FileUp size={16} aria-hidden />
              Importar transcrição
            </button>
          </div>
        </section>

        {error ? (
          <p className="tm-atas-alert" role="alert">
            {error}
          </p>
        ) : null}
        {notice ? (
          <p className="tm-ata-editor__notice" role="status">
            {notice}
          </p>
        ) : null}

        <section className="tm-ata-editor__section ds-card">
          <header className="tm-ata-editor__section-head">
            <div>
              <h2>Detalhes da reunião</h2>
              <p className="ds-muted">Informações que aparecem no cabeçalho da ata.</p>
            </div>
          </header>
          <div className="tm-ata-editor__grid">
            <div className="tm-ata-editor__field tm-ata-editor__field--wide">
              <FieldLabel label="Título" htmlFor="ata-title" />
              <NativeTextControl
                id="ata-title"
                value={title}
                onChange={setTitle}
                placeholder="Ex.: Acompanhamento semanal Transforma+"
              />
            </div>
            <div className="tm-ata-editor__field">
              <FieldLabel label="Unidade" htmlFor="ata-unit" />
              <NativeSelectControl
                id="ata-unit"
                value={unitCode}
                onChange={setUnitCode}
                options={[
                  { value: "01", label: "Unidade 01" },
                  { value: "02", label: "Unidade 02" },
                ]}
              />
            </div>
            <div className="tm-ata-editor__field">
              <FieldLabel label="Tipo" htmlFor="ata-type" />
              <NativeSelectControl
                id="ata-type"
                value={meetingType}
                onChange={setMeetingType}
                options={Object.entries(ATA_MEETING_TYPE_LABELS).map(([value, label]) => ({
                  value,
                  label,
                }))}
              />
            </div>
            <div className="tm-ata-editor__field">
              <FieldLabel label="Data" htmlFor="ata-date" />
              <NativeTextControl
                id="ata-date"
                type="date"
                value={meetingDate}
                onChange={setMeetingDate}
              />
            </div>
            <div className="tm-ata-editor__field">
              <FieldLabel label="Local" htmlFor="ata-location" />
              <NativeTextControl
                id="ata-location"
                value={location}
                onChange={setLocation}
                placeholder="Sala, planta ou remoto"
              />
            </div>
          </div>

          <div className="tm-ata-editor__times">
            <ActionButton variant="link" onClick={() => setShowTimes((value) => !value)}>
              <Clock3 size={16} aria-hidden />
              {showTimes ? "Ocultar horários" : "Informar horários (opcional)"}
            </ActionButton>
            {showTimes ? (
              <div className="tm-ata-editor__grid tm-ata-editor__grid--times">
                <div className="tm-ata-editor__field">
                  <FieldLabel label="Início" htmlFor="ata-start" />
                  <NativeTextControl
                    id="ata-start"
                    type="time"
                    value={startTime}
                    onChange={setStartTime}
                  />
                </div>
                <div className="tm-ata-editor__field">
                  <FieldLabel label="Término" htmlFor="ata-end" />
                  <NativeTextControl
                    id="ata-end"
                    type="time"
                    value={endTime}
                    onChange={setEndTime}
                  />
                </div>
              </div>
            ) : null}
          </div>
        </section>

        {mode === "import" ? (
          <section className="tm-ata-editor__section tm-ata-editor__import ds-card">
            <header className="tm-ata-editor__section-head">
              <div>
                <h2>Transcrição (.docx)</h2>
                <p className="ds-muted">
                  O texto entra no editor para revisão. Depois você pode gerar a ata estruturada com
                  IA.
                </p>
              </div>
            </header>
            <label className="tm-ata-editor__upload">
              <FileUp size={20} aria-hidden />
              <span>
                <strong>{importing ? "Lendo documento…" : "Selecionar arquivo DOCX"}</strong>
                <small>Arraste ou clique para escolher o arquivo da reunião</small>
              </span>
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                aria-label="Arquivo DOCX da transcrição"
                disabled={importing || generating}
                onChange={(event) => void onDocxSelected(event.target.files?.[0] ?? null)}
              />
            </label>
            {docxTruncated ? (
              <p className="tm-ata-editor__warn" role="status">
                O documento foi truncado por tamanho; revise o final do texto.
              </p>
            ) : null}
            <div className="tm-ata-editor__ai-row">
              <ActionButton
                variant="primary"
                disabled={generating || importing}
                onClick={() => void onGenerateAi()}
              >
                <Sparkles size={16} aria-hidden />
                {generating ? "Gerando… (cerca de 1 min)" : "Gerar ata com IA"}
              </ActionButton>
              {generating ? (
                <p className="ds-muted" role="status">
                  Processando a transcrição. Não feche nem recarregue a página.
                </p>
              ) : (
                <p className="ds-muted">Use após importar ou colar o conteúdo no editor abaixo.</p>
              )}
            </div>
          </section>
        ) : null}

        <section className="tm-ata-editor__section ds-card">
          <header className="tm-ata-editor__section-head">
            <div>
              <h2>Conteúdo da ata</h2>
              <p className="ds-muted">
                Pauta, discussão, decisões, pendências e observações em um único documento.
              </p>
            </div>
          </header>
          <div className="tm-ata-editor__rich">
            <RichTextEditor
              value={contentHtml}
              onChange={setContentHtml}
              portalScopeClassName="dashboard-transformometro"
            />
          </div>
        </section>

        <section className="tm-ata-editor__section ds-card">
          <header className="tm-ata-editor__section-head">
            <div>
              <h2>
                <Users size={18} aria-hidden /> Quem assina
              </h2>
              <p className="ds-muted">
                Busque pessoas do Minha Delpi. Por padrão, quem você adicionar assina a ata.
              </p>
            </div>
            <span className="tm-ata-editor__badge">
              {signerCount} signatário{signerCount === 1 ? "" : "s"}
            </span>
          </header>

          <UserDirectoryPicker
            value={directoryUsers}
            onChange={onDirectoryChange}
            searchUsers={searchUsers}
            showSelectedList={false}
            showEmail
            labels={{
              title: "Pessoas do Minha Delpi",
              hint: "Digite ao menos 2 letras do nome",
              placeholder: "Buscar usuário…",
            }}
          />

          {internalPeople.length > 0 ? (
            <ul className="tm-ata-editor__people">
              {internalPeople.map((item) => (
                <li key={item.user_id} className="tm-ata-editor__person">
                  <div className="tm-ata-editor__person-main">
                    <strong>{item.display_name}</strong>
                    <NativeCheckboxControl
                      checked={item.must_sign}
                      onChange={(checked) =>
                        setParticipants((prev) =>
                          prev.map((row) =>
                            row.user_id === item.user_id ? { ...row, must_sign: checked } : row,
                          ),
                        )
                      }
                      label="Assina"
                    />
                  </div>
                  <ActionButton
                    variant="link"
                    onClick={() =>
                      setParticipants((prev) => prev.filter((row) => row.user_id !== item.user_id))
                    }
                  >
                    Remover
                  </ActionButton>
                </li>
              ))}
            </ul>
          ) : (
            <p className="tm-ata-editor__empty ds-muted">Nenhum signatário selecionado ainda.</p>
          )}

          <div className="tm-ata-editor__external">
            <h3>
              <UserPlus size={16} aria-hidden /> Convidado externo
            </h3>
            <p className="ds-muted">Aparece na ata, mas não assina digitalmente.</p>
            <div className="tm-ata-editor__external-row">
              <NativeTextControl
                value={externalName}
                onChange={setExternalName}
                placeholder="Nome completo"
              />
              <ActionButton disabled={!externalName.trim()} onClick={addExternal}>
                Adicionar
              </ActionButton>
            </div>
            {externalPeople.length > 0 ? (
              <ul className="tm-ata-editor__people tm-ata-editor__people--external">
                {externalPeople.map((item, index) => (
                  <li key={`${item.display_name}-${index}`} className="tm-ata-editor__person">
                    <div className="tm-ata-editor__person-main">
                      <strong>{item.display_name}</strong>
                      <span className="ds-muted">Convidado</span>
                    </div>
                    <ActionButton
                      variant="link"
                      onClick={() =>
                        setParticipants((prev) =>
                          prev.filter(
                            (row) => !(row.is_external && row.display_name === item.display_name),
                          ),
                        )
                      }
                    >
                      Remover
                    </ActionButton>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
        </section>

        {postSave ? (
          <section className="tm-ata-editor__next ds-card" role="region" aria-label="Próximos passos">
            <header className="tm-ata-editor__section-head">
              <div>
                <h2>Rascunho salvo</h2>
                <p className="ds-muted">Escolha o próximo passo. Você pode continuar editando depois.</p>
              </div>
            </header>
            <div className="tm-ata-editor__next-actions">
              <ActionButton
                variant="primary"
                disabled={sending}
                onClick={() => void saveAndSend()}
              >
                <Send size={16} aria-hidden />
                {sending ? "Enviando…" : "Enviar para assinatura"}
              </ActionButton>
              <ActionButton onClick={() => onNavigate(buildAtaPath(postSave.id))}>
                Ver ata
              </ActionButton>
              <ActionButton
                variant="link"
                onClick={() => {
                  setPostSave(null);
                  setNotice("Pode continuar editando.");
                }}
              >
                Continuar editando
              </ActionButton>
            </div>
          </section>
        ) : null}

        <footer className="tm-ata-editor__footer ds-card">
          <div className="tm-ata-editor__footer-meta ds-muted">
            {signerCount > 0
              ? `${signerCount} pessoa(s) vão assinar`
              : "Selecione ao menos um signatário para salvar"}
          </div>
          <div className="tm-ata-editor__footer-actions">
            <ActionButton onClick={() => onNavigate(TRANSFORMOMETRO_ROUTES.atas)}>
              Cancelar
            </ActionButton>
            <ActionButton variant="primary" disabled={saving} onClick={() => void save()}>
              <Save size={16} aria-hidden />
              {saving ? "Salvando…" : "Salvar rascunho"}
            </ActionButton>
          </div>
        </footer>
      </div>
    </TransformometroShell>
  );
}
