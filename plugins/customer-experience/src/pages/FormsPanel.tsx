import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Copy,
  Eye,
  FileText,
  GripVertical,
  Plus,
  Power,
  QrCode,
  Save,
  Trash2,
} from "lucide-react";
import {
  activateForm,
  createForm,
  deactivateForm,
  deleteForm,
  downloadFormQr,
  getDashboard,
  getForm,
  listForms,
  listResponses,
  removeFormBackground,
  removePageBackground,
  removePagePointImage,
  removeQuestionPointImage,
  setQuestions as apiSetQuestions,
  updateForm,
  uploadFormBackground,
  uploadPagePointImage,
  uploadQuestionPointImage,
} from "../api/formsApi";
import { PhotoDropzone } from "../components/PhotoDropzone";
import { FormPreviewModal } from "../components/FormPreviewModal";
import type {
  BackgroundFit,
  FormDashboard,
  FormDetail,
  FormPage,
  FormQuestion,
  FormResponseList,
  FormSummary,
  QuestionType,
} from "../types";
import {
  BACKGROUND_FIT_LABELS,
  BACKGROUND_FITS,
  normalizeBackgroundFit,
} from "../types";
import { useCxPermissions } from "../context/CxPermissionsContext";
import {
  formDashboardPath,
  formEditPath,
  formsListPath,
  type FormsView,
} from "../constants/routes";
import {
  buildEditorPreview,
  buildPreviewFormFromDetail,
  type PreviewForm,
} from "../utils/formPreviewModel";

const TYPE_LABELS: Record<QuestionType, string> = {
  rating: "Nota (estrelas 1–5)",
  short_text: "Texto curto",
  long_text: "Texto longo",
  single_choice: "Múltipla escolha (uma)",
  multi_choice: "Caixas de seleção (várias)",
  yes_no: "Sim / Não",
};

const CHOICE_TYPES: QuestionType[] = ["single_choice", "multi_choice"];

function blankQuestion(): FormQuestion {
  return { type: "rating", label: "", helpText: null, required: false, options: [] };
}

function blankPage(): FormPage {
  return { title: null, backgroundImageUrl: null, pointImageUrl: null };
}

function ensurePageCount(pages: FormPage[], count: number): FormPage[] {
  if (count <= 0) return [];
  if (pages.length >= count) return pages.slice(0, count);
  const extra = Array.from({ length: count - pages.length }, () => blankPage());
  return [...pages, ...extra];
}

type PendingImages = {
  formBackground?: File;
  pagePoint: Record<number, File>;
  questionPoint: Record<number, File>;
};

type RemovedImages = {
  pagePoint: Record<number, true>;
  questionPoint: Record<number, true>;
};

const EMPTY_REMOVED: RemovedImages = {
  pagePoint: {},
  questionPoint: {},
};

type View = FormsView;

