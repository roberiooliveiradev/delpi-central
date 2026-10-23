import type { ConsumptionAnalysisItem } from "../types/consumptionAnalysis";
import type { SafetyStockItem } from "../types/safetyStock";
import { ConsumptionAnalysisDetailProductSearch } from "./ConsumptionAnalysisDetailProductSearch";
import { SafetyStockDetailProductSearch } from "./SafetyStockDetailProductSearch";

type ProductQuickSearchProps =
  | {
      mode: "monitor";
      branch: string;
      disabled?: boolean;
      onSelect: (item: SafetyStockItem) => void;
    }
  | {
      mode: "analysis";
      branch: string;
      disabled?: boolean;
      onSelect: (item: ConsumptionAnalysisItem) => void;
    };

/** Consulta rápida no topo da página — abre o detalhe sem filtrar a tabela. */
export function ProductQuickSearch(props: ProductQuickSearchProps) {
  const { branch, disabled = false } = props;
  const inputId =
    props.mode === "monitor" ? "ess-quick-search-monitor" : "ess-quick-search-analysis";

  return (
    <section className="ess-quick-search ess-card delpi-ui-card" aria-label="Consulta rápida">
      <div className="ess-quick-search__header">
        <label className="ess-quick-search__label" htmlFor={inputId}>
          Consultar produto
        </label>
        <p className="ess-quick-search__hint">
          Digite o código ou a descrição para abrir o detalhe sem percorrer a lista.
        </p>
      </div>
      {props.mode === "monitor" ? (
        <SafetyStockDetailProductSearch
          branch={branch}
          onNavigate={props.onSelect}
          inputId={inputId}
          variant="page"
          disabled={disabled}
          placeholder="Código ou descrição…"
          ariaLabel="Consultar produto"
        />
      ) : (
        <ConsumptionAnalysisDetailProductSearch
          branch={branch}
          onNavigate={props.onSelect}
          inputId={inputId}
          variant="page"
          disabled={disabled}
          placeholder="Código ou descrição…"
          ariaLabel="Consultar produto"
        />
      )}
    </section>
  );
}
