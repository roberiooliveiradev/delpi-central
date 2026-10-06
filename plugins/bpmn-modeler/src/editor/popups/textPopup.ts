/**
 * Provider customizado de popup "text" (editor ampliado de campos
 * textarea, ex.: Documentação). Equivalente ao `TextPopup` interno do
 * vendor, registrado via extension point oficial
 * `feelPopup.registerProvider('text', ...)` — prioridade default (1000)
 * ganha do built-in LOW_PRIORITY.
 *
 * Motivo: o vendor hardcoded `closeButtonTooltip: "Save and close"` sem
 * prop de tradução em `bpmn-js-properties-panel@5.65.1` /
 * `@bpmn-io/properties-panel@3.55.0`. Aqui o tooltip recebe a tradução
 * PT-BR injetada. O componente precisa renderizar vnodes preact —
 * usa `preact/jsx-runtime` do root (10.29.8, mesma versão empacotada
 * pelo vendor) e é deliberadamente hooks-free: o popup é renderizado
 * pela instância preact DO VENDOR, e hooks importados de outra instância
 * leriam internals inexistentes (`__H` undefined). Vnodes são objetos
 * planos — renderizam sob qualquer instância preact compatível.
 *
 * Vendor equivalente: `@bpmn-io/properties-panel` `TextPopup`
 * (dist/index.esm.js ~L5076). Se o vendor expuser `closeButtonTooltip`
 * como prop/translate, este provider pode ser removido.
 */

import { jsx, jsxs } from "preact/jsx-runtime";
import { Popup } from "@bpmn-io/properties-panel";

/* eslint-disable @typescript-eslint/no-explicit-any */

const TEXT_POPUP_WIDTH = 700;
const TEXT_POPUP_HEIGHT = 400;

// mesma regra do vendor: id do editor do popup tem prefixo para não
// colidir com o campo in-panel, que segue montado (oculto) no DOM
function popupEntryId(id: string) {
  return `bio-properties-panel-popup-${id}`;
}

export interface TextPopupPtBrProps {
  entryId: string;
  onInput: (value: string) => void;
  onClose: () => void;
  title: string;
  value: string;
  sourceElement?: HTMLElement;
  translate: (s: string) => string;
}

export function TextPopupPtBr(props: TextPopupPtBrProps) {
  const { entryId, onInput, onClose, title, value, sourceElement, translate } =
    props;

  const handleSetReturnFocus = () => {
    sourceElement && sourceElement.focus();
  };

  return jsxs(Popup, {
    className: "bio-properties-panel-text-popup",
    title: title,
    returnFocus: false,
    closeOnEscape: true,
    delayInitialFocus: false,
    onClose: onClose,
    onPostDeactivate: handleSetReturnFocus,
    height: TEXT_POPUP_HEIGHT,
    width: TEXT_POPUP_WIDTH,
    children: [
      jsx(Popup.Title, {
        title: title,
        showCloseButton: true,
        closeButtonTooltip: translate("Save and close"),
        onClose: onClose,
        draggable: true,
      }),
      jsx(Popup.Body, {
        children: jsx("textarea", {
          id: popupEntryId(entryId),
          name: entryId,
          class: "bio-properties-panel-input",
          // autofocus do vendor é useEffect pós-mount; ref callback
          // dispara no mesmo momento sem depender de hooks
          ref: ((el: HTMLTextAreaElement | null) => el?.focus()) as any,
          onInput: (e: any) => onInput(e.target.value),
          value: value || "",
          spellCheck: "false",
          autoComplete: "off",
          "aria-label": title,
          "data-gramm": "false",
        }),
      }),
    ],
  });
}
