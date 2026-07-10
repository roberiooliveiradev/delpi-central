import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

const CXFORM_PREVIEW_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "cxform-field",
  spanWideModifier: "cxform-field--full",
  fieldLabel: "cxform-label",
};

export const {
  TextField: CxFormPreviewTextField,
  TextAreaField: CxFormPreviewTextAreaField,
} = createDashboardNativeFormFields({
  classNames: CXFORM_PREVIEW_FIELD_CLASS_NAMES,
});
