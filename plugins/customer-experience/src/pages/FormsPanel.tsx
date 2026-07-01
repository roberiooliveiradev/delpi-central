import { useCallback, useEffect, useState } from "react";
import {
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardList,
  Copy,
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
  setQuestions as apiSetQuestions,
  updateForm,
} from "../api/formsApi";
import type {
  FormDashboard,
  FormDetail,
  FormQuestion,
  FormResponseList,
  FormSummary,
  QuestionType,
} from "../types";

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

type View = "list" | "editor" | "dashboard";

export function FormsPanel() {
  const [view, setView] = useState<View>("list");
  const [forms, setForms] = useState<FormSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [selected, setSelected] = useState<FormDetail | null>(null);

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

  const openEditor = async (id: string) => {
    setError(null);
    try {
      setSelected(await getForm(id));
      setView("editor");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir formulário.");
    }
  };

  const openDashboard = async (id: string) => {
    setError(null);
    try {
      setSelected(await getForm(id));
      setView("dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir dashboard.");
    }
  };

  const backToList = async () => {
    setSelected(null);
    setView("list");
    await load();
  };

  if (view === "editor" && selected) {
    return (
      <FormEditor
        form={selected}
        onBack={backToList}
        onSaved={(msg) => setFeedback(msg)}
      />
    );
  }

  if (view === "dashboard" && selected) {
    return <FormDashboardView form={selected} onBack={backToList} />;
  }

  return (
    <>
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
        onCreated={async (form) => {
          setSelected(form);
          setView("editor");
        }}
        onEdit={openEditor}
        onDashboard={openDashboard}
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
  onCreated,
  onEdit,
  onDashboard,
  onChanged,
  onError,
}: {
  forms: FormSummary[];
  loading: boolean;
  onCreated: (form: FormDetail) => void;
  onEdit: (id: string) => void;
  onDashboard: (id: string) => void;
  onChanged: (msg: string) => void;
  onError: (msg: string) => void;
}) {
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
    <div className="cx-layout">
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
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => onEdit(form.id)}>
                    <ClipboardList size={16} /> Perguntas
                  </button>
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => onDashboard(form.id)}>
                    <BarChart3 size={16} /> Respostas
                  </button>
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => downloadQr(form)}>
                    <QrCode size={16} /> QR
                  </button>
                  <button className="cx-button cx-button--ghost" type="button" onClick={() => copyLink(form)}>
                    <Copy size={16} /> Link
                  </button>
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

function FormEditor({
  form,
  onBack,
  onSaved,
}: {
  form: FormDetail;
  onBack: () => void;
  onSaved: (msg: string) => void;
}) {
  const [title, setTitle] = useState(form.title);
  const [description, setDescription] = useState(form.description ?? "");
  const [questions, setQuestions] = useState<FormQuestion[]>(form.questions);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Índice sendo arrastado (habilita `draggable` só ao segurar a alça, para não
  // atrapalhar a seleção de texto nos inputs) e o índice sob o cursor.
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [overIndex, setOverIndex] = useState<number | null>(null);

  const update = (index: number, patch: Partial<FormQuestion>) => {
    setQuestions((prev) => prev.map((q, i) => (i === index ? { ...q, ...patch } : q)));
  };

  const reorder = (from: number, to: number) => {
    setQuestions((prev) => {
      if (to < 0 || to >= prev.length || from === to) return prev;
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  };

  const move = (index: number, delta: number) => reorder(index, index + delta);

  const resetDrag = () => {
    setDragIndex(null);
    setOverIndex(null);
  };

  const addQuestion = () => setQuestions((prev) => [...prev, blankQuestion()]);
  const removeQuestion = (index: number) =>
    setQuestions((prev) => prev.filter((_, i) => i !== index));

  const changeType = (index: number, type: QuestionType) => {
    const needsOptions = CHOICE_TYPES.includes(type);
    update(index, {
      type,
      options: needsOptions && questions[index].options.length === 0
        ? ["", ""]
        : needsOptions
          ? questions[index].options
          : [],
    });
  };

  const setOption = (qi: number, oi: number, value: string) =>
    update(qi, {
      options: questions[qi].options.map((o, i) => (i === oi ? value : o)),
    });
  const addOption = (qi: number) => update(qi, { options: [...questions[qi].options, ""] });
  const removeOption = (qi: number, oi: number) =>
    update(qi, { options: questions[qi].options.filter((_, i) => i !== oi) });

  const handleSave = async () => {
    if (!title.trim()) {
      setError("Informe um título para o formulário.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updateForm(form.id, { title: title.trim(), description: description.trim() || null });
      const cleaned = questions.map((q) => ({
        ...q,
        options: CHOICE_TYPES.includes(q.type)
          ? q.options.map((o) => o.trim()).filter(Boolean)
          : [],
      }));
      await apiSetQuestions(form.id, cleaned);
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
        <button className="cx-button cx-button--primary" type="button" onClick={handleSave} disabled={saving}>
          <Save size={16} /> {saving ? "Salvando..." : "Salvar formulário"}
        </button>
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
      </section>

      <div className="cx-question-list">
        {questions.map((q, index) => (
          <section
            className={`cx-card cx-question${dragIndex === index ? " is-dragging" : ""}${
              overIndex === index && dragIndex !== null && dragIndex !== index ? " is-over" : ""
            }`}
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
              <span className="cx-question__num">{index + 1}</span>
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
        ))}
      </div>

      <button className="cx-button cx-button--dashed" type="button" onClick={addQuestion}>
        <Plus size={16} /> Adicionar pergunta
      </button>
    </div>
  );
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
