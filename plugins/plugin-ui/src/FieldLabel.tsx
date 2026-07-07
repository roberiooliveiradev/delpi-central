import { HelpTooltip } from "./HelpTooltip";

export type FieldLabelProps = {
  label: string;
  hint?: string;
  htmlFor?: string;
  className?: string;
};

/** Rótulo de formulário com balão de ajuda opcional (?). */
export function FieldLabel({ label, hint, htmlFor, className = "delpi-ui-field-label" }: FieldLabelProps) {
  const content = (
    <>
      {label}
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} /> : null}
    </>
  );

  if (htmlFor) {
    return (
      <label className={className} htmlFor={htmlFor}>
        {content}
      </label>
    );
  }

  return <span className={className}>{content}</span>;
}
