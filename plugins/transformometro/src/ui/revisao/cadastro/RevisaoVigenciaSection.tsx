import type { Revisao } from "../../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

type RevisaoDatas = {
  data_inicio_vigencia: string;
  data_implantacao: string;
  data_fim_vigencia: string;
};

type Props = {
  revisaoDatas: RevisaoDatas;
  onChange: (value: RevisaoDatas) => void;
  onSubmit: (e: React.FormEvent) => void;
};

export function RevisaoVigenciaSection({ revisaoDatas, onChange, onSubmit }: Props) {
  return (
    <CadastroSection
      title="Vigência da revisão"
      hint="Período em que a revisão entra no cálculo do dashboard. Deixe fim vazio para vigência aberta."
    >
      <form onSubmit={onSubmit}>
        <div className="ds-filters-row">
          <label className="ds-filter-box">
            Início vigência *
            <input
              type="date"
              required
              value={revisaoDatas.data_inicio_vigencia}
              onChange={(e) =>
                onChange({ ...revisaoDatas, data_inicio_vigencia: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box">
            Implantação
            <input
              type="date"
              value={revisaoDatas.data_implantacao}
              onChange={(e) =>
                onChange({ ...revisaoDatas, data_implantacao: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box">
            Fim vigência
            <input
              type="date"
              value={revisaoDatas.data_fim_vigencia}
              onChange={(e) =>
                onChange({ ...revisaoDatas, data_fim_vigencia: e.target.value })
              }
            />
          </label>
        </div>
        <button type="submit" className="ds-primary-btn">
          Salvar vigência
        </button>
      </form>
    </CadastroSection>
  );
}

export function buildRevisaoDatasFromRevisao(revisao: Revisao): RevisaoDatas {
  return {
    data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
    data_implantacao: toDateInputValue(revisao.data_implantacao),
    data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
  };
}

export function revisaoPayloadDates(datas: RevisaoDatas) {
  return {
    data_inicio_vigencia: datas.data_inicio_vigencia,
    data_implantacao: optionalDateField(datas.data_implantacao),
    data_fim_vigencia: optionalDateField(datas.data_fim_vigencia),
  };
}
