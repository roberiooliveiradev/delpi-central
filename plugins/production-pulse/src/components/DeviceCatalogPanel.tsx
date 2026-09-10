import { PanelPage } from "../pages/PanelPage";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";

type DeviceCatalogPanelProps = {
  search: string;
  permissions: ProductionPulsePermissionFlags;
};

/** Ex-Painel frota — reutilizado como painel overlay no Admin mapa (modo embedded). */
export function DeviceCatalogPanel({ search, permissions }: DeviceCatalogPanelProps) {
  return (
    <div className="pp-device-catalog-panel">
      <PanelPage search={search} permissions={permissions} embedded />
    </div>
  );
}
