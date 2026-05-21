import type { Medicao } from "../../../data/api/transformometroApi";
import { toMonthInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

type Props = {
  medicao: Medicao;
  onChange: (value: Medicao) => void;
  onSubmit: (e: React.FormEvent) => void;
};

export function RevisaoMedicaoSection({ medicao, onChange, onSubmit }: Props) {
  return (
    <CadastroSection
      title="Medição operacional"
      hint="Volume, tempos e custos usados para calcular economia bruta da revisão."
    >
      <form onSubmit={onSubmit}>
        <div className="ds-filters-row">
          <label className="ds-filter-box">
            Volume mensal
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.volume_mensal}
              onChange={(e) => onChange({ ...medicao, volume_mensal: Number(e.target.value) })}
            />
          </label>
          <label className="ds-filter-box">
            Tempo médio (min)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.tempo_medio_execucao_min}
              onChange={(e) =>
                onChange({ ...medicao, tempo_medio_execucao_min: Number(e.target.value) })
              }
            />
          </label>
          <label className="ds-filter-box">
            Custo hora MO (R$)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.custo_hora_mao_obra}
              onChange={(e) =>
                onChange({ ...medicao, custo_hora_mao_obra: Number(e.target.value) })
              }
            />
          </label>
          <label className="ds-filter-box">
            % retrabalho
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.percentual_retrabalho}
              onChange={(e) =>
                onChange({ ...medicao, percentual_retrabalho: Number(e.target.value) })
              }
            />
          </label>
          <label className="ds-filter-box">
            % erro
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.percentual_erro}
              onChange={(e) => onChange({ ...medicao, percentual_erro: Number(e.target.value) })}
            />
          </label>
          <label className="ds-filter-box">
            Outros desperdícios (R$/mês)
            <input
              type="number"
              min={0}
              step="any"
              value={medicao.custo_outros_desperdicios}
              onChange={(e) =>
                onChange({ ...medicao, custo_outros_desperdicios: Number(e.target.value) })
              }
            />
          </label>
          <label className="ds-filter-box">
            Mês de referência
            <input
              type="month"
              value={toMonthInputValue(medicao.base_referencia_mes)}
              onChange={(e) =>
                onChange({
                  ...medicao,
                  base_referencia_mes: e.target.value || undefined,
                })
              }
            />
          </label>
        </div>
        <button type="submit" className="ds-primary-btn">
          Salvar medição
        </button>
      </form>
    </CadastroSection>
  );
}
