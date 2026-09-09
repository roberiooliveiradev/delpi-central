import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchFirmwareDrivers,
  fetchFirmwares,
  publishFirmware,
  type FirmwareDriverCatalogItem,
  type FirmwareListItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpCatalogSearchBar,
  PpDataTable,
  PpFirmwareFileField,
  PpNativeSelectField,
  PpNativeTextAreaField,
  PpNativeTextField,
  PpPageHero,
  PpSectionCard,
  PpStateBox,
  ppShellIcon,
  type DataTableColumn,
} from "../app/productionPulseUi";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import { productionPulseFirmwareDetailPath, productionPulseFirmwareLinksPath } from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwaresPageProps = {
  permissions: ProductionPulsePermissionFlags;
};

function lifecycleLabel(row: FirmwareListItem): string {
  if (row.lifecycle === "draft") return PP_HELP.ota.status.draft;
  if (row.lifecycle === "archived") return PP_HELP.ota.statusArchived;
  return PP_HELP.ota.statusPublished;
}

export function FirmwaresPage({ permissions }: FirmwaresPageProps) {
  const canManage = permissions.canManageDevices;
  const [items, setItems] = useState<FirmwareListItem[]>([]);
  const [drivers, setDrivers] = useState<FirmwareDriverCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [firmwareKey, setFirmwareKey] = useState("esp8266_counter_v1");
  const [driverKey, setDriverKey] = useState("esp8266_counter_v1");
  const [version, setVersion] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [sourceText, setSourceText] = useState("");
  const [binFile, setBinFile] = useState<File | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [catalog, driverItems] = await Promise.all([
        fetchFirmwares({ includeArchived: true }),
        fetchFirmwareDrivers().catch(() => [] as FirmwareDriverCatalogItem[]),
      ]);
      setItems(catalog);
      setDrivers(driverItems);
      setDriverKey((current) => {
        if (driverItems.some((d) => d.key === current)) return current;
        return driverItems[0]?.key ?? current;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar firmwares.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const driverOptions = useMemo(
    () =>
      drivers.map((driver) => ({
        value: driver.key,
        label: typeof driver.labelPt === "string" ? `${driver.labelPt} (${driver.key})` : driver.key,
      })),
    [drivers],
  );

  const filteredItems = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return items;
    return items.filter((item) => {
      const hay = [
        item.firmwareKey,
        item.driverKey,
        item.version,
        item.displayName,
        item.lifecycle,
        item.artifactSha256 ?? "",
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [items, search]);

  const groupedItems = useMemo(() => {
    const groups = new Map<string, FirmwareListItem[]>();
    for (const item of filteredItems) {
      const key = item.firmwareKey;
      const bucket = groups.get(key) ?? [];
      bucket.push(item);
      groups.set(key, bucket);
    }
    return [...groups.entries()].sort(([a], [b]) => a.localeCompare(b));
  }, [filteredItems]);

  const loadInoFile = async (file: File | null) => {
    if (!file) return;
    try {
      setSourceText(await file.text());
    } catch {
      setFormError(PP_HELP.ota.sourceFileReadFailed);
    }
  };

  const submitVersion = async (publish: boolean) => {
    if (!canManage || !version.trim()) return;
    if (publish && !binFile) {
      setFormError(PP_HELP.ota.publishRequiresBin);
      return;
    }
    const data = new FormData();
    data.set("firmwareKey", firmwareKey);
    data.set("driverKey", driverKey);
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
      setVersion("");
      setDisplayName("");
      setReleaseNotes("");
      setSourceText("");
      setBinFile(null);
      if (publish) {
        navigateProductionPulse(
          productionPulseFirmwareLinksPath({
            firmwareKey,
            branch: "01",
          }),
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

  const columns: DataTableColumn<FirmwareListItem>[] = useMemo(
    () => [
      {
        key: "version",
        header: "Versão",
        render: (row) => row.version,
      },
      {
        key: "displayName",
        header: "Nome",
        render: (row) => row.displayName || "—",
      },
      {
        key: "lifecycle",
        header: "Estado",
        render: (row) => lifecycleLabel(row),
      },
      {
        key: "source",
        header: "Sketch",
        render: (row) => (row.hasSource ? "Sim" : "—"),
      },
      {
        key: "artifact",
        header: "Bin",
        render: (row) =>
          row.hasArtifact && row.artifactSha256 ? <code>{row.artifactSha256.slice(0, 10)}…</code> : "—",
      },
      {
        key: "published",
        header: "Publicado",
        render: (row) => (row.publishedAt ? new Date(row.publishedAt).toLocaleString() : "—"),
      },
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
            <PpActionButton
              variant="ghost"
              onClick={() => navigateProductionPulse(productionPulseFirmwareDetailPath(row.id))}
            >
              Detalhe
            </PpActionButton>
            {row.lifecycle === "published" && !row.archivedAt ? (
              <PpActionButton
                variant="ghost"
                onClick={() =>
                  navigateProductionPulse(
                    productionPulseFirmwareLinksPath({
                      firmwareKey: row.firmwareKey,
                      branch: "01",
                    }),
                  )
                }
              >
                Amarrar
              </PpActionButton>
            ) : null}
          </div>
        ),
      },
    ],
    [],
  );

  return (
    <div className="pp-page-stack">
      <PpPageHero
        title="Firmwares OTA"
        badge={ppShellIcon}
        description={PP_HELP.ota.catalogHero}
      />

      {canManage ? (
        <PpSectionCard title="Nova versão" hint={PP_HELP.ota.createVersionForm}>
          <div className="pp-form-grid">
            <PpNativeTextField
              id="ota-firmware-key"
              label="Família (firmwareKey)"
              hint={PP_HELP.ota.firmwareKey}
              value={firmwareKey}
              onChange={setFirmwareKey}
            />
            {driverOptions.length > 0 ? (
              <PpNativeSelectField
                id="ota-driver-key"
                label="Driver"
                hint={PP_HELP.ota.driverKey}
                value={driverKey}
                onChange={setDriverKey}
                options={driverOptions}
                searchable={false}
              />
            ) : (
              <PpNativeTextField
                id="ota-driver-key"
                label="Driver"
                hint={PP_HELP.ota.driverKeyEmpty}
                value={driverKey}
                onChange={setDriverKey}
              />
            )}
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
              id="ota-ino"
              label="Sketch (.ino)"
              hint={PP_HELP.ota.sourceFile}
              accept=".ino,.txt,text/plain"
              file={null}
              onChange={(file) => void loadInoFile(file)}
            />
            <PpNativeTextAreaField
              id="ota-source"
              label="Código-fonte"
              hint={PP_HELP.ota.sourceTextarea}
              value={sourceText}
              onChange={setSourceText}
              rows={8}
              span
            />
            <PpFirmwareFileField
              id="ota-file"
              label="Artefato compilado (.bin)"
              hint={PP_HELP.ota.fileOptionalDraft}
              file={binFile}
              onChange={setBinFile}
            />
            <PpNativeTextAreaField
              id="ota-notes"
              label="Notas"
              hint={PP_HELP.ota.releaseNotes}
              value={releaseNotes}
              onChange={setReleaseNotes}
              span
            />
            {formError ? <PpStateBox variant="error" title="Versão" message={formError} /> : null}
            <div className="pp-inline-actions">
              <PpActionButton
                variant="ghost"
                disabled={submitting || !version.trim()}
                onClick={() => void submitVersion(false)}
              >
                {submitting ? "Salvando…" : "Salvar rascunho"}
              </PpActionButton>
              <PpActionButton
                disabled={submitting || !version.trim() || !binFile}
                onClick={() => void submitVersion(true)}
              >
                {submitting ? "Publicando…" : "Publicar agora"}
              </PpActionButton>
            </div>
          </div>
        </PpSectionCard>
      ) : null}

      <PpSectionCard title="Catálogo" hint={PP_HELP.ota.catalogList}>
        <PpCatalogSearchBar
          value={search}
          onChange={setSearch}
          placeholder="Buscar família, versão, driver…"
        />
        {loading ? (
          <PpStateBox variant="loading" title="Carregando firmwares" />
        ) : error ? (
          <PpStateBox variant="error" title="Erro" message={error} />
        ) : groupedItems.length === 0 ? (
          <PpStateBox variant="empty" title="Nenhum firmware" message={PP_HELP.ota.catalogEmpty} />
        ) : (
          groupedItems.map(([familyKey, rows]) => (
            <div key={familyKey} className="pp-firmware-family-group">
              <h3 className="pp-firmware-family-group__title">
                <code>{familyKey}</code>
              </h3>
              <PpDataTable
                columns={columns}
                rows={rows}
                rowKey={(row) => row.id}
                emptyMessage={PP_HELP.ota.catalogEmpty}
              />
            </div>
          ))
        )}
      </PpSectionCard>
    </div>
  );
}
