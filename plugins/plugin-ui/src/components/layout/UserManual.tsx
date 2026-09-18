import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type UserManualClassNames = {
  root: string;
  eyebrow: string;
  scope: string;
  layout: string;
  toc: string;
  tocTitle: string;
  tocList: string;
  tocLink: string;
  main: string;
  section: string;
  intro: string;
  concepts: string;
  concept: string;
  list: string;
  tableWrap: string;
  table: string;
  where: string;
  toolLink: string;
  faq: string;
  faqItem: string;
  glossary: string;
  glossaryItem: string;
  glossaryGroup: string;
  glossaryGroupTitle: string;
  glossaryApplies: string;
  glossaryAppliesLabel: string;
};

export function userManualBemClasses(prefix: string): UserManualClassNames {
  const base = `${prefix}-user-manual`;
  const ui = "delpi-ui-user-manual";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    eyebrow: pair(`${base}__eyebrow`, `${ui}__eyebrow`),
    scope: pair(`${base}__scope`, `${ui}__scope`),
    layout: pair(`${base}__layout`, `${ui}__layout`),
    toc: pair(`${base}__toc`, `${ui}__toc`),
    tocTitle: pair(`${base}__toc-title`, `${ui}__toc-title`),
    tocList: pair(`${base}__toc-list`, `${ui}__toc-list`),
    tocLink: pair(`${base}__toc-link`, `${ui}__toc-link`),
    main: pair(`${base}__main`, `${ui}__main`),
    section: pair(`${base}__section`, `${ui}__section`),
    intro: pair(`${base}__intro`, `${ui}__intro`),
    concepts: pair(`${base}__concepts`, `${ui}__concepts`),
    concept: pair(`${base}__concept`, `${ui}__concept`),
    list: pair(`${base}__list`, `${ui}__list`),
    tableWrap: pair(`${base}__table-wrap`, `${ui}__table-wrap`),
    table: pair(`${base}__table`, `${ui}__table`),
    where: pair(`${base}__where`, `${ui}__where`),
    toolLink: pair(`${base}__tool-link`, `${ui}__tool-link`),
    faq: pair(`${base}__faq`, `${ui}__faq`),
    faqItem: pair(`${base}__faq-item`, `${ui}__faq-item`),
    glossary: pair(`${base}__glossary`, `${ui}__glossary`),
    glossaryItem: pair(`${base}__glossary-item`, `${ui}__glossary-item`),
    glossaryGroup: pair(`${base}__glossary-group`, `${ui}__glossary-group`),
    glossaryGroupTitle: pair(`${base}__glossary-group-title`, `${ui}__glossary-group-title`),
    glossaryApplies: pair(`${base}__glossary-applies`, `${ui}__glossary-applies`),
    glossaryAppliesLabel: pair(`${base}__glossary-applies-label`, `${ui}__glossary-applies-label`),
  };
}

export function UserManual({
  classNames,
  children,
  className,
}: {
  classNames: UserManualClassNames;
  children: ReactNode;
  className?: string;
}) {
  return <div className={[classNames.root, className].filter(Boolean).join(" ")}>{children}</div>;
}

export function UserManualEyebrow({
  classNames,
  children,
}: {
  classNames: UserManualClassNames;
  children: ReactNode;
}) {
  return <span className={classNames.eyebrow}>{children}</span>;
}

export function UserManualScope({
  classNames,
  children,
}: {
  classNames: UserManualClassNames;
  children: ReactNode;
}) {
  return <p className={classNames.scope}>{children}</p>;
}

export function UserManualSection({
  classNames,
  id,
  children,
}: {
  classNames: UserManualClassNames;
  id?: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className={classNames.section}>
      {children}
    </section>
  );
}

export type UserManualTocItem = {
  id: string;
  label: string;
  onSelect: () => void;
};

