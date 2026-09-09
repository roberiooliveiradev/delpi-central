import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveFirmware,
  attachFirmwareArtifact,
  fetchFirmwareById,
  patchFirmware,
  publishFirmwareVersion,
  type FirmwareDetail,
  type FirmwareLifecycle,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpFirmwareFileField,
  PpHintAction,
  PpHostContainedDialog,
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
  productionPulseFirmwareLinksPath,
  productionPulseFirmwaresPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { navigateProductionPulse } from "../utils/navigation";

type FirmwareDetailPageProps = {
  firmwareId: string;
  permissions: ProductionPulsePermissionFlags;
};

function lifecycleLabel(lifecycle: FirmwareLifecycle): string {
  if (lifecycle === "draft") return PP_HELP.ota.status.draft;
  if (lifecycle === "archived") return PP_HELP.ota.statusArchived;
  return PP_HELP.ota.statusPublished;
}

function lifecycleBadgeClass(lifecycle: FirmwareLifecycle): string {
  if (lifecycle === "draft") return "pp-lifecycle-badge pp-lifecycle-badge--draft";
  if (lifecycle === "archived") return "pp-lifecycle-badge pp-lifecycle-badge--archived";
  return "pp-lifecycle-badge pp-lifecycle-badge--published";
}

export function FirmwareDetailPage({ firmwareId, permissions }: FirmwareDetailPageProps) {
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
    return `Família ${item.firmwareKey} · Versão ${item.version} · Driver ${item.driverKey} · ${lifecycleLabel(item.lifecycle)}`;
  }, [item]);

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

  const loadInoFile = async (file: File | null) => {
    if (!file) return;
    try {
      const text = await file.text();
      setSourceDraft(text);
    } catch {
      setActionError(PP_HELP.ota.sourceFileReadFailed);
    }
  };

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={ppShellIcon} />
        <PpStateBox variant="error" title="Sem permissão" message="Você não tem permissão para visualizar firmwares." />
      </div>
    );
  }

  if (loading && !item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={ppShellIcon} />
        <PpStateBox variant="loading" title="Carregando versão…" />
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="pp-page-stack">
        <ProductionPulsePagePath
          panelHref={PRODUCTION_PULSE_BASE_PATH}
          items={[{ label: "Firmwares", href: productionPulseFirmwaresPath() }]}
          current="Versão"
        />
        <PpPageHero title="Versão de firmware" badge={ppShellIcon} />
        <PpStateBox variant="error" title="Erro" message={error} />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title="Versão de firmware" badge={ppShellIcon} />
        <PpStateBox variant="empty" title="Versão não encontrada" />
      </div>
    );
  }

  return (
    <div className="pp-page-stack pp-firmware-detail">
      <ProductionPulsePagePath
        panelHref={PRODUCTION_PULSE_BASE_PATH}
        items={[{ label: "Firmwares", href: productionPulseFirmwaresPath() }]}
        current={item.displayName || `${item.firmwareKey} · ${item.version}`}
      />

      <PpPageHero
        title={
          <>
            {item.displayName || item.firmwareKey}{" "}
            <span className={lifecycleBadgeClass(item.lifecycle)}>{lifecycleLabel(item.lifecycle)}</span>
          </>
        }
        description={heroDescription}
        badge={ppShellIcon}
        actions={
          canManage ? (
            <div className="pp-inline-actions">
              {canEditMeta ? (
                <PpHintAction hint={PP_HELP.ota.editMetadata} ariaLabel="Ajuda: Editar metadados">
                  <PpActionButton variant="ghost" className="pp-hero-brand-btn" onClick={() => setEditMetaOpen(true)}>
                    Editar metadados
                  </PpActionButton>
                </PpHintAction>
              ) : null}
              {canPublish ? (
                <PpHintAction hint={PP_HELP.ota.publishVersion} ariaLabel="Ajuda: Publicar">
                  <PpActionButton className="pp-hero-brand-btn" onClick={() => setPublishOpen(true)} disabled={busy}>
                    Publicar versão
                  </PpActionButton>
                </PpHintAction>
              ) : null}
              {canArchive ? (
                <PpHintAction hint={PP_HELP.ota.archiveFirmware} ariaLabel="Ajuda: Arquivar">
                  <PpActionButton variant="ghost" className="pp-hero-brand-btn" onClick={() => setArchiveOpen(true)} disabled={busy}>
                    Arquivar
                  </PpActionButton>
                </PpHintAction>
              ) : null}
              <PpHintAction hint={PP_HELP.otaLinks.afterPublish} ariaLabel="Ajuda: Hub OTA">
                <PpActionButton
                  variant="ghost"
                  className="pp-hero-brand-btn"
                  onClick={() =>
                    navigateProductionPulse(
                      productionPulseFirmwareLinksPath({ firmwareKey: item.firmwareKey, branch: "01" }),
                    )
                  }
                >
                  Abrir hub OTA
                </PpActionButton>
              </PpHintAction>
            </div>
          ) : null
        }
      />

      {actionError ? <PpStateBox variant="error" title="Operação" message={actionError} /> : null}

      <PpSectionCard title="Metadados" hint={PP_HELP.ota.detailMetadata}>
        <dl className="pp-definition-list">
          <div>
            <dt>Família</dt>
            <dd>
              <code>{item.firmwareKey}</code>
            </dd>
          </div>
          <div>
            <dt>Versão</dt>
            <dd>
              <code>{item.version}</code>
            </dd>
          </div>
          <div>
            <dt>Driver</dt>
            <dd>
              <code>{item.driverKey}</code>
            </dd>
          </div>
          <div>
            <dt>Publicado em</dt>
            <dd>{item.publishedAt ? new Date(item.publishedAt).toLocaleString() : "—"}</dd>
          </div>
          <div>
            <dt>Arquivado em</dt>
            <dd>{item.archivedAt ? new Date(item.archivedAt).toLocaleString() : "—"}</dd>
          </div>
        </dl>
        {item.releaseNotes ? (
          <p className="pp-muted" title={PP_HELP.ota.releaseNotes}>
            <strong>Notas:</strong> {item.releaseNotes}
          </p>
        ) : null}
      </PpSectionCard>

      <PpSectionCard title="Sketch (.ino)" hint={PP_HELP.ota.detailSource}>
        {canEditSource ? (
          <div className="pp-form-grid">
            <PpFirmwareFileField
              id="fw-detail-ino"
              label="Importar .ino"
              hint={PP_HELP.ota.sourceFile}
              accept=".ino,.txt,text/plain"
              file={null}
              onChange={(file) => void loadInoFile(file)}
            />
            <PpNativeTextAreaField
              id="fw-detail-source"
              label="Código-fonte"
              hint={PP_HELP.ota.sourceTextarea}
              value={sourceDraft}
              onChange={setSourceDraft}
              rows={16}
              span
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
      </PpSectionCard>

      <PpSectionCard title="Artefato OTA (.bin)" hint={PP_HELP.ota.detailArtifact}>
        {item.hasArtifact && item.artifactSha256 ? (
          <dl className="pp-definition-list">
            <div>
              <dt>SHA256</dt>
              <dd>
                <code>{item.artifactSha256}</code>
              </dd>
            </div>
            <div>
              <dt>Tamanho</dt>
              <dd>{item.artifactSizeBytes ? `${item.artifactSizeBytes.toLocaleString("pt-BR")} bytes` : "—"}</dd>
            </div>
          </dl>
        ) : (
          <PpStateBox variant="empty" title="Sem artefato" message={PP_HELP.ota.artifactEmptyDraft} />
        )}
        {canAttachArtifact ? (
          <div className="pp-form-grid">
            <PpFirmwareFileField
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
      </PpSectionCard>

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
