import { Sparkles } from "lucide-react";

import { topBarSearchTriggerBemClasses } from "@delpi/plugin-ui/index";

import { useFloatingNotice } from "../../components/ui/FloatingNoticeProvider";
import {
  buildTeoContextClipboardText,
  teoAreaLabel,
  type TeoPortalContext,
} from "./teoPortalContext";

const PILL = topBarSearchTriggerBemClasses("ds");

const NOTICE_ID = "tm-teo-context";

type TeoContextActionProps = {
  context: TeoPortalContext;
  /** View de rota canônica — rotula a área no tooltip. */
  view: string;
};

/**
 * Ação transversal "TÉO" na barra superior. Visível apenas dentro do
 * workspace de processo. Copia o contexto identificador atual para ser
 * usado com o TÉO no ChatGPT — não é autorização nem dado de domínio.
 */
export function TeoContextAction({ context, view }: TeoContextActionProps) {
  const { notifySuccess, notifyError } = useFloatingNotice();

  if (!context.process_id) return null;

  const areaLabel = teoAreaLabel(view, context.area);
  const actionLabel = areaLabel
    ? `Analisar ${areaLabel.toLowerCase()} com TÉO`
    : "Analisar com TÉO";
  const title = `${actionLabel} — copia o contexto atual do Portal para o ChatGPT.`;

  async function handleClick() {
    try {
      await navigator.clipboard.writeText(buildTeoContextClipboardText(context));
      notifySuccess(
        "Contexto copiado para o TÉO",
        "Cole no ChatGPT para o TÉO usar o contexto atual do Portal.",
        NOTICE_ID,
      );
    } catch {
      notifyError("Não foi possível copiar o contexto para o TÉO.", {
        id: NOTICE_ID,
      });
    }
  }

  return (
    <button
      type="button"
      className={PILL.root}
      onClick={() => void handleClick()}
      aria-label={title}
      title={title}
    >
      <Sparkles size={16} strokeWidth={1.75} aria-hidden="true" />
      <span className={`${PILL.label} delpi-ui-topbar-collapse-label`}>TÉO</span>
    </button>
  );
}
