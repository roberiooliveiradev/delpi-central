import {
  createDashboardNativeFormFields,
  NativeCheckboxControl,
  NativeTextControl,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

/** Alias estáveis — um único import do remote evita duplicate export no Vite/MF. */
export const TmNativeTextControl = NativeTextControl;
export const TmNativeCheckboxControl = NativeCheckboxControl;

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
