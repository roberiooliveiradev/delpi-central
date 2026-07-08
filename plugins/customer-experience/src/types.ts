export type Participant = {
  id: string;
  publicToken: string;
  fullName: string;
  companyName: string;
  visitDate: string;
  participantInfo: string | null;
  thankYouMessage: string | null;
  photoUrl: string;
  qrUrl: string;
  publicUrl: string | null;
  viewCount: number;
  isActive: boolean;
  createdByName: string | null;
  createdAt: string;
  updatedAt: string;
};

export type ParticipantListResult = {
  items: Participant[];
  total: number;
  limit: number;
  offset: number;
};

export type CreateParticipantInput = {
  fullName: string;
  companyName: string;
  visitDate: string;
  participantInfo?: string;
  thankYouMessage?: string;
  photo: File;
};

export type UpdateParticipantInput = {
  fullName?: string;
  companyName?: string;
  visitDate?: string;
  participantInfo?: string;
  thankYouMessage?: string;
  photo?: File;
};

// ----- Clientes TOTVS (api-delpi / SA1) ------------------------------------

export type Customer = {
  code: string;
  store: string;
  name: string;
  blocked: string | null;
};

export type CustomerSearchResult = {
  items: Customer[];
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
};

// ----- Formulários (estilo Google Forms) -----------------------------------

export type QuestionType =
  | "rating"
  | "short_text"
  | "long_text"
  | "single_choice"
  | "multi_choice"
  | "yes_no";

/** Como a imagem de fundo preenche a viewport pública. */
export type BackgroundFit = "fixed" | "scale" | "tile";

export const BACKGROUND_FIT_LABELS: Record<BackgroundFit, string> = {
  fixed: "Tamanho fixo (original)",
  scale: "Escalável (preenche a tela)",
  tile: "Repetir (mosaico)",
};

/** Mesmos modos, rótulos para imagem ilustrativa. */
export const POINT_IMAGE_FIT_LABELS: Record<BackgroundFit, string> = {
  fixed: "Tamanho fixo (original)",
  scale: "Preencher (adapta ao container)",
  tile: "Repetir (mosaico)",
};

export const BACKGROUND_FITS: BackgroundFit[] = ["fixed", "scale", "tile"];

export function normalizeBackgroundFit(value: string | null | undefined): BackgroundFit {
  if (value === "fixed" || value === "tile" || value === "scale") return value;
  return "scale";
}

export type FormQuestion = {
  id?: string;
  type: QuestionType;
  label: string;
  helpText: string | null;
  required: boolean;
  options: string[];
  position?: number;
  pageId?: string | null;
  pageIndex?: number | null;
  pointImageUrl?: string | null;
  pointImageFit?: BackgroundFit;
};

export type FormPage = {
  id?: string;
  title: string | null;
  position?: number;
  backgroundImageUrl?: string | null;
  pointImageUrl?: string | null;
  pointImageFit?: BackgroundFit;
};

export type FormSummary = {
  id: string;
  publicToken: string;
  title: string;
  description: string | null;
  isActive: boolean;
  responseCount: number;
  oneQuestionPerPage: boolean;
  backgroundFit: BackgroundFit;
  backgroundImageUrl?: string | null;
  qrUrl: string;
  publicUrl: string | null;
  createdByName: string | null;
  createdAt: string;
  updatedAt: string;
};

export type FormDetail = FormSummary & {
  questions: FormQuestion[];
  pages: FormPage[];
};

export type CreateFormInput = {
  title: string;
  description?: string;
  oneQuestionPerPage?: boolean;
  backgroundFit?: BackgroundFit;
};

export type DashboardQuestion = {
  id: string;
  label: string;
  type: QuestionType;
  active: boolean;
  answered: number;
  average?: number | null;
  distribution?: Record<string, number>;
  optionCounts?: Record<string, number>;
  samples?: string[];
};

export type FormDashboard = {
  formId: string;
  title: string;
  totalResponses: number;
  questions: DashboardQuestion[];
};

export type FormResponseAnswer = {
  questionId: string;
  label: string | null;
  type: QuestionType | null;
  value: string | number | string[] | null;
};

export type FormResponseItem = {
  id: string;
  respondentName: string;
  respondentCompany: string | null;
  createdAt: string;
  answers: FormResponseAnswer[];
};

export type FormResponseList = {
  items: FormResponseItem[];
  total: number;
  limit: number;
  offset: number;
};
