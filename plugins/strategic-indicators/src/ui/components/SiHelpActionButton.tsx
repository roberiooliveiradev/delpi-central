import type { ButtonHTMLAttributes, ReactNode } from "react";

type SiHelpActionButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  helpHint: string;
  children: ReactNode;
};

/** Botão admin com tooltip de help canônico (`SI_HELP`). */
export function SiHelpActionButton({
  helpHint,
  children,
  title,
  ...rest
}: SiHelpActionButtonProps) {
  return (
    <button type="button" title={title ?? helpHint} {...rest}>
      {children}
    </button>
  );
}
