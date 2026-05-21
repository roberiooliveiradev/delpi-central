import type { Revisao } from "../../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

export type RevisaoVigenciaForm = {
  data_inicio_vigencia: string;
  data_implantacao: string;
  data_fim_vigencia: string;
  descricao_revisao: string;
  motivo_revisao: string;
  observacoes: string;
};

type Props = {
  revisaoVigencia: RevisaoVigenciaForm;
  onChange: (value: RevisaoVigenciaForm) => void;
  onSubmit: (e: React.FormEvent) => void;
};

export function RevisaoVigenciaSection({ revisaoVigencia, onChange, onSubmit }: Props) {
  return (
    <CadastroSection
      embedded
      title="Vigência e identificação"
      hint="Período de cálculo no dashboard e texto de apoio à revisão. Deixe fim vazio para vigência aberta."
    >
      <form onSubmit={onSubmit}>
        <div className="ds-filters-row">
          <label className="ds-filter-box">
            Início vigência *
            <input
              type="date"
              required
              value={revisaoVigencia.data_inicio_vigencia}
              onChange={(e) =>
                onChange({ ...revisaoVigencia, data_inicio_vigencia: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box">
            Implantação
            <input
              type="date"
              value={revisaoVigencia.data_implantacao}
              onChange={(e) =>
                onChange({ ...revisaoVigencia, data_implantacao: e.target.value })
              }
            />
          </label>
          <label className="ds-filter-box">
            Fim vigência
            <input
              type="date"
              value={revisaoVigencia.data_fim_vigencia}
              onChange={(e) =>
                onChange({ ...revisaoVigencia, data_fim_vigencia: e.target.value })
              }
            />
          </label>
        </div>
        <label className="ds-filter-box ds-filter-box--wide">
          Descrição da revisão
          <input
            value={revisaoVigencia.descricao_revisao}
            onChange={(e) =>
              onChange({ ...revisaoVigencia, descricao_revisao: e.target.value })
            }
            placeholder="Ex.: Automação do fechamento mensal"
          />
        </label>
        <label className="ds-filter-box ds-filter-box--wide">
          Motivo da revisão
          <input
            value={revisaoVigencia.motivo_revisao}
            onChange={(e) =>
              onChange({ ...revisaoVigencia, motivo_revisao: e.target.value })
            }
            placeholder="Ex.: Nova ferramenta / mudança de escopo"
          />
        </label>
        <label className="ds-filter-box ds-filter-box--wide">
          Observações
          <textarea
            rows={2}
            value={revisaoVigencia.observacoes}
            onChange={(e) => onChange({ ...revisaoVigencia, observacoes: e.target.value })}
          />
        </label>
        <button type="submit" className="ds-primary-btn">
          Salvar vigência e identificação
        </button>
      </form>
    </CadastroSection>
  );
}

export function buildRevisaoVigenciaFromRevisao(revisao: Revisao): RevisaoVigenciaForm {
  return {
    data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
    data_implantacao: toDateInputValue(revisao.data_implantacao),
    data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
    descricao_revisao: revisao.descricao_revisao ?? "",
    motivo_revisao: revisao.motivo_revisao ?? "",
    observacoes: revisao.observacoes ?? "",
  };
}

export function revisaoPayloadFromVigenciaForm(form: RevisaoVigenciaForm) {
  return {
    data_inicio_vigencia: form.data_inicio_vigencia,
    data_implantacao: optionalDateField(form.data_implantacao),
    data_fim_vigencia: optionalDateField(form.data_fim_vigencia),
    descricao_revisao: form.descricao_revisao.trim() || undefined,
    motivo_revisao: form.motivo_revisao.trim() || undefined,
    observacoes: form.observacoes.trim() || undefined,
  };
}
