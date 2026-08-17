import type { MouseEventHandler, ReactNode } from "react";

import { isSafeNavigationHref } from "../layout/PagePath";
import { delpiUiClass } from "../../utils/delpiUiClass";

export type DataRecordCardField = {
  id: string;
  label: ReactNode;
  value: ReactNode;
  present?: boolean;
};

export type DataRecordCardClassNames = {
  root: string;
  leading: string;
  body: string;
  header: string;
  title: string;
  subtitle: string;
  status: string;
  fields: string;
  field: string;
  fieldLabel: string;
  fieldValue: string;
  context: string;
};

export type DataRecordCardProps = {
  leading?: ReactNode;
  title: ReactNode;
  subtitle?: ReactNode;
  status?: ReactNode;
  fields?: DataRecordCardField[];
  context?: ReactNode;
  href?: string;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
  ariaLabel?: string;
  className?: string;
  classNames: DataRecordCardClassNames;
};

export function dataRecordCardBemClasses(prefix: string): DataRecordCardClassNames {
  const base = `${prefix}-data-record-card`;
  const ui = "delpi-ui-data-record-card";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    leading: pair(`${base}__leading`, `${ui}__leading`),
    body: pair(`${base}__body`, `${ui}__body`),
    header: pair(`${base}__header`, `${ui}__header`),
    title: pair(`${base}__title`, `${ui}__title`),
    subtitle: pair(`${base}__subtitle`, `${ui}__subtitle`),
    status: pair(`${base}__status`, `${ui}__status`),
    fields: pair(`${base}__fields`, `${ui}__fields`),
    field: pair(`${base}__field`, `${ui}__field`),
    fieldLabel: pair(`${base}__field-label`, `${ui}__field-label`),
    fieldValue: pair(`${base}__field-value`, `${ui}__field-value`),
    context: pair(`${base}__context`, `${ui}__context`),
  };
}

export function DataRecordCard({
  leading,
  title,
  subtitle,
  status,
  fields = [],
  context,
  href,
  onNavigate,
  ariaLabel,
  className,
  classNames,
}: DataRecordCardProps) {
  if (href != null && !isSafeNavigationHref(href)) {
    throw new Error("DataRecordCard recebeu um href que não é interno ao host.");
  }

  const visibleFields = fields.filter((field) => field.present !== false);
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const content = (
    <>
      {leading ? (
        <span className={classNames.leading} aria-hidden="true">
          {leading}
        </span>
      ) : null}
      <div className={classNames.body}>
        <div className={classNames.header}>
          <div>
            <span className={classNames.title}>{title}</span>
            {subtitle ? <span className={classNames.subtitle}>{subtitle}</span> : null}
          </div>
          {status ? <span className={classNames.status}>{status}</span> : null}
        </div>
        {visibleFields.length > 0 ? (
          <dl className={classNames.fields}>
            {visibleFields.map((field) => (
              <div key={field.id} className={classNames.field}>
                <dt className={classNames.fieldLabel}>{field.label}</dt>
                <dd className={classNames.fieldValue}>{field.value}</dd>
              </div>
            ))}
          </dl>
        ) : null}
        {context ? <span className={classNames.context}>{context}</span> : null}
      </div>
    </>
  );

  if (href != null) {
    return (
      <a
        className={rootClass}
        href={href.trim()}
        onClick={onNavigate}
        aria-label={ariaLabel}
      >
        {content}
      </a>
    );
  }

  return (
    <article className={rootClass} aria-label={ariaLabel}>
      {content}
    </article>
  );
}

export type DashboardDataRecordCardProps = Omit<
  DataRecordCardProps,
  "classNames"
>;

export function createDashboardDataRecordCard(config: { prefix: string }) {
  const classNames = dataRecordCardBemClasses(config.prefix);
  return function DashboardDataRecordCard(props: DashboardDataRecordCardProps) {
    return <DataRecordCard classNames={classNames} {...props} />;
  };
}
