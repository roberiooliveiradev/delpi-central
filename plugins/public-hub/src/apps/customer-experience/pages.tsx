import type { AppPublicPages } from "../../shell/types";
import {
  fetchPublicForm,
  fetchPublicParticipant,
  type PublicForm,
  type PublicParticipant,
} from "./api";
import { ThanksView } from "./ThanksPage";
import { FormView } from "./FormPage";

export const customerExperiencePages: AppPublicPages = {
  thanks: {
    documentTitle: "Obrigado pela visita — DELPI",
    notFoundMessage: "Este link de agradecimento não está mais disponível.",
    load: ({ token }) => fetchPublicParticipant(token),
    render: (data) => <ThanksView participant={data as PublicParticipant} />,
  },
  form: {
    documentTitle: "Formulário — DELPI",
    chrome: "fullpage",
    notFoundMessage: "Este formulário não está mais disponível.",
    load: ({ token }) => fetchPublicForm(token),
    render: (data) => <FormView form={data as PublicForm} />,
  },
};
