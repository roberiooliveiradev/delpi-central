import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui";

/** Shell alinhado ao CSS histórico `.ql-field` / `.ql-label-text`. */
const QL_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "ql-field",
  spanWideModifier: "ql-field--wide",
  fieldLabel: "ql-label-text",
};

export const {
  TextField: QlNativeTextField,
  SelectField: QlNativeSelectField,
  TextAreaField: QlNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: QL_FIELD_CLASS_NAMES,
});
