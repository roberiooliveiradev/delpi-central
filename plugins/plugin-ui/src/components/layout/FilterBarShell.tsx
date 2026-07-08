import type { FormEvent, ReactNode } from "react";

export type FilterBarShellClassNames = {
  root: string;
  rootWithCard: string;
  grid?: string;
};

export type FilterBarShellProps = {
  children: ReactNode;
  leading?: ReactNode;
  onSubmit?: (event: FormEvent<HTMLFormElement>) => void;
  embedded?: boolean;
  layout?: "inline" | "grid";
  className?: string;
  ariaLabel?: string;
  classNames: FilterBarShellClassNames;
};

export function filterBarShellBemClasses(
  prefix: string,
  options?: { withGrid?: boolean; block?: string },
): FilterBarShellClassNames {
  const block = options?.block ?? "filter-bar";
  const bar = `${prefix}-${block}`;
  const card = `${prefix}-card`;
  const useCard = block === "filter-bar";

  return {
    root: bar,
    rootWithCard: useCard ? `${card} ${bar}` : bar,
    grid: options?.withGrid ? `${bar}__grid` : undefined,
  };
}

export function FilterBarShell({
  children,
  leading,
  onSubmit,
  embedded = false,
  layout = "inline",
  className,
  ariaLabel,
  classNames,
}: FilterBarShellProps) {
  const rootClass = [embedded ? classNames.root : classNames.rootWithCard, className]
    .filter(Boolean)
    .join(" ");

  const body =
    layout === "grid" && classNames.grid ? (
      <div className={classNames.grid}>{children}</div>
    ) : (
      children
    );

  const content = (
    <>
      {leading}
      {body}
    </>
  );

  if (onSubmit) {
    return (
      <form className={rootClass} onSubmit={onSubmit} aria-label={ariaLabel}>
        {content}
      </form>
    );
  }

  return (
    <section className={rootClass} aria-label={ariaLabel}>
      {content}
    </section>
  );
}

export type DashboardFilterBarShellProps = Omit<FilterBarShellProps, "classNames">;

export function createFilterBarShell(config: {
  prefix: string;
  withGrid?: boolean;
  /** BEM block (default `filter-bar`). Ex.: `analytics-filters`. */
  block?: string;
  /** Se true, usa só `root` (sem classe de card). */
  embeddedByDefault?: boolean;
  defaultAriaLabel?: string;
}) {
  const classNames = filterBarShellBemClasses(config.prefix, {
    withGrid: config.withGrid,
    block: config.block,
  });

  return function DashboardFilterBarShell({
    ariaLabel,
    embedded,
    ...props
  }: DashboardFilterBarShellProps) {
    return (
      <FilterBarShell
        classNames={classNames}
        ariaLabel={ariaLabel ?? config.defaultAriaLabel}
        layout={config.withGrid ? "grid" : "inline"}
        embedded={embedded ?? config.embeddedByDefault ?? false}
        {...props}
      />
    );
  };
}
