import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

export {
  NativeTextControl as TmNativeTextControl,
  NativeCheckboxControl as TmNativeCheckboxControl,
} from "@delpi/plugin-ui/index";

/** Campos nativos alinhados ao shell `ds-filter-box` / `tm-field__label`. */
const TM_NATIVE_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "ds-filter-box",
  spanWideModifier: "ds-filter-box--wide",
  fieldLabel: "tm-field__label",
};

export const {
  TextField: TmNativeTextField,
  TextAreaField: TmNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: TM_NATIVE_FIELD_CLASS_NAMES,
});
