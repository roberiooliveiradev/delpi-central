export type LoadingActivityCardVariant = "compact" | "panel";
export type LoadingActivityCardTone = "neutral" | "info";

export type LoadingActivityCardClassNames = {
  root: string;
  rootVariant: (variant: LoadingActivityCardVariant) => string;
  rootTone: (tone: LoadingActivityCardTone) => string;
  rootSticky: string;
  spinner: string;
  content: string;
  copy?: string;
  title: string;
  description: string;
  progressWrap: string;
  progressLabel: string;
  progress: string;
  progressIndicator: string;
  progressIndicatorDeterminate: string;
};

export type LoadingActivityCardLabels = {
  progressRemaining: (remainingPercent: number) => string;
  /** Ex.: «Iniciando…» quando progresso = 0 (strategic-indicators). */
  progressStarting?: string;
  /** Só exibe «Faltam N%» após progresso > 0. */
  progressRemainingOnlyAfterStart?: boolean;
  progressAriaDeterminate: (remainingPercent: number) => string;
  progressAriaStarting?: string;
  progressAriaIndeterminate: string;
};

export type LoadingActivityCardProps = {
  title: string;
  description?: string;
  variant?: LoadingActivityCardVariant;
  tone?: LoadingActivityCardTone;
  sticky?: boolean;
  progressPercent?: number;
  classNames: LoadingActivityCardClassNames;
  labels: LoadingActivityCardLabels;
  className?: string;
};

export function loadingActivityBemClasses(
  prefix: string,
  options?: { withCopyWrapper?: boolean; block?: string },
): LoadingActivityCardClassNames {
  const base = `${prefix}-${options?.block ?? "loading-activity"}`;

  return {
    root: base,
    rootVariant: (variant) => `${base}--${variant}`,
    rootTone: (tone) => `${base}--${tone}`,
    rootSticky: `${base}--sticky`,
    spinner: `${base}__spinner`,
    content: `${base}__content`,
    copy: options?.withCopyWrapper ? `${base}__copy` : undefined,
    title: `${base}__title`,
    description: `${base}__description`,
    progressWrap: `${base}__progress-wrap`,
    progressLabel: `${base}__progress-label`,
    progress: `${base}__progress`,
    progressIndicator: `${base}__progress-indicator`,
    progressIndicatorDeterminate: `${base}__progress-indicator--determinate`,
  };
}

function resolveProgress(progressPercent: number | undefined, labels: LoadingActivityCardLabels) {
  const hasProgress =
    typeof progressPercent === "number" && Number.isFinite(progressPercent);
  const clampedProgress = hasProgress
    ? Math.min(100, Math.max(0, Math.round(progressPercent)))
    : null;

  let remainingPercent: number | null = null;
  if (clampedProgress !== null) {
    if (labels.progressRemainingOnlyAfterStart) {
      remainingPercent =
        clampedProgress > 0 ? Math.max(0, 100 - clampedProgress) : null;
    } else {
      remainingPercent = Math.max(0, 100 - clampedProgress);
    }
  }

  return { clampedProgress, remainingPercent };
}

function resolveProgressLabel(
  clampedProgress: number | null,
  remainingPercent: number | null,
  labels: LoadingActivityCardLabels,
): string | null {
  if (clampedProgress !== null && clampedProgress <= 0 && labels.progressStarting) {
    return labels.progressStarting;
  }
  if (remainingPercent !== null) {
    return labels.progressRemaining(remainingPercent);
  }
  return null;
}

function resolveProgressAriaLabel(
  progressLabel: string | null,
  remainingPercent: number | null,
  labels: LoadingActivityCardLabels,
): string {
  if (progressLabel && labels.progressStarting && progressLabel === labels.progressStarting) {
    return labels.progressAriaStarting ?? `Carregamento: ${labels.progressStarting}`;
  }
  if (remainingPercent !== null) {
    return labels.progressAriaDeterminate(remainingPercent);
  }
  return labels.progressAriaIndeterminate;
}

export function LoadingActivityCard({
  title,
  description,
  variant = "panel",
  tone = "info",
  sticky = variant === "compact",
  progressPercent,
  classNames,
  labels,
  className,
}: LoadingActivityCardProps) {
  const { clampedProgress, remainingPercent } = resolveProgress(progressPercent, labels);
  const progressLabel = resolveProgressLabel(clampedProgress, remainingPercent, labels);
  const rootClass = [
    classNames.root,
    classNames.rootVariant(variant),
    classNames.rootTone(tone),
    sticky ? classNames.rootSticky : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const copyBlock = (
    <>
      <strong className={classNames.title}>{title}</strong>
      {description ? <p className={classNames.description}>{description}</p> : null}
    </>
  );

  return (
    <div className={rootClass} role="status" aria-live="polite">
      <div className={classNames.spinner} aria-hidden="true" />
      <div className={classNames.content}>
        {classNames.copy ? <div className={classNames.copy}>{copyBlock}</div> : copyBlock}
        <div className={classNames.progressWrap}>
          {progressLabel ? (
            <span className={classNames.progressLabel}>{progressLabel}</span>
          ) : null}
          <div
            className={classNames.progress}
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={clampedProgress ?? undefined}
            aria-label={resolveProgressAriaLabel(progressLabel, remainingPercent, labels)}
          >
            <div
              className={[
                classNames.progressIndicator,
                clampedProgress !== null ? classNames.progressIndicatorDeterminate : "",
              ]
                .filter(Boolean)
                .join(" ")}
              style={
                clampedProgress !== null ? { width: `${clampedProgress}%` } : undefined
              }
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export type DashboardLoadingActivityCardProps = Omit<
  LoadingActivityCardProps,
  "classNames" | "labels"
>;

export function createDashboardLoadingActivityCard(config: {
  prefix: string;
  labels: LoadingActivityCardLabels;
  withCopyWrapper?: boolean;
  block?: string;
  defaultTone?: LoadingActivityCardTone;
}) {
  const classNames = loadingActivityBemClasses(config.prefix, {
    withCopyWrapper: config.withCopyWrapper,
    block: config.block,
  });
  const defaultTone = config.defaultTone ?? "info";

  return function DashboardLoadingActivityCard({
    tone,
    ...props
  }: DashboardLoadingActivityCardProps) {
    return (
      <LoadingActivityCard
        classNames={classNames}
        labels={config.labels}
        tone={tone ?? defaultTone}
        {...props}
      />
    );
  };
}
