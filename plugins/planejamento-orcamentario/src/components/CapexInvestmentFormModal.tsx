import { CapexInvestmentFormPage } from "../pages/CapexInvestmentFormPage";
import type { CapexInvestment } from "../types/budgetPlanning";
import { HostContainedModal } from "./uiKit";

export type CapexInvestmentFormModalState =
  | { open: false }
  | { open: true; mode: "create" }
  | { open: true; mode: "edit"; investmentId: string };

type CapexInvestmentFormModalProps = {
  state: CapexInvestmentFormModalState;
  costCenterId: string;
  unitId?: string | null;
  onClose: () => void;
  onSaved?: (investment: CapexInvestment) => void;
};

export function CapexInvestmentFormModal({
  state,
  costCenterId,
  unitId,
  onClose,
  onSaved,
}: CapexInvestmentFormModalProps) {
  const open = state.open;
  const mode = open ? state.mode : "create";
  const investmentId = open && state.mode === "edit" ? state.investmentId : null;
  const title =
    mode === "create"
      ? "Novo investimento"
      : "Editar investimento";

  return (
    <HostContainedModal open={open} title={title} onClose={onClose}>
      {open ? (
        <CapexInvestmentFormPage
          key={mode === "edit" ? investmentId ?? "edit" : "create"}
          mode={mode}
          investmentId={investmentId}
          costCenterId={costCenterId}
          unitId={unitId}
          presentation="panel"
          onClose={onClose}
          onSaved={onSaved}
        />
      ) : null}
    </HostContainedModal>
  );
}
