import type { ReactNode } from "react";
import { createDashboardFormFieldShell } from "@delpi/plugin-ui/index";

import { TD_FIELD_CLASS_NAMES } from "../tdFormFields";

const Shell = createDashboardFormFieldShell({ classNames: TD_FIELD_CLASS_NAMES });

type Props = {
  id?: string;
  label: string;
  hint?: string;
  children: ReactNode;
  className?: string;
};

/**
 * Campo de formulário do deck — shell canônico do plugin-ui (`FormFieldShell`)
 * com classes `td-field` do TV Dashboard.
 */
export function DeckField({ id, label, hint, children, className }: Props) {
  return (
    <Shell id={id ?? ""} label={label} hint={hint} className={className}>
      {children}
    </Shell>
  );
}
