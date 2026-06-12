import type { FormEvent, ReactNode } from "react";

type FilterBarProps = {
  children?: ReactNode;
  leading?: ReactNode;
  onSubmit?: (event: FormEvent<HTMLFormElement>) => void;
  className?: string;
  embedded?: boolean;
};

export function FilterBar({ children, leading, onSubmit, className, embedded = false }: FilterBarProps) {
  const rootClass = [embedded ? "" : "dm-card", "dm-filter-bar", className]
    .filter(Boolean)
    .join(" ");

  if (onSubmit) {
    return (
      <form className={rootClass} onSubmit={onSubmit}>
        {leading}
        {children}
      </form>
    );
  }

  return (
    <section className={rootClass}>
      {leading}
      {children}
    </section>
  );
}
