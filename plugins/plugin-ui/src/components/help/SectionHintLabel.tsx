import { HelpTooltip } from "./HelpTooltip";

export type SectionHintLabelProps = {
  label: string;
  hint: string;
  className?: string;
};

/** Rótulo de seção (ribbon, painel) com balão ao passar o mouse. */
export function SectionHintLabel({ label, hint, className }: SectionHintLabelProps) {
  return (
    <HelpTooltip content={hint} ariaLabel={`Ajuda: ${label}`} wrap placement="bottom">
      <span className={className}>{label}</span>
    </HelpTooltip>
  );
}
