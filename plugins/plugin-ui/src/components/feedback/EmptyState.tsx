import { delpiUiClass } from "../../utils/delpiUiClass";

export type EmptyStateClassNames = {
  root: string;
  withTitle: boolean;
};

export type EmptyStateProps = {
  title?: string;
  message?: string;
  classNames: EmptyStateClassNames;
  defaultTitle?: string;
  defaultMessage: string;
};

export function emptyStateCardBemClasses(prefix: string): EmptyStateClassNames {
  return {
    root: delpiUiClass(
      `${prefix}-card ${prefix}-state-box ${prefix}-state-box--empty`,
      "delpi-ui-card delpi-ui-state-box delpi-ui-state-box--empty",
    ),
    withTitle: false,
  };
}

export function emptyStatePanelBemClasses(prefix: string): EmptyStateClassNames {
  return {
    root: `${prefix}-state ${prefix}-state--empty`,
    withTitle: true,
  };
}

export function EmptyState({
  title,
  message,
  classNames,
  defaultTitle,
  defaultMessage,
}: EmptyStateProps) {
  const resolvedMessage = message ?? defaultMessage;

  if (classNames.withTitle) {
    return (
      <div className={classNames.root}>
        <h3>{title ?? defaultTitle}</h3>
        <p>{resolvedMessage}</p>
      </div>
    );
  }

  return (
    <div className={classNames.root}>
      <p>{resolvedMessage}</p>
    </div>
  );
}

export type DashboardEmptyStateProps = {
  title?: string;
  message?: string;
};

export function createDashboardEmptyState(config: {
  classNames: EmptyStateClassNames;
  defaultTitle?: string;
  defaultMessage: string;
}) {
  return function DashboardEmptyState(props: DashboardEmptyStateProps) {
    return (
      <EmptyState
        classNames={config.classNames}
        defaultTitle={config.defaultTitle}
        defaultMessage={config.defaultMessage}
        {...props}
      />
    );
  };
}

export type LoadingStateClassNames = {
  root: string;
  spinner?: string;
};

export type LoadingStateProps = {
  message?: string;
  classNames: LoadingStateClassNames;
  defaultMessage: string;
};

export function loadingStateCardBemClasses(prefix: string): LoadingStateClassNames {
  return {
    root: delpiUiClass(
      `${prefix}-card ${prefix}-state-box`,
      "delpi-ui-card delpi-ui-state-box",
    ),
  };
}

export function loadingStatePanelBemClasses(
  prefix: string,
  modifier = "loading",
): LoadingStateClassNames {
  return {
    root: `${prefix}-state ${prefix}-state--${modifier}`,
    spinner: `${prefix}-spinner`,
  };
}

export function LoadingState({ message, classNames, defaultMessage }: LoadingStateProps) {
  return (
    <div className={classNames.root} role="status" aria-live="polite">
      {classNames.spinner ? <span className={classNames.spinner} aria-hidden="true" /> : null}
      <p>{message ?? defaultMessage}</p>
    </div>
  );
}

export function createDashboardLoadingState(config: {
  classNames: LoadingStateClassNames;
  defaultMessage: string;
}) {
  return function DashboardLoadingState(props: { message?: string }) {
    return (
      <LoadingState
        classNames={config.classNames}
        defaultMessage={config.defaultMessage}
        {...props}
      />
    );
  };
}
