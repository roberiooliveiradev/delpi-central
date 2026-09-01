import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchOperatorPlacementDevices,
  fetchOperatorPlacements,
} from "../../api/productionPulseApi";
import { PpActionButton, PpSegmentToggle, PpStateBox } from "../../app/productionPulseUi";
import { OperatorBrandBar } from "../../components/operator/OperatorBrandBar";
import { OperatorPlacementCard } from "../../components/operator/OperatorPlacementCard";
import { PpFilterInputField, PpFiltersRow } from "../../components/data/filtersUi";
import { resolveBranchOptions } from "../../constants/branches";
import type { ProductionPulsePermissionFlags } from "../../constants/permissions";
import {
  productionPulseOperatorDevicePath,
  productionPulseOperatorPath,
  productionPulseOperatorPlacementPath,
  type OperatorAnchorFilter,
} from "../../constants/routes";
import { PP_HELP } from "../../content/helpTooltips";
import type { OperatorPlacement } from "../../types/operator";
import { navigateProductionPulse, replaceProductionPulse } from "../../utils/navigation";
import { readLastPlacementKey, writeLastPlacementKey } from "../../utils/operatorStorage";

type OperatorPlacementHubProps = {
  branch: string;
  anchorType: OperatorAnchorFilter;
  search: string;
  permissions: ProductionPulsePermissionFlags;
};

export function OperatorPlacementHub({
  branch,
  anchorType,
  search,
  permissions,
}: OperatorPlacementHubProps) {
  const [placements, setPlacements] = useState<OperatorPlacement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [localSearch, setLocalSearch] = useState(search);
  const lastPlacementKey = readLastPlacementKey();

  useEffect(() => {
    setLocalSearch(search);
  }, [search]);

  const branchOptions = useMemo(
    () => resolveBranchOptions(permissions.allowedBranches),
    [permissions.allowedBranches],
  );
  const activeBranch =
    branchOptions.find((item) => item.id === branch)?.id ?? branchOptions[0]?.id ?? branch;

  const reload = useCallback(async (signal?: AbortSignal) => {
    setLoading(true);
    setError(null);
    try {
      const items = await fetchOperatorPlacements({
        branch: activeBranch,
        anchorType: anchorType || undefined,
        search: localSearch || undefined,
        signal,
      });
      setPlacements(items);
      setLoading(false);
    } catch (err) {
      if (signal?.aborted) return;
      setError(err instanceof Error ? err.message : "Erro ao carregar locais.");
      setLoading(false);
    }
  }, [activeBranch, anchorType, localSearch]);

  useEffect(() => {
    const controller = new AbortController();
    void reload(controller.signal);
    return () => controller.abort();
  }, [reload]);

  const updateFilters = (patch: { anchorType?: OperatorAnchorFilter; search?: string; branch?: string }) => {
    replaceProductionPulse(
      productionPulseOperatorPath(patch.branch ?? activeBranch, {
        anchorType: patch.anchorType ?? anchorType,
        search: patch.search ?? localSearch,
      }),
    );
  };

  const openPlacement = async (placement: OperatorPlacement) => {
    writeLastPlacementKey(placement.placementKey);
    try {
      const devices = await fetchOperatorPlacementDevices(placement.placementKey, activeBranch);
      if (devices.length === 0) {
        setError("Local sem dispositivo operável.");
        return;
      }
      if (devices.length === 1) {
        navigateProductionPulse(
          productionPulseOperatorDevicePath(devices[0].id, activeBranch, placement.placementKey),
        );
        return;
      }
      navigateProductionPulse(
        productionPulseOperatorPlacementPath(placement.placementKey, activeBranch),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir local.");
    }
  };

  if (!permissions.canOperator) {
    return (
      <PpStateBox
        variant="error"
        title="Sem permissão"
        message="Você não tem permissão para o modo operador."
      />
    );
  }

  return (
    <div className="pp-operator-hub">
      <OperatorBrandBar
        branch={activeBranch}
        title="Escolha onde vai trabalhar"
        subtitle={PP_HELP.operator.hubTitle}
        showAdminLink={permissions.canViewDevices}
      />

      {branchOptions.length > 1 ? (
        <PpSegmentToggle
          ariaLabel="Filial"
          value={activeBranch}
          onChange={(value) => updateFilters({ branch: value })}
          options={branchOptions.map((item) => ({ value: item.id, label: item.label }))}
        />
      ) : null}

      <PpSegmentToggle
        ariaLabel="Filtro de tipo de local"
        value={anchorType}
        onChange={(value) => updateFilters({ anchorType: value as OperatorAnchorFilter })}
        options={[
          { value: "", label: "Todos" },
          { value: "work_center", label: "Postos PCP" },
          { value: "machine", label: "Máquinas" },
          { value: "equipment", label: "Equipamentos" },
        ]}
      />

      <PpFiltersRow>
        <PpFilterInputField
          id="pp-operator-hub-search"
          label="Busca"
          type="search"
          hint={PP_HELP.operator.hubSearch}
          value={localSearch}
          onChange={setLocalSearch}
          placeholder="Ventilador, CT-53…"
        />
        <PpActionButton variant="ghost" onClick={() => updateFilters({ search: localSearch })}>
          Buscar
        </PpActionButton>
      </PpFiltersRow>

      {error ? <p className="pp-detail-error">{error}</p> : null}

      {loading ? (
        <div className="pp-operator-hub__grid pp-operator-hub__grid--skeleton" aria-hidden="true">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="pp-kpi-skeleton pp-operator-hub-card-skeleton" />
          ))}
        </div>
      ) : placements.length === 0 ? (
        <PpStateBox
          variant="empty"
          title="Nenhum local encontrado"
          message={
            localSearch.trim()
              ? "Nenhum local corresponde à busca — limpe o filtro e tente novamente."
              : "Nenhum posto, máquina ou equipamento com sensor operável nesta filial."
          }
        />
      ) : (
        <div className="pp-operator-hub__grid">
          {placements.map((placement) => (
            <OperatorPlacementCard
              key={placement.placementKey}
              placement={placement}
              recent={placement.placementKey === lastPlacementKey}
              onSelect={(item) => void openPlacement(item)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
