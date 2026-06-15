import type { ReactNode } from "react";

type FormSectionProps = {
  title: string;
  children: ReactNode;
};

export function FormSection({ title, children }: FormSectionProps) {
  return (
    <section>
      <h2 className="kz-section-title">{title}</h2>
      <div className="kz-form-grid">{children}</div>
    </section>
  );
}
