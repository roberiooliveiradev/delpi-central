import type { AppPublicPages } from "../../shell/types";
import {
  fetchFeedbackStatus,
  fetchPublicForm,
  fetchPublicParticipant,
  type FeedbackStatus,
  type PublicForm,
  type PublicParticipant,
} from "./api";
import { ThanksView } from "./ThanksPage";
import { FeedbackView } from "./FeedbackPage";
import { FormView } from "./FormPage";

export const customerExperiencePages: AppPublicPages = {
  thanks: {
    documentTitle: "Obrigado pela visita — DELPI",
    notFoundMessage: "Este link de agradecimento não está mais disponível.",
    load: ({ token }) => fetchPublicParticipant(token),
    render: (data) => <ThanksView participant={data as PublicParticipant} />,
  },
  feedback: {
    documentTitle: "Sua experiência — DELPI",
    notFoundMessage: "Este link de feedback não está mais disponível.",
    load: ({ token }) => fetchFeedbackStatus(token),
    render: (data, ctx) => (
      <FeedbackView token={ctx.token} status={data as FeedbackStatus} />
    ),
  },
  form: {
    documentTitle: "Formulário — DELPI",
    notFoundMessage: "Este formulário não está mais disponível.",
    load: ({ token }) => fetchPublicForm(token),
    render: (data) => <FormView form={data as PublicForm} />,
  },
};
