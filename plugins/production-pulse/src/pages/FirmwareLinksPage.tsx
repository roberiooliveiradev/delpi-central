import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchDevices, fetchFirmwares } from "../api/productionPulseApi";
import { FirmwareDeviceLinkCanvas } from "../components/FirmwareDeviceLinkCanvas";
import {
  PpActionButton,
  PpHintAction,
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
import { uniqueFirmwareFamilies } from "../utils/firmwareLinkGraph";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareLinksPageProps = {
  branch: string;
  highlightFirmwareKey?: string;
  permissions: ProductionPulsePermissionFlags;
};

export function FirmwareLinksPage({
  branch: initialBranch,
  highlightFirmwareKey,
  permissions,
}: FirmwareLinksPageProps) {
  const [branch, setBranch] = useState(initialBranch || "01");
  const [firmwaresRaw, setFirmwaresRaw] = useState<
    Awaited<ReturnType<typeof fetchFirmwares>>
  >([]);
  const [devices, setDevices] = useState<DeviceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(
    highlightFirmwareKey
      ? `Firmware ${highlightFirmwareKey} publicado — ligue os IoTs no canvas.`
      : null,
  );

  const families = useMemo(() => uniqueFirmwareFamilies(firmwaresRaw), [firmwaresRaw]);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [fw, devs] = await Promise.all([fetchFirmwares(), fetchDevices({ branch })]);
      setFirmwaresRaw(fw);
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
        description={PP_HELP.otaLinks.hero}
        actions={
          <>
            <PpHintAction hint={PP_HELP.shell.backToPanel} ariaLabel="Ajuda: Painel">
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
              >
                Painel
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openCatalog} ariaLabel="Ajuda: Firmwares">
              <PpActionButton
                variant="ghost"
                onClick={() => navigateProductionPulse(productionPulseFirmwaresPath())}
              >
                Firmwares
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openJobs} ariaLabel="Ajuda: Campanhas OTA">
              <PpActionButton
                variant="secondary"
                onClick={() => navigateProductionPulse(productionPulseFirmwareJobsPath(branch))}
              >
                Campanhas OTA
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.otaLinks.refresh} ariaLabel="Ajuda: Atualizar conexões">
              <PpActionButton
                variant="primary"
                onClick={() => void reload()}
                disabled={loading}
              >
                Atualizar conexões
              </PpActionButton>
            </PpHintAction>
          </>
        }
      />

      <PpSectionCard title="Filial" hint={PP_HELP.otaLinks.branch}>
        <PpNativeSelectField
          id="ota-links-branch"
          label="Filial"
          hint={PP_HELP.otaLinks.branch}
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
          variant="empty"
          title="Publicação"
          message={notice || PP_HELP.otaLinks.afterPublish}
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
        <PpSectionCard
          title={`Canvas · ${families.length} firmwares · ${devices.length} IoTs`}
          hint={PP_HELP.otaLinks.canvas}
        >
          <p className="pp-muted">{PP_HELP.otaLinks.oneFirmwarePerDevice}</p>
          <p className="pp-muted">{PP_HELP.otaLinks.legend}</p>
          <FirmwareDeviceLinkCanvas
            families={families}
            devices={devices}
            canManage={permissions.canManageDevices}
            onLinked={() => void reload()}
          />
        </PpSectionCard>
      )}
    </div>
  );
}
