import { formatSurveyWindow } from "./surveyForm.ts";

export type SurveyTerminalStatus =
  | "not_open"
  | "closed"
  | "already_submitted"
  | "invalid"
  | "temporary_error";

type SurveyStateViewProps = {
  status: SurveyTerminalStatus;
  campaignName?: string;
  startsAt?: string;
  endsAt?: string;
};

const COPY: Record<SurveyTerminalStatus, { title: string; message: string; alert: boolean }> = {
  not_open: {
    title: "A pesquisa ainda não está aberta",
    message: "Este link será liberado no início do período da pesquisa. Volte a acessá-lo nessa data.",
    alert: false,
  },
  closed: {
    title: "A pesquisa foi encerrada",
    message: "O período de respostas terminou. Agradecemos o seu interesse.",
    alert: false,
  },
  already_submitted: {
    title: "Resposta já registrada",
    message: "Já recebemos a resposta da sua empresa nesta pesquisa. Ela não pode ser enviada novamente.",
    alert: false,
  },
  invalid: {
    title: "Link inválido ou indisponível",
    message: "Não foi possível localizar esta pesquisa. Confira o link recebido ou solicite um novo convite.",
    alert: true,
  },
  temporary_error: {
    title: "Pesquisa temporariamente indisponível",
    message: "Não foi possível carregar a pesquisa agora. Tente novamente em alguns instantes.",
    alert: true,
  },
};

/** Estados terminais sem dados a preservar — nunca simulam sucesso de envio. */
export function SurveyStateView({ status, campaignName, startsAt, endsAt }: SurveyStateViewProps) {
  const copy = COPY[status];
  const period =
    (status === "not_open" || status === "closed") && startsAt && endsAt
      ? formatSurveyWindow(startsAt, endsAt)
      : null;
  return (
    <div className="satform satform--message" role={copy.alert ? "alert" : "status"}>
      <h1 className="satform-title">{copy.title}</h1>
      {campaignName && status !== "invalid" && status !== "temporary_error" ? (
        <p className="satform-subtitle">{campaignName}</p>
      ) : null}
      <p className="satform-subtitle">{copy.message}</p>
      {period ? <p className="satform-help">Período da pesquisa: {period}</p> : null}
      {status === "temporary_error" ? (
        <button type="button" className="satform-btn satform-btn--primary" onClick={() => window.location.reload()}>
          Tentar novamente
        </button>
      ) : null}
    </div>
  );
}
