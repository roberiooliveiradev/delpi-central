import {
  ContextMenu,
  ContextMenuItem,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import { ArrowUpToLine, CalendarOff, Folders, Group, ListChecks, MoveRight, Route, X } from "lucide-react";

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
  /**
   * Quando ≥2 operações estão selecionadas e o clique direito cai em uma delas,
   * o menu assume o modo coletivo: «Agrupar» executa o agrupamento da Etapa 3
   * quando elegível; transferência e retirada coletivas seguem desabilitadas
   * até os contratos da Etapa 4 existirem.
   */
  selectionCount?: number;
  onClearSelection?: () => void;
  /** Elegível → habilita «Agrupar operações selecionadas». */
  onGroupSelected?: () => void;
  /** Bloqueios de elegibilidade (run aberto, filtro, execução indisponível). */
  groupDisabled?: boolean;
  groupDisabledHint?: string;
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
  selectionCount = 0,
  onClearSelection,
  onGroupSelected,
  groupDisabled = false,
  groupDisabledHint,
}: Props) {
  const conjuntoKey = conjuntoKeyFromOrder(operation?.production_order);
  const hasConjunto = Boolean(conjuntoKey);
  const hasOperation = Boolean(operation?.production_order && operation?.operation_code);
  const collective = selectionCount >= 2 && Boolean(onClearSelection);

  if (collective) {
    return (
      <ContextMenu
        open={open}
        position={position}
        onClose={onClose}
        aria-label={copy.machineLoad.rowActions.selectionMenuAria}
        portalScopeClassName="dashboard-production-control"
      >
        <ContextMenuItem
          label={copy.machineLoad.rowActions.selectionHeader(selectionCount)}
          icon={ListChecks}
          disabled
        />
        <ContextMenuItem
          label={copy.machineLoad.rowActions.groupSelected}
          icon={Group}
          disabled={groupDisabled || !onGroupSelected}
          hint={groupDisabled ? groupDisabledHint : undefined}
          hintTrigger="label"
          onSelect={() => {
            onGroupSelected?.();
            onClose();
          }}
        />
        <ContextMenuItem
          label={copy.machineLoad.rowActions.transferSelected}
          icon={MoveRight}
          disabled
          hint={copy.machineLoad.rowActions.collectivePendingHint}
          hintTrigger="label"
        />
        <ContextMenuItem
          label={copy.machineLoad.rowActions.withdrawSelected}
          icon={CalendarOff}
          disabled
          hint={copy.machineLoad.rowActions.collectivePendingHint}
          hintTrigger="label"
        />
        <ContextMenuItem
          label={copy.machineLoad.rowActions.clearSelection}
          icon={X}
          onSelect={() => {
            onClearSelection?.();
            onClose();
          }}
        />
      </ContextMenu>
    );
  }

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
