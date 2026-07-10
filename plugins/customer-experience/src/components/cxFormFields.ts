import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

const CX_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "cx-field",
  spanWideModifier: "cx-field--full",
  fieldLabel: "cx-field__label",
};

export const {
  TextField: CxNativeTextField,
  SelectField: CxNativeSelectField,
  TextAreaField: CxNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: CX_FIELD_CLASS_NAMES,
});
