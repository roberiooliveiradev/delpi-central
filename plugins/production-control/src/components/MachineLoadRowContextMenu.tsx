import {
  ContextMenu,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import { ArrowUpToLine, CalendarOff, Folders, MoveRight, Route } from "lucide-react";

import { copy } from "../content/copy";
import type { MachineLoadOperation } from "../types";
import { conjuntoKeyFromOrder } from "../utils/machineLoadLocate";

type Props = {
  open: boolean;
  position: FixedPanelPoint | null;
  operation: MachineLoadOperation | null;
  onClose: () => void;
  /** Rastreia o conjunto = todas as OPs com o mesmo C2_NUM (6 primeiros dígitos). */
  onTraceConjunto: (conjuntoKey: string) => void;
  /** Leva as OPs do conjunto ao topo da fila de cada centro de trabalho. */
  onPrioritizeConjunto: (conjuntoKey: string) => void;
  /** Tira o conjunto da fila de todos os centros e do cockpit do operador. */
  onWithdrawConjunto: (conjuntoKey: string) => void;
  /** Move só as OPs do conjunto que estão no centro atual. */
  onTransferConjunto: (operation: MachineLoadOperation) => void;
  /** Abre a escolha do centro de trabalho de destino desta operação (item). */
  onTransferOperation: (operation: MachineLoadOperation) => void;
  prioritizeDisabled?: boolean;
  withdrawDisabled?: boolean;
  transferDisabled?: boolean;
};

/** Menu de ações do PCP ao clicar com o botão direito em uma linha da carga máquina. */
export function MachineLoadRowContextMenu({
  open,
  position,
  operation,
  onClose,
  onTraceConjunto,
  onPrioritizeConjunto,
  onWithdrawConjunto,
  onTransferConjunto,
  onTransferOperation,
  prioritizeDisabled = false,
  withdrawDisabled = false,
  transferDisabled = false,
}: Props) {
  const conjuntoKey = conjuntoKeyFromOrder(operation?.production_order);
  const hasConjunto = Boolean(conjuntoKey);
  const hasOperation = Boolean(operation?.production_order && operation?.operation_code);

  return (
    <ContextMenu
      open={open}
      position={position}
      onClose={onClose}
      aria-label={copy.machineLoad.rowActions.menuAria}
      portalScopeClassName="dashboard-production-control"
    >
      <ContextMenuItem
        label={
          hasConjunto
            ? copy.machineLoad.rowActions.traceConjunto
            : copy.machineLoad.rowActions.traceConjuntoDisabled
        }
        icon={Route}
        disabled={!hasConjunto}
        onSelect={() => {
          if (!conjuntoKey) return;
          onTraceConjunto(conjuntoKey);
          onClose();
        }}
      />
      <ContextMenuItem
        label={
          hasConjunto
            ? copy.machineLoad.rowActions.prioritizeConjunto
            : copy.machineLoad.rowActions.prioritizeConjuntoDisabled
        }
        icon={ArrowUpToLine}
        disabled={!hasConjunto || prioritizeDisabled}
        onSelect={() => {
          if (!conjuntoKey) return;
          onPrioritizeConjunto(conjuntoKey);
          onClose();
        }}
      />
      <ContextMenuItem
        label={
          hasConjunto
            ? copy.machineLoad.rowActions.withdrawConjunto
            : copy.machineLoad.rowActions.withdrawConjuntoDisabled
        }
        icon={CalendarOff}
        disabled={!hasConjunto || withdrawDisabled}
        onSelect={() => {
          if (!conjuntoKey) return;
          onWithdrawConjunto(conjuntoKey);
          onClose();
        }}
      />
      <ContextMenuItem
        label={
          hasConjunto
            ? copy.machineLoad.rowActions.transferConjunto
            : copy.machineLoad.rowActions.transferConjuntoDisabled
        }
        icon={Folders}
        disabled={!hasConjunto || transferDisabled}
        onSelect={() => {
          if (!operation) return;
          onTransferConjunto(operation);
          onClose();
        }}
      />
      <ContextMenuItem
        label={
          hasOperation
            ? copy.machineLoad.rowActions.transferOperation
            : copy.machineLoad.rowActions.transferOperationDisabled
        }
        icon={MoveRight}
        disabled={!hasOperation || transferDisabled}
        onSelect={() => {
          if (!operation) return;
          onTransferOperation(operation);
          onClose();
        }}
      />
    </ContextMenu>
  );
}
