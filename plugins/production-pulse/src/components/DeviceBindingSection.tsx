import { useEffect, useState } from "react";

import { fetchWorkCenters } from "../api/productionPulseApi";
import { PpFieldLabel, PpFormGrid } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import { getPpSectionIntro } from "../content/sectionIntros";
import type { BindingFormValues } from "../types/form";
import type { WorkCenterCatalogItem } from "../types/form";
import { AnchorTypeSegmented } from "./AnchorTypeSegmented";

type DeviceBindingSectionProps = {
  binding: BindingFormValues;
  branch: string;
  errors?: Partial<Record<keyof BindingFormValues, string>>;
  stackedAnchor?: boolean;
  onChange: (patch: Partial<BindingFormValues>) => void;
};

export function DeviceBindingSection({
  binding,
  branch,
  errors,
  stackedAnchor,
  onChange,
}: DeviceBindingSectionProps) {
  const [totvsOpen, setTotvsOpen] = useState(
    Boolean(binding.workCenterCode || binding.resourceCode || binding.toolCode),
  );
  const [workCenterSearch, setWorkCenterSearch] = useState(binding.workCenterCode);
  const [workCenters, setWorkCenters] = useState<WorkCenterCatalogItem[]>([]);
  const [loadingWorkCenters, setLoadingWorkCenters] = useState(false);

  useEffect(() => {
    if (!totvsOpen && binding.anchorType !== "work_center") return;
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoadingWorkCenters(true);
      fetchWorkCenters(branch, workCenterSearch)
        .then((items) => {
          if (!controller.signal.aborted) setWorkCenters(items);
        })
        .catch(() => {
          if (!controller.signal.aborted) setWorkCenters([]);
        })
        .finally(() => {
          if (!controller.signal.aborted) setLoadingWorkCenters(false);
        });
    }, 250);
    return () => {
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [branch, binding.anchorType, totvsOpen, workCenterSearch]);

  return (
    <div className="pp-binding-section">
      <p className="pp-section-intro">{getPpSectionIntro("form.placement")}</p>
      <AnchorTypeSegmented
        value={binding.anchorType}
        stacked={stackedAnchor}
        onChange={(anchorType) => onChange({ anchorType })}
      />

      {binding.anchorType === "work_center" ? (
        <PpFormGrid className="pp-form-grid--single">
          <label className="pp-field">
            <PpFieldLabel label="Centro de trabalho" hint={PP_HELP.form.anchorWorkCenter} />
            <input
              list="pp-work-centers"
              value={binding.workCenterCode}
              onChange={(event) => {
                const code = event.target.value;
                const match = workCenters.find((item) => item.workCenterCode === code);
                onChange({
                  workCenterCode: code,
                  workCenterName: match?.workCenterName ?? binding.workCenterName,
                });
                setWorkCenterSearch(code);
              }}
              placeholder="CT-53"
            />
            <datalist id="pp-work-centers">
              {workCenters.map((item) => (
                <option
                  key={item.workCenterCode}
                  value={item.workCenterCode}
                  label={item.workCenterName}
                />
              ))}
            </datalist>
            {errors?.workCenterCode ? (
              <span className="pp-field-error">{errors.workCenterCode}</span>
            ) : null}
            {loadingWorkCenters ? (
              <span className="pp-field-hint">Carregando catálogo TOTVS…</span>
            ) : null}
          </label>
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "machine" ? (
        <PpFormGrid className="pp-form-grid--single">
          <label className="pp-field">
            <PpFieldLabel label="Máquina" hint={PP_HELP.form.anchorMachine} />
            <input
              value={binding.machineLabel}
              onChange={(event) => onChange({ machineLabel: event.target.value })}
              placeholder="Motor bomba recirculação #2"
            />
            {errors?.machineLabel ? (
              <span className="pp-field-error">{errors.machineLabel}</span>
            ) : null}
          </label>
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "equipment" ? (
        <PpFormGrid className="pp-form-grid--single">
          <label className="pp-field">
            <PpFieldLabel label="Equipamento" hint={PP_HELP.form.anchorEquipment} />
            <input
              value={binding.equipmentLabel}
              onChange={(event) => onChange({ equipmentLabel: event.target.value })}
              placeholder="Ventilador exaustão setor A"
            />
            {errors?.equipmentLabel ? (
              <span className="pp-field-error">{errors.equipmentLabel}</span>
            ) : null}
          </label>
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "area" ? (
        <PpFormGrid className="pp-form-grid--single">
          <label className="pp-field">
            <PpFieldLabel label="Área" hint={PP_HELP.form.anchorArea} />
            <input
              value={binding.areaLabel}
              onChange={(event) => onChange({ areaLabel: event.target.value })}
              placeholder="Sala HVAC"
            />
            {errors?.areaLabel ? <span className="pp-field-error">{errors.areaLabel}</span> : null}
          </label>
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "standalone" ? (
        <PpFormGrid className="pp-form-grid--single">
          <label className="pp-field">
            <PpFieldLabel label="Observações" hint={PP_HELP.form.anchorStandalone} />
            <textarea
              rows={3}
              value={binding.notes}
              onChange={(event) => onChange({ notes: event.target.value })}
              placeholder="Referência operacional do device avulso"
            />
          </label>
        </PpFormGrid>
      ) : null}

      {binding.anchorType !== "work_center" ? (
        <details
          className="pp-totvs-details"
          open={totvsOpen}
          onToggle={(event) => setTotvsOpen((event.target as HTMLDetailsElement).open)}
        >
          <summary>Vincular ao TOTVS (opcional)</summary>
          <p className="pp-section-intro">{getPpSectionIntro("form.totvsDetails")}</p>
          <PpFormGrid className="pp-form-grid--single">
            <label className="pp-field">
              <PpFieldLabel label="Centro de trabalho" hint={PP_HELP.form.workCenterOptional} />
              <input
                list="pp-work-centers-opt"
                value={binding.workCenterCode}
                onChange={(event) => {
                  const code = event.target.value;
                  const match = workCenters.find((item) => item.workCenterCode === code);
                  onChange({
                    workCenterCode: code,
                    workCenterName: match?.workCenterName ?? binding.workCenterName,
                  });
                  setWorkCenterSearch(code);
                }}
                placeholder="Opcional"
              />
              <datalist id="pp-work-centers-opt">
                {workCenters.map((item) => (
                  <option key={item.workCenterCode} value={item.workCenterCode} label={item.workCenterName} />
                ))}
              </datalist>
            </label>
            <label className="pp-field">
              <PpFieldLabel label="Recurso" hint={PP_HELP.form.resourceOptional} />
              <input
                value={binding.resourceCode}
                onChange={(event) => onChange({ resourceCode: event.target.value })}
              />
            </label>
            <label className="pp-field">
              <PpFieldLabel label="Ferramenta" hint={PP_HELP.form.toolOptional} />
              <input
                value={binding.toolCode}
                onChange={(event) => onChange({ toolCode: event.target.value })}
              />
            </label>
          </PpFormGrid>
        </details>
      ) : null}
    </div>
  );
}
