import { HelpTooltip } from "@delpi/plugin-ui";

type TitleWithHelpProps = {
  title: string;
  hint?: string;
  className?: string;
};

export function TitleWithHelp({ title, hint, className }: TitleWithHelpProps) {
  return (
    <span className={`pac-title-with-help${className ? ` ${className}` : ""}`}>
      <span>{title}</span>
      {hint ? <HelpTooltip content={hint} ariaLabel={`Ajuda: ${title}`} /> : null}
    </span>
  );
}
