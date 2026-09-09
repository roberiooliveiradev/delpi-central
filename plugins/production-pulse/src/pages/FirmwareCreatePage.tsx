import { useEffect, useMemo, useState } from "react";

import {
  fetchFirmwareDrivers,
  publishFirmware,
  type FirmwareDriverCatalogItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFirmwareArtifactField,
  PpFirmwareSourceField,
  PpFormActions,
  PpNativeSelectField,
  PpNativeTextAreaField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareDetailPath,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareCreatePageProps = {
  branch?: string;
  permissions: ProductionPulsePermissionFlags;
};

const DEFAULT_FIRMWARE_KEY = "esp8266_counter_v1";

export function FirmwareCreatePage({ branch = "01", permissions }: FirmwareCreatePageProps) {
  const canManage = permissions.canManageDevices;
  const [drivers, setDrivers] = useState<FirmwareDriverCatalogItem[]>([]);
  const [firmwareKey, setFirmwareKey] = useState(DEFAULT_FIRMWARE_KEY);
  const [driverKey, setDriverKey] = useState(DEFAULT_FIRMWARE_KEY);
  const [version, setVersion] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [binFile, setBinFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    void fetchFirmwareDrivers()
      .then((items) => {
        if (!active) return;
        setDrivers(items);
        setDriverKey((current) =>
          items.some((driver) => driver.key === current) ? current : items[0]?.key ?? current,
        );
      })
      .catch(() => {
        if (active) setDrivers([]);
      });
    return () => {
      active = false;
    };
  }, []);

  const driverOptions = useMemo(
    () =>
      drivers.map((driver) => ({
        value: driver.key,
        label:
          typeof driver.labelPt === "string" ? `${driver.labelPt} (${driver.key})` : driver.key,
      })),
    [drivers],
  );

  const hubPath = productionPulseFirmwareLinksPath({ branch, focus: "catalog" });

  const goToHub = () => {
    navigateProductionPulse(hubPath);
  };

  const submitVersion = async (publish: boolean) => {
    if (!canManage || !version.trim()) return;
    if (publish && !binFile) {
      setFormError(PP_HELP.ota.publishRequiresBin);
      return;
    }
    const data = new FormData();
    data.set("firmwareKey", firmwareKey.trim());
    data.set("driverKey", driverKey.trim());
    data.set("version", version.trim());
    data.set("displayName", displayName);
    data.set("releaseNotes", releaseNotes);
    data.set("sourceText", sourceText);
    data.set("publish", publish ? "true" : "false");
    if (binFile) data.set("file", binFile);

    setSubmitting(true);
    setFormError(null);
    try {
      const created = await publishFirmware(data);
      if (publish) {
        navigateProductionPulse(
          productionPulseFirmwareLinksPath({ branch, firmwareKey: firmwareKey.trim() }),
        );
      } else {
        navigateProductionPulse(productionPulseFirmwareDetailPath(created.id));
      }
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Falha ao salvar versão.");
    } finally {
      setSubmitting(false);
    }
  };

  if (!canManage) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.firmwareCreate.breadcrumb} badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para criar versões de firmware."
        />
      </div>
    );
  }

  return (
    <div className="pp-page-stack pp-form-page">
      <ProductionPulsePagePath
        panelHref={PRODUCTION_PULSE_BASE_PATH}
        items={[{ id: "hub", label: "Hub OTA", href: hubPath }]}
        current={PP_HELP.firmwareCreate.breadcrumb}
      />

      <PpPageHero
        title={PP_HELP.firmwareCreate.breadcrumb}
        description={PP_HELP.firmwareCreate.hero}
        badge={ppShellIcon}
      />

      {formError ? (
        <PpStateBox variant="error" title="Não foi possível salvar" message={formError} />
      ) : null}

      <div className="pp-form-layout">
        <PpSectionCard
          title="Identificação"
          hint={PP_HELP.firmwareCreate.sectionIdentity}
        >
          <div className="pp-form-grid pp-form-grid--pair">
            <PpNativeTextField
              id="firmware-new-key"
              label="Família (firmwareKey)"
              hint={PP_HELP.ota.firmwareKey}
              value={firmwareKey}
              onChange={setFirmwareKey}
            />
            {driverOptions.length > 0 ? (
              <PpNativeSelectField
                id="firmware-new-driver"
                label="Driver"
                hint={PP_HELP.ota.driverKey}
                value={driverKey}
                onChange={setDriverKey}
                options={driverOptions}
                searchable={false}
              />
            ) : (
              <PpNativeTextField
                id="firmware-new-driver"
                label="Driver"
                hint={PP_HELP.ota.driverKeyEmpty}
                value={driverKey}
                onChange={setDriverKey}
              />
            )}
            <PpNativeTextField
              id="firmware-new-version"
              label="Versão"
              hint={PP_HELP.ota.version}
              value={version}
              onChange={setVersion}
              placeholder="1.3.0"
            />
            <PpNativeTextField
              id="firmware-new-display-name"
              label="Nome exibido"
              hint={PP_HELP.ota.displayName}
              value={displayName}
              onChange={setDisplayName}
              placeholder="Leitor de máquina"
            />
          </div>
        </PpSectionCard>

        <PpSectionCard title="Sketch (.ino)" hint={PP_HELP.firmwareCreate.sectionSource}>
          <div className="pp-form-grid">
            <PpFirmwareSourceField
              id="firmware-new-source"
              label="Importar sketch (.ino)"
              hint={PP_HELP.firmwareCreate.sourceField}
              editorLabel="Código-fonte"
              editorHint={PP_HELP.firmwareCreate.sourceEditor}
              value={sourceText}
              onChange={setSourceText}
              rows={14}
              onReadError={() => setFormError(PP_HELP.ota.sourceFileReadFailed)}
            />
          </div>
        </PpSectionCard>

        <PpSectionCard
          title="Artefato OTA (.bin)"
          hint={PP_HELP.firmwareCreate.sectionArtifact}
        >
          <div className="pp-form-grid">
            <PpFirmwareArtifactField
              id="firmware-new-bin"
              label="Artefato compilado (.bin)"
              hint={PP_HELP.firmwareCreate.artifactField}
              file={binFile}
              onChange={setBinFile}
            />
          </div>
        </PpSectionCard>

        <PpSectionCard title="Notas" hint={PP_HELP.firmwareCreate.sectionNotes}>
          <div className="pp-form-grid">
            <PpNativeTextAreaField
              id="firmware-new-notes"
              label="Notas da versão"
              hint={PP_HELP.ota.releaseNotes}
              value={releaseNotes}
              onChange={setReleaseNotes}
              rows={4}
              span
            />
          </div>
        </PpSectionCard>
      </div>

      <div className="pp-form-footer">
        <PpFormActions>
          <PpActionButton variant="ghost" onClick={goToHub} disabled={submitting}>
            Cancelar
          </PpActionButton>
          <PpActionButton
            variant="ghost"
            disabled={submitting || !version.trim()}
            onClick={() => void submitVersion(false)}
          >
            {submitting ? "Salvando…" : "Salvar rascunho"}
          </PpActionButton>
          <PpActionButton
            variant="primary"
            disabled={submitting || !version.trim() || !binFile}
            onClick={() => void submitVersion(true)}
          >
            {submitting ? "Publicando…" : "Publicar"}
          </PpActionButton>
        </PpFormActions>
      </div>
    </div>
  );
}
