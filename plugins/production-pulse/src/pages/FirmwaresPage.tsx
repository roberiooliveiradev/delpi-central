import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveFirmware,
  fetchFirmwareDrivers,
  fetchFirmwares,
  patchFirmware,
  publishFirmware,
  type FirmwareCatalogItem,
  type FirmwareDriverCatalogItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpCatalogSearchBar,
  PpDataTable,
  PpFirmwareFileField,
  PpHintAction,
  PpHostContainedDialog,
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
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwaresPageProps = {
  permissions: ProductionPulsePermissionFlags;
};

export function FirmwaresPage({ permissions }: FirmwaresPageProps) {
  const canManage = permissions.canManageDevices;
  const [items, setItems] = useState<FirmwareCatalogItem[]>([]);
  const [drivers, setDrivers] = useState<FirmwareDriverCatalogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [firmwareKey, setFirmwareKey] = useState("esp8266_counter_v1");
  const [driverKey, setDriverKey] = useState("esp8266_counter_v1");
  const [version, setVersion] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [releaseNotes, setReleaseNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [archiveTarget, setArchiveTarget] = useState<FirmwareCatalogItem | null>(null);
  const [archiving, setArchiving] = useState(false);
  const [editTarget, setEditTarget] = useState<FirmwareCatalogItem | null>(null);
  const [editDisplayName, setEditDisplayName] = useState("");
  const [editReleaseNotes, setEditReleaseNotes] = useState("");
  const [savingEdit, setSavingEdit] = useState(false);

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
        item.artifactSha256,
      ]
        .join(" ")
        .toLowerCase();
      return hay.includes(q);
    });
  }, [items, search]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!canManage || !file) return;
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

  const openEdit = (row: FirmwareCatalogItem) => {
    setEditTarget(row);
    setEditDisplayName(row.displayName || "");
    setEditReleaseNotes(row.releaseNotes || "");
  };

  const confirmEdit = async () => {
    if (!editTarget || !canManage) return;
    setSavingEdit(true);
    try {
      await patchFirmware(editTarget.id, {
        displayName: editDisplayName.trim() || editTarget.displayName,
        releaseNotes: editReleaseNotes,
      });
      setEditTarget(null);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar metadados.");
    } finally {
      setSavingEdit(false);
    }
  };

  const confirmArchive = async () => {
    if (!archiveTarget || !canManage) return;
    setArchiving(true);
    try {
      await archiveFirmware(archiveTarget.id);
      setArchiveTarget(null);
      await reload();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao arquivar firmware.");
      setArchiveTarget(null);
    } finally {
      setArchiving(false);
    }
  };

  const columns: DataTableColumn<FirmwareCatalogItem>[] = useMemo(
    () => [
      {
        key: "family",
        header: "Família",
        render: (row) => row.displayName || row.firmwareKey,
      },
      {
        key: "version",
        header: "Versão",
        render: (row) => row.version,
      },
      {
        key: "driver",
        header: "Driver",
        render: (row) => row.driverKey,
      },
      {
        key: "sha",
        header: "SHA256",
        render: (row) => <code>{row.artifactSha256.slice(0, 12)}…</code>,
      },
      {
        key: "published",
        header: "Publicado",
        render: (row) => (row.publishedAt ? new Date(row.publishedAt).toLocaleString() : "—"),
      },
      {
        key: "archived",
        header: "Arquivo",
        render: (row) =>
          row.archivedAt ? new Date(row.archivedAt).toLocaleString() : "Ativo",
      },
      {
        key: "actions",
        header: "",
        render: (row) => (
          <div className="pp-inline-actions">
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
            {canManage && !row.archivedAt ? (
              <>
                <PpActionButton variant="ghost" onClick={() => openEdit(row)}>
                  Editar
                </PpActionButton>
                <PpActionButton variant="ghost" onClick={() => setArchiveTarget(row)}>
                  Arquivar
                </PpActionButton>
              </>
            ) : null}
          </div>
        ),
      },
    ],
    [canManage],
  );

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
                onClick={() => navigateProductionPulse(PRODUCTION_PULSE_BASE_PATH)}
              >
                Painel
              </PpActionButton>
            </PpHintAction>
            <PpHintAction hint={PP_HELP.ota.openLinks} ariaLabel="Ajuda: Hub OTA">
              <PpActionButton
                variant="primary"
                onClick={() => navigateProductionPulse(productionPulseFirmwareLinksPath())}
              >
                Hub OTA
              </PpActionButton>
            </PpHintAction>
          </>
        }
      />

      {canManage ? (
        <PpSectionCard title="Publicar versão" hint={PP_HELP.ota.publishForm}>
          <form className="pp-form-grid" onSubmit={(e) => void onSubmit(e)}>
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
        <PpCatalogSearchBar
          value={search}
          onChange={setSearch}
          placeholder="Buscar família, versão, driver…"
        />
        {loading ? (
          <PpStateBox variant="loading" title="Carregando firmwares" />
        ) : error ? (
          <PpStateBox variant="error" title="Erro" message={error} />
        ) : filteredItems.length === 0 ? (
          <PpStateBox variant="empty" title="Nenhum firmware" message={PP_HELP.ota.catalogEmpty} />
        ) : (
          <PpDataTable
            columns={columns}
            rows={filteredItems}
            rowKey={(row) => row.id}
            emptyMessage={PP_HELP.ota.catalogEmpty}
          />
        )}
      </PpSectionCard>

      <PpHostContainedDialog
        open={Boolean(editTarget)}
        title="Editar metadados"
        onClose={() => setEditTarget(null)}
      >
        {editTarget ? (
          <div className="pp-form-grid">
            <p className="pp-muted">
              <code>
                {editTarget.firmwareKey} · {editTarget.version}
              </code>{" "}
              (chave e versão imutáveis)
            </p>
            <PpNativeTextField
              id="ota-edit-display-name"
              label="Nome exibido"
              hint={PP_HELP.ota.displayName}
              value={editDisplayName}
              onChange={setEditDisplayName}
            />
            <PpNativeTextAreaField
              id="ota-edit-notes"
              label="Notas"
              hint={PP_HELP.ota.releaseNotes}
              value={editReleaseNotes}
              onChange={setEditReleaseNotes}
              span
            />
            <div className="pp-inline-actions">
              <PpActionButton variant="ghost" onClick={() => setEditTarget(null)} disabled={savingEdit}>
                Cancelar
              </PpActionButton>
              <PpActionButton onClick={() => void confirmEdit()} disabled={savingEdit}>
                {savingEdit ? "Salvando…" : "Salvar"}
              </PpActionButton>
            </div>
          </div>
        ) : null}
      </PpHostContainedDialog>

      <PpHostContainedDialog
        open={Boolean(archiveTarget)}
        title={PP_HELP.ota.archiveConfirmTitle}
        onClose={() => setArchiveTarget(null)}
      >
        <p>{PP_HELP.ota.archiveConfirmBody}</p>
        {archiveTarget ? (
          <p className="pp-muted">
            <code>
              {archiveTarget.firmwareKey} · {archiveTarget.version}
            </code>
          </p>
        ) : null}
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={() => setArchiveTarget(null)} disabled={archiving}>
            Cancelar
          </PpActionButton>
          <PpActionButton onClick={() => void confirmArchive()} disabled={archiving}>
            {archiving ? "Arquivando…" : "Arquivar"}
          </PpActionButton>
        </div>
      </PpHostContainedDialog>
    </div>
  );
}
