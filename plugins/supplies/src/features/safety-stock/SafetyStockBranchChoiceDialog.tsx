import { useState } from "react";

import { formatSuppliesUnitName } from "../../app/suppliesUnits";
import {
  SuppliesActionButton,
  SuppliesModal,
} from "../../app/suppliesUi";
import { SAFETY_STOCK_DETAIL_CONTENT as D } from "./content";
import { SAFETY_STOCK_ALL_SCOPE } from "./types";
import { normalizeBranchScope } from "./query";

type SafetyStockBranchChoiceDialogProps = {
  /** Código do material consolidado; `null` = fechado. */
  productCode: string | null;
  /** Filiais operacionais ofertadas (`01`, `02`, …) — sem `all`. */
  branches: string[];
  onPick: (branch: string) => void;
  onClose: () => void;
};

/**
 * E11.S7 — etapa de escolha de filial para linhas consolidadas (`branch=all`).
 * Apenas seleção: nenhum request de detalhe é feito antes do usuário confirmar;
 * sem filial pré-selecionada por padrão.
 */
export function SafetyStockBranchChoiceDialog({
  productCode,
  branches,
  onPick,
  onClose,
}: SafetyStockBranchChoiceDialogProps) {
  // Escolha chaveada pelo material: cada abertura começa sem seleção e
  // nunca assume a filial usada antes — sem setState dentro de effect.
  const [picked, setPicked] = useState<{ key: string; branch: string } | null>(
    null,
  );
  const open = productCode != null;
  const selected =
    productCode != null && picked?.key === productCode ? picked.branch : null;

  const close = () => {
    setPicked(null);
    onClose();
  };

  const concreteBranches = branches.filter(
    (branch) => normalizeBranchScope(branch) !== SAFETY_STOCK_ALL_SCOPE,
  );

  return (
    <SuppliesModal
      open={open}
      title={D.chooseBranchTitle}
      onClose={close}
      className="sp-safety-stock-branch-choice"
      closeAriaLabel={D.chooseBranchCancel}
      footer={
        <>
          <SuppliesActionButton
            type="button"
            variant="ghost"
            onClick={close}
          >
            {D.chooseBranchCancel}
          </SuppliesActionButton>
          <SuppliesActionButton
            type="button"
            variant="primary"
            disabled={!selected}
            onClick={() => {
              if (!selected) return;
              setPicked(null);
              onPick(selected);
            }}
          >
            {D.chooseBranchConfirm}
          </SuppliesActionButton>
        </>
      }
    >
      <p className="sp-safety-stock-branch-choice__description">
        {D.chooseBranchDescription(productCode ?? "")}
      </p>
      <div
        className="sp-safety-stock-branch-choice__options"
        role="radiogroup"
        aria-label={D.chooseBranchTitle}
      >
        {concreteBranches.map((branch) => {
          const name = formatSuppliesUnitName(branch);
          const active = selected === branch;
          return (
            <button
              key={branch}
              type="button"
              role="radio"
              aria-checked={active}
              aria-label={D.chooseBranchOptionAria(name, branch)}
              className={`sp-safety-stock-branch-choice__option${
                active
                  ? " sp-safety-stock-branch-choice__option--active"
                  : ""
              }`}
              onClick={() => {
                if (productCode != null) {
                  setPicked({ key: productCode, branch });
                }
              }}
            >
              <span className="sp-safety-stock-branch-choice__option-name">
                {name}
              </span>
              <span className="sp-safety-stock-branch-choice__option-code">
                {branch}
              </span>
            </button>
          );
        })}
      </div>
    </SuppliesModal>
  );
}
