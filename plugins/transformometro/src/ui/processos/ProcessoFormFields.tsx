import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions, mapSelectOptionsFromItems } from "../../components/ui/selectTypes";
import { TmNativeTextAreaField, TmNativeTextField } from "../../components/ui/tmNativeFormFields";
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
        <TmNativeTextField
          id="tm-proc-codigo"
          label="Código"
          hint={TM_HELP_TOOLTIPS.processos.codigo}
          value={codigoProcesso}
          onChange={() => undefined}
          readOnly
        />
      ) : null}
      <TmNativeTextField
        id="tm-proc-nome"
        label="Nome do processo *"
        hint={TM_HELP_TOOLTIPS.processos.nome}
        className="ds-filter-box--wide"
        value={form.nome_processo}
        onChange={(nome_processo) => set({ nome_processo })}
        required
      />
      {showInstanciaFields ? (
        <>
          <SelectField
            id="tm-proc-filial"
            label="Unidade *"
            hint={TM_HELP_TOOLTIPS.processos.unidade}
            value={form.filial_id}
            onChange={handleFilialChange}
            options={mapSelectOptionsFromItems(
              options.filiais,
              (filial) => filial.id,
              (filial) => filial.label
            )}
          />
          <SelectField
            id="tm-proc-setor"
            label="Departamento *"
            hint={TM_HELP_TOOLTIPS.processos.setor}
            value={form.setor_id}
            onChange={(setorId) => set({ setor_id: setorId })}
            disabled={setoresDisponiveis.length === 0}
            options={mapSelectOptionsFromItems(
              setoresDisponiveis,
              (setor) => setor.id,
              (setor) => setor.label
            )}
          />
        </>
      ) : null}
      <SelectField
        id="tm-proc-status"
        label="Status *"
        hint={TM_HELP_TOOLTIPS.processos.status}
        value={form.status_processo}
        onChange={(status) => set({ status_processo: status })}
        options={mapSelectOptions(options.status_processo)}
      />
      <TmNativeTextField
        id="tm-proc-familia"
        label="Família (rateio)"
        hint={TM_HELP_TOOLTIPS.processos.familia}
        value={form.familia_processo}
        onChange={(familia_processo) => set({ familia_processo })}
        placeholder="ex.: ia, automação"
      />
      <TmNativeTextField
        id="tm-proc-ferramenta"
        label="Agrupador ferramenta"
        hint={TM_HELP_TOOLTIPS.processos.agrupadorFerramenta}
        value={form.agrupador_ferramenta}
        onChange={(agrupador_ferramenta) => set({ agrupador_ferramenta })}
        placeholder="ex.: ChatGPT, Power Automate"
      />
      <TmNativeTextField
        id="tm-proc-gestor"
        label="Gestor responsável"
        hint={TM_HELP_TOOLTIPS.processos.gestor}
        value={form.gestor_responsavel}
        onChange={(gestor_responsavel) => set({ gestor_responsavel })}
      />
      <TmNativeTextAreaField
        id="tm-proc-objetivo"
        label="Objetivo"
        hint={TM_HELP_TOOLTIPS.processos.objetivo}
        className="ds-filter-box--wide"
        span={false}
        rows={2}
        value={form.objetivo_processo}
        onChange={(objetivo_processo) => set({ objetivo_processo })}
      />
      <TmNativeTextAreaField
        id="tm-proc-descricao"
        label="Descrição"
        hint={TM_HELP_TOOLTIPS.processos.descricao}
        className="ds-filter-box--wide"
        span={false}
        rows={2}
        value={form.descricao_processo}
        onChange={(descricao_processo) => set({ descricao_processo })}
      />
    </div>
  );
}
