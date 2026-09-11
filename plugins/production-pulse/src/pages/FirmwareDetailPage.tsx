import { useCallback, useEffect, useMemo, useState } from "react";
import { Code2, FileCode, Package } from "lucide-react";

import {
  archiveFirmware,
  attachFirmwareArtifact,
  fetchFirmwareById,
  patchFirmware,
  publishFirmwareVersion,
  type FirmwareDetail,
  type FirmwareListItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFirmwareArtifactField,
  PpFirmwareSourceField,
  PpHintAction,
  PpHostContainedDialog,
  PpNativeSelectField,
  PpNativeTextAreaField,
  PpNativeTextField,
  PpPageHero,
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { DetailFactList } from "../components/detail/DetailFactList";
import { DetailLightCard } from "../components/detail/DetailLightCard";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareLinksPath,
  productionPulseFirmwaresPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import {
  formatFirmwareArtifactBytes,
  firmwareLifecycleBadgeClass,
  firmwareLifecycleLabel,
} from "../utils/firmwareCatalogDisplay";
import { firmwareSiblingsForFamily } from "../utils/firmwareCatalogGrouping";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareDetailPageProps = {
  firmwareId: string;
  permissions: ProductionPulsePermissionFlags;
  embedded?: boolean;
  onDone?: () => void;
  onCancel?: () => void;
  /** Other versions of the same family (from Hub catalog cache). */
  siblingFirmwares?: FirmwareListItem[];
  onSelectVersion?: (firmwareId: string) => void;
};

export function FirmwareDetailPage({
  firmwareId,
  permissions,
  embedded = false,
  onDone,
  onCancel,
  siblingFirmwares = [],
  onSelectVersion,
}: FirmwareDetailPageProps) {
  const canManage = permissions.canManageDevices;
  const [item, setItem] = useState<FirmwareDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [editMetaOpen, setEditMetaOpen] = useState(false);
  const [editDisplayName, setEditDisplayName] = useState("");
  const [editReleaseNotes, setEditReleaseNotes] = useState("");
  const [sourceDraft, setSourceDraft] = useState("");
  const [artifactFile, setArtifactFile] = useState<File | null>(null);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [publishOpen, setPublishOpen] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchFirmwareById(firmwareId);
      setItem(data);
      setSourceDraft(data.sourceText ?? "");
      setEditDisplayName(data.displayName || "");
      setEditReleaseNotes(data.releaseNotes || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar versão.");
    } finally {
      setLoading(false);
    }
  }, [firmwareId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const isDraft = item?.lifecycle === "draft";
  const isPublished = item?.lifecycle === "published";
  const isArchived = item?.lifecycle === "archived";
  const canEditSource = canManage && isDraft;
  const canAttachArtifact = canManage && isDraft;
  const canPublish = canManage && isDraft && item?.hasArtifact;
  const canArchive = canManage && !isArchived;
  const canEditMeta = canManage && !isArchived;

  const heroDescription = useMemo(() => {
    if (!item) return "";
    return `Família ${item.firmwareKey} · v${item.version} · Driver ${item.driverKey}`;
  }, [item]);

  const versionSwitcherOptions = useMemo(() => {
    if (!item || !onSelectVersion) return [];
    const siblings = firmwareSiblingsForFamily(siblingFirmwares, item.firmwareKey);
    if (siblings.length <= 1) return [];
    return siblings.map((sibling) => {
      const life = firmwareLifecycleLabel(sibling.lifecycle);
      const archived = sibling.archivedAt ? " · arquivada" : "";
      return {
        value: sibling.id,
        label: `v${sibling.version} · ${life}${archived}`,
      };
    });
  }, [item, onSelectVersion, siblingFirmwares]);

  const metaFacts = useMemo(() => {
    if (!item) return [];
    return [
      { label: "Família", value: <code>{item.firmwareKey}</code> },
      { label: "Versão", value: <code>{item.version}</code> },
      { label: "Driver", value: <code>{item.driverKey}</code> },
      {
        label: "Publicado em",
        value: item.publishedAt ? new Date(item.publishedAt).toLocaleString() : "—",
      },
      {
        label: "Arquivado em",
        value: item.archivedAt ? new Date(item.archivedAt).toLocaleString() : "—",
      },
    ];
  }, [item]);

  const artifactSizeLabel = item
    ? formatFirmwareArtifactBytes(item.artifactSizeBytes)
    : null;

  const saveSource = async () => {
    if (!item || !canEditSource) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await patchFirmware(item.id, { sourceText: sourceDraft });
      setItem(updated);
      setSourceDraft(updated.sourceText ?? "");
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao salvar sketch.");
    } finally {
      setBusy(false);
    }
  };

  const attachArtifact = async () => {
    if (!item || !artifactFile || !canAttachArtifact) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await attachFirmwareArtifact(item.id, artifactFile);
      setItem(updated);
      setArtifactFile(null);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao anexar artefato.");
    } finally {
      setBusy(false);
    }
  };

  const confirmPublish = async () => {
    if (!item || !canPublish) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await publishFirmwareVersion(item.id);
      setItem(updated);
      setPublishOpen(false);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao publicar.");
    } finally {
      setBusy(false);
    }
  };

  const confirmArchive = async () => {
    if (!item || !canArchive) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await archiveFirmware(item.id);
      setItem(updated);
      setArchiveOpen(false);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao arquivar.");
    } finally {
      setBusy(false);
    }
  };

  const confirmEditMeta = async () => {
    if (!item || !canEditMeta) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await patchFirmware(item.id, {
        displayName: editDisplayName.trim() || item.displayName,
        releaseNotes: editReleaseNotes,
      });
      setItem(updated);
      setEditMetaOpen(false);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao salvar metadados.");
    } finally {
      setBusy(false);
    }
  };

  const heroActions = item ? (
    <div className="pp-detail-hero-actions">
      <span className={firmwareLifecycleBadgeClass(item.lifecycle)}>
        {firmwareLifecycleLabel(item.lifecycle)}
      </span>
      {canEditMeta ? (
        <PpHintAction hint={PP_HELP.ota.editMetadata} ariaLabel="Ajuda: Editar metadados">
          <PpActionButton
            variant="ghost"
            className="pp-hero-brand-btn"
            onClick={() => setEditMetaOpen(true)}
          >
            Editar metadados
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {canPublish ? (
        <PpHintAction hint={PP_HELP.ota.publishVersion} ariaLabel="Ajuda: Publicar">
          <PpActionButton
            className="pp-hero-brand-btn"
            onClick={() => setPublishOpen(true)}
            disabled={busy}
          >
            Publicar versão
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {canArchive ? (
        <PpHintAction hint={PP_HELP.ota.archiveFirmware} ariaLabel="Ajuda: Arquivar">
          <PpActionButton
            variant="ghost"
            className="pp-hero-brand-btn"
            onClick={() => setArchiveOpen(true)}
            disabled={busy}
          >
            Arquivar
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {!embedded ? (
        <PpHintAction hint={PP_HELP.otaLinks.afterPublish} ariaLabel="Ajuda: Admin mapa">
          <PpActionButton
            variant="ghost"
            className="pp-hero-brand-btn"
            onClick={() => {
              if (onDone) {
                onDone();
                return;
              }
              navigateProductionPulse(
                productionPulseFirmwareLinksPath({ firmwareKey: item.firmwareKey, branch: "01" }),
              );
            }}
          >
            Voltar ao mapa
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {embedded && onCancel ? (
        <PpActionButton variant="ghost" className="pp-hero-brand-btn" onClick={onCancel}>
          Fechar
        </PpActionButton>
      ) : null}
    </div>
  ) : null;

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar firmwares."
        />
      </div>
    );
  }

  if (loading && !item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={embedded ? undefined : ppShellIcon} />
        <PpStateBox variant="loading" title="Carregando versão…" />
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="pp-page-stack">
        {!embedded ? (
          <ProductionPulsePagePath
            panelHref={PRODUCTION_PULSE_BASE_PATH}
            items={[{ id: "hub", label: "Hub OTA", href: productionPulseFirmwaresPath() }]}
            current="Versão"
          />
        ) : null}
        <PpPageHero title="Versão de firmware" badge={embedded ? undefined : ppShellIcon} />
        <PpStateBox variant="error" title="Erro" message={error} />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={embedded ? undefined : ppShellIcon} />
        <PpStateBox variant="empty" title="Versão não encontrada" />
      </div>
    );
  }

  return (
    <div className={`pp-page-stack pp-firmware-detail${embedded ? " pp-form-page--embedded" : ""}`}>
      {!embedded ? (
        <ProductionPulsePagePath
          panelHref={PRODUCTION_PULSE_BASE_PATH}
          items={[{ id: "hub", label: "Admin", href: productionPulseFirmwaresPath() }]}
          current={item.displayName || `${item.firmwareKey} · ${item.version}`}
        />
      ) : null}

      <PpPageHero
        title={item.displayName || item.firmwareKey}
        description={heroDescription}
        badge={embedded ? undefined : ppShellIcon}
        actions={heroActions}
      />

      {versionSwitcherOptions.length > 0 && onSelectVersion ? (
        <div className="pp-firmware-version-switcher">
          <PpNativeSelectField
            id="fw-detail-version-switcher"
            label="Versão da família"
            hint={PP_HELP.hub.firmwareVersionSwitcher}
            value={item.id}
            onChange={(nextId) => {
              if (nextId && nextId !== item.id) onSelectVersion(nextId);
            }}
            options={versionSwitcherOptions}
            searchable={false}
          />
        </div>
      ) : null}

      {actionError ? (
        <PpStateBox variant="error" title="Operação" message={actionError} />
      ) : null}

      <div className="pp-detail-stack">
        <DetailLightCard icon={FileCode} title="Metadados" hint={PP_HELP.ota.detailMetadata}>
          <DetailFactList facts={metaFacts} />
          {item.releaseNotes ? (
            <p className="pp-muted" title={PP_HELP.ota.releaseNotes}>
              <strong>Notas:</strong> {item.releaseNotes}
            </p>
          ) : null}
        </DetailLightCard>

        <DetailLightCard icon={Code2} title="Sketch (.ino)" hint={PP_HELP.ota.detailSource}>
          {canEditSource ? (
            <div className="pp-form-grid">
              <PpFirmwareSourceField
                id="fw-detail-source"
                label="Importar .ino"
                hint={PP_HELP.ota.sourceFile}
                editorLabel="Código-fonte"
                editorHint={PP_HELP.ota.sourceTextarea}
                value={sourceDraft}
                onChange={setSourceDraft}
                rows={16}
                onReadError={() => setActionError(PP_HELP.ota.sourceFileReadFailed)}
              />
              <PpActionButton onClick={() => void saveSource()} disabled={busy}>
                {busy ? "Salvando…" : "Salvar sketch"}
              </PpActionButton>
            </div>
          ) : item.hasSource && item.sourceText ? (
            <pre className="pp-firmware-source" tabIndex={0}>
              {item.sourceText}
            </pre>
          ) : (
            <PpStateBox variant="empty" title="Sem sketch" message={PP_HELP.ota.sourceEmpty} />
          )}
        </DetailLightCard>

        <DetailLightCard icon={Package} title="Artefato OTA (.bin)" hint={PP_HELP.ota.detailArtifact}>
          {item.hasArtifact && item.artifactSha256 ? (
            <DetailFactList
              facts={[
                {
                  label: "SHA256",
                  value: <code title={item.artifactSha256}>{item.artifactSha256}</code>,
                },
                {
                  label: "Tamanho",
                  value:
                    artifactSizeLabel ||
                    (item.artifactSizeBytes
                      ? `${item.artifactSizeBytes.toLocaleString("pt-BR")} bytes`
                      : "—"),
                },
              ]}
            />
          ) : (
            <PpStateBox variant="empty" title="Sem binário" message={PP_HELP.ota.artifactEmptyDraft} />
          )}
          {canAttachArtifact ? (
            <div className="pp-form-grid">
              <PpFirmwareArtifactField
                id="fw-detail-bin"
                label="Anexar .bin"
                hint={PP_HELP.ota.file}
                file={artifactFile}
                onChange={setArtifactFile}
              />
              <PpActionButton onClick={() => void attachArtifact()} disabled={busy || !artifactFile}>
                {busy ? "Anexando…" : "Anexar artefato"}
              </PpActionButton>
            </div>
          ) : null}
          {isPublished ? (
            <p className="pp-muted" title={PP_HELP.ota.artifactImmutable}>
              Artefato publicado é imutável — publique uma nova versão para corrigir o binário.
            </p>
          ) : null}
        </DetailLightCard>
      </div>

      <PpHostContainedDialog open={editMetaOpen} title="Editar metadados" onClose={() => setEditMetaOpen(false)}>
        <div className="pp-form-grid">
          <PpNativeTextField
            id="fw-edit-display-name"
            label="Nome exibido"
            hint={PP_HELP.ota.displayName}
            value={editDisplayName}
            onChange={setEditDisplayName}
          />
          <PpNativeTextAreaField
            id="fw-edit-notes"
            label="Notas"
            hint={PP_HELP.ota.releaseNotes}
            value={editReleaseNotes}
            onChange={setEditReleaseNotes}
            span
          />
          <div className="pp-inline-actions">
            <PpActionButton variant="ghost" onClick={() => setEditMetaOpen(false)} disabled={busy}>
              Cancelar
            </PpActionButton>
            <PpActionButton onClick={() => void confirmEditMeta()} disabled={busy}>
              {busy ? "Salvando…" : "Salvar"}
            </PpActionButton>
          </div>
        </div>
      </PpHostContainedDialog>

      <PpHostContainedDialog open={publishOpen} title={PP_HELP.ota.publishConfirmTitle} onClose={() => setPublishOpen(false)}>
        <p>{PP_HELP.ota.publishConfirmBody}</p>
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={() => setPublishOpen(false)} disabled={busy}>
            Cancelar
          </PpActionButton>
          <PpActionButton onClick={() => void confirmPublish()} disabled={busy}>
            {busy ? "Publicando…" : "Publicar"}
          </PpActionButton>
        </div>
      </PpHostContainedDialog>

      <PpHostContainedDialog open={archiveOpen} title={PP_HELP.ota.archiveConfirmTitle} onClose={() => setArchiveOpen(false)}>
        <p>{PP_HELP.ota.archiveConfirmBody}</p>
        <div className="pp-inline-actions">
          <PpActionButton variant="ghost" onClick={() => setArchiveOpen(false)} disabled={busy}>
            Cancelar
          </PpActionButton>
          <PpActionButton onClick={() => void confirmArchive()} disabled={busy}>
            {busy ? "Arquivando…" : "Arquivar"}
          </PpActionButton>
        </div>
      </PpHostContainedDialog>
    </div>
  );
}
