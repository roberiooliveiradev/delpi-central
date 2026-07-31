import { useEffect, useState } from "react";
import {
  ActionButton,
  BackLink,
  FieldLabel,
  FormSelectControl,
  NativeTextAreaControl,
  NativeTextControl,
} from "@delpi/plugin-ui/index";
import { ArrowDown, ArrowUp, Plus, Trash2 } from "lucide-react";

import {
  applySipatTemplate,
  createSipatSurvey,
  getSipatSurvey,
  listSipatSurveys,
  publishSipatSurvey,
  updateSipatSurvey,
  type SipatQuestion,
  type SipatQuestionType,
  type SipatTemplate,
} from "../api/cipaApi";
import { SIPAT_QUESTION_TYPE_LABELS, UNIT_LABELS } from "../constants/labels";
import { navigateCipa } from "../hooks/useCipaRouterPath";
import type { CipaUnitCode } from "../security/cipaAccess";
import {
  CipaContentCard,
  CipaFormActions,
  CipaPageHeader,
  CipaPageNotices,
  CipaSectionCard,
  CipaStateBanner,
} from "../ui/cipaUi";

type Props = {
  unitCode: CipaUnitCode;
  surveyId?: string;
};

type DraftQuestion = SipatQuestion & { key: string };

const TYPE_OPTIONS = Object.entries(SIPAT_QUESTION_TYPE_LABELS).map(([value, label]) => ({
  value,
  label,
}));

function newKey() {
  return `q-${Math.random().toString(36).slice(2, 10)}`;
}

function emptyQuestion(): DraftQuestion {
  return {
    key: newKey(),
    question_type: "yes_no",
    label: "",
    help_text: "",
    is_required: true,
    options: ["Sim", "Não"],
  };
}

function normalizeOptionsForType(
  type: SipatQuestionType,
  options: string[] | null | undefined,
): string[] | null {
  if (type === "single_choice" || type === "multi_choice") {
    return options && options.length >= 2 ? options : ["Opção 1", "Opção 2"];
  }
  if (type === "likert_5") return ["1", "2", "3", "4", "5"];
  if (type === "yes_no") return ["Sim", "Não"];
  return null;
}