export function FormsPanel({
  view,
  formId,
  onNavigate,
}: {
  view: View;
  formId?: string;
  onNavigate: (path: string) => void;
}) {
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingForm, setLoadingForm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [selected, setSelected] = useState<FormDetail | null>(null);
  const [previewForm, setPreviewForm] = useState<PreviewForm | null>(null);
  const [previewLoadingId, setPreviewLoadingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setForms(await listForms());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar formulários.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!feedback) return;
    const timer = window.setTimeout(() => setFeedback(null), 4000);
    return () => window.clearTimeout(timer);
  }, [feedback]);

  useEffect(() => {
    if (view === "list") {
      setSelected(null);
      return;
    }
    if (!formId) return;
    if (selected?.id === formId) return;

    let alive = true;
    setLoadingForm(true);
    setError(null);
    (async () => {
      try {
        const form = await getForm(formId);
        if (!alive) return;
        setSelected(form);
      } catch (err) {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "Erro ao carregar formulário.");
        setSelected(null);
      } finally {
        if (alive) setLoadingForm(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, [view, formId, selected?.id]);

  const openEditor = (id: string) => {
    onNavigate(formEditPath(id));
  };

  const openDashboard = (id: string) => {
    onNavigate(formDashboardPath(id));
  };

  const backToList = async () => {
    onNavigate(formsListPath());
    await load();
  };

  const openPreviewFromList = async (id: string) => {
    setPreviewLoadingId(id);
    setError(null);
    try {
      const detail = await getForm(id);
      setPreviewForm(buildPreviewFormFromDetail(detail));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir prévia.");
    } finally {
      setPreviewLoadingId(null);
    }
  };

  if (loadingForm && (view === "editor" || view === "dashboard")) {
    return <p className="cx-state">Carregando formulário...</p>;
  }

  const previewOverlay = previewForm ? (
    <FormPreviewModal form={previewForm} onClose={() => setPreviewForm(null)} />
  ) : null;

  if (view === "editor" && selected) {
    return (
      <>
        {previewOverlay}
        <FormEditor
          form={selected}
          onBack={backToList}
          onSaved={(msg) => setFeedback(msg)}
          onPreview={(model) => setPreviewForm(model)}
        />
      </>
    );
  }

  if (view === "dashboard" && selected) {
    return (
      <>
        {previewOverlay}
        <FormDashboardView form={selected} onBack={backToList} />
      </>
    );
  }

  if ((view === "editor" || view === "dashboard") && formId && !selected && !loadingForm) {
    return (
      <>
        {error && (
          <div className="cx-banner cx-banner--error" role="alert">
            {error}
          </div>
        )}
        <button className="cx-button cx-button--ghost" type="button" onClick={() => void backToList()}>
          <ArrowLeft size={16} /> Voltar para formulários
        </button>
      </>
    );
  }

  return (
    <>
      {previewOverlay}
      {feedback && (
        <div className="cx-banner cx-banner--success" role="status">
          <CheckCircle2 size={18} /> {feedback}
        </div>
      )}
      {error && (
        <div className="cx-banner cx-banner--error" role="alert">
          {error}
        </div>
      )}

      <FormsList
        forms={forms}
        loading={loading}
        previewLoadingId={previewLoadingId}
        onCreated={(form) => onNavigate(formEditPath(form.id))}
        onEdit={openEditor}
        onDashboard={openDashboard}
        onPreview={(id) => void openPreviewFromList(id)}
        onChanged={(msg) => {
          setFeedback(msg);
          void load();
        }}
        onError={setError}
      />
    </>
  );
}

// ----- Lista de formulários --------------------------------------------------

function FormsList({
  forms,
  loading,
  previewLoadingId,
  onCreated,
  onEdit,
  onDashboard,
  onPreview,
  onChanged,
  onError,
}: {
  forms: FormSummary[];
  loading: boolean;
  previewLoadingId: string | null;
  onCreated: (form: FormDetail) => void;
  onEdit: (id: string) => void;
  onDashboard: (id: string) => void;
  onPreview: (id: string) => void;
  onChanged: (msg: string) => void;
  onError: (msg: string) => void;
}) {
  const { canWriteForms, canManageForms } = useCxPermissions();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);

  const handleCreate = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!title.trim()) {
      onError("Informe um título para o formulário.");
      return;
    }
    setCreating(true);
    try {
      const form = await createForm({ title: title.trim(), description: description.trim() || undefined });
      setTitle("");
      setDescription("");
      onCreated(form);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao criar formulário.");
    } finally {
      setCreating(false);
    }
  };

  const copyLink = async (form: FormSummary) => {
    if (!form.publicUrl) return;
    try {
      await navigator.clipboard.writeText(form.publicUrl);
      onChanged("Link do formulário copiado.");
    } catch {
      onChanged(form.publicUrl);
    }
  };

  const downloadQr = async (form: FormSummary) => {
    try {
      const blob = await downloadFormQr(form.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `qr-form-${form.title.replace(/\s+/g, "-").toLowerCase()}.png`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao baixar QR code.");
    }
  };

  const togglePublish = async (form: FormSummary) => {
    try {
      if (form.isActive) {
        await deactivateForm(form.id);
        onChanged("Formulário despublicado.");
      } else {
        await activateForm(form.id);
        onChanged("Formulário publicado.");
      }
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao alterar publicação.");
    }
  };

  const remove = async (form: FormSummary) => {
    if (!window.confirm(`Excluir "${form.title}" e todas as respostas coletadas?`)) return;
    try {
      await deleteForm(form.id);
      onChanged("Formulário excluído.");
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao excluir formulário.");
    }
  };

  return (
    <div className={`cx-layout${canWriteForms ? "" : " cx-layout--list-only"}`}>
      {canWriteForms && (
      <section className="cx-card cx-form-card">
        <h2 className="cx-card__title">
          <Plus size={18} /> Novo formulário
        </h2>
        <form className="cx-form" onSubmit={handleCreate}>
          <label className="cx-field">
            <span>Título</span>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex.: Pesquisa de experiência da visita"
            />
          </label>
          <label className="cx-field">
            <span>Descrição (opcional)</span>
            <textarea
              rows={3}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Texto de abertura exibido ao visitante."
            />
          </label>
          <button className="cx-button cx-button--primary" type="submit" disabled={creating}>
            {creating ? "Criando..." : "Criar e editar perguntas"}
          </button>
        </form>
      </section>
      )}

      <section className="cx-card cx-list-card">
        <h2 className="cx-card__title">
          <FileText size={18} /> Formulários
          <span className="cx-count">{forms.length}</span>
        </h2>

        {loading ? (
          <p className="cx-state">Carregando formulários...</p>
        ) : forms.length === 0 ? (
          <p className="cx-state">Nenhum formulário criado ainda.</p>
        ) : (
          <ul className="cx-form-list">
            {forms.map((form) => (
              <li key={form.id} className="cx-form-item">
                <div className="cx-form-item__head">
                  <div>
                    <strong>{form.title}</strong>
                    {form.description && <p className="cx-form-item__desc">{form.description}</p>}
                  </div>
                  <span className={`cx-chip ${form.isActive ? "cx-chip--on" : "cx-chip--off"}`}>
                    {form.isActive ? "Publicado" : "Rascunho"}
                  </span>
                </div>
                <div className="cx-form-item__meta">
                  <span>{form.responseCount} resposta(s)</span>
                </div>
                <div className="cx-participant__actions">
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => onDashboard(form.id)}>
                    <BarChart3 size={16} /> Respostas
                  </button>
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => downloadQr(form)}>
                    <QrCode size={16} /> QR
                  </button>
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => copyLink(form)}>
                    <Copy size={16} /> Link
                  </button>
                  <button
                    className="cx-button cx-button--ghost"
                    type="button"
                    onClick={() => onPreview(form.id)}
                    disabled={previewLoadingId === form.id}
                  >
                    <Eye size={16} /> {previewLoadingId === form.id ? "Abrindo..." : "Prévia"}
                  </button>
                  {canWriteForms && (
                    <button className="cx-button cx-button--ghost" type="button" onClick={() => onEdit(form.id)}>
                      <ClipboardList size={16} /> Perguntas
                    </button>
                  )}
                  {canManageForms && (
                    <>
                      <button className="cx-button cx-button--ghost" type="button" onClick={() => togglePublish(form)}>
                        <Power size={16} /> {form.isActive ? "Despublicar" : "Publicar"}
                      </button>
                      <button
                        className="cx-button cx-button--danger-ghost"
                        type="button"
                        onClick={() => remove(form)}
                      >
                        <Trash2 size={16} /> Excluir
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

// ----- Editor de perguntas ---------------------------------------------------

function PageVisualFields({
  page,
  pageIndex,
  pendingImages,
  onUpdatePage,
  onPendingPoint,
  onClearPoint,
  mode = "page",
}: {
  page: FormPage;
  pageIndex: number;
  pendingImages: PendingImages;
  onUpdatePage: (index: number, patch: Partial<FormPage>) => void;
  onPendingPoint: (index: number, file: File) => void;
  onClearPoint: (index: number) => void;
  mode?: "page" | "step";
}) {
  const titleLabel = mode === "step" ? "Título da etapa (opcional)" : "Título da página (opcional)";
  return (
    <>
      <label className="cx-field">
        <span>{titleLabel}</span>
        <input
          type="text"
          value={page.title ?? ""}
          onChange={(e) => onUpdatePage(pageIndex, { title: e.target.value || null })}
          placeholder="Ex.: Percepção"
        />
      </label>
      <div className="cx-field">
        <span>Imagem ilustrativa</span>
        <PhotoDropzone
          previewUrl={
            pendingImages.pagePoint[pageIndex]
              ? URL.createObjectURL(pendingImages.pagePoint[pageIndex])
              : page.pointImageUrl ?? null
          }
          isExisting={Boolean(page.pointImageUrl && !pendingImages.pagePoint[pageIndex])}
          onSelect={(file) => onPendingPoint(pageIndex, file)}
          onClear={() => onClearPoint(pageIndex)}
        />
      </div>
    </>
  );
}

function FormEditor({
  form,
  onBack,
  onSaved,
  onPreview,
}: {
  form: FormDetail;
  onBack: () => void;
  onSaved: (msg: string) => void;
  onPreview: (model: PreviewForm) => void;
}) {
  const [title, setTitle] = useState(form.title);
  const [description, setDescription] = useState(form.description ?? "");
  const [oneQuestionPerPage, setOneQuestionPerPage] = useState(form.oneQuestionPerPage ?? false);
  const [backgroundFit, setBackgroundFit] = useState<BackgroundFit>(
    normalizeBackgroundFit(form.backgroundFit),
  );
  const [backgroundPreview, setBackgroundPreview] = useState<string | null>(
    form.backgroundImageUrl ?? null,
  );
  const [pages, setPages] = useState<FormPage[]>(() =>
    form.oneQuestionPerPage
      ? ensurePageCount(form.pages ?? [], form.questions.length)
      : form.pages ?? [],
  );
  const [questions, setQuestions] = useState<FormQuestion[]>(form.questions);
  const [pendingImages, setPendingImages] = useState<PendingImages>({
    pagePoint: {},
    questionPoint: {},
  });
  const [removedImages, setRemovedImages] = useState<RemovedImages>(EMPTY_REMOVED);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);

  useEffect(() => {
    if (!oneQuestionPerPage) return;
    setPages((prev) => ensurePageCount(prev, questions.length));
  }, [oneQuestionPerPage, questions.length]);

  const update = (index: number, patch: Partial<FormQuestion>) => {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  };

  const resolvePageIndex = (q: FormQuestion) => {
    if (q.pageIndex != null) return q.pageIndex;
    if (!q.pageId) return -1;
    return pages.findIndex((p) => p.id === q.pageId);
  };

  const updatePage = (index: number, patch: Partial<FormPage>) => {
    setPages((prev) => {
      const next = prev.map((p, i) => (i === index ? { ...p, ...patch } : p));
      return oneQuestionPerPage ? ensurePageCount(next, questions.length) : next;
    });
  };

  const setPendingPagePoint = (index: number, file: File) => {
    setRemovedImages((prev) => {
      const next = { ...prev.pagePoint };
      delete next[index];
      return { ...prev, pagePoint: next };
    });
    setPendingImages((prev) => ({
      ...prev,
      pagePoint: { ...prev.pagePoint, [index]: file },
    }));
  };

  const clearPendingPagePoint = (index: number) => {
    setPages((prev) => {
      const page = prev[index];
      if (page?.id && page.pointImageUrl) {
        setRemovedImages((r) => ({
          ...r,
          pagePoint: { ...r.pagePoint, [index]: true },
        }));
      }
      return prev.map((p, i) => (i === index ? { ...p, pointImageUrl: null } : p));
    });
    setPendingImages((prev) => {
      const next = { ...prev.pagePoint };
      delete next[index];
      return { ...prev, pagePoint: next };
    });
  };

  const setQuestionPageIndex = (qIndex: number, pageIndex: number | null) => {
    update(qIndex, {
      pageId: pageIndex != null && pageIndex >= 0 ? pages[pageIndex]?.id ?? null : null,
      pageIndex,
    });
  };

  const reorder = (from: number, to: number) => {
    setQuestions((prev) => {
      if (to < 0 || to >= prev.length || from === to) return prev;
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
    if (oneQuestionPerPage) {
      setPages((prev) => {
        if (to < 0 || to >= prev.length || from === to) return prev;
        const next = [...prev];
        const [moved] = next.splice(from, 1);
        next.splice(to, 0, moved);
        return next;
      });
    }
  };

  const move = (index: number, delta: number) => reorder(index, index + delta);

  const resetDrag = () => {
    setDragIndex(null);
    setOverIndex(null);
  };

  const addQuestion = () => {
    setQuestions((prev) => {
      const next = [...prev, blankQuestion()];
      if (oneQuestionPerPage) {
        setPages((p) => ensurePageCount(p, next.length));
      }
      return next;
    });
  };

  const removeQuestion = (index: number) => {
    setQuestions((prev) => {
      const next = prev.filter((_, i) => i !== index);
      if (oneQuestionPerPage) {
        setPages((p) => ensurePageCount(p.filter((_, i) => i !== index), next.length));
      }
      return next;
    });
  };

  const addPage = () => setPages((prev) => [...prev, blankPage()]);

  const removePage = (index: number) => {
    const pageId = pages[index]?.id;
    setPages((prev) => prev.filter((_, i) => i !== index));
    if (pageId) {
      setQuestions((prev) =>
        prev.map((q) => (q.pageId === pageId ? { ...q, pageId: null } : q)),
      );
    }
  };

  const handleFormBackground = (file: File) => {
    setPendingImages((prev) => ({ ...prev, formBackground: file }));
    setBackgroundPreview(URL.createObjectURL(file));
  };

  const clearFormBackground = () => {
    setPendingImages((prev) => ({ ...prev, formBackground: undefined }));
    setBackgroundPreview(null);
  };

  const setPendingQuestionPoint = (index: number, file: File) => {
    setRemovedImages((prev) => {
      const next = { ...prev.questionPoint };
      delete next[index];
      return { ...prev, questionPoint: next };
    });
    setPendingImages((prev) => ({
      ...prev,
      questionPoint: { ...prev.questionPoint, [index]: file },
    }));
  };

  const clearPendingQuestionPoint = (index: number) => {
    const question = questions[index];
    if (question?.id && question.pointImageUrl) {
      setRemovedImages((r) => ({
        ...r,
        questionPoint: { ...r.questionPoint, [index]: true },
      }));
    }
    update(index, { pointImageUrl: null });
    setPendingImages((prev) => {
      const next = { ...prev.questionPoint };
      delete next[index];
      return { ...prev, questionPoint: next };
    });
  };

  const handleSave = async () => {
    if (!title.trim()) {
      setError("Informe um título para o formulário.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateForm(form.id, {
        title: title.trim(),
        description: description.trim() || null,
        oneQuestionPerPage,
        backgroundFit,
      });

      const pagesPayload = oneQuestionPerPage ? ensurePageCount(pages, questions.length) : pages;

      const cleaned = questions.map((q) => ({
        ...q,
        pageIndex: resolvePageIndex(q) >= 0 ? resolvePageIndex(q) : q.pageIndex ?? null,
        options: CHOICE_TYPES.includes(q.type)
          ? q.options.map((o) => o.trim()).filter(Boolean)
          : [],
      }));

      let saved = await apiSetQuestions(form.id, {
        questions: cleaned,
        pages: pagesPayload,
        oneQuestionPerPage,
      });

      if (pendingImages.formBackground) {
        saved = await uploadFormBackground(form.id, pendingImages.formBackground);
      } else if (!backgroundPreview && form.backgroundImageUrl) {
        saved = await removeFormBackground(form.id);
      }

      for (const [indexStr, mark] of Object.entries(removedImages.pagePoint)) {
        if (!mark || pendingImages.pagePoint[Number(indexStr)]) continue;
        const pageId = saved.pages[Number(indexStr)]?.id;
        if (pageId) saved = await removePagePointImage(form.id, pageId);
      }
      for (const [indexStr, mark] of Object.entries(removedImages.questionPoint)) {
        if (!mark || pendingImages.questionPoint[Number(indexStr)]) continue;
        const questionId = saved.questions[Number(indexStr)]?.id;
        if (questionId) saved = await removeQuestionPointImage(form.id, questionId);
      }

      // Fundos por página/etapa deixaram de existir no editor — limpa restos legados.
      for (const page of saved.pages ?? []) {
        if (page.backgroundImageUrl && page.id) {
          saved = await removePageBackground(form.id, page.id);
        }
      }

      for (const [indexStr, file] of Object.entries(pendingImages.pagePoint)) {
        const pageId = saved.pages[Number(indexStr)]?.id;
        if (pageId) saved = await uploadPagePointImage(form.id, pageId, file);
      }
      for (const [indexStr, file] of Object.entries(pendingImages.questionPoint)) {
        const questionId = saved.questions[Number(indexStr)]?.id;
        if (questionId) saved = await uploadQuestionPointImage(form.id, questionId, file);
      }

      onSaved("Formulário salvo.");
      onBack();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar formulário.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="cx-editor">
      <div className="cx-editor__bar">
        <button className="cx-button cx-button--ghost" type="button" onClick={onBack}>
          <ArrowLeft size={16} /> Voltar
        </button>
        <div className="cx-editor__bar-actions">
          <button
            className="cx-button cx-button--ghost"
            type="button"
            onClick={() =>
              onPreview(
                buildEditorPreview({
                  publicToken: form.publicToken,
                  title,
                  description,
                  oneQuestionPerPage,
                  backgroundFit,
                  backgroundPreview,
                  pages,
                  questions,
                  pendingImages,
                }),
              )
            }
          >
            <Eye size={16} /> Prévia
          </button>
          <button className="cx-button cx-button--primary" type="button" onClick={handleSave} disabled={saving}>
            <Save size={16} /> {saving ? "Salvando..." : "Salvar formulário"}
          </button>
        </div>
      </div>

      {error && (
        <div className="cx-banner cx-banner--error" role="alert">
          {error}
        </div>
      )}

      <section className="cx-card">
        <label className="cx-field">
          <span>Título do formulário</span>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label className="cx-field">
          <span>Descrição (opcional)</span>
          <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
        </label>
        <label className="cx-check">
          <input
            type="checkbox"
            checked={oneQuestionPerPage}
            onChange={(e) => {
              const enabled = e.target.checked;
              setOneQuestionPerPage(enabled);
              if (enabled) {
                setPages((prev) => ensurePageCount(prev, questions.length));
              }
            }}
          />
          <span>Uma pergunta por página (modo passo a passo com barra de progresso)</span>
        </label>
        <div className="cx-field">
          <span className="cx-field__label">Imagem de fundo do formulário</span>
          <PhotoDropzone
            previewUrl={backgroundPreview}
            isExisting={Boolean(form.backgroundImageUrl && !pendingImages.formBackground)}
            onSelect={handleFormBackground}
            onClear={clearFormBackground}
          />
        </div>
        {(backgroundPreview || form.backgroundImageUrl) && (
          <label className="cx-field">
            <span>Exibição do fundo</span>
            <select
              className="cx-select"
              value={backgroundFit}
              onChange={(e) => setBackgroundFit(normalizeBackgroundFit(e.target.value))}
            >
              {BACKGROUND_FITS.map((fit) => (
                <option key={fit} value={fit}>
                  {BACKGROUND_FIT_LABELS[fit]}
                </option>
              ))}
            </select>
            <span className="cx-field-hint">
              Fixo mantém o tamanho original; escalável preenche a tela; repetir monta um mosaico.
            </span>
          </label>
        )}
      </section>

      {!oneQuestionPerPage && (
      <section className="cx-card">
        <div className="cx-card__title-row">
          <h2 className="cx-card__title">Páginas do formulário</h2>
          <button className="cx-button cx-button--ghost" type="button" onClick={addPage}>
            <Plus size={14} /> Adicionar página
          </button>
        </div>
        <p className="cx-field-hint">
          Agrupe perguntas em páginas com título e imagem ilustrativa. Deixe vazio para um
          formulário contínuo em uma única tela. O fundo geral fica em «Imagem de fundo do
          formulário».
        </p>
        {pages.length === 0 ? (
          <p className="cx-state">Nenhuma página — todas as perguntas aparecem juntas.</p>
        ) : (
          <div className="cx-page-list">
            {pages.map((page, pageIndex) => (
              <div className="cx-page-block" key={pageIndex}>
                <div className="cx-page-block__head">
                  <strong>Página {pageIndex + 1}</strong>
                  <button
                    className="cx-icon-btn cx-icon-btn--danger"
                    type="button"
                    onClick={() => removePage(pageIndex)}
                    title="Remover página"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <PageVisualFields
                  page={page}
                  pageIndex={pageIndex}
                  pendingImages={pendingImages}
                  onUpdatePage={updatePage}
                  onPendingPoint={setPendingPagePoint}
                  onClearPoint={clearPendingPagePoint}
                />
              </div>
            ))}
          </div>
        )}
      </section>
      )}

      <div className="cx-question-list">
        {oneQuestionPerPage && questions.length > 0 && (
          <p className="cx-field-hint cx-question-list__hint">
            Cada pergunta abaixo é uma etapa do passo a passo. Use arrastar ou as setas para
            reordenar — título e imagem ilustrativa ficam no próprio card.
          </p>
        )}
        {questions.map((q, index) => {
          const stepPage = oneQuestionPerPage
            ? ensurePageCount(pages, questions.length)[index] ?? blankPage()
            : null;
          return (
          <section
            className={`cx-card cx-question${oneQuestionPerPage ? " cx-question--step" : ""}${
              dragIndex === index ? " is-dragging" : ""
            }${overIndex === index && dragIndex !== null && dragIndex !== index ? " is-over" : ""}`}
            key={index}
            draggable={dragIndex === index}
            onDragStart={(e) => {
              e.dataTransfer.effectAllowed = "move";
            }}
            onDragOver={(e) => {
              if (dragIndex === null) return;
              e.preventDefault();
              if (overIndex !== index) setOverIndex(index);
            }}
            onDrop={(e) => {
              e.preventDefault();
              if (dragIndex !== null) reorder(dragIndex, index);
              resetDrag();
            }}
            onDragEnd={resetDrag}
          >
            <div className="cx-question__head">
              <span
                className="cx-drag"
                title="Arraste para reordenar"
                aria-label="Arraste para reordenar a pergunta"
                onMouseDown={() => setDragIndex(index)}
                onMouseUp={resetDrag}
              >
                <GripVertical size={16} />
              </span>
              <span className="cx-question__num">
                {oneQuestionPerPage ? `Etapa ${index + 1}` : index + 1}
              </span>
              <select
                className="cx-select"
                value={q.type}
                onChange={(e) => changeType(index, e.target.value as QuestionType)}
              >
                {(Object.keys(TYPE_LABELS) as QuestionType[]).map((t) => (
                  <option key={t} value={t}>
                    {TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
              <div className="cx-question__move">
                <button
                  className="cx-icon-btn"
                  type="button"
                  onClick={() => move(index, -1)}
                  disabled={index === 0}
                  title="Mover para cima"
                >
                  <ChevronUp size={16} />
                </button>
                <button
                  className="cx-icon-btn"
                  type="button"
                  onClick={() => move(index, 1)}
                  disabled={index === questions.length - 1}
                  title="Mover para baixo"
                >
                  <ChevronDown size={16} />
                </button>
                <button className="cx-icon-btn cx-icon-btn--danger" type="button" onClick={() => removeQuestion(index)} title="Remover">
                  <Trash2 size={16} />
                </button>
              </div>
            </div>

            {oneQuestionPerPage && stepPage && (
              <div className="cx-page-visual">
                <span className="cx-page-visual__label">Visual da etapa</span>
                <PageVisualFields
                  page={stepPage}
                  pageIndex={index}
                  mode="step"
                  pendingImages={pendingImages}
                  onUpdatePage={updatePage}
                  onPendingPoint={setPendingPagePoint}
                  onClearPoint={clearPendingPagePoint}
                />
              </div>
            )}

            {!oneQuestionPerPage && pages.length > 0 && (
              <label className="cx-field">
                <span>Página</span>
                <select
                  className="cx-select"
                  value={resolvePageIndex(q) >= 0 ? String(resolvePageIndex(q)) : ""}
                  onChange={(e) => {
                    const raw = e.target.value;
                    setQuestionPageIndex(
                      index,
                      raw === "" ? null : Number(raw),
                    );
                  }}
                >
                  <option value="">Sem página (formulário contínuo)</option>
                  {pages.map((p, pi) => (
                    <option key={p.id ?? pi} value={String(pi)}>
                      {p.title || `Página ${pi + 1}`}
                    </option>
                  ))}
                </select>
              </label>
            )}

            <label className="cx-field">
              <span>Enunciado</span>
              <input
                type="text"
                value={q.label}
                onChange={(e) => update(index, { label: e.target.value })}
                placeholder="Ex.: Qual sua nota para a visita?"
              />
            </label>

            <label className="cx-field">
              <span>Texto de ajuda (opcional)</span>
              <input
                type="text"
                value={q.helpText ?? ""}
                onChange={(e) => update(index, { helpText: e.target.value || null })}
                placeholder="Instrução curta exibida abaixo do enunciado."
              />
            </label>

            {!oneQuestionPerPage && (
              <div className="cx-field">
                <span className="cx-field__label">Imagem ilustrativa da pergunta</span>
                <PhotoDropzone
                  previewUrl={
                    pendingImages.questionPoint[index]
                      ? URL.createObjectURL(pendingImages.questionPoint[index])
                      : q.pointImageUrl ?? null
                  }
                  isExisting={Boolean(q.pointImageUrl && !pendingImages.questionPoint[index])}
                  onSelect={(file) => setPendingQuestionPoint(index, file)}
                  onClear={() => clearPendingQuestionPoint(index)}
                />
              </div>
            )}

            {CHOICE_TYPES.includes(q.type) && (
              <div className="cx-field">
                <span className="cx-field__label">Opções</span>
                <div className="cx-options-edit">
                  {q.options.map((opt, oi) => (
                    <div className="cx-option-row" key={oi}>
                      <input
                        type="text"
                        value={opt}
                        onChange={(e) => setOption(index, oi, e.target.value)}
                        placeholder={`Opção ${oi + 1}`}
                      />
                      <button
                        className="cx-icon-btn cx-icon-btn--danger"
                        type="button"
                        onClick={() => removeOption(index, oi)}
                        title="Remover opção"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  ))}
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => addOption(index)}>
                    <Plus size={14} /> Adicionar opção
                  </button>
                </div>
              </div>
            )}

            <label className="cx-check">
              <input
                type="checkbox"
                checked={q.required}
                onChange={(e) => update(index, { required: e.target.checked })}
              />
              <span>Resposta obrigatória</span>
            </label>
          </section>
          );
        })}
      </div>

      <button className="cx-button cx-button--dashed" type="button" onClick={addQuestion}>
        <Plus size={16} /> Adicionar pergunta
      </button>
    </div>
  );

  function changeType(index: number, type: QuestionType) {
    const needsOptions = CHOICE_TYPES.includes(type);
    update(index, {
      type,
      options: needsOptions && questions[index].options.length === 0
        ? ["", ""]
        : needsOptions
          ? questions[index].options
          : [],
    });
  }

  function setOption(qi: number, oi: number, value: string) {
    update(qi, {
      options: questions[qi].options.map((o, i) => (i === oi ? value : o)),
    });
  }

  function addOption(qi: number) {
    update(qi, { options: [...questions[qi].options, ""] });
  }

  function removeOption(qi: number, oi: number) {
    update(qi, { options: questions[qi].options.filter((_, i) => i !== oi) });
  }
}

// ----- Dashboard / respostas -------------------------------------------------

function FormDashboardView({ form, onBack }: { form: FormDetail; onBack: () => void }) {
  const [dashboard, setDashboard] = useState<FormDashboard | null>(null);
  const [responses, setResponses] = useState<FormResponseList | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"summary" | "responses">("summary");

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [d, r] = await Promise.all([
          getDashboard(form.id),
          listResponses(form.id, { limit: 200 }),
        ]);
        if (!alive) return;
        setDashboard(d);
        setResponses(r);
      } catch (err) {
        if (alive) setError(err instanceof Error ? err.message : "Erro ao carregar dados.");
      }
    })();
    return () => {
      alive = false;
    };
  }, [form.id]);

  return (
    <div className="cx-editor">
      <div className="cx-editor__bar">
        <button className="cx-button cx-button--ghost" type="button" onClick={onBack}>
          <ArrowLeft size={16} /> Voltar
        </button>
        <div className="cx-subtabs">
          <button
            className={`cx-subtab ${tab === "summary" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("summary")}
          >
            Resumo
          </button>
          <button
            className={`cx-subtab ${tab === "responses" ? "is-active" : ""}`}
            type="button"
            onClick={() => setTab("responses")}
          >
            Respostas
          </button>
        </div>
      </div>

      {error && (
        <div className="cx-banner cx-banner--error" role="alert">
          {error}
        </div>
      )}

      <section className="cx-card">
        <h2 className="cx-card__title">
          <BarChart3 size={18} /> {form.title}
        </h2>
        <p className="cx-dash-total">
          <strong>{dashboard?.totalResponses ?? 0}</strong> resposta(s) recebida(s)
        </p>
      </section>

      {tab === "summary" ? (
        <div className="cx-dash-grid">
          {(dashboard?.questions ?? []).map((q) => (
            <section className="cx-card cx-dash-q" key={q.id}>
              <h3 className="cx-dash-q__title">
                {q.label}
                {!q.active && <span className="cx-chip cx-chip--off">removida</span>}
              </h3>
              <span className="cx-dash-q__sub">{q.answered} resposta(s)</span>
              {q.type === "rating" && <RatingSummary q={q} />}
              {(q.optionCounts && (
                <ChoiceSummary counts={q.optionCounts} total={q.answered} />
              )) ||
                null}
              {q.samples && <TextSummary samples={q.samples} />}
            </section>
          ))}
          {dashboard && dashboard.questions.length === 0 && (
            <p className="cx-state">Este formulário ainda não tem perguntas.</p>
          )}
        </div>
      ) : (
        <ResponsesTable responses={responses} />
      )}
    </div>
  );
}

function RatingSummary({ q }: { q: { average?: number | null; distribution?: Record<string, number> } }) {
  const dist = q.distribution ?? {};
  const max = Math.max(1, ...Object.values(dist));
  return (
    <div className="cx-rating-summary">
      <div className="cx-rating-avg">
        <strong>{q.average ?? "—"}</strong> <span>média</span>
      </div>
      <div className="cx-bars">
        {[5, 4, 3, 2, 1].map((n) => (
          <div className="cx-bar-row" key={n}>
            <span className="cx-bar-label">{n}★</span>
            <div className="cx-bar-track">
              <div className="cx-bar-fill" style={{ width: `${((dist[String(n)] ?? 0) / max) * 100}%` }} />
            </div>
            <span className="cx-bar-value">{dist[String(n)] ?? 0}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ChoiceSummary({ counts, total }: { counts: Record<string, number>; total: number }) {
  const max = Math.max(1, ...Object.values(counts));
  return (
    <div className="cx-bars">
      {Object.entries(counts).map(([opt, n]) => (
        <div className="cx-bar-row" key={opt}>
          <span className="cx-bar-label cx-bar-label--wide">{opt}</span>
          <div className="cx-bar-track">
            <div className="cx-bar-fill" style={{ width: `${(n / max) * 100}%` }} />
          </div>
          <span className="cx-bar-value">
            {n}
            {total > 0 ? ` (${Math.round((n / total) * 100)}%)` : ""}
          </span>
        </div>
      ))}
    </div>
  );
}

function TextSummary({ samples }: { samples: string[] }) {
  if (samples.length === 0) return <p className="cx-dash-empty">Sem respostas de texto.</p>;
  return (
    <ul className="cx-text-samples">
      {samples.map((s, i) => (
        <li key={i}>“{s}”</li>
      ))}
    </ul>
  );
}

function ResponsesTable({ responses }: { responses: FormResponseList | null }) {
  if (!responses) return <p className="cx-state">Carregando respostas...</p>;
  if (responses.items.length === 0)
    return <p className="cx-state">Nenhuma resposta recebida ainda.</p>;

  return (
    <div className="cx-responses">
      {responses.items.map((r) => (
        <section className="cx-card cx-response" key={r.id}>
          <div className="cx-response__head">
            <strong>{r.respondentName}</strong>
            {r.respondentCompany && <span> · {r.respondentCompany}</span>}
            <span className="cx-response__date">{new Date(r.createdAt).toLocaleString("pt-BR")}</span>
          </div>
          <dl className="cx-response__answers">
            {r.answers.map((a) => (
              <div className="cx-response__answer" key={a.questionId}>
                <dt>{a.label ?? "Pergunta removida"}</dt>
                <dd>{formatValue(a.value)}</dd>
              </div>
            ))}
          </dl>
        </section>
      ))}
    </div>
  );
}

function formatValue(value: string | number | string[] | null): string {
  if (value == null) return "—";
  if (Array.isArray(value)) return value.join(", ");
  return String(value);
}
