import {
  createDashboardNativeFormFields,
  formFieldShellBemClasses,
} from "@delpi/plugin-ui";

/** Campos nativos do formulário de nova auditoria (BEM a5s-field*). */
export const {
  TextField: AuditNativeTextField,
  SelectField: AuditNativeSelectField,
  TextAreaField: AuditNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: formFieldShellBemClasses("a5s"),
});
