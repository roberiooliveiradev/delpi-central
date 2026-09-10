import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, CircuitBoard, Terminal } from "lucide-react";

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
  PpStateBox,
  ppShellIcon,
} from "../app/productionPulseUi";
import { DetailCommandChips } from "../components/detail/DetailCommandChips";
import { DetailFactList } from "../components/detail/DetailFactList";
import { DetailLightCard } from "../components/detail/DetailLightCard";
import { DetailMetricDefs } from "../components/detail/DetailMetricDefs";
import { ProductionPulsePagePath } from "../components/ProductionPulsePagePath";
import type { ProductionPulsePermissionFlags } from "../constants/permissions";
import {
  PRODUCTION_PULSE_BASE_PATH,
  productionPulseFirmwareLinksPath,
} from "../constants/routes";
import { PP_HELP } from "../content/helpTooltips";
import { resolveDriverProtocolDisplay } from "../utils/driverCatalogDisplay";
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
  const protocol = resolveDriverProtocolDisplay(item?.protocolKind);

  const heroDescription = useMemo(() => {
    if (!item) return "";
    return `${item.key} · ${protocol.shortLabel} · ${item.roleKey}`;
  }, [item, protocol.shortLabel]);

  const identityFacts = useMemo(() => {
    if (!item) return [];
    return [
      { label: "Chave", value: <code>{item.key}</code> },
      { label: "Protocolo", value: protocol.label },
      { label: "Role", value: item.roleKey },
      {
        label: "Operador",
        value: `${item.operatorSurface} · ${
          item.operatorEligible ? "elegível" : "não elegível"
        }`,
      },
      { label: "Poll timeout", value: `${item.poll?.timeoutMs ?? 3000} ms` },
    ];
  }, [item, protocol.label]);

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

  const handleArchive = () => {
    if (!item || !canManage) return;
    if (onRequestArchive) {
      onRequestArchive(item.key);
      return;
    }
    void archiveDriver(item.key).then((updated) => {
      setItem(updated);
      onDone?.();
    });
  };

  const statusBadge = (
    <span
      className={
        isArchived
          ? "pp-lifecycle-badge pp-lifecycle-badge--archived"
          : "pp-lifecycle-badge pp-lifecycle-badge--published"
      }
    >
      {isArchived ? PP_HELP.drivers.statusArchived : PP_HELP.drivers.statusActive}
    </span>
  );

  const heroActions = item ? (
    <div className="pp-detail-hero-actions">
      {statusBadge}
      {canManage && !isArchived ? (
        <PpActionButton
          variant="ghost"
          className="pp-hero-brand-btn"
          onClick={() => setEditing(true)}
        >
          Editar metadados
        </PpActionButton>
      ) : null}
      {canManage && isArchived ? (
        <PpHintAction hint={PP_HELP.drivers.unarchive} ariaLabel="Ajuda: Reativar">
          <PpActionButton
            variant="ghost"
            className="pp-hero-brand-btn"
            disabled={busy}
            onClick={() => void handleUnarchive()}
          >
            Reativar
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {canManage && !isArchived ? (
        <PpHintAction hint={PP_HELP.drivers.archive} ariaLabel="Ajuda: Arquivar">
          <PpActionButton
            variant="ghost"
            className="pp-hero-brand-btn"
            disabled={busy}
            onClick={handleArchive}
          >
            Arquivar
          </PpActionButton>
        </PpHintAction>
      ) : null}
      {embedded ? (
        <PpActionButton variant="ghost" className="pp-hero-brand-btn" onClick={goBack}>
          Fechar
        </PpActionButton>
      ) : null}
    </div>
  ) : null;

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
        <PpPageHero
          title={PP_HELP.drivers.breadcrumbDetail}
          badge={embedded ? undefined : ppShellIcon}
        />
        <PpStateBox variant="loading" title="Carregando tipo de driver…" />
      </div>
    );
  }

  if (error && !item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero
          title={PP_HELP.drivers.breadcrumbDetail}
          badge={embedded ? undefined : ppShellIcon}
        />
        <PpStateBox variant="error" title="Erro" message={error} />
      </div>
    );
  }

  if (!item) {
    return (
      <div className="pp-page-stack">
        <PpPageHero
          title={PP_HELP.drivers.breadcrumbDetail}
          badge={embedded ? undefined : ppShellIcon}
        />
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
        <ProductionPulsePagePath
          panelHref={PRODUCTION_PULSE_BASE_PATH}
          items={[{ id: "hub", label: "Admin", href: hubPath }]}
          current={item.labelPt || item.key}
        />
      ) : null}

      <PpPageHero
        title={item.labelPt || item.key}
        description={heroDescription}
        badge={embedded ? undefined : ppShellIcon}
        actions={heroActions}
      />

      {actionError ? (
        <PpStateBox variant="error" title="Ação falhou" message={actionError} />
      ) : null}

      <div className="pp-detail-stack">
        <DetailLightCard
          icon={CircuitBoard}
          title="Identidade"
          hint={PP_HELP.drivers.sectionIdentity}
        >
          <DetailFactList facts={identityFacts} />
          {item.descriptionPt ? (
            <p className="pp-muted">
              <strong>Descrição:</strong> {item.descriptionPt}
            </p>
          ) : null}
        </DetailLightCard>

        <DetailLightCard icon={Activity} title="Métricas" hint={PP_HELP.drivers.sectionMetrics}>
          <DetailMetricDefs metrics={item.metrics ?? []} />
        </DetailLightCard>

        <DetailLightCard icon={Terminal} title="Comandos" hint={PP_HELP.drivers.sectionCommands}>
          <DetailCommandChips commands={item.commands ?? []} />
        </DetailLightCard>
      </div>
    </div>
  );
}
