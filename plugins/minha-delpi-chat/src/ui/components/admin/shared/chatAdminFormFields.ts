import {
  createDashboardNativeFormFields,
  type FormFieldShellClassNames,
} from "@delpi/plugin-ui/index";

const CHAT_ADMIN_FIELD_CLASS_NAMES: FormFieldShellClassNames = {
  root: "mdc-admin-field",
  spanWideModifier: "mdc-admin-field--wide",
  fieldLabel: "mdc-admin-field__label",
};

export const {
  TextField: ChatAdminNativeTextField,
  SelectField: ChatAdminNativeSelectField,
  TextAreaField: ChatAdminNativeTextAreaField,
} = createDashboardNativeFormFields({
  classNames: CHAT_ADMIN_FIELD_CLASS_NAMES,
});

export { ChatNativeTextAreaControl } from "../../shared/chatNativeFormFields";
