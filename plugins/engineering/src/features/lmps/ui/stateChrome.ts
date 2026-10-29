import {
  delpiUiClass,
  stateBoxPlaceholderBemClasses,
} from "@delpi/plugin-ui/index";

/** Placeholder de gráfico/lista — dual `state-box--empty`. */
export const STATE_BOX_EMPTY = stateBoxPlaceholderBemClasses("lmps");

/** Erro com shell card. */
export const STATE_BOX_ERROR = delpiUiClass(
  "lmps-card lmps-state-box lmps-state-box--error",
  "delpi-ui-card delpi-ui-state-box delpi-ui-state-box--error",
);
