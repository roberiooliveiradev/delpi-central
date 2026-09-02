import type { ReactNode } from "react";

import {
  createDashboardNativeFormFields,
  formFieldShellBemClasses,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

const PP_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  ...formFieldShellBemClasses("pp"),
  spanWideModifier: "pp-form-grid__span-full",
};

export const {
  FormFieldShell: PpFormFieldShell,
  TextField: PpNativeTextField,
  SelectField: PpNativeSelectField,
  TextAreaField: PpNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: PP_FIELD_CLASS_NAMES,
});

export function ppFieldError(message?: string | null): ReactNode {
  return message ? <span className="pp-field-error">{message}</span> : null;
}

export function ppFieldHint(message?: string | null): ReactNode {
  return message ? <span className="pp-field-hint">{message}</span> : null;
}
