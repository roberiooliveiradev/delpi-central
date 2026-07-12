/** Junta classes CSS sem espaços vazios. */
export function mergeClassNames(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

export const NATIVE_CONTROL_CLASS = "delpi-ui-native-control";
export const NATIVE_CONTROL_SELECT_CLASS = "delpi-ui-native-control--select";
export const NATIVE_CONTROL_TEXTAREA_CLASS = "delpi-ui-native-control--textarea";
export const NATIVE_CONTROL_COMPACT_CLASS = "delpi-ui-native-control--compact";
