import { createDashboardNativeFormFields, formFieldShellKaizenClasses } from "@delpi/plugin-ui/index";

export const { FormFieldShell, TextField, SelectField, TextAreaField } =
  createDashboardNativeFormFields({
    classNames: formFieldShellKaizenClasses("kz"),
  });

/** Alias semântico do shell label + controle. */
export const FormField = FormFieldShell;

export type { NativeSelectOption as SelectOption } from "@delpi/plugin-ui/index";
