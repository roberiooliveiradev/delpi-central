import type { ReactNode } from "react";

import { delpiUiClass, withBemModifier } from "../../utils/delpiUiClass";

export type EntityUnfurlField = {
  id: string;
  label: string;
  value: string;
};

export type EntityUnfurlCardClassNames = {
  root: string;
  title: string;
  kind: string;
  fields: string;
  field: string;
  fieldLabel: string;
  fieldValue: string;
  denied: string;
  actions: string;
  action: string;
};

export type EntityUnfurlCardProps = {
  title: string;
  classNames: EntityUnfurlCardClassNames;
  /** Host kind label (already localized). */
  kindLabel?: string;
  fields?: readonly EntityUnfurlField[];
  /** When false, show denied state instead of fields. */
  accessible?: boolean;
  deniedLabel?: string;
  openLabel?: string;
  onOpen?: () => void;
  footer?: ReactNode;
  className?: string;
};

export function entityUnfurlCardBemClasses(prefix: string): EntityUnfurlCardClassNames {
  const base = `${prefix}-entity-unfurl`;
  const ui = "delpi-ui-entity-unfurl";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    title: pair(`${base}__title`, `${ui}__title`),
    kind: pair(`${base}__kind`, `${ui}__kind`),
    fields: pair(`${base}__fields`, `${ui}__fields`),
    field: pair(`${base}__field`, `${ui}__field`),
    fieldLabel: pair(`${base}__field-label`, `${ui}__field-label`),
    fieldValue: pair(`${base}__field-value`, `${ui}__field-value`),
    denied: pair(`${base}__denied`, `${ui}__denied`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
    action: pair(`${base}__action`, `${ui}__action`),
  };
}

/**
 * Generic entity preview card. Host supplies fields / denied copy —
 * the kit never branches on entity kind.
 */
export function EntityUnfurlCard({
  title,
  classNames,
  kindLabel,
  fields = [],
  accessible = true,
  deniedLabel,
  openLabel,
  onOpen,
  footer,
  className,
}: EntityUnfurlCardProps) {
  const rootClass = [
    accessible ? classNames.root : withBemModifier(classNames.root, "denied"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <aside className={rootClass} data-accessible={accessible ? "true" : "false"}>
      <div className={classNames.title}>{title}</div>
      {kindLabel ? <div className={classNames.kind}>{kindLabel}</div> : null}
      {accessible ? (
        fields.length > 0 ? (
          <dl className={classNames.fields}>
            {fields.map((field) => (
              <div key={field.id} className={classNames.field}>
                <dt className={classNames.fieldLabel}>{field.label}</dt>
                <dd className={classNames.fieldValue}>{field.value}</dd>
              </div>
            ))}
          </dl>
        ) : null
      ) : (
        <p className={classNames.denied}>{deniedLabel}</p>
      )}
      {accessible && openLabel && onOpen ? (
        <div className={classNames.actions}>
          <button type="button" className={classNames.action} onClick={onOpen}>
            {openLabel}
          </button>
        </div>
      ) : null}
      {footer}
    </aside>
  );
}

export type DashboardEntityUnfurlCardProps = Omit<EntityUnfurlCardProps, "classNames">;

export function createDashboardEntityUnfurlCard(prefix: string) {
  const classNames = entityUnfurlCardBemClasses(prefix);
  return function DashboardEntityUnfurlCard(props: DashboardEntityUnfurlCardProps) {
    return <EntityUnfurlCard classNames={classNames} {...props} />;
  };
}
