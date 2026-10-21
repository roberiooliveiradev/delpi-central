/**
 * Feedback padronizado do Portal — adaptador fino sobre `CfStateBanner`
 * (`@delpi/plugin-ui`). Intenções semânticas mapeadas às variantes reais
 * do kit (`default`/`error`/`success`); nenhum chrome novo é criado.
 */
import type { ReactNode } from "react";

import { CfActionButton, CfStateBanner } from "./controllershipFinanceUi";

export type CfFeedbackIntent = "info" | "warning" | "error" | "success";

const INTENT_VARIANT: Record<
  CfFeedbackIntent,
  "default" | "error" | "success"
> = {
  info: "default",
  warning: "default",
  error: "error",
  success: "success",
};

export type CfFeedbackMessageProps = {
  intent: CfFeedbackIntent;
  title: string;
  children?: ReactNode;
  /** Ação contextual opcional (ex.: Tentar novamente). */
  action?: ReactNode;
};

export function CfFeedbackMessage({
  intent,
  title,
  children,
  action,
}: CfFeedbackMessageProps) {
  return (
    <CfStateBanner
      variant={INTENT_VARIANT[intent]}
      className={`cf-feedback cf-feedback--${intent}`}
    >
      <p className="cf-banner-title">
        <span className="cf-feedback-icon" aria-hidden="true">
          {intent === "error"
            ? "✕"
            : intent === "warning"
              ? "⚠"
              : intent === "success"
                ? "✓"
                : "ℹ"}
        </span>
        {title}
      </p>
      {children ? <p className="cf-banner-text">{children}</p> : null}
      {action}
    </CfStateBanner>
  );
}

export type CfQueryError = {
  status: number;
  code: string | null;
  message: string;
};

/**
 * Mapeamento canônico de falhas de consulta do Portal — distingue gate de
 * dataset (`scope_unavailable`), credencial S2S (`S2S_*`), sessão, RBAC e
 * dependência indisponível. `dataset` é o nome amigável do conjunto
 * consultado (ex.: "o estoque histórico", "as baixas financeiras").
 */
export function CfQueryErrorBanner({
  error,
  dataset,
  onRetry,
}: {
  error: CfQueryError;
  dataset: string;
  onRetry?: () => void;
}) {
  const retryAction = onRetry ? (
    <CfActionButton variant="ghost" onClick={onRetry}>
      Tentar novamente
    </CfActionButton>
  ) : null;

  if (error.code === "scope_unavailable") {
    return (
      <CfFeedbackMessage intent="error" title="Consulta ainda não habilitada">
        O acesso ao conjunto de dados de {dataset} ainda não está liberado
        para este ambiente.
      </CfFeedbackMessage>
    );
  }
  if (error.code && error.code.startsWith("S2S_")) {
    return (
      <CfFeedbackMessage intent="error" title="Integração de dados pendente">
        A credencial técnica entre o Portal e a origem de dados ainda não
        possui a autorização necessária para esta consulta. Acione o suporte
        informando esta tela.
      </CfFeedbackMessage>
    );
  }
  if (error.status === 401) {
    return (
      <CfFeedbackMessage intent="error" title="Sessão expirada">
        Entre novamente para continuar.
      </CfFeedbackMessage>
    );
  }
  if (error.status === 403) {
    return (
      <CfFeedbackMessage intent="error" title="Acesso restrito">
        Você não tem autorização para consultar {dataset}.
      </CfFeedbackMessage>
    );
  }
  if (error.status === 503) {
    return (
      <CfFeedbackMessage
        intent="error"
        title="Origem indisponível"
        action={retryAction}
      >
        A fonte de dados de {dataset} está temporariamente indisponível.
      </CfFeedbackMessage>
    );
  }
  return (
    <CfFeedbackMessage
      intent="error"
      title="Falha de comunicação"
      action={retryAction}
    >
      {error.message}
    </CfFeedbackMessage>
  );
}
