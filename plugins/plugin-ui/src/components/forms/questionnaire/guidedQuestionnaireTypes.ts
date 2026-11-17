import type { ReactNode } from "react";

import type { FormResultPanelProps } from "./FormResultPanel";
import type { RatingScaleValue } from "./RatingScale";

/** Resposta de uma pergunta: nota, "na" (não se aplica) ou texto. */
export type QuestionnaireAnswer = number | "na" | string;

/** Respostas por `key` da pergunta. */
export type QuestionnaireAnswers = Record<string, QuestionnaireAnswer>;

export type QuestionnaireScaleQuestion = {
  kind: "scale";
  key: string;
  number?: ReactNode;
  eyebrow?: ReactNode;
  prompt: ReactNode;
  required: boolean;
  scale: {
    min: number;
    max: number;
    optionLabel: (n: number) => string;
    endLabels: { min: ReactNode; max: ReactNode };
    endLabelsPosition?: "below" | "above";
    narrowColumns?: number;
    selectionCaption?: (n: number) => ReactNode;
    notApplicable?: { label: string };
    /** Como a nota aparece na revisão (padrão: o número). */
    reviewValue?: (n: number) => ReactNode;
  };
};

export type QuestionnaireTextQuestion = {
  kind: "text";
  key: string;
  number?: ReactNode;
  eyebrow?: ReactNode;
  prompt: ReactNode;
  required: boolean;
  text: {
    label: string;
    placeholder?: string;
    maxLength?: number;
  };
};

export type QuestionnaireQuestion =
  | QuestionnaireScaleQuestion
  | QuestionnaireTextQuestion;

export type QuestionnaireStep = {
  id: string;
  title: string;
  /** Título da seção na revisão (padrão: `title`). */
  reviewTitle?: string;
  questions: QuestionnaireQuestion[];
};

/** Toda a microcopy do fluxo — o kit não tem texto fixo. */
export type GuidedQuestionnaireTexts = {
  back: ReactNode;
  next: ReactNode;
  review: ReactNode;
  backToReview: ReactNode;
  submit: ReactNode;
  submitting: ReactNode;
  /** "obrigatória" para leitor de tela (o asterisco visual é aria-hidden). */
  requiredLabel: string;
  optionalLabel: ReactNode;
  /** Erro de escala obrigatória sem opção N/A. */
  scaleError: string;
  /** Erro de escala obrigatória que aceita "não se aplica". */
  scaleErrorWithNa: string;
  /** Erro de texto obrigatório vazio. */
  textError: string;
  /** Pendências no rodapé (ex.: "Responda 2 perguntas para continuar."). */
  stepFooterPending: (count: number) => string;
  /** Linha da etapa (ex.: "Etapa 1 de 3 · Treinamento"). */
  stepLabel: (index: number, total: number, title: string) => string;
  /** Texto do progresso (ex.: "3 de 12"). Reusado na revisão (§10.8). */
  progressLabel: (done: number, total: number) => string;
  progressAriaLabel: (done: number, total: number) => string;
  /** Título da etapa de revisão no cabeçalho. */
  reviewTitle: string;
  /** Orientação no topo da revisão (ex.: "Confira antes de enviar…"). §10.8 */
  reviewDescription: ReactNode;
  /** Aviso de imutabilidade exibido antes do rodapé da revisão. */
  reviewNotice: ReactNode;
  /** Valor exibido na revisão quando a resposta é "não se aplica". */
  reviewNaValue: ReactNode;
  /** Valor exibido (em itálico) para resposta vazia/opcional não respondida. */
  reviewEmptyValue: string;
  /** Erro genérico quando `onSubmit` lança exceção. */
  submitError: ReactNode;
  editLabel: ReactNode;
  /** Nome acessível do botão Editar de cada seção (por título da etapa). */
  editAriaLabel: (stepTitle: string) => string;
  themeToggleAriaLabel: string;
};

/** Resultado do envio decidido pelo aplicativo. */
export type QuestionnaireSubmitOutcome =
  | { type: "result"; result: FormResultPanelProps }
  | { type: "retry"; message: ReactNode };

export type GuidedQuestionnaireIntro = {
  eyebrow?: ReactNode;
  title: ReactNode;
  context?: { label: ReactNode; value: ReactNode };
  description?: ReactNode;
  items?: { icon: ReactNode; content: ReactNode }[];
  startLabel: ReactNode;
  footnote?: ReactNode;
};

export type GuidedQuestionnaireHeader = {
  title: ReactNode;
  subtitle?: ReactNode;
  meta?: ReactNode;
};

export type GuidedQuestionnaireProps = {
  logo: { src: string; alt: string };
  intro: GuidedQuestionnaireIntro;
  header: GuidedQuestionnaireHeader;
  steps: QuestionnaireStep[];
  texts: GuidedQuestionnaireTexts;
  /** Tema do escopo ("auto" segue o aparelho). */
  colorScheme?: "auto" | "light" | "dark";
  showThemeToggle?: boolean;
  /** Chamado uma única vez por envio, só a partir da revisão. */
  onSubmit: (answers: QuestionnaireAnswers) => Promise<QuestionnaireSubmitOutcome>;
  /** `beforeunload` enquanto houver respostas não enviadas. Padrão true. */
  warnOnUnsaved?: boolean;
  /** Prefixo BEM do consumidor (dual-class). */
  prefix?: string;
  className?: string;
};

export type { RatingScaleValue };
