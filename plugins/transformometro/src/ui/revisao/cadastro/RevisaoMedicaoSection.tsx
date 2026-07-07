import type { Medicao } from "../../../data/api/transformometroApi";
import { FieldLabel } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import { toMonthInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

const R = TM_HELP_TOOLTIPS.revisao;

type Props = {
  medicao: Medicao;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  hideSubmit?: boolean;
  onChange: (value: Medicao) => void;
  onSubmit: (e: React.FormEvent) => void;
};

function MedicaoReadContent({ medicao }: { medicao: Medicao }) {
  return (
    <>
      <dl className="ds-dl-grid">
        <div><dt>Volume mensal</dt><dd>{medicao.volume_mensal}</dd></div>
        <div><dt>Tempo médio (min)</dt><dd>{medicao.tempo_medio_execucao_min}</dd></div>
        <div><dt>Tempo retrabalho (min)</dt><dd>{medicao.tempo_retrabalho_min}</dd></div>
        <div><dt>Custo hora MO</dt><dd>{medicao.custo_hora_mao_obra}</dd></div>
        <div><dt>% retrabalho</dt><dd>{medicao.percentual_retrabalho}</dd></div>
        <div><dt>% erro</dt><dd>{medicao.percentual_erro}</dd></div>
        <div><dt>Qtd. erros/mês</dt><dd>{medicao.quantidade_erros_mes}</dd></div>
        <div><dt>Custo unit. erro</dt><dd>{medicao.custo_unitario_erro}</dd></div>
        <div><dt>Custo unit. retrabalho</dt><dd>{medicao.custo_unitario_retrabalho}</dd></div>
        <div><dt>Outros desperdícios</dt><dd>{medicao.custo_outros_desperdicios}</dd></div>
        <div><dt>Mês referência</dt><dd>{toMonthInputValue(medicao.base_referencia_mes) || "—"}</dd></div>
      </dl>
      {medicao.observacoes ? (
        <p className="ds-hint"><strong>Observações:</strong> {medicao.observacoes}</p>
      ) : null}
    </>
  );
}

export function RevisaoMedicaoSection({
  medicao,
  readOnly = false,
  embeddedInCard = false,
  hideSubmit = false,
  onChange,
  onSubmit,
}: Props) {
  if (readOnly) {
    const content = <MedicaoReadContent medicao={medicao} />;
    if (embeddedInCard) return content;
    return (
      <CadastroSection embedded title="Medição operacional">
        {content}
      </CadastroSection>
    );
  }

  const form = (
    <form onSubmit={onSubmit}>
      <div className="ds-filters-row">
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Volume mensal" hint={R.volumeMensal} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.volume_mensal}
            onChange={(e) => onChange({ ...medicao, volume_mensal: Number(e.target.value) })}
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Tempo médio (min)" hint={R.tempoMedio} />
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
          <FieldLabel className="tm-field__label" label="Tempo retrabalho (min)" hint={R.tempoRetrabalho} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.tempo_retrabalho_min}
            onChange={(e) =>
              onChange({ ...medicao, tempo_retrabalho_min: Number(e.target.value) })
            }
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Custo hora MO (R$)" hint={R.custoHoraMo} />
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
          <FieldLabel className="tm-field__label" label="% retrabalho" hint={R.percentualRetrabalho} />
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
          <FieldLabel className="tm-field__label" label="% erro" hint={R.percentualErro} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.percentual_erro}
            onChange={(e) => onChange({ ...medicao, percentual_erro: Number(e.target.value) })}
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Qtd. erros/mês" hint={R.quantidadeErros} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.quantidade_erros_mes}
            onChange={(e) =>
              onChange({ ...medicao, quantidade_erros_mes: Number(e.target.value) })
            }
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Custo unit. erro (R$)" hint={R.custoUnitarioErro} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.custo_unitario_erro}
            onChange={(e) =>
              onChange({ ...medicao, custo_unitario_erro: Number(e.target.value) })
            }
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Custo unit. retrabalho (R$)" hint={R.custoUnitarioRetrabalho} />
          <input
            type="number"
            min={0}
            step="any"
            value={medicao.custo_unitario_retrabalho}
            onChange={(e) =>
              onChange({ ...medicao, custo_unitario_retrabalho: Number(e.target.value) })
            }
          />
        </label>
        <label className="ds-filter-box">
          <FieldLabel className="tm-field__label" label="Outros desperdícios (R$/mês)" hint={R.outrosDesperdicios} />
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
          <FieldLabel className="tm-field__label" label="Mês de referência" hint={R.mesReferencia} />
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
      <label className="ds-filter-box ds-filter-box--wide">
        <FieldLabel className="tm-field__label" label="Observações" hint={R.medicaoObservacoes} />
        <textarea
          rows={2}
          value={medicao.observacoes ?? ""}
          onChange={(e) =>
            onChange({
              ...medicao,
              observacoes: e.target.value.trim() || undefined,
            })
          }
        />
      </label>
      {hideSubmit ? null : (
        <button type="submit" className="ds-primary-btn">
          Salvar medição
        </button>
      )}
    </form>
  );

  if (embeddedInCard) return form;

  return (
    <CadastroSection
      embedded
      title="Medição operacional"
      hint="Volume, tempos e custos usados para calcular economia bruta da revisão."
    >
      {form}
    </CadastroSection>
  );
}
