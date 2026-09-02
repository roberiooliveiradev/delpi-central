import { useEffect, useMemo, useState } from "react";

import { fetchWorkCenters } from "../api/productionPulseApi";
import { PpFormGrid } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import { getPpSectionIntro } from "../content/sectionIntros";
import type { BindingFormValues } from "../types/form";
import type { WorkCenterCatalogItem } from "../types/form";
import { AnchorTypeSegmented } from "./AnchorTypeSegmented";
import {
  PpNativeSelectField,
  PpNativeTextAreaField,
  PpNativeTextField,
  ppFieldError,
  ppFieldHint,
} from "./data/ppFormFields";

type DeviceBindingSectionProps = {
  binding: BindingFormValues;
  branch: string;
  errors?: Partial<Record<keyof BindingFormValues, string>>;
  stackedAnchor?: boolean;
  onChange: (patch: Partial<BindingFormValues>) => void;
};

function workCenterOptions(items: WorkCenterCatalogItem[]) {
  return items.map((item) => ({
    value: item.workCenterCode,
    label: `${item.workCenterCode} — ${item.workCenterName}`,
  }));
}

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

  const catalogOptions = useMemo(() => workCenterOptions(workCenters), [workCenters]);

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

  const applyWorkCenterCode = (code: string) => {
    const match = workCenters.find((item) => item.workCenterCode === code);
    onChange({
      workCenterCode: code,
      workCenterName: match?.workCenterName ?? binding.workCenterName,
    });
    setWorkCenterSearch(code);
  };

  const workCenterFields = (
    <>
      <PpNativeTextField
        id="pp-binding-wc-search"
        label="Buscar centro de trabalho"
        hint={PP_HELP.form.anchorWorkCenter}
        value={workCenterSearch}
        placeholder="CT-53"
        onChange={(value) => {
          setWorkCenterSearch(value);
          const match = workCenters.find((item) => item.workCenterCode === value);
          onChange({
            workCenterCode: value,
            workCenterName: match?.workCenterName ?? binding.workCenterName,
          });
        }}
        afterControl={
          <>
            {ppFieldError(errors?.workCenterCode)}
            {loadingWorkCenters ? ppFieldHint("Carregando catálogo TOTVS…") : null}
          </>
        }
      />
      <PpNativeSelectField
        id="pp-binding-wc-pick"
        label="Catálogo TOTVS"
        hint="Escolha um CT retornado pela busca"
        value={binding.workCenterCode}
        disabled={catalogOptions.length === 0}
        placeholderOption={loadingWorkCenters ? "Carregando…" : "Selecione…"}
        options={catalogOptions}
        onChange={applyWorkCenterCode}
      />
    </>
  );

  return (
    <div className="pp-binding-section">
      <p className="pp-section-intro">{getPpSectionIntro("form.placement")}</p>
      <AnchorTypeSegmented
        value={binding.anchorType}
        stacked={stackedAnchor}
        onChange={(anchorType) => onChange({ anchorType })}
      />

      {binding.anchorType === "work_center" ? (
        <PpFormGrid className="pp-form-grid--pair">{workCenterFields}</PpFormGrid>
      ) : null}

      {binding.anchorType === "machine" ? (
        <PpFormGrid>
          <PpNativeTextField
            id="pp-binding-machine"
            label="Máquina"
            hint={PP_HELP.form.anchorMachine}
            value={binding.machineLabel}
            placeholder="Motor bomba recirculação #2"
            onChange={(value) => onChange({ machineLabel: value })}
            afterControl={ppFieldError(errors?.machineLabel)}
          />
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "equipment" ? (
        <PpFormGrid>
          <PpNativeTextField
            id="pp-binding-equipment"
            label="Equipamento"
            hint={PP_HELP.form.anchorEquipment}
            value={binding.equipmentLabel}
            placeholder="Ventilador exaustão setor A"
            onChange={(value) => onChange({ equipmentLabel: value })}
            afterControl={ppFieldError(errors?.equipmentLabel)}
          />
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "area" ? (
        <PpFormGrid>
          <PpNativeTextField
            id="pp-binding-area"
            label="Área"
            hint={PP_HELP.form.anchorArea}
            value={binding.areaLabel}
            placeholder="Sala HVAC"
            onChange={(value) => onChange({ areaLabel: value })}
            afterControl={ppFieldError(errors?.areaLabel)}
          />
        </PpFormGrid>
      ) : null}

      {binding.anchorType === "standalone" ? (
        <PpFormGrid>
          <PpNativeTextAreaField
            id="pp-binding-notes"
            label="Observações"
            hint={PP_HELP.form.anchorStandalone}
            rows={3}
            value={binding.notes}
            placeholder="Referência operacional do device avulso"
            onChange={(value) => onChange({ notes: value })}
            afterControl={ppFieldError(errors?.notes)}
          />
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
          <PpFormGrid className="pp-form-grid--pair">
            <PpNativeTextField
              id="pp-binding-wc-opt-search"
              label="Buscar centro de trabalho"
              hint={PP_HELP.form.workCenterOptional}
              span
              value={workCenterSearch}
              placeholder="Opcional"
              onChange={(value) => {
                setWorkCenterSearch(value);
                const match = workCenters.find((item) => item.workCenterCode === value);
                onChange({
                  workCenterCode: value,
                  workCenterName: match?.workCenterName ?? binding.workCenterName,
                });
              }}
            />
            <PpNativeSelectField
              id="pp-binding-wc-opt-pick"
              label="Catálogo TOTVS"
              span
              value={binding.workCenterCode}
              disabled={catalogOptions.length === 0}
              placeholderOption="Selecione…"
              options={catalogOptions}
              onChange={applyWorkCenterCode}
            />
            <PpNativeTextField
              id="pp-binding-resource"
              label="Recurso"
              hint={PP_HELP.form.resourceOptional}
              value={binding.resourceCode}
              onChange={(value) => onChange({ resourceCode: value })}
            />
            <PpNativeTextField
              id="pp-binding-tool"
              label="Ferramenta"
              hint={PP_HELP.form.toolOptional}
              value={binding.toolCode}
              onChange={(value) => onChange({ toolCode: value })}
            />
          </PpFormGrid>
        </details>
      ) : null}
    </div>
  );
}
