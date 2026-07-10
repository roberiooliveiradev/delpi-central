import { FieldLabel, HelpTooltip } from "@delpi/plugin-ui/index";

import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData } from "../../data/api/transformometroApi";
import {
  defaultSetorIdsForFilial,
  setoresDisponiveisForEscopo,
  type ProcessoEscopoState,
} from "./processoEscopo";

type Props = {
  value: ProcessoEscopoState;
  options: OptionsData;
  onChange: (next: ProcessoEscopoState) => void;
  disabled?: boolean;
  showTodasFiliais?: boolean;
  activeFilialCount?: number;
  unidadesLabel?: string;
  departamentosLabel?: string;
};

function multiplicadorHint(activeFilialCount: number): string {
  const base = TM_HELP_TOOLTIPS.instancias.multiplicadorConsolidado;
  if (activeFilialCount <= 1) return base;
  return `${base} Hoje: ${activeFilialCount} unidades ativas.`;
}

export function ProcessoEscopoFields({
  value,
  options,
  onChange,
  disabled = false,
  showTodasFiliais = true,
  activeFilialCount = options.filiais.length,
  unidadesLabel = "Unidades",
  departamentosLabel = "Departamentos",
}: Props) {
  const set = (patch: Partial<ProcessoEscopoState>) => onChange({ ...value, ...patch });
  const setoresDisponiveis = setoresDisponiveisForEscopo(options, value);

  function toggleFilial(filialId: string) {
    const key = filialId.trim().toLowerCase();
    const nextFilialIds = value.filial_ids.some((id) => id.toLowerCase() === key)
      ? value.filial_ids.filter((id) => id.toLowerCase() !== key)
      : [...value.filial_ids, filialId];
    let nextSetorIds = value.setor_ids;
    if (nextFilialIds.length > 0 && nextSetorIds.length === 0) {
      nextSetorIds = defaultSetorIdsForFilial(options.setores, nextFilialIds[0]);
    }
    onChange({
      ...value,
      filial_ids: nextFilialIds,
      setor_ids: nextSetorIds,
    });
  }

  function toggleSetor(setorId: string) {
    const key = setorId.toLowerCase();
    const nextSetorIds = value.setor_ids.some((id) => id.toLowerCase() === key)
      ? value.setor_ids.filter((id) => id.toLowerCase() !== key)
      : [...value.setor_ids, setorId];
    set({ setor_ids: nextSetorIds });
  }

  return (
    <>
      {showTodasFiliais ? (
        <div className="ds-filter-box ds-filter-box--checkbox tm-inst-form__field--full">
          <label className="ds-check-label">
            <input
              type="checkbox"
              checked={value.todas_filiais_ativas}
              disabled={disabled}
              onChange={(event) => {
                const next = event.target.checked;
                onChange({
                  ...value,
                  todas_filiais_ativas: next,
                  filial_ids: next
                    ? []
                    : value.filial_ids.length
                      ? value.filial_ids
                      : [options.filiais[0]?.id ?? "01"].filter(Boolean),
                  setor_ids:
                    value.setor_ids.length > 0
                      ? value.setor_ids
                      : defaultSetorIdsForFilial(
                          options.setores,
                          options.filiais[0]?.id ?? "01"
                        ),
                });
              }}
            />
            <span>Todas as unidades ativas</span>
            <HelpTooltip
              content={multiplicadorHint(activeFilialCount)}
              ariaLabel="Ajuda: todas as unidades"
            />
          </label>
        </div>
      ) : null}

      {!value.todas_filiais_ativas ? (
        <div className="ds-filter-box tm-inst-form__field--full">
          <span className="ds-field-label">
            <FieldLabel
              className="tm-field__label"
              label={`${unidadesLabel} *`}
              hint={TM_HELP_TOOLTIPS.processos.unidade}
            />
          </span>
          <div className="tm-check-grid" role="group" aria-label={unidadesLabel}>
            {options.filiais.map((filial) => {
              const checked = value.filial_ids.some(
                (id) => id.toLowerCase() === filial.id.toLowerCase()
              );
              return (
                <label key={filial.id} className="tm-check-option">
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleFilial(filial.id)}
                  />
                  <span>{filial.label}</span>
                </label>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="ds-filter-box tm-inst-form__field--full">
        <span className="ds-field-label">
          <FieldLabel
            className="tm-field__label"
            label={`${departamentosLabel} *`}
            hint={TM_HELP_TOOLTIPS.processos.setor}
          />
        </span>
        <div className="tm-check-grid" role="group" aria-label={departamentosLabel}>
          {setoresDisponiveis.length === 0 ? (
            <p className="ds-hint">
              {!value.todas_filiais_ativas && value.filial_ids.length === 0
                ? "Selecione ao menos uma unidade para listar os departamentos."
                : "Nenhum departamento disponível para esta seleção."}
            </p>
          ) : (
            setoresDisponiveis.map((setor) => {
              const checked = value.setor_ids.some(
                (id) => id.toLowerCase() === setor.id.toLowerCase()
              );
              return (
                <label key={setor.id} className="tm-check-option">
                  <input
                    type="checkbox"
                    checked={checked}
                    disabled={disabled}
                    onChange={() => toggleSetor(setor.id)}
                  />
                  <span>{setor.label}</span>
                </label>
              );
            })
          )}
        </div>
      </div>
    </>
  );
}
