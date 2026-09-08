import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchDevices,
  fetchFirmwares,
  type FirmwareCatalogItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpNativeSelectField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareJobsPath,
  productionPulseFirmwaresPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareLinksPageProps = {
  branch: string;
  highlightFirmwareKey?: string;
  permissions: ProductionPulsePermissionFlags;
};

function uniqueFirmwareFamilies(items: FirmwareCatalogItem[]): FirmwareCatalogItem[] {
  const byKey = new Map<string, FirmwareCatalogItem>();
  for (const item of items) {
    const prev = byKey.get(item.firmwareKey);
    if (!prev) {
      byKey.set(item.firmwareKey, item);
      continue;
    }
    const prevAt = prev.publishedAt ? Date.parse(prev.publishedAt) : 0;
    const nextAt = item.publishedAt ? Date.parse(item.publishedAt) : 0;
    if (nextAt >= prevAt) byKey.set(item.firmwareKey, item);
  }
  return [...byKey.values()].sort((a, b) => a.firmwareKey.localeCompare(b.firmwareKey));
}

export function FirmwareLinksPage({
  branch: initialBranch,
  highlightFirmwareKey,
  permissions,
}: FirmwareLinksPageProps) {
  const [branch, setBranch] = useState(initialBranch || "01");
  const [firmwares, setFirmwares] = useState<FirmwareCatalogItem[]>([]);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(
    highlightFirmwareKey
      ? `Firmware ${highlightFirmwareKey} publicado — ligue os IoTs abaixo.`
      : null,
  );

  const families = useMemo(() => uniqueFirmwareFamilies(firmwares), [firmwares]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fw, devs] = await Promise.all([
        fetchFirmwares(),
        fetchDevices({ branch }),
      ]);
      setFirmwares(fw);
      setDevices(devs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar conexões.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  useEffect(() => {
    void reload();
  }, [reload]);

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Amarração Firmware ↔ IoT" badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar dispositivos."
        />
      </div>
    );
  }

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Amarração Firmware ↔ IoT"
        badge={ppShellIcon}
        description={PP_HELP.ota.openCatalog}
        actions={
          <>
            <PpActionButton
              variant="ghost"
              onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
            >
              Painel
            </PpActionButton>
            <PpActionButton
              variant="ghost"
              onClick={() => navigateProductionPulse(productionPulseFirmwaresPath())}
            >
              Firmwares
            </PpActionButton>
            <PpActionButton
              variant="secondary"
              onClick={() => navigateProductionPulse(productionPulseFirmwareJobsPath(branch))}
            >
              Campanhas OTA
            </PpActionButton>
            <PpActionButton variant="primary" onClick={() => void reload()} disabled={loading}>
              Atualizar conexões
            </PpActionButton>
          </>
        }
      />

      <PpSectionCard title="Filial">
        <PpNativeSelectField
          id="ota-links-branch"
          label="Filial"
          value={branch}
          onChange={setBranch}
          options={[
            { value: "01", label: "Filial 01" },
            { value: "02", label: "Filial 02" },
          ]}
        />
      </PpSectionCard>

      {notice ? (
        <PpStateBox
          variant="success"
          title="Publicação"
          message={notice}
          action={
            <PpActionButton variant="ghost" onClick={() => setNotice(null)}>
              Fechar
            </PpActionButton>
          }
        />
      ) : null}

      {loading ? (
        <PpStateBox variant="loading" title="Carregando firmwares e IoTs" />
      ) : error ? (
        <PpStateBox variant="error" title="Erro" message={error} />
      ) : (
        <div className="pp-ota-links-columns">
          <PpSectionCard title={`Firmwares (${families.length})`} hint={PP_HELP.ota.catalogList}>
            {families.length === 0 ? (
              <PpStateBox variant="empty" title="Nenhum firmware" message={PP_HELP.ota.catalogEmpty} />
            ) : (
              <ul className="pp-list-plain">
                {families.map((item) => (
                  <li key={item.firmwareKey}>
                    <strong>{item.firmwareKey}</strong>
                    <span>
                      {" "}
                      · {item.displayName || item.version} · driver {item.driverKey}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </PpSectionCard>
          <PpSectionCard title={`IoTs filial ${branch} (${devices.length})`}>
            {devices.length === 0 ? (
              <PpStateBox
                variant="empty"
                title="Nenhum device"
                message="Cadastre dispositivos nesta filial para amarrar ao firmware."
              />
            ) : (
              <ul className="pp-list-plain">
                {devices.map((device) => (
                  <li key={device.id}>
                    <strong>{device.name}</strong>
                    <span>
                      {" "}
                      · {device.ipAddress} · FW{" "}
                      {device.assignedFirmwareKey || `(via driver) ${device.driverKey}`}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </PpSectionCard>
        </div>
      )}
    </div>
  );
}
