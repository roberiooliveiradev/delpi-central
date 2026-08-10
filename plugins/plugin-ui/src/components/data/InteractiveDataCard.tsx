import type { KeyboardEvent, ReactNode } from "react";

import { FieldLabel } from "../help/FieldLabel";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type InteractiveDataCardValueTone = "title" | "value" | "meta";

export type InteractiveDataCardField = {
  id: string;
  label: string;
  hint?: string;
  value: ReactNode;
  valueTone?: InteractiveDataCardValueTone;
  present?: boolean;
};

export type InteractiveDataCardClassNames = {
  root: string;
  interactive: string;
  field: string;
  fieldLabel: string;
  title: string;
  value: string;
  meta: string;
  actions: string;
  openHint: string;
};

export type InteractiveDataCardProps = {
  fields?: InteractiveDataCardField[];
  children?: ReactNode;
  actions?: ReactNode;
  openHint?: ReactNode;
  ariaLabel?: string;
  onActivate?: () => void;
  interactive?: boolean;
  className?: string;
  classNames: InteractiveDataCardClassNames;
};

export function interactiveDataCardBemClasses(
  prefix: string,
): InteractiveDataCardClassNames {
  const base = `${prefix}-interactive-data-card`;
  const ui = "delpi-ui-interactive-data-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    interactive: pair(`${base}--interactive`, `${ui}--interactive`),
    field: pair(`${base}__field`, `${ui}__field`),
    fieldLabel: pair(`${base}__field-label`, `${ui}__field-label`),
    title: pair(`${base}__title`, `${ui}__title`),
    value: pair(`${base}__value`, `${ui}__value`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    openHint: pair(`${base}__open-hint`, `${ui}__open-hint`),
  };
}

function valueToneClass(
  tone: InteractiveDataCardValueTone | undefined,
  classNames: InteractiveDataCardClassNames,
): string {
  if (tone === "title") return classNames.title;
  if (tone === "value") return classNames.value;
  return classNames.meta;
}

export function InteractiveDataCard({
  fields = [],
  children,
  actions,
  openHint,
  ariaLabel,
  onActivate,
  interactive = Boolean(onActivate),
  className,
  classNames,
}: InteractiveDataCardProps) {
  const visibleFields = fields.filter((field) => field.present !== false);
  const rootClass = [
    classNames.root,
    interactive ? classNames.interactive : null,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const onKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!interactive || !onActivate) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onActivate();
    }
  };

  const fieldNodes =
    children ??
    visibleFields.map((field) => (
      <div key={field.id} className={classNames.field}>
        <FieldLabel
          label={field.label}
          hint={field.hint}
          className={classNames.fieldLabel}
        />
        <div className={valueToneClass(field.valueTone, classNames)}>{field.value}</div>
      </div>
    ));

  const actionsNode =
    actions ??
    (openHint != null ? (
      <div className={classNames.actions}>
        <span className={classNames.openHint} aria-hidden="true">
          {openHint}
        </span>
      </div>
    ) : null);

  return (
    <article
      className={rootClass}
      aria-label={ariaLabel}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={interactive ? onActivate : undefined}
      onKeyDown={interactive ? onKeyDown : undefined}
    >
      {fieldNodes}
      {actionsNode}
    </article>
  );
}

export type DashboardInteractiveDataCardProps = Omit<
  InteractiveDataCardProps,
  "classNames"
>;

export function createDashboardInteractiveDataCard(config: { prefix: string }) {
  const classNames = interactiveDataCardBemClasses(config.prefix);
  return function DashboardInteractiveDataCard(
    props: DashboardInteractiveDataCardProps,
  ) {
    return <InteractiveDataCard classNames={classNames} {...props} />;
  };
}
