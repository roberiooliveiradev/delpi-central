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
 * workspace de processo. O contexto de navegação já é compartilhado
 * automaticamente pelo canal canônico (workspace_context_v1 no Core +
 * site tool WebMCP) — o clique apenas explica isso e orienta a conversa.
 * "Copiar contexto" permanece como fallback explícito dentro do aviso
 * para ambientes onde o canal automático não alcança o TÉO.
 */
export function TeoContextAction({ context, view }: TeoContextActionProps) {
  const { notice, notifySuccess, notifyError } = useFloatingNotice();

  if (!context.process_id) return null;

  const areaLabel = teoAreaLabel(view, context.area);
  const actionLabel = areaLabel
    ? `Analisar ${areaLabel.toLowerCase()} com TÉO`
    : "Analisar com TÉO";
  const title = `${actionLabel} — o TÉO já recebe o contexto atual do Portal automaticamente.`;

  const sharedParts = ["processo"];
  if (context.instance_id) sharedParts.push("melhoria");
  if (context.revision_id) sharedParts.push("revisão");
  if (areaLabel) sharedParts.push(`seção ${areaLabel.toLowerCase()}`);

  async function copyContextFallback() {
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

  function handleClick() {
    notice({
      id: NOTICE_ID,
      variant: "info",
      title: "O TÉO já sabe onde você está",
      message:
        `O contexto atual do Portal (${sharedParts.join(", ")}) é ` +
        `compartilhado automaticamente. Abra o TÉO no ChatGPT e pergunte ` +
        `normalmente — por exemplo, "analise este processo".`,
      autoDismissMs: null,
      action: {
        label: "Copiar contexto",
        onClick: () => void copyContextFallback(),
      },
    });
  }

  return (
    <button
      type="button"
      className={PILL.root}
      onClick={handleClick}
      aria-label={title}
      title={title}
    >
      <Sparkles size={16} strokeWidth={1.75} aria-hidden="true" />
      <span className={`${PILL.label} delpi-ui-topbar-collapse-label`}>TÉO</span>
    </button>
  );
}
