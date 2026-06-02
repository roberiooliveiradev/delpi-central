import type { OptionsData, Revisao } from "../../../data/api/transformometroApi";
import { optionalDateField, toDateInputValue } from "../../../utils/dateInputs";
import { CadastroSection } from "./CadastroSection";

export type RevisaoVigenciaForm = {
  versao_revisao: string;
  cenario_tipo: string;
  data_inicio_vigencia: string;
  data_implantacao: string;
  data_fim_vigencia: string;
  revisao_ativa: boolean;
  descricao_revisao: string;
  motivo_revisao: string;
  observacoes: string;
};

type Props = {
  revisaoVigencia: RevisaoVigenciaForm;
  options: OptionsData;
  onChange: (value: RevisaoVigenciaForm) => void;
  onSubmit: (e: React.FormEvent) => void;
};

export function RevisaoVigenciaSection({ revisaoVigencia, options, onChange, onSubmit }: Props) {
  const isBaseline = revisaoVigencia.cenario_tipo === "baseline";

  return (
    <CadastroSection
      embedded
      title="Vigência e identificação"
      hint="Versão, cenário e período usados no dashboard. Para reativar uma revisão, remova o fim da vigência e marque como ativa."
    >
      <form onSubmit={onSubmit}>
        <div className="ds-filters-row">
          <label className="ds-filter-box">
            Versão *
            <input
              required
              value={revisaoVigencia.versao_revisao}
              onChange={(e) => onChange({ ...revisaoVigencia, versao_revisao: e.target.value })}
            />
          </label>
          <label className="ds-filter-box">
            Cenário *
            <select
              required
              value={revisaoVigencia.cenario_tipo}
              onChange={(e) => {
                const cenario = e.target.value;
                onChange({
                  ...revisaoVigencia,
                  cenario_tipo: cenario,
                  revisao_ativa: cenario === "baseline" ? false : revisaoVigencia.revisao_ativa,
                });
              }}
            >
              {options.cenario_tipo.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>
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
                onChange({
                  ...revisaoVigencia,
                  data_fim_vigencia: e.target.value,
                  revisao_ativa: e.target.value || isBaseline ? false : revisaoVigencia.revisao_ativa,
                })
              }
            />
          </label>
          <label className="ds-filter-box ds-filter-box--checkbox">
            <input
              type="checkbox"
              checked={revisaoVigencia.revisao_ativa}
              disabled={isBaseline || Boolean(revisaoVigencia.data_fim_vigencia)}
              onChange={(e) =>
                onChange({ ...revisaoVigencia, revisao_ativa: e.target.checked })
              }
            />
            Marcar como revisão ativa
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
    versao_revisao: revisao.versao_revisao ?? "",
    cenario_tipo: revisao.cenario_tipo ?? "baseline",
    data_inicio_vigencia: toDateInputValue(revisao.data_inicio_vigencia),
    data_implantacao: toDateInputValue(revisao.data_implantacao),
    data_fim_vigencia: toDateInputValue(revisao.data_fim_vigencia),
    revisao_ativa: Boolean(revisao.revisao_ativa),
    descricao_revisao: revisao.descricao_revisao ?? "",
    motivo_revisao: revisao.motivo_revisao ?? "",
    observacoes: revisao.observacoes ?? "",
  };
}

export function revisaoPayloadFromVigenciaForm(form: RevisaoVigenciaForm) {
  return {
    versao_revisao: form.versao_revisao.trim(),
    cenario_tipo: form.cenario_tipo,
    data_inicio_vigencia: form.data_inicio_vigencia,
    data_implantacao: optionalDateField(form.data_implantacao),
    data_fim_vigencia: optionalDateField(form.data_fim_vigencia),
    revisao_ativa: form.cenario_tipo === "baseline" ? false : form.revisao_ativa,
    descricao_revisao: form.descricao_revisao.trim() || undefined,
    motivo_revisao: form.motivo_revisao.trim() || undefined,
    observacoes: form.observacoes.trim() || undefined,
  };
}
