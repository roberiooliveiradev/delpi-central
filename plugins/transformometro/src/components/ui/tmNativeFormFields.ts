import {
  createDashboardNativeFormFields,
  NativeCheckboxControl,
  NativeTextControl,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

import { DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_WIDE_MOD } from "../filterChrome";

/** Alias estáveis — um único import do remote evita duplicate export no Vite/MF. */
export const TmNativeTextControl = NativeTextControl;
export const TmNativeCheckboxControl = NativeCheckboxControl;

/** Campos nativos alinhados ao shell `ds-filter-box` dual + `tm-field__label`. */
const TM_NATIVE_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: DS_FILTER_BOX_PLAIN,
  spanWideModifier: DS_FILTER_BOX_WIDE_MOD,
  fieldLabel: "tm-field__label",
};

export const {
  TextField: TmNativeTextField,
  TextAreaField: TmNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: TM_NATIVE_FIELD_CLASS_NAMES,
});
