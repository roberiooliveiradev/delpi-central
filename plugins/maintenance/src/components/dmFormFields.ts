import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

const DM_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "dm-field",
  spanWideModifier: "dm-field--span-full",
  fieldLabel: "dm-field__label",
};

export const {
  TextField: DmNativeTextField,
  SelectField: DmNativeSelectField,
  TextAreaField: DmNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: DM_FIELD_CLASS_NAMES,
});
