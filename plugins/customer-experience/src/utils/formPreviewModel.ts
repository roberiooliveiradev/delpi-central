import type { BackgroundFit, FormDetail, FormPage, FormQuestion } from "../types";
import { normalizeBackgroundFit } from "../types";

export type PreviewForm = {
  token: string;
  title: string;
  description: string | null;
  oneQuestionPerPage: boolean;
  backgroundFit: BackgroundFit;
  backgroundImageUrl?: string | null;
  pages: PreviewFormPage[];
  questions: PreviewFormQuestion[];
};

export type PreviewFormPage = {
  id: string;
  title: string | null;
  position?: number;
  backgroundImageUrl?: string | null;
  pointImageUrl?: string | null;
};

export type PreviewFormQuestion = {
  id: string;
  type: FormQuestion["type"];
  label: string;
  helpText: string | null;
  required: boolean;
  options: string[];
  pageId?: string | null;
  pointImageUrl?: string | null;
};

type PendingImages = {
  formBackground?: File;
  pageBackground: Record<number, File>;
  pagePoint: Record<number, File>;
  questionPoint: Record<number, File>;
};

type BuildPreviewInput = {
  publicToken: string;
  title: string;
  description: string | null;
  oneQuestionPerPage: boolean;
  backgroundFit?: BackgroundFit | null;
  backgroundImageUrl: string | null;
  pages: FormPage[];
  questions: FormQuestion[];
  pendingImages?: PendingImages;
};

function pageIdAt(pages: FormPage[], index: number): string {
  return pages[index]?.id ?? `preview-page-${index}`;
}

export function buildPreviewForm(input: BuildPreviewInput): PreviewForm {
  const {
    publicToken,
    title,
    description,
    oneQuestionPerPage,
    backgroundFit,
    backgroundImageUrl,
    pages,
    questions,
    pendingImages,
  } = input;

  const resolvedBackground = pendingImages?.formBackground
    ? URL.createObjectURL(pendingImages.formBackground)
    : backgroundImageUrl;

  const previewPages: PreviewFormPage[] = pages.map((page, index) => ({
    id: pageIdAt(pages, index),
    title: page.title,
    position: page.position ?? index,
    backgroundImageUrl: pendingImages?.pageBackground[index]
      ? URL.createObjectURL(pendingImages.pageBackground[index])
      : page.backgroundImageUrl ?? null,
    pointImageUrl: pendingImages?.pagePoint[index]
      ? URL.createObjectURL(pendingImages.pagePoint[index])
      : page.pointImageUrl ?? null,
  }));

  const previewQuestions: PreviewFormQuestion[] = questions.map((question, index) => {
    const pageIndex =
      question.pageIndex ??
      (question.pageId ? pages.findIndex((p) => p.id === question.pageId) : -1);
    const pageId = pageIndex >= 0 ? pageIdAt(pages, pageIndex) : null;

    return {
      id: question.id ?? `preview-question-${index}`,
      type: question.type,
      label: question.label || `Pergunta ${index + 1}`,
      helpText: question.helpText,
      required: question.required,
      options: question.options,
      pageId,
      pointImageUrl: pendingImages?.questionPoint[index]
        ? URL.createObjectURL(pendingImages.questionPoint[index])
        : question.pointImageUrl ?? null,
    };
  });

  return {
    token: publicToken,
    title: title.trim() || "Formulário sem título",
    description: description?.trim() || null,
    oneQuestionPerPage,
    backgroundFit: normalizeBackgroundFit(backgroundFit),
    backgroundImageUrl: resolvedBackground,
    pages: previewPages,
    questions: previewQuestions,
  };
}

export function buildPreviewFormFromDetail(form: FormDetail): PreviewForm {
  return buildPreviewForm({
    publicToken: form.publicToken,
    title: form.title,
    description: form.description,
    oneQuestionPerPage: form.oneQuestionPerPage,
    backgroundFit: form.backgroundFit,
    backgroundImageUrl: form.backgroundImageUrl ?? null,
    pages: form.pages ?? [],
    questions: form.questions,
  });
}

const CHOICE_TYPES = new Set(["single_choice", "multi_choice"]);

function ensurePageCount(pages: FormPage[], count: number): FormPage[] {
  if (count <= 0) return [];
  if (pages.length >= count) return pages.slice(0, count);
  const blank = (): FormPage => ({
    title: null,
    backgroundImageUrl: null,
    pointImageUrl: null,
  });
  return [...pages, ...Array.from({ length: count - pages.length }, blank)];
}

export function buildEditorPreview(input: {
  publicToken: string;
  title: string;
  description: string;
  oneQuestionPerPage: boolean;
  backgroundFit: BackgroundFit;
  backgroundPreview: string | null;
  pages: FormPage[];
  questions: FormQuestion[];
  pendingImages: PendingImages;
}): PreviewForm {
  const pages = input.oneQuestionPerPage
    ? ensurePageCount(input.pages, input.questions.length)
    : input.pages;

  const questions = input.questions.map((q) => ({
    ...q,
    options: CHOICE_TYPES.has(q.type) ? q.options.map((o) => o.trim()).filter(Boolean) : q.options,
  }));

  return buildPreviewForm({
    publicToken: input.publicToken,
    title: input.title,
    description: input.description || null,
    oneQuestionPerPage: input.oneQuestionPerPage,
    backgroundFit: input.backgroundFit,
    backgroundImageUrl: input.backgroundPreview,
    pages,
    questions,
    pendingImages: input.pendingImages,
  });
}
