import { useEffect, useRef, useState } from "react";
import { HandHelping } from "lucide-react";
import type { MachineLoadOperation } from "./api.ts";
import { useOperatorSession } from "./OperatorSessionContext.ts";
import { feedbackStatusPresentation } from "./operatorFeedback.ts";
import { OperatorHelpSheet } from "./OperatorHelpSheet.tsx";
import { useOperatorFeedback } from "./useOperatorFeedback.ts";
import type { MachineLoadRealtimeEvent } from "./usePublicMachineLoadRealtime.ts";

type Props = {
  token: string;
  branch: string;
  operation: MachineLoadOperation;
  workCenter: string;
  realtimeConnected: boolean;
  resyncSignal: number;
  feedbackRealtimeEvent: MachineLoadRealtimeEvent | null;
};

/**
 * Entrada compacta «Pedir ajuda» do detalhe da operação. Substitui a área
 * fixa «Solicitações do operador»: ocupa uma linha no corpo da página e abre
 * a central guiada (OperatorHelpSheet) sob demanda. O badge resume o
 * impedimento PCP ativo sem card permanente — o hook segue vivo aqui para
 * sinalizar status e alimentar a etapa «Em andamento» do sheet.
 */
export function OperatorHelpLauncher({
  token,
  branch,
  operation,
  workCenter,
  realtimeConnected,
  resyncSignal,
  feedbackRealtimeEvent,
}: Props) {
  const { session, invalidate } = useOperatorSession();
  const feedback = useOperatorFeedback({
    token,
    productionOrder: operation.production_order,
    operationCode: operation.operation_code,
    sessionToken: session?.sessionToken ?? null,
    realtimeConnected,
    feedbackRealtimeEvent,
    resyncSignal,
    onAuthError: invalidate,
  });
  const [open, setOpen] = useState(false);
  const launcherRef = useRef<HTMLButtonElement>(null);

  // Retorno de foco: ao fechar a superfície, o launcher recebe o foco de
  // volta — ciclo completo de acessibilidade do diálogo.
  const wasOpenRef = useRef(false);
  useEffect(() => {
    if (wasOpenRef.current && !open) {
      launcherRef.current?.focus();
    }
    wasOpenRef.current = open;
  }, [open]);

  const activePresentation = feedbackStatusPresentation(
    feedback.active?.status,
  );
  const ariaLabel = feedback.active
    ? "Pedir ajuda — " + activePresentation.label
    : "Pedir ajuda";

  return (
    <div className="pcp-pub__help">
      <button
        ref={launcherRef}
        type="button"
        className="pcp-pub__help-launcher"
        aria-label={ariaLabel}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen(true)}
      >
        <HandHelping size={20} strokeWidth={2.2} aria-hidden="true" />
        Pedir ajuda
        {feedback.active ? (
          <span className="pcp-pub__help-badge" aria-hidden="true">
            1
          </span>
        ) : null}
      </button>

      <OperatorHelpSheet
        open={open}
        token={token}
        branch={branch}
        operation={operation}
        workCenter={workCenter}
        feedback={feedback}
        onClose={() => setOpen(false)}
      />
    </div>
  );
}
