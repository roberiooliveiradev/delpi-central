import { delpiUiClass, sectionCardPacBemClasses } from "@delpi/plugin-ui/index";

/** Placeholder vazio de gráfico/lista — dual `pac-state-box` + kit `--empty`. */
export const PAC_STATE_BOX_EMPTY = delpiUiClass(
  "pac-state-box",
  "delpi-ui-state-box delpi-ui-state-box--empty",
);

/** Classes dual SectionCard (headers thin fora de `<SectionCard>`). */
export const PAC_SECTION = sectionCardPacBemClasses("pac");