export function UserManualLayout({
  classNames,
  title,
  "aria-label": ariaLabel,
  items,
  children,
}: {
  classNames: UserManualClassNames;
  title: string;
  "aria-label": string;
  items: readonly UserManualTocItem[];
  children: ReactNode;
}) {
  return (
    <div className={classNames.layout}>
      <nav className={classNames.toc} aria-label={ariaLabel}>
        <p className={classNames.tocTitle}>{title}</p>
        <ul className={classNames.tocList}>
          {items.map((item) => (
            <li key={item.id}>
              <button type="button" className={classNames.tocLink} onClick={item.onSelect}>
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>
      <div className={classNames.main}>{children}</div>
    </div>
  );
}

export function UserManualConcepts({
  classNames,
  items,
}: {
  classNames: UserManualClassNames;
  items: readonly { term: string; meaning: ReactNode }[];
}) {
  return (
    <ul className={classNames.concepts}>
      {items.map((item) => (
        <li key={item.term} className={classNames.concept}>
          <strong>{item.term}</strong>
          {typeof item.meaning === "string" ? <p>{item.meaning}</p> : item.meaning}
        </li>
      ))}
    </ul>
  );
}

export function UserManualGuideTable({
  classNames,
  rows,
}: {
  classNames: UserManualClassNames;
  rows: readonly { want: ReactNode; where: ReactNode; how: ReactNode }[];
}) {
  return (
    <div className={classNames.tableWrap}>
      <table className={classNames.table}>
        <thead>
          <tr>
            <th scope="col">Quero…</th>
            <th scope="col">Onde ir</th>
            <th scope="col">Como</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={index}>
              <td>{row.want}</td>
              <td>{row.where}</td>
              <td>{row.how}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function UserManualFaq({
  classNames,
  items,
}: {
  classNames: UserManualClassNames;
  items: readonly { q: ReactNode; a: ReactNode }[];
}) {
  return (
    <dl className={classNames.faq}>
      {items.map((item, index) => (
        <div key={index} className={classNames.faqItem}>
          <dt>{item.q}</dt>
          <dd>{item.a}</dd>
        </div>
      ))}
    </dl>
  );
}

export type UserManualGlossaryEntry = {
  term: ReactNode;
  meaning: ReactNode;
  applies?: ReactNode;
};

export function UserManualGlossary({
  classNames,
  items,
  appliesLabel = "Onde aparece",
}: {
  classNames: UserManualClassNames;
  items: readonly UserManualGlossaryEntry[];
  appliesLabel?: string;
}) {
  return (
    <dl className={classNames.glossary}>
      {items.map((item, index) => (
        <div key={index} className={classNames.glossaryItem}>
          <dt>{item.term}</dt>
          <dd>
            {item.meaning}
            {item.applies ? (
              <p className={classNames.glossaryApplies}>
                <span className={classNames.glossaryAppliesLabel}>{appliesLabel}</span>
                {item.applies}
              </p>
            ) : null}
          </dd>
        </div>
      ))}
    </dl>
  );
}

export function createDashboardUserManual(config: { prefix: string }) {
  const classNames = userManualBemClasses(config.prefix);
  return {
    classNames,
    Frame: (props: { children: ReactNode; className?: string }) => (
      <UserManual classNames={classNames} {...props} />
    ),
    Eyebrow: (props: { children: ReactNode }) => (
      <UserManualEyebrow classNames={classNames} {...props} />
    ),
    Scope: (props: { children: ReactNode }) => (
      <UserManualScope classNames={classNames} {...props} />
    ),
    Section: (props: { id?: string; children: ReactNode }) => (
      <UserManualSection classNames={classNames} {...props} />
    ),
    Layout: (
      props: Omit<Parameters<typeof UserManualLayout>[0], "classNames">,
    ) => <UserManualLayout classNames={classNames} {...props} />,
    Concepts: (
      props: Omit<Parameters<typeof UserManualConcepts>[0], "classNames">,
    ) => <UserManualConcepts classNames={classNames} {...props} />,
    GuideTable: (
      props: Omit<Parameters<typeof UserManualGuideTable>[0], "classNames">,
    ) => <UserManualGuideTable classNames={classNames} {...props} />,
    Faq: (props: Omit<Parameters<typeof UserManualFaq>[0], "classNames">) => (
      <UserManualFaq classNames={classNames} {...props} />
    ),
    Glossary: (
      props: Omit<Parameters<typeof UserManualGlossary>[0], "classNames">,
    ) => <UserManualGlossary classNames={classNames} {...props} />,
  };
}
