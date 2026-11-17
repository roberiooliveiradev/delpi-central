import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";

import { FormButton } from "./FormButton";
import { FormHeaderCard } from "./FormHeaderCard";
import { FormIntroCard } from "./FormIntroCard";
import { FormLogo } from "./FormLogo";
import { FormNotice } from "./FormNotice";
import { FormPageLayout } from "./FormPageLayout";
import {
  FormResultPanel,
  type FormResultPanelProps,
} from "./FormResultPanel";
import { FormReviewSection } from "./FormReviewSection";
import { FormStepFooter } from "./FormStepFooter";
import { FormThemeToggle } from "./FormThemeToggle";
import { QuestionAnswerStack } from "./QuestionAnswerStack";
import { QuestionCard } from "./QuestionCard";
import { QuestionTextAnswer } from "./QuestionTextAnswer";
import { QuestionnaireThemeScope } from "./QuestionnaireThemeScope";
import { RatingScale, type RatingScaleValue } from "./RatingScale";
import {
  buildSubmitAnswers,
  goBack,
  goNext,
  hasAnyAnswer,
  initialFlow,
  isQuestionAnswered,
  missingInStep,
  questionnaireProgress,
  startEdit,
  startFlow,
  type GuidedFlow,
} from "./guidedQuestionnaireState";
import type {
  GuidedQuestionnaireProps,
  QuestionnaireAnswers,
  QuestionnaireQuestion,
} from "./guidedQuestionnaireTypes";
import { useUnsavedChangesWarning } from "./useUnsavedChangesWarning";

/**
 * Formulário guiado completo (camada 2 do kit): abertura → etapas → revisão →
 * envio → resultado, montado só com componentes P1–P4 a partir de uma
 * definição declarativa. Respostas vivem só em memória React — sem
 * localStorage/sessionStorage/cookie/URL. Todos os textos chegam por props.
 */
