import { type FormEvent, useCallback, useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";

import {
  archiveAdminDocument,
  downloadGuidanceDocument,
  fetchAdminGuidance,
  listAdminExercises,
  listAdminGuidanceDocuments,
  publishAdminGuidance,
  saveAdminGuidanceDraft,
  updateAdminDocument,
  uploadAdminGuidanceDocument,
} from "../../api/budgetPlanningApi";
import type {
  GuidanceCurrent,
  GuidanceDocument,
  GuidancePremise,
  GuidanceScheduleItem,
} from "../../types/budgetPlanning";
import { PageShell } from "../../components/PageShell";
import { LoadingActivityCard, SectionCard, StateBox } from "../../components/uiKit";
import { usePermissions } from "../../hooks/usePermissions";
import { hasGuidanceManageAccess } from "../../utils/permissions";
import {
  DOCUMENT_KIND_OPTIONS,
  formatBytes,
  validateClientUpload,
} from "../../utils/documentUpload";

type UploadState = "empty" | "selected" | "uploading" | "success" | "error";

export function AdminGuidancePage() {
  const { profile, loading: permLoading } = usePermissions();
  const [exerciseId, setExerciseId] = useState<string>("");
  const [draft, setDraft] = useState<GuidanceCurrent | null>(null);
  const [documents, setDocuments] = useState<GuidanceDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [description, setDescription] = useState("");
  const [documentKind, setDocumentKind] = useState("pdf");
  const [displayOrder, setDisplayOrder] = useState(0);
  const [uploadState, setUploadState] = useState<UploadState>("empty");
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadMessage, setUploadMessage] = useState<string | null>(null);
  const canAccess = hasGuidanceManageAccess(profile);

  const reloadDocuments = useCallback(
    async (guidanceId: string, signal?: AbortSignal) => {
      const items = await listAdminGuidanceDocuments(guidanceId, signal);
      setDocuments(items);
    },
    [],
  );

  useEffect(() => {
    if (permLoading) return;
    if (!canAccess) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    listAdminExercises(controller.signal)
      .then(async (exercises) => {
        const preferred =
          exercises.find((e) => e.is_active) ??
          exercises.find((e) => e.status === "open") ??
          exercises[0];
        if (!preferred) {
          setError("Crie um exercício antes de editar orientações.");
          return;
        }
        setExerciseId(preferred.id);
        const bundle = await fetchAdminGuidance(preferred.id, controller.signal);
        setDraft(bundle.draft as GuidanceCurrent);
        await reloadDocuments(bundle.draft.id, controller.signal);
        setError(null);
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Erro ao carregar.");
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [canAccess, permLoading, reloadDocuments]);

  async function handleSave(event: FormEvent) {
    event.preventDefault();
    if (!draft?.id) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await saveAdminGuidanceDraft(draft.id, {
        title: draft.title,
        board_message: draft.board_message,
        objective: draft.objective,
        general_guidance: draft.general_guidance,
        additional_notes: draft.additional_notes,
        sender_name: draft.sender_name,
        sender_role: draft.sender_role,
        premises: draft.premises,
        schedule: draft.schedule,
      });
      setDraft(saved);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  async function handlePublish() {
    if (!draft?.id) return;
    if (!window.confirm("Publicar nova versão imutável das orientações?")) return;
    setPublishing(true);
    setError(null);
    try {
      const published = await publishAdminGuidance(draft.id);
      const bundle = await fetchAdminGuidance(exerciseId);
      setDraft(bundle.draft as GuidanceCurrent);
      await reloadDocuments(bundle.draft.id);
      window.alert(`Versão ${published.version_number} publicada.`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao publicar.");
    } finally {
      setPublishing(false);
    }
  }

  function updatePremise(index: number, patch: Partial<GuidancePremise>) {
    setDraft((prev) => {
      if (!prev) return prev;
      const premises = [...prev.premises];
      premises[index] = { ...premises[index], ...patch };
      return { ...prev, premises };
    });
  }

  function updateSchedule(index: number, patch: Partial<GuidanceScheduleItem>) {
    setDraft((prev) => {
      if (!prev) return prev;
      const schedule = [...prev.schedule];
      schedule[index] = { ...schedule[index], ...patch };
      return { ...prev, schedule };
    });
  }

  function onFileSelected(next: File | null) {
    setFile(next);
    setUploadMessage(null);
    if (!next) {
      setUploadState("empty");
      return;
    }
    const validation = validateClientUpload(next);
    if (!validation.ok) {
      setUploadState("error");
      setUploadMessage(validation.message);
      return;
    }
    setUploadState("selected");
    if (!displayName.trim()) {
      setDisplayName(next.name.replace(/\.[^.]+$/, ""));
    }
  }

  async function handleUpload(event: FormEvent) {
    event.preventDefault();
    if (!draft?.id || !exerciseId || uploadState === "uploading") return;
    const validation = validateClientUpload(file);
    if (!validation.ok) {
      setUploadState("error");
      setUploadMessage(validation.message);
      return;
    }
    if (!displayName.trim()) {
      setUploadState("error");
      setUploadMessage("Informe o nome de exibição.");
      return;
    }
    setUploadState("uploading");
    setUploadProgress(0);
    setUploadMessage(null);
    setError(null);
    try {
      await uploadAdminGuidanceDocument(
        {
          exerciseId,
          guidanceId: draft.id,
          file,
          displayName: displayName.trim(),
          description: description.trim() || undefined,
          displayOrder,
          documentKind: documentKind === "external_link" ? undefined : documentKind,
        },
        { onProgress: setUploadProgress },
      );
      setUploadState("success");
      setUploadMessage("Documento enviado com sucesso.");
      setFile(null);
      setDisplayName("");
      setDescription("");
      setDisplayOrder(0);
      await reloadDocuments(draft.id);
    } catch (err: unknown) {
      setUploadState("error");
      setUploadMessage(err instanceof Error ? err.message : "Falha no upload.");
    }
  }

  async function handleArchive(documentId: string) {
    if (!draft?.id) return;
    try {
      await archiveAdminDocument(documentId);
      await reloadDocuments(draft.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao arquivar.");
    }
  }

  async function handleRename(doc: GuidanceDocument) {
    if (!draft?.id) return;
    const next = window.prompt("Nome de exibição", doc.display_name);
    if (next == null || !next.trim()) return;
    try {
      await updateAdminDocument(doc.id, {
        display_name: next.trim(),
        description: doc.description,
        display_order: doc.display_order ?? 0,
      });
      await reloadDocuments(draft.id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha ao atualizar metadados.");
    }
  }

  async function handleDownload(documentId: string, name: string) {
    try {
      const blob = await downloadGuidanceDocument(documentId);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = name;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro no download.");
    }
  }

  if (permLoading || loading) {
    return (
      <PageShell title="Orientações" subtitle="Administração">
        <LoadingActivityCard title="Carregando…" variant="panel" />
      </PageShell>
    );
  }

  if (!canAccess) {
    return (
      <PageShell title="Orientações" subtitle="Acesso restrito.">
        <StateBox variant="error" dismissible={false}>
          Sem permissão para gerenciar orientações.
        </StateBox>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Orientações (admin)"
      subtitle="Edite o rascunho, anexe documentos e publique versões imutáveis."
      icon={<ClipboardList size={28} strokeWidth={1.75} aria-hidden="true" />}
      backRoute="admin"
    >
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}

      {draft ? (
        <form className="po-page-stack" onSubmit={(e) => void handleSave(e)}>
          <SectionCard title="Mensagem institucional">
            <label>
              Título
              <input
                required
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              />
            </label>
            <label>
              Mensagem da Diretoria
              <textarea
                required
                rows={6}
                value={draft.board_message}
                onChange={(e) => setDraft({ ...draft, board_message: e.target.value })}
              />
            </label>
            <label>
              Objetivo
              <textarea
                rows={3}
                value={draft.objective}
                onChange={(e) => setDraft({ ...draft, objective: e.target.value })}
              />
            </label>
            <label>
              Orientações gerais
              <textarea
                rows={4}
                value={draft.general_guidance}
                onChange={(e) => setDraft({ ...draft, general_guidance: e.target.value })}
              />
            </label>
          </SectionCard>

          <SectionCard title="Premissas">
            <button
              type="button"
              className="po-btn po-btn--secondary"
              onClick={() =>
                setDraft({
                  ...draft,
                  premises: [...draft.premises, { name: "", value_text: "" }],
                })
              }
            >
              Adicionar premissa
            </button>
            {draft.premises.map((premise, index) => (
              <div key={index} className="po-form">
                <input
                  placeholder="Nome"
                  value={premise.name}
                  onChange={(e) => updatePremise(index, { name: e.target.value })}
                />
                <input
                  placeholder="Valor"
                  value={premise.value_text ?? ""}
                  onChange={(e) => updatePremise(index, { value_text: e.target.value })}
                />
                <input
                  placeholder="Unidade"
                  value={premise.unit_label ?? ""}
                  onChange={(e) => updatePremise(index, { unit_label: e.target.value })}
                />
              </div>
            ))}
          </SectionCard>

          <SectionCard title="Cronograma">
            <button
              type="button"
              className="po-btn po-btn--secondary"
              onClick={() =>
                setDraft({
                  ...draft,
                  schedule: [
                    ...draft.schedule,
                    { title: "", starts_on: new Date().toISOString().slice(0, 10) },
                  ],
                })
              }
            >
              Adicionar marco
            </button>
            {draft.schedule.map((item, index) => (
              <div key={index} className="po-form">
                <input
                  placeholder="Título"
                  value={item.title}
                  onChange={(e) => updateSchedule(index, { title: e.target.value })}
                />
                <input
                  type="date"
                  value={item.starts_on}
                  onChange={(e) => updateSchedule(index, { starts_on: e.target.value })}
                />
              </div>
            ))}
          </SectionCard>

          <div className="po-form-actions">
            <button className="po-btn po-btn--primary" type="submit" disabled={saving}>
              {saving ? "Salvando…" : "Salvar rascunho"}
            </button>
            <button
              className="po-btn po-btn--secondary"
              type="button"
              disabled={publishing}
              onClick={() => void handlePublish()}
            >
              {publishing ? "Publicando…" : "Publicar versão"}
            </button>
          </div>
        </form>
      ) : null}

      {draft ? (
        <SectionCard
          title="Documentos de apoio"
          hint="Upload multipart (máx. 25 MB). O caminho físico não é exposto ao cliente."
        >
          <form className="po-form" onSubmit={(e) => void handleUpload(e)}>
            <label>
              Arquivo
              <input
                type="file"
                disabled={uploadState === "uploading"}
                onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
              />
            </label>
            <label>
              Nome de exibição
              <input
                required
                value={displayName}
                disabled={uploadState === "uploading"}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            </label>
            <label>
              Descrição
              <input
                value={description}
                disabled={uploadState === "uploading"}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <label>
              Categoria
              <select
                value={documentKind}
                disabled={uploadState === "uploading"}
                onChange={(e) => setDocumentKind(e.target.value)}
              >
                {DOCUMENT_KIND_OPTIONS.filter((o) => o.value !== "external_link").map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Ordem
              <input
                type="number"
                min={0}
                value={displayOrder}
                disabled={uploadState === "uploading"}
                onChange={(e) => setDisplayOrder(Number(e.target.value) || 0)}
              />
            </label>
            {file ? (
              <p className="po-muted">
                Selecionado: {file.name} ({formatBytes(file.size)}) — estado: {uploadState}
              </p>
            ) : (
              <p className="po-muted">Nenhum arquivo selecionado.</p>
            )}
            {uploadState === "uploading" ? (
              <p className="po-muted">Enviando… {Math.round(uploadProgress * 100)}%</p>
            ) : null}
            {uploadMessage ? (
              <StateBox
                variant={uploadState === "error" ? "error" : "success"}
                dismissible={false}
              >
                {uploadMessage}
              </StateBox>
            ) : null}
            <button
              className="po-btn po-btn--primary"
              type="submit"
              disabled={uploadState === "uploading" || !file}
            >
              {uploadState === "uploading" ? "Enviando…" : "Enviar documento"}
            </button>
          </form>

          <ul className="po-link-list">
            {documents.length === 0 ? (
              <li className="po-muted">Nenhum documento neste rascunho.</li>
            ) : null}
            {documents.map((doc) => (
              <li key={doc.id}>
                <div>
                  <strong>{doc.display_name}</strong>
                  <span className="po-muted">
                    {" "}
                    · {doc.document_kind} · {formatBytes(doc.size_bytes)} ·{" "}
                    {doc.status === "archived" ? "arquivado" : "ativo"}
                  </span>
                </div>
                <div className="po-form-actions">
                  {doc.status !== "archived" ? (
                    <>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        onClick={() => void handleDownload(doc.id, doc.original_name || doc.display_name)}
                      >
                        Baixar
                      </button>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        onClick={() => void handleRename(doc)}
                      >
                        Metadados
                      </button>
                      <button
                        type="button"
                        className="po-btn po-btn--secondary"
                        onClick={() => void handleArchive(doc.id)}
                      >
                        Arquivar
                      </button>
                    </>
                  ) : (
                    <span className="po-muted">Arquivado</span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </SectionCard>
      ) : null}
    </PageShell>
  );
}
