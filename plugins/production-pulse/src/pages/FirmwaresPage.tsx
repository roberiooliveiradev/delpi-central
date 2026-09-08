import { useCallback, useEffect, useState } from "react";

import {
  fetchFirmwares,
  publishFirmware,
  type FirmwareCatalogItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFirmwareFileField,
  PpHintAction,
  PpNativeTextAreaField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareJobsPath,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwaresPageProps = {
  permissions: ProductionPulsePermissionFlags;
};

export function FirmwaresPage({ permissions }: FirmwaresPageProps) {
  const [items, setItems] = useState<FirmwareCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [firmwareKey, setFirmwareKey] = useState("esp8266_counter_v1");
  const [driverKey, setDriverKey] = useState("esp8266_counter_v1");
  const [version, setVersion] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchFirmwares());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar firmwares.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!permissions.canManageDevices || !file) return;
    const data = new FormData();
    data.set("firmwareKey", firmwareKey);
    data.set("driverKey", driverKey);
    data.set("version", version);
    data.set("displayName", displayName);
    data.set("releaseNotes", releaseNotes);
    data.set("publish", "true");
    data.set("file", file);
    setPublishing(true);
    setFormError(null);
    try {
      await publishFirmware(data);
      setVersion("");
      setDisplayName("");
      setReleaseNotes("");
      setFile(null);
      navigateProductionPulse(
        productionPulseFirmwareLinksPath({
          firmwareKey,
          branch: "01",
        }),
      );
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Falha ao publicar firmware.");
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Firmwares OTA"
        badge={ppShellIcon}
        description={PP_HELP.ota.catalogHero}
        actions={
          <>
            <PpHintAction hint={PP_HELP.shell.backToPanel} ariaLabel="Ajuda: Painel">
              <PpActionButton
                variant="ghost"
                title={PP_HELP.shell.backToPanel}
                onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
              >
                Painel
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openJobs} ariaLabel="Ajuda: Campanhas">
              <PpActionButton
                variant="secondary"
                title={PP_HELP.ota.openJobs}
                onClick={() => navigateProductionPulse(productionPulseFirmwareJobsPath())}
              >
                Campanhas
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openLinks} ariaLabel="Ajuda: Amarração IoT">
              <PpActionButton
                variant="primary"
                title={PP_HELP.ota.openLinks}
                onClick={() => navigateProductionPulse(productionPulseFirmwareLinksPath())}
              >
                Amarração IoT
              </PpActionButton>
            </PpHintAction>
          </>
        }
      />

      {permissions.canManageDevices ? (
        <PpSectionCard title="Publicar versão" hint={PP_HELP.ota.publishForm}>
          <form className="pp-form-grid" onSubmit={(e) => void onSubmit(e)}>
            <PpNativeTextField
              id="ota-firmware-key"
              label="Família (firmwareKey)"
              hint={PP_HELP.ota.firmwareKey}
              value={firmwareKey}
              onChange={setFirmwareKey}
            />
            <PpNativeTextField
              id="ota-driver-key"
              label="Driver"
              hint={PP_HELP.ota.driverKey}
              value={driverKey}
              onChange={setDriverKey}
            />
            <PpNativeTextField
              id="ota-version"
              label="Versão"
              hint={PP_HELP.ota.version}
              value={version}
              onChange={setVersion}
              placeholder="1.3.0"
            />
            <PpNativeTextField
              id="ota-display-name"
              label="Nome exibido"
              hint={PP_HELP.ota.displayName}
              value={displayName}
              onChange={setDisplayName}
              placeholder="Leitor de máquina"
            />
            <PpFirmwareFileField
              id="ota-file"
              label="Artefato compilado (.bin)"
              hint={PP_HELP.ota.file}
              file={file}
              onChange={setFile}
            />
            <PpNativeTextAreaField
              id="ota-notes"
              label="Notas"
              hint={PP_HELP.ota.releaseNotes}
              value={releaseNotes}
              onChange={setReleaseNotes}
              span
            />
            {formError ? <PpStateBox variant="error" title="Publicação" message={formError} /> : null}
            <PpActionButton type="submit" disabled={publishing || !file || !version.trim()}>
              {publishing ? "Publicando…" : "Publicar firmware"}
            </PpActionButton>
          </form>
        </PpSectionCard>
      ) : null}

      <PpSectionCard title="Catálogo" hint={PP_HELP.ota.catalogList}>
        {loading ? (
          <PpStateBox variant="loading" title="Carregando firmwares" />
        ) : error ? (
          <PpStateBox variant="error" title="Erro" message={error} />
        ) : items.length === 0 ? (
          <PpStateBox variant="empty" title="Nenhum firmware" message={PP_HELP.ota.catalogEmpty} />
        ) : (
          <div className="pp-table-wrap">
            <table className="pp-table">
              <thead>
                <tr>
                  <th>Família</th>
                  <th>Versão</th>
                  <th>Driver</th>
                  <th>SHA256</th>
                  <th>Publicado</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id}>
                    <td>{item.displayName || item.firmwareKey}</td>
                    <td>{item.version}</td>
                    <td>{item.driverKey}</td>
                    <td>
                      <code>{item.artifactSha256.slice(0, 12)}…</code>
                    </td>
                    <td>{item.publishedAt ? new Date(item.publishedAt).toLocaleString() : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </PpSectionCard>
    </div>
  );
}
