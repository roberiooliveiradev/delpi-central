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
  progressAriaDeterminate: (remainingPercent: number) => string;
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
  options?: { withCopyWrapper?: boolean },
): LoadingActivityCardClassNames {
  const base = `${prefix}-loading-activity`;

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

function resolveProgress(progressPercent?: number) {
  const hasProgress =
    typeof progressPercent === "number" && Number.isFinite(progressPercent);
  const clampedProgress = hasProgress
    ? Math.min(100, Math.max(0, Math.round(progressPercent)))
    : null;
  const remainingPercent =
    clampedProgress !== null ? Math.max(0, 100 - clampedProgress) : null;

  return { clampedProgress, remainingPercent };
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
  const { clampedProgress, remainingPercent } = resolveProgress(progressPercent);
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
          {remainingPercent !== null ? (
            <span className={classNames.progressLabel}>
              {labels.progressRemaining(remainingPercent)}
            </span>
          ) : null}
          <div
            className={classNames.progress}
            role="progressbar"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={clampedProgress ?? undefined}
            aria-label={
              remainingPercent !== null
                ? labels.progressAriaDeterminate(remainingPercent)
                : labels.progressAriaIndeterminate
            }
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
}) {
  const classNames = loadingActivityBemClasses(config.prefix, {
    withCopyWrapper: config.withCopyWrapper,
  });

  return function DashboardLoadingActivityCard(props: DashboardLoadingActivityCardProps) {
    return (
      <LoadingActivityCard classNames={classNames} labels={config.labels} {...props} />
    );
  };
}