export function SipatWizardPage({ unitCode, surveyId }: Props) {
  const [step, setStep] = useState(1);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [questions, setQuestions] = useState<DraftQuestion[]>([emptyQuestion()]);
  const [templates, setTemplates] = useState<SipatTemplate[]>([]);
  const [currentId, setCurrentId] = useState<string | undefined>(surveyId);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [publicUrl, setPublicUrl] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    listSipatSurveys(unitCode, controller.signal)
      .then((data) => setTemplates(data.templates))
      .catch(() => undefined);
    return () => controller.abort();
  }, [unitCode]);

  useEffect(() => {
    if (!surveyId) return;
    const controller = new AbortController();
    getSipatSurvey(surveyId, controller.signal)
      .then((detail) => {
        setTitle(detail.survey.title);
        setDescription(detail.survey.description || "");
        setCurrentId(detail.survey.id);
        setQuestions(
          detail.questions.map((item) => ({
            ...item,
            key: item.id || newKey(),
            question_type: item.question_type as SipatQuestionType,
          })),
        );
        setPublicUrl(detail.survey.public_url || null);
      })
      .catch((err) => {
        if (err instanceof DOMException && err.name === "AbortError") return;
        setError(err instanceof Error ? err.message : "Erro ao carregar pesquisa.");
      });
    return () => controller.abort();
  }, [surveyId]);

  const updateQuestion = (key: string, patch: Partial<DraftQuestion>) => {
    setQuestions((prev) =>
      prev.map((item) => {
        if (item.key !== key) return item;
        const next = { ...item, ...patch };
        if (patch.question_type) {
          next.options = normalizeOptionsForType(patch.question_type, next.options);
        }
        return next;
      }),
    );
  };

  const moveQuestion = (index: number, delta: number) => {
    setQuestions((prev) => {
      const next = [...prev];
      const target = index + delta;
      if (target < 0 || target >= next.length) return prev;
      const tmp = next[index];
      next[index] = next[target];
      next[target] = tmp;
      return next;
    });
  };

  const payloadQuestions = () =>
    questions.map((item, index) => ({
      question_type: item.question_type,
      label: item.label,
      help_text: item.help_text || null,
      is_required: Boolean(item.is_required),
      options: normalizeOptionsForType(item.question_type, item.options),
      position: index,
    }));

  const saveDraft = async () => {
    setSaving(true);
    setError(null);
    try {
      if (!title.trim()) throw new Error("Informe o título da pesquisa.");
      if (questions.some((q) => !q.label.trim())) {
        throw new Error("Todas as perguntas precisam de enunciado.");
      }
      const body = {
        unit_code: unitCode,
        title: title.trim(),
        description: description.trim() || null,
        questions: payloadQuestions(),
      };
      const detail = currentId
        ? await updateSipatSurvey(currentId, body)
        : await createSipatSurvey(body);
      setCurrentId(detail.survey.id);
      setSuccess("Rascunho salvo.");
      setStep(3);
      return detail.survey.id;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
      return null;
    } finally {
      setSaving(false);
    }
  };

  const applyTemplate = async (templateId: string) => {
    setSaving(true);
    setError(null);
    try {
      let id = currentId;
      if (!id) {
        const created = await createSipatSurvey({
          unit_code: unitCode,
          title: title.trim() || "Nova pesquisa SIPAT",
          description: description.trim() || null,
          template_id: templateId,
        });
        id = created.survey.id;
        setCurrentId(id);
        setTitle(created.survey.title);
        setDescription(created.survey.description || "");
        setQuestions(
          created.questions.map((item) => ({
            ...item,
            key: item.id || newKey(),
            question_type: item.question_type as SipatQuestionType,
          })),
        );
      } else {
        const applied = await applySipatTemplate(id, templateId);
        setTitle(applied.survey.title);
        setDescription(applied.survey.description || "");
        setQuestions(
          applied.questions.map((item) => ({
            ...item,
            key: item.id || newKey(),
            question_type: item.question_type as SipatQuestionType,
          })),
        );
      }
      setSuccess("Template aplicado. Revise as perguntas.");
      setStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao aplicar template.");
    } finally {
      setSaving(false);
    }
  };

  const publish = async () => {
    const id = (await saveDraft()) || currentId;
    if (!id) return;
    setSaving(true);
    try {
      const detail = await publishSipatSurvey(id);
      setPublicUrl(detail.survey.public_url || null);
      setSuccess("Pesquisa publicada. Compartilhe o link ou baixe o QR.");
      setStep(4);
      navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao publicar.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="cipa-page-stack">
      <CipaPageHeader
        nav={
          <BackLink
            variant="prominent"
            onClick={() => navigateCipa(`/apps/cipa/filial-${unitCode}/sipat`)}
          >
            SIPAT
          </BackLink>
        }
        title={surveyId ? "Editar pesquisa SIPAT" : "Nova pesquisa SIPAT"}
        subtitle={`${UNIT_LABELS[unitCode]} · passo ${step} de 4`}
      />

      <CipaPageNotices>
        {error ? <CipaStateBanner variant="error">{error}</CipaStateBanner> : null}
        {success ? <CipaStateBanner variant="success">{success}</CipaStateBanner> : null}
      </CipaPageNotices>

      {step === 1 ? (
        <CipaSectionCard title="Dados da pesquisa">
          <div className="cipa-sipat-wizard-basics">
            <div className="cipa-sipat-wizard-basics__fields">
              <div className="cipa-field">
                <FieldLabel label="Título" htmlFor="sipat-title" />
                <NativeTextControl id="sipat-title" value={title} onChange={setTitle} />
              </div>
              <div className="cipa-field">
                <FieldLabel label="Descrição" htmlFor="sipat-description" />
                <NativeTextAreaControl
                  id="sipat-description"
                  value={description}
                  onChange={setDescription}
                  rows={4}
                />
              </div>
            </div>

            {templates.length > 0 ? (
              <aside className="cipa-sipat-wizard-templates" aria-label="Templates">
                <header className="cipa-sipat-wizard-templates__head">
                  <span>Começar com template</span>
                  <p>Preenche título, descrição e perguntas. Você revisa no próximo passo.</p>
                </header>
                <div className="cipa-sipat-wizard-templates__list">
                  {templates.map((tpl) => (
                    <button
                      key={tpl.id}
                      type="button"
                      className="cipa-sipat-wizard-template"
                      disabled={saving}
                      onClick={() => void applyTemplate(tpl.id)}
                    >
                      <strong>{tpl.title}</strong>
                      {tpl.description ? <span>{tpl.description}</span> : null}
                      <em>
                        {tpl.question_count} pergunta
                        {tpl.question_count === 1 ? "" : "s"}
                      </em>
                    </button>
                  ))}
                </div>
              </aside>
            ) : null}
          </div>

          <CipaFormActions>
            <ActionButton variant="primary" onClick={() => setStep(2)}>
              Continuar para perguntas
            </ActionButton>
          </CipaFormActions>
        </CipaSectionCard>
      ) : null}

      {step === 2 ? (
        <CipaSectionCard title="Perguntas">
          {questions.map((question, index) => (
            <CipaContentCard key={question.key}>
              <div className="cipa-field">
                <FieldLabel label={`Pergunta ${index + 1}`} htmlFor={`sipat-q-${question.key}`} />
                <NativeTextControl
                  id={`sipat-q-${question.key}`}
                  value={question.label}
                  onChange={(value) => updateQuestion(question.key, { label: value })}
                />
              </div>
              <div className="cipa-field">
                <FieldLabel label="Tipo de resposta" htmlFor={`sipat-type-${question.key}`} />
                <FormSelectControl
                  id={`sipat-type-${question.key}`}
                  value={question.question_type}
                  onChange={(value) =>
                    updateQuestion(question.key, {
                      question_type: value as SipatQuestionType,
                    })
                  }
                  portalScopeClassName="dashboard-cipa"
                  options={TYPE_OPTIONS}
                />
              </div>
              <div className="cipa-field">
                <FieldLabel
                  label="Texto de ajuda (opcional)"
                  htmlFor={`sipat-help-${question.key}`}
                />
                <NativeTextControl
                  id={`sipat-help-${question.key}`}
                  value={question.help_text || ""}
                  onChange={(value) => updateQuestion(question.key, { help_text: value })}
                />
              </div>
              {question.question_type === "single_choice" ||
              question.question_type === "multi_choice" ? (
                <div className="cipa-field">
                  <FieldLabel
                    label="Opções (uma por linha)"
                    htmlFor={`sipat-opts-${question.key}`}
                  />
                  <NativeTextAreaControl
                    id={`sipat-opts-${question.key}`}
                    rows={4}
                    value={(question.options || []).join("\n")}
                    onChange={(value) =>
                      updateQuestion(question.key, {
                        options: value
                          .split("\n")
                          .map((line) => line.trim())
                          .filter(Boolean),
                      })
                    }
                  />
                </div>
              ) : null}
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(question.is_required)}
                  onChange={(e) =>
                    updateQuestion(question.key, { is_required: e.target.checked })
                  }
                />{" "}
                Obrigatória
              </label>
              <CipaFormActions>
                <ActionButton onClick={() => moveQuestion(index, -1)}>
                  <ArrowUp size={14} />
                </ActionButton>
                <ActionButton onClick={() => moveQuestion(index, 1)}>
                  <ArrowDown size={14} />
                </ActionButton>
                <ActionButton
                  onClick={() =>
                    setQuestions((prev) => prev.filter((item) => item.key !== question.key))
                  }
                >
                  <Trash2 size={14} />
                </ActionButton>
              </CipaFormActions>
            </CipaContentCard>
          ))}
          <CipaFormActions>
            <ActionButton onClick={() => setQuestions((prev) => [...prev, emptyQuestion()])}>
              <Plus size={16} /> Adicionar pergunta
            </ActionButton>
            <ActionButton onClick={() => setStep(1)}>Voltar</ActionButton>
            <ActionButton variant="primary" onClick={() => setStep(3)}>
              Revisar
            </ActionButton>
          </CipaFormActions>
        </CipaSectionCard>
      ) : null}

      {step === 3 ? (
        <CipaSectionCard title="Revisar e salvar">
          <p>
            <strong>{title || "Sem título"}</strong>
          </p>
          <p>{description || "Sem descrição"}</p>
          <ul>
            {questions.map((q) => (
              <li key={q.key}>
                {q.label || "(sem enunciado)"} —{" "}
                {SIPAT_QUESTION_TYPE_LABELS[q.question_type] || q.question_type}
              </li>
            ))}
          </ul>
          <CipaFormActions>
            <ActionButton onClick={() => setStep(2)}>Voltar</ActionButton>
            <ActionButton disabled={saving} onClick={() => void saveDraft()}>
              Salvar rascunho
            </ActionButton>
            <ActionButton variant="primary" disabled={saving} onClick={() => void publish()}>
              Publicar e gerar QR
            </ActionButton>
          </CipaFormActions>
        </CipaSectionCard>
      ) : null}

      {step === 4 ? (
        <CipaSectionCard title="Publicada">
          <p>Link público:</p>
          <code>{publicUrl || "—"}</code>
          <CipaFormActions>
            <ActionButton
              variant="primary"
              onClick={() =>
                navigateCipa(`/apps/cipa/filial-${unitCode}/sipat/${currentId || ""}`)
              }
            >
              Ir para detalhe
            </ActionButton>
          </CipaFormActions>
        </CipaSectionCard>
      ) : null}
    </div>
  );
}