export function GuidedQuestionnaire({
  logo,
  intro,
  header,
  steps,
  texts,
  colorScheme = "auto",
  showThemeToggle = true,
  onSubmit,
  warnOnUnsaved = true,
  prefix = "ds",
  className,
}: GuidedQuestionnaireProps) {
  const [flow, setFlow] = useState<GuidedFlow>(initialFlow);
  const [answers, setAnswers] = useState<QuestionnaireAnswers>({});
  const [pending, setPending] = useState<ReadonlySet<string>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [retryMessage, setRetryMessage] = useState<ReactNode>(null);
  const [result, setResult] = useState<FormResultPanelProps | null>(null);

  const rootRef = useRef<HTMLDivElement>(null);
  const pageTopRef = useRef<HTMLDivElement>(null);
  const stepTitleRef = useRef<HTMLSpanElement>(null);
  const resultTitleRef = useRef<HTMLSpanElement>(null);
  const retryNoticeRef = useRef<HTMLDivElement>(null);

  const { done, total } = questionnaireProgress(steps, answers);

  useUnsavedChangesWarning(
    warnOnUnsaved && hasAnyAnswer(answers) && flow.phase !== "result",
  );

  // Foco e rolagem ao trocar de etapa/fase (§10.4.4 + §10.8.2).
  useEffect(() => {
    if (flow.phase === "step" || flow.phase === "review") {
      pageTopRef.current?.scrollIntoView();
      stepTitleRef.current?.focus();
    } else if (flow.phase === "result") {
      pageTopRef.current?.scrollIntoView();
      resultTitleRef.current?.focus();
    }
  }, [flow.phase, flow.stepIndex]);

  // Nova tentativa: foco no aviso para o leitor de tela (§10.8.2).
  useEffect(() => {
    if (retryMessage != null) retryNoticeRef.current?.focus();
  }, [retryMessage]);

  const setAnswer = useCallback(
    (key: string, value: number | "na" | string) => {
      setAnswers((prev) => ({ ...prev, [key]: value }));
      setPending((prev) => {
        if (!prev.has(key)) return prev;
        const next = new Set(prev);
        next.delete(key);
        return next;
      });
    },
    [],
  );

  /** Valida a etapa corrente; com pendência, marca erros e foca a primeira. */
  const attemptAdvance = useCallback(() => {
    const step = steps[flow.stepIndex];
    const missing = missingInStep(step, answers);
    if (missing.length > 0) {
      setPending(new Set(missing.map((q) => q.key)));
      const el = rootRef.current?.querySelector<HTMLElement>(
        `[data-gq-question="${missing[0].key}"]`,
      );
      el?.scrollIntoView();
      (
        el?.querySelector<HTMLElement>(
          'input[type="radio"], textarea, input',
        ) ?? null
      )?.focus();
      return;
    }
    setPending(new Set());
    setFlow((prev) => goNext(prev, steps.length));
  }, [answers, flow.stepIndex, steps]);

  const submit = useCallback(async () => {
    if (submitting) return; // envio único — cliques repetidos ignorados
    setSubmitting(true);
    setRetryMessage(null);
    try {
      const outcome = await onSubmit(buildSubmitAnswers(answers));
      if (outcome.type === "result") {
        setResult(outcome.result);
        setAnswers({});
        setFlow({ phase: "result", stepIndex: 0, editingFromReview: false });
      } else {
        setRetryMessage(outcome.message);
      }
    } catch {
      setRetryMessage(texts.submitError);
    } finally {
      setSubmitting(false);
    }
  }, [answers, onSubmit, submitting, texts.submitError]);

  const questionError = (q: QuestionnaireQuestion): string | undefined => {
    if (!pending.has(q.key)) return undefined;
    if (q.kind === "scale") {
      return q.scale.notApplicable != null
        ? texts.scaleErrorWithNa
        : texts.scaleError;
    }
    return texts.textError;
  };

  const themeToggle = showThemeToggle ? (
    <FormThemeToggle ariaLabel={texts.themeToggleAriaLabel} prefix={prefix} />
  ) : undefined;

  const stepLabelNode = (label: string) => (
    <span ref={stepTitleRef} tabIndex={-1}>
      {label}
    </span>
  );

  const renderQuestion = (q: QuestionnaireQuestion, index: number) => (
    <div key={q.key} data-gq-question={q.key}>
      <QuestionCard
        prefix={prefix}
        number={q.number ?? index + 1}
        eyebrow={q.eyebrow}
        prompt={q.prompt}
        required={q.required}
        requiredLabel={texts.requiredLabel}
        optionalLabel={texts.optionalLabel}
        error={questionError(q)}
      >
        <QuestionAnswerStack prefix={prefix}>
          {q.kind === "scale" ? (
            <RatingScale
              prefix={prefix}
              name={`gq-${q.key}`}
              min={q.scale.min}
              max={q.scale.max}
              value={(answers[q.key] as RatingScaleValue) ?? null}
              onChange={(v) => {
                if (v != null) setAnswer(q.key, v);
              }}
              optionLabel={q.scale.optionLabel}
              endLabels={q.scale.endLabels}
              endLabelsPosition={q.scale.endLabelsPosition}
              narrowColumns={q.scale.narrowColumns}
              selectionCaption={q.scale.selectionCaption}
              notApplicable={q.scale.notApplicable}
              invalid={pending.has(q.key)}
            />
          ) : (
            <QuestionTextAnswer
              prefix={prefix}
              label={q.text.label}
              placeholder={q.text.placeholder}
              maxLength={q.text.maxLength}
              value={typeof answers[q.key] === "string" ? (answers[q.key] as string) : ""}
              onChange={(v) => setAnswer(q.key, v)}
            />
          )}
        </QuestionAnswerStack>
      </QuestionCard>
    </div>
  );

  const headerLogo = <FormLogo src={logo.src} alt={logo.alt} prefix={prefix} />;
  const progressProps = {
    done,
    total,
    ariaLabel: texts.progressAriaLabel(done, total),
  };

  let content: ReactNode;

  if (flow.phase === "intro") {
    content = (
      <FormPageLayout band="tall" prefix={prefix}>
        <FormIntroCard
          prefix={prefix}
          logo={
            <FormLogo src={logo.src} alt={logo.alt} size="lg" prefix={prefix} />
          }
          headerAction={themeToggle}
          eyebrow={intro.eyebrow}
          title={intro.title}
          context={intro.context}
          description={intro.description}
          items={intro.items}
          footnote={intro.footnote}
          action={
            <FormButton prefix={prefix} onClick={() => setFlow(startFlow())}>
              {intro.startLabel}
            </FormButton>
          }
        />
      </FormPageLayout>
    );
  } else if (flow.phase === "step") {
    const step = steps[flow.stepIndex];
    const editing = flow.editingFromReview;
    content = (
      <FormPageLayout band="compact" prefix={prefix}>
        <div ref={pageTopRef}>
          <FormHeaderCard
            prefix={prefix}
            logo={headerLogo}
            meta={header.meta}
            headerAction={themeToggle}
            title={header.title}
            subtitle={header.subtitle}
            step={{
              label: stepLabelNode(
                texts.stepLabel(flow.stepIndex + 1, steps.length, step.title),
              ),
              progressLabel: texts.progressLabel(done, total),
            }}
            progress={progressProps}
          />
        </div>
        {step.questions.map(renderQuestion)}
        <FormStepFooter
          prefix={prefix}
          message={
            pending.size > 0 ? texts.stepFooterPending(pending.size) : null
          }
          back={
            !editing && flow.stepIndex > 0
              ? {
                  label: texts.back,
                  onClick: () => setFlow((prev) => goBack(prev, steps.length)),
                }
              : undefined
          }
          next={{
            label: editing
              ? texts.backToReview
              : flow.stepIndex === steps.length - 1
                ? texts.review
                : texts.next,
            onClick: attemptAdvance,
          }}
        />
      </FormPageLayout>
    );
  } else if (flow.phase === "review") {
    content = (
      <FormPageLayout band="compact" prefix={prefix}>
        <div ref={pageTopRef}>
          <FormHeaderCard
            prefix={prefix}
            logo={headerLogo}
            meta={header.meta}
            headerAction={themeToggle}
            title={header.title}
            subtitle={header.subtitle}
            step={{
              label: stepLabelNode(texts.reviewTitle),
              progressLabel: texts.progressLabel(done, total),
            }}
            progress={progressProps}
          />
        </div>
        {texts.reviewDescription != null && (
          <FormNotice prefix={prefix} tone="info">
            {texts.reviewDescription}
          </FormNotice>
        )}
        {steps.map((step, i) => (
          <FormReviewSection
            key={step.id}
            prefix={prefix}
            title={step.reviewTitle ?? step.title}
            edit={{
              label: texts.editLabel,
              ariaLabel: texts.editAriaLabel(step.title),
              onClick: () => setFlow(startEdit(i)),
            }}
            rows={step.questions.map((q) => {
              const value = answers[q.key];
              if (q.kind === "scale") {
                if (typeof value === "number") {
                  return {
                    label: q.eyebrow ?? q.prompt,
                    value: q.scale.reviewValue?.(value) ?? value,
                  };
                }
                if (value === "na") {
                  return { label: q.eyebrow ?? q.prompt, value: texts.reviewNaValue };
                }
                return {
                  label: q.eyebrow ?? q.prompt,
                  value: texts.reviewEmptyValue,
                  muted: true,
                };
              }
              const text = typeof value === "string" ? value.trim() : "";
              if (text.length === 0) {
                return {
                  label: q.eyebrow ?? q.prompt,
                  value: texts.reviewEmptyValue,
                  muted: true,
                };
              }
              return { label: q.eyebrow ?? q.prompt, value: text, block: true };
            })}
          />
        ))}
        <FormNotice prefix={prefix} tone="warning">
          {texts.reviewNotice}
        </FormNotice>
        {retryMessage != null && (
          <div ref={retryNoticeRef} tabIndex={-1}>
            <FormNotice prefix={prefix} tone="warning">
              {retryMessage}
            </FormNotice>
          </div>
        )}
        <FormStepFooter
          prefix={prefix}
          back={{
            label: texts.back,
            onClick: () => setFlow((prev) => goBack(prev, steps.length)),
          }}
          next={{
            label: texts.submit,
            onClick: submit,
            busy: submitting,
            busyLabel: texts.submitting,
          }}
        />
      </FormPageLayout>
    );
  } else {
    // result — sem cabeçalho nem rodapé de ações (§10.4.7)
    content = (
      <FormPageLayout band="tall" prefix={prefix}>
        <div ref={pageTopRef}>
          {result != null && (
            <FormResultPanel
              {...result}
              prefix={prefix}
              title={
                <span ref={resultTitleRef} tabIndex={-1}>
                  {result.title}
                </span>
              }
            />
          )}
        </div>
      </FormPageLayout>
    );
  }

  return (
    <div
      ref={rootRef}
      className={[
        delpiUiClass(`${prefix}-form-guided`, "delpi-ui-form-guided"),
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <QuestionnaireThemeScope prefix={prefix} colorScheme={colorScheme}>
        {content}
      </QuestionnaireThemeScope>
    </div>
  );
}

export { isQuestionAnswered };
