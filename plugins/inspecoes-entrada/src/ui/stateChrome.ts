import {
  delpiUiClass,
  stateBoxCompactPlaceholderBemClasses,
  stateBoxPlaceholderBemClasses,
} from "@delpi/plugin-ui/index";

/** Empty / loading de página — dual `--empty`. */
export const IE_STATE_BOX = stateBoxPlaceholderBemClasses("ie");

/** Placeholder compacto (listas / modal). */
export const IE_STATE_BOX_COMPACT = stateBoxCompactPlaceholderBemClasses("ie");

/** Mensagem positiva compacta (ex.: sem rejeições). */
export const IE_STATE_BOX_COMPACT_POSITIVE = delpiUiClass(
  "ie-state-box ie-state-box--empty ie-state-box--compact ie-state-box--positive",
  "delpi-ui-state-box delpi-ui-state-box--empty delpi-ui-state-box--compact delpi-ui-state-box--positive",
);
