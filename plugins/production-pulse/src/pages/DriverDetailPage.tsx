import { useCallback, useEffect, useMemo, useState } from "react";

import {
  archiveDriver,
  getDriver,
  unarchiveDriver,
  type DriverListItem,
} from "../api/productionPulseApi";
import {
  PpActionButton,
  PpHintAction,
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
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { DriverFormPage } from "./DriverFormPage";
import { navigateProductionPulse } from "../utils/navigation";

type DriverDetailPageProps = {
  driverKey: string;
  permissions: ProductionPulsePermissionFlags;
  embedded?: boolean;
  onDone?: () => void;
  onCancel?: () => void;
  onRequestArchive?: (driverKey: string) => void;
};

export function DriverDetailPage({
  driverKey,
  permissions,
  embedded = false,
  onDone,
  onCancel,
  onRequestArchive,
}: DriverDetailPageProps) {
  const canManage = permissions.canManageDevices;
  const [item, setItem] = useState<DriverListItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDriver(driverKey);
      setItem(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao carregar tipo de driver.");
    } finally {
      setLoading(false);
    }
  }, [driverKey]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const isArchived = Boolean(item?.archivedAt);
  const hubPath = productionPulseFirmwareLinksPath({ branch: "01", panel: "drivers" });

  const heroDescription = useMemo(() => {
    if (!item) return "";
    const status = isArchived ? PP_HELP.drivers.statusArchived : PP_HELP.drivers.statusActive;
    return `${item.key} · ${item.protocolKind} · ${item.roleKey} · ${status}`;
  }, [isArchived, item]);

  const goBack = () => {
    if (onCancel) {
      onCancel();
      return;
    }
    navigateProductionPulse(hubPath);
  };

  const handleUnarchive = async () => {
    if (!item || !canManage) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await unarchiveDriver(item.key);
      setItem(updated);
      onDone?.();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Falha ao reativar.");
    } finally {
      setBusy(false);
    }
  };

  if (!permissions.canViewDevices) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.drivers.breadcrumbDetail} badge={ppShellIcon} />
        <PpStateBox
          variant="error"
          title="Sem permissão"
          message="Você não tem permissão para visualizar tipos de driver."
        />
      </div>
    );
  }

  if (loading && !item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.drivers.breadcrumbDetail} badge={ppShellIcon} />
        <PpStateBox variant="loading" title="Carregando tipo de driver…" />
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.drivers.breadcrumbDetail} badge={ppShellIcon} />
        <PpStateBox variant="error" title="Erro" message={error} />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero title={PP_HELP.drivers.breadcrumbDetail} badge={ppShellIcon} />
        <PpStateBox variant="empty" title="Tipo de driver não encontrado" />
      </div>
    );
  }

  if (editing && canManage && !isArchived) {
    return (
      <DriverFormPage
        mode="edit"
        initial={item}
        permissions={permissions}
        embedded={embedded}
        onCancel={() => setEditing(false)}
        onDone={(saved) => {
          setItem(saved);
          setEditing(false);
          onDone?.();
        }}
      />
    );
  }

  return (
    <div className={`pp-page-stack pp-form-page${embedded ? " pp-form-page--embedded" : ""}`}>
      {!embedded ? (
        <>
          <ProductionPulsePagePath
            panelHref={PRODUCTION_PULSE_BASE_PATH}
            items={[{ id: "hub", label: "Admin", href: hubPath }]}
            current={item.labelPt || item.key}
          />
          <PpPageHero
            title={item.labelPt || item.key}
            description={heroDescription}
            badge={ppShellIcon}
            actions={
              canManage ? (
                <div className="pp-inline-actions">
                  {!isArchived ? (
                    <PpHintAction hint={PP_HELP.drivers.archive} ariaLabel="Ajuda: Arquivar">
                      <PpActionButton
                        variant="ghost"
                        disabled={busy}
                        onClick={() => {
                          if (onRequestArchive) {
                            onRequestArchive(item.key);
                            return;
                          }
                          void archiveDriver(item.key).then((updated) => {
                            setItem(updated);
                            onDone?.();
                          });
                        }}
                      >
                        Arquivar
                      </PpActionButton>
                    </PpHintAction>
                  ) : (
                    <PpHintAction hint={PP_HELP.drivers.unarchive} ariaLabel="Ajuda: Reativar">
                      <PpActionButton
                        variant="ghost"
                        disabled={busy}
                        onClick={() => void handleUnarchive()}
                      >
                        Reativar
                      </PpActionButton>
                    </PpHintAction>
                  )}
                  {!isArchived ? (
                    <PpActionButton onClick={() => setEditing(true)}>Editar</PpActionButton>
                  ) : null}
                </div>
              ) : null
            }
          />
        </>
      ) : (
        <div className="pp-inline-actions pp-mb-sm">
          {canManage && !isArchived ? (
            <PpActionButton onClick={() => setEditing(true)}>Editar metadados</PpActionButton>
          ) : null}
          {canManage && isArchived ? (
            <PpActionButton
              variant="ghost"
              disabled={busy}
              onClick={() => void handleUnarchive()}
            >
              Reativar
            </PpActionButton>
          ) : null}
          {canManage && !isArchived ? (
            <PpActionButton
              variant="ghost"
              disabled={busy}
              onClick={() => {
                if (onRequestArchive) {
                  onRequestArchive(item.key);
                  return;
                }
                void archiveDriver(item.key).then((updated) => {
                  setItem(updated);
                  onDone?.();
                });
              }}
            >
              Arquivar
            </PpActionButton>
          ) : null}
          <PpActionButton variant="ghost" onClick={goBack}>
            Fechar
          </PpActionButton>
        </div>
      )}

      {actionError ? (
        <PpStateBox variant="error" title="Ação falhou" message={actionError} />
      ) : null}

      <div className="pp-form-layout">
        <PpSectionCard title="Identidade" hint={PP_HELP.drivers.sectionIdentity}>
          <dl className="pp-detail-dl">
            <div>
              <dt>Chave</dt>
              <dd>
                <code>{item.key}</code>
              </dd>
            </div>
            <div>
              <dt>Protocolo</dt>
              <dd>{item.protocolKind}</dd>
            </div>
            <div>
              <dt>Role</dt>
              <dd>{item.roleKey}</dd>
            </div>
            <div>
              <dt>Estado</dt>
              <dd>
                {isArchived ? PP_HELP.drivers.statusArchived : PP_HELP.drivers.statusActive}
              </dd>
            </div>
            <div>
              <dt>Rótulo</dt>
              <dd>{item.labelPt}</dd>
            </div>
            <div>
              <dt>Descrição</dt>
              <dd>{item.descriptionPt || "—"}</dd>
            </div>
            <div>
              <dt>Operador</dt>
              <dd>
                {item.operatorSurface} ·{" "}
                {item.operatorEligible ? "elegível" : "não elegível"}
              </dd>
            </div>
            <div>
              <dt>Poll timeout</dt>
              <dd>{item.poll?.timeoutMs ?? 3000} ms</dd>
            </div>
          </dl>
        </PpSectionCard>

        <PpSectionCard title="Métricas" hint={PP_HELP.drivers.sectionMetrics}>
          {(item.metrics ?? []).length === 0 ? (
            <p className="pp-muted">Sem métricas.</p>
          ) : (
            <ul className="pp-muted">
              {(item.metrics ?? []).map((metric) => (
                <li key={metric.key}>
                  <code>{metric.key}</code> — {metric.labelPt || metric.key} ({metric.type})
                  {metric.primary ? " · primária" : ""}
                </li>
              ))}
            </ul>
          )}
        </PpSectionCard>

        <PpSectionCard title="Comandos" hint={PP_HELP.drivers.sectionCommands}>
          {(item.commands ?? []).length === 0 ? (
            <p className="pp-muted">Sem comandos.</p>
          ) : (
            <p>{(item.commands ?? []).join(", ")}</p>
          )}
        </PpSectionCard>
      </div>
    </div>
  );
}
