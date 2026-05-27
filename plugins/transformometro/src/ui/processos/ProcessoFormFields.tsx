import type { OptionsData } from "../../data/api/transformometroApi";
import type { ProcessoFormState } from "./processoForm";

type Props = {
  form: ProcessoFormState;
  options: OptionsData;
  codigoProcesso?: string | null;
  onChange: (next: ProcessoFormState) => void;
};

export function ProcessoFormFields({ form, options, codigoProcesso, onChange }: Props) {
  const set = (patch: Partial<ProcessoFormState>) => onChange({ ...form, ...patch });

  return (
    <div className="ds-filters-row ds-filters-row--extended">
      {codigoProcesso ? (
        <div className="ds-filter-box">
          <label htmlFor="tm-proc-codigo">Código</label>
          <input id="tm-proc-codigo" readOnly value={codigoProcesso} />
        </div>
      ) : null}
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-nome">Nome do processo *</label>
        <input
          id="tm-proc-nome"
          required
          value={form.nome_processo}
          onChange={(e) => set({ nome_processo: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-filial">Filial *</label>
        <select
          id="tm-proc-filial"
          value={form.filial_id}
          onChange={(e) => set({ filial_id: e.target.value })}
        >
          {options.filiais.map((f) => (
            <option key={f.id} value={f.id}>
              {f.label}
            </option>
          ))}
        </select>
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-setor">Setor *</label>
        <select
          id="tm-proc-setor"
          value={form.setor_id}
          onChange={(e) => set({ setor_id: e.target.value })}
        >
          {options.setores.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-status">Status *</label>
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
        <label htmlFor="tm-proc-familia">Família (rateio)</label>
        <input
          id="tm-proc-familia"
          placeholder="ex.: ia, automação"
          value={form.familia_processo}
          onChange={(e) => set({ familia_processo: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-ferramenta">Agrupador ferramenta</label>
        <input
          id="tm-proc-ferramenta"
          placeholder="ex.: ChatGPT, Power Automate"
          value={form.agrupador_ferramenta}
          onChange={(e) => set({ agrupador_ferramenta: e.target.value })}
        />
      </div>
      <div className="ds-filter-box">
        <label htmlFor="tm-proc-gestor">Gestor responsável</label>
        <input
          id="tm-proc-gestor"
          value={form.gestor_responsavel}
          onChange={(e) => set({ gestor_responsavel: e.target.value })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-objetivo">Objetivo</label>
        <textarea
          id="tm-proc-objetivo"
          rows={2}
          value={form.objetivo_processo}
          onChange={(e) => set({ objetivo_processo: e.target.value })}
        />
      </div>
      <div className="ds-filter-box ds-filter-box--wide">
        <label htmlFor="tm-proc-descricao">Descrição</label>
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
