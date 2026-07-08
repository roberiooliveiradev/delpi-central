import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui";

const CA_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "ca-field",
  spanWideModifier: "ca-field--wide",
  fieldLabel: "ca-field__label",
};

export const {
  TextField: CaNativeTextField,
  SelectField: CaNativeSelectField,
  TextAreaField: CaNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: CA_FIELD_CLASS_NAMES,
});
