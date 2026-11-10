/** Estados canônicos de consulta: carregando, erro, sessão, acesso negado e indisponível. */
import { Lock, RefreshCw } from "lucide-react";

import type { ApiError } from "../api/httpClient";
import { STATE_CONTENT } from "../content/labels";
import { ItpActionButton, ItpEmptyState, ItpLoadingCard, ItpStateBanner } from "./itPortalUi";

export function LoadingBlock({ title, description }: { title: string; description?: string }) {
  return <ItpLoadingCard title={title} description={description ?? STATE_CONTENT.loading} variant="panel" />;
}

export function ForbiddenState({ message }: { message?: string }) {
  return (
    <ItpEmptyState title={STATE_CONTENT.forbiddenTitle} message={message ?? STATE_CONTENT.forbiddenArea} role="alert">
      <Lock size={20} strokeWidth={1.75} aria-hidden="true" />
    </ItpEmptyState>
  );
}

export function QueryErrorState({ error, onRetry }: { error: ApiError; onRetry?: () => void }) {
  if (error.status === 403) return <ForbiddenState />;
  const title =
    error.status === 401
      ? STATE_CONTENT.sessionTitle
      : error.status === 404
        ? STATE_CONTENT.notFoundTitle
        : error.status === 503 || error.status === 0
          ? STATE_CONTENT.unavailableTitle
          : STATE_CONTENT.errorTitle;
  return (
    <ItpStateBanner variant="error">
      <div role="alert" className="itp-state-content">
        <p className="itp-state-title">{title}</p>
        <p className="itp-state-text">{error.message}</p>
        {onRetry && error.status !== 401 && error.status !== 404 ? (
          <ItpActionButton variant="ghost" onClick={onRetry}>
            <RefreshCw size={14} strokeWidth={1.75} aria-hidden="true" /> {STATE_CONTENT.retry}
          </ItpActionButton>
        ) : null}
      </div>
    </ItpStateBanner>
  );
}
