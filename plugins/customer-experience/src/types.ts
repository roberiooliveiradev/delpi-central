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
  feedbackQrUrl: string;
  publicUrl: string | null;
  feedbackPublicUrl: string | null;
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

// ----- Formulários (estilo Google Forms) -----------------------------------

export type QuestionType =
  | "rating"
  | "short_text"
  | "long_text"
  | "single_choice"
  | "multi_choice"
  | "yes_no";

export type FormQuestion = {
  id?: string;
  type: QuestionType;
  label: string;
  helpText: string | null;
  required: boolean;
  options: string[];
  position?: number;
};

export type FormSummary = {
  id: string;
  publicToken: string;
  title: string;
  description: string | null;
  isActive: boolean;
  responseCount: number;
  qrUrl: string;
  publicUrl: string | null;
  createdByName: string | null;
  createdAt: string;
  updatedAt: string;
};

export type FormDetail = FormSummary & {
  questions: FormQuestion[];
};

export type CreateFormInput = {
  title: string;
  description?: string;
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
