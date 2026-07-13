import {
  createDashboardNativeFormFields,
  NativeTextAreaControl,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

export const TD_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "td-field",
  spanWideModifier: "td-deck-tabs__field--wide",
  fieldLabel: "td-field__label",
};

export const {
  TextField: TdNativeTextField,
  SelectField: TdNativeSelectField,
  TextAreaField: TdNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: TD_FIELD_CLASS_NAMES,
});

export { NativeTextAreaControl as TdNativeTextAreaControl };
