import { FieldLabel } from "../../components/HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import { filterSetoresByFilial, resolveSetorIdForFilial } from "../../utils/setores";
import type { ProcessoFormState } from "./processoForm";

type Props = {
  form: ProcessoFormState;
  options: OptionsData;
  codigoProcesso?: string | null;
  showInstanciaFields?: boolean;
  onChange: (next: ProcessoFormState) => void;
};

export function ProcessoFormFields({
  form,
  options,
  codigoProcesso,
  showInstanciaFields = true,
  onChange,
}: Props) {
  const set = (patch: Partial<ProcessoFormState>) => onChange({ ...form, ...patch });
  const setoresDisponiveis = filterSetoresByFilial(options.setores, form.filial_id);

  function handleFilialChange(filialId: string) {
    onChange({
      ...form,
      filial_id: filialId,
      setor_id: resolveSetorIdForFilial(options.setores, filialId, form.setor_id),
    });
  }

  return (
    <div className="ds-filters-row ds-filters-row--extended">
      {codigoProcesso ? (
        <div className="ds-filter-box">
          <FieldLabel label="Código" hint={TM_HELP_TOOLTIPS.processos.codigo} />
          <input id="tm-proc-codigo" readOnly value={codigoProcesso} />
        </div>
      ) : null}
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-nome">
          <FieldLabel label="Nome do processo *" hint={TM_HELP_TOOLTIPS.processos.nome} />
        </label>
        <input
          id="tm-proc-nome"
          required
          value={form.nome_processo}
          onChange={(e) => set({ nome_processo: e.target.value })}
        />
      </div>
      {showInstanciaFields ? (
        <>
          <div className="ds-filter-box">
            <label htmlFor="tm-proc-filial">
              <FieldLabel label="Unidade *" hint={TM_HELP_TOOLTIPS.processos.unidade} />
            </label>
            <select
              id="tm-proc-filial"
              value={form.filial_id}
              onChange={(e) => handleFilialChange(e.target.value)}
            >
              {options.filiais.map((f) => (
                <option key={f.id} value={f.id}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
          <div className="ds-filter-box">
            <label htmlFor="tm-proc-setor">
              <FieldLabel label="Setor *" hint={TM_HELP_TOOLTIPS.processos.setor} />
            </label>
            <select
              id="tm-proc-setor"
              value={form.setor_id}
              onChange={(e) => set({ setor_id: e.target.value })}
              disabled={setoresDisponiveis.length === 0}
            >
              {setoresDisponiveis.map((setor) => (
                <option key={setor.id} value={setor.id}>
                  {setor.label}
                </option>
              ))}
            </select>
          </div>
        </>
      ) : null}
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-status">
          <FieldLabel label="Status *" hint={TM_HELP_TOOLTIPS.processos.status} />
        </label>
        <select
          id="tm-proc-status"
          value={form.status_processo}
          onChange={(e) => set({ status_processo: e.target.value })}
        >
          {options.status_processo.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-familia">
          <FieldLabel label="Família (rateio)" hint={TM_HELP_TOOLTIPS.processos.familia} />
        </label>
        <input
          id="tm-proc-familia"
          placeholder="ex.: ia, automação"
          value={form.familia_processo}
          onChange={(e) => set({ familia_processo: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-ferramenta">
          <FieldLabel label="Agrupador ferramenta" hint={TM_HELP_TOOLTIPS.processos.agrupadorFerramenta} />
        </label>
        <input
          id="tm-proc-ferramenta"
          placeholder="ex.: ChatGPT, Power Automate"
          value={form.agrupador_ferramenta}
          onChange={(e) => set({ agrupador_ferramenta: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-gestor">
          <FieldLabel label="Gestor responsável" hint={TM_HELP_TOOLTIPS.processos.gestor} />
        </label>
        <input
          id="tm-proc-gestor"
          value={form.gestor_responsavel}
          onChange={(e) => set({ gestor_responsavel: e.target.value })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-objetivo">
          <FieldLabel label="Objetivo" hint={TM_HELP_TOOLTIPS.processos.objetivo} />
        </label>
        <textarea
          id="tm-proc-objetivo"
          rows={2}
          value={form.objetivo_processo}
          onChange={(e) => set({ objetivo_processo: e.target.value })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-descricao">
          <FieldLabel label="Descrição" hint={TM_HELP_TOOLTIPS.processos.descricao} />
        </label>
        <textarea
          id="tm-proc-descricao"
          rows={2}
          value={form.descricao_processo}
          onChange={(e) => set({ descricao_processo: e.target.value })}
        />
      </div>
    </div>
  );
}
