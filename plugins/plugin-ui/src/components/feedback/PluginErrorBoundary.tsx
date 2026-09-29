/**
 * Error boundary canônico para montagens de MFE no Portal.
 * Sem boundary, uma exceção de render desmonta a raiz do remote e a área do
 * app fica vazia/escura sem feedback. O fallback é só apresentação — o host
 * decide retry/reset e recebe `onError` para observabilidade.
 */
import { Component, type ErrorInfo, type ReactNode } from "react";

import { ActionButton } from "../actions/ActionButton";
import { EmptyGuidance, emptyGuidanceBemClasses } from "./EmptyGuidance";

export type PluginErrorBoundaryLabels = {
  title: string;
  message?: string;
  retry?: string;
};

export type PluginErrorBoundaryProps = {
  children: ReactNode;
  labels: PluginErrorBoundaryLabels;
  /** Prefixo BEM do plugin (default `ds`). */
  prefix?: string;
  /** Re-renderiza os filhos quando muda (ex.: roomId, rota). */
  resetKey?: unknown;
  /** Log/telemetria do host — o boundary nunca engole a exceção em silêncio. */
  onError?: (error: Error, info: ErrorInfo) => void;
  /** Chamado junto do reset quando o usuário clica em retry. */
  onRetry?: () => void;
};

export function pluginErrorBoundaryBemClasses(prefix = "ds") {
  return emptyGuidanceBemClasses(prefix);
}

type State = { error: Error | null };

export class PluginErrorBoundary extends Component<
  PluginErrorBoundaryProps,
  State
> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info);
  }

  componentDidUpdate(prevProps: PluginErrorBoundaryProps) {
    if (this.state.error && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ error: null });
    }
  }

  private retry = () => {
    this.setState({ error: null });
    this.props.onRetry?.();
  };

  render() {
    const { children, labels, prefix = "ds" } = this.props;
    const { error } = this.state;
    if (!error) return children;
    const classes = pluginErrorBoundaryBemClasses(prefix);
    return (
      <EmptyGuidance
        variant="panel"
        classNames={classes}
        role="alert"
        title={labels.title}
        message={labels.message ?? error.message}
      >
        {labels.retry ? (
          <ActionButton type="button" variant="ghost" onClick={this.retry}>
            {labels.retry}
          </ActionButton>
        ) : null}
      </EmptyGuidance>
    );
  }
}
