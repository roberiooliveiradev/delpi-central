import { PackageSearch, RefreshCw } from "lucide-react";
import { useEffect, useState, type CSSProperties } from "react";

import warehouseSpoolsUrl from "../assets/line-feeder/warehouse-spools.png";
import { LineFeederCollectModal } from "../components/LineFeederCollectModal";
import { LineFeederIdleCard } from "../components/LineFeederIdleCard";
import { LineFeederMaterialsPanel } from "../components/LineFeederMaterialsPanel";
import { LineFeederPreviewProgress } from "../components/LineFeederPreviewProgress";
import { LineFeederUrgentBell } from "../components/LineFeederUrgentBell";
import { PpcWorkspaceHeader } from "../components/PpcWorkspaceHeader";
import { copy } from "../content/copy";
import { helpTooltips } from "../content/helpTooltips";
import { useLineFeederMaterialsPreview } from "../hooks/useLineFeederMaterialsPreview";
import type { PpcBranch } from "../types";
import { buildPpcHref, navigatePpc } from "../utils/routeParser";

type LineFeederPageProps = {
  branch: PpcBranch;
  /** Parâmetros legados da URL — ignorados no fluxo novo (compatibilidade de link). */
  cutoffDate?: string | null;
  cutoffTime?: string | null;
  workCenter?: string | null;
  status?: string | null;
  planId?: string | null;
};

export function LineFeederPage({ branch }: LineFeederPageProps) {
  const texts = copy.lineFeeder;
  const [modalOpen, setModalOpen] = useState(false);
  const preview = useLineFeederMaterialsPreview(branch);

  // Links antigos com cutoff/plan não quebram a página; a URL canônica fica só com filial.
  useEffect(() => {
    navigatePpc(
      buildPpcHref({
        subpluginId: "line-feeder",
        branch,
      }),
    );
  }, [branch]);

  const errorMessage = (() => {
    if (!preview.error) return null;
    if (preview.error.kind === "forbidden") return texts.materialsPreview.forbidden;
    if (preview.error.kind === "stale") return texts.materialsPreview.staleError;
    if (preview.error.kind === "gateway") return texts.materialsPreview.gateway;
    return preview.error.message;
  })();

  const sceneStyle = {
    ["--ppc-feeder-scene-image" as string]: `url(${JSON.stringify(warehouseSpoolsUrl)})`,
  } as CSSProperties;

  return (
    <div
      className="ppc-page-stack ppc-page-stack--demand ppc-feeder-scene"
      style={sceneStyle}
    >
      <PpcWorkspaceHeader
        title={texts.title}
        subtitle={texts.subtitle}
        titleHint={helpTooltips.lineFeeder}
        branch={branch}
        subpluginId="line-feeder"
        actions={
          <div className="ppc-feeder-toolbar">
            <LineFeederUrgentBell branch={branch} />
            {preview.hasQuery ? (
              <button
                type="button"
                className="ppc-icon-btn"
                onClick={() => preview.reload()}
                disabled={preview.loading}
                title={texts.refreshQuery}
              >
                <RefreshCw size={16} strokeWidth={1.75} aria-hidden />
                <span>{preview.loading ? texts.refreshBusy : texts.refreshQuery}</span>
              </button>
            ) : null}
            <button
              type="button"
              className="ppc-icon-btn ppc-feeder__collect-cta"
              onClick={() => setModalOpen(true)}
              disabled={preview.loading}
            >
              <PackageSearch size={16} strokeWidth={1.75} aria-hidden />
              <span>{texts.collectAction}</span>
            </button>
          </div>
        }
        onRefresh={preview.hasQuery ? () => preview.reload() : undefined}
        refreshBusy={preview.loading && preview.hasQuery}
      />

      {!preview.hasQuery && !preview.loading ? (
        <LineFeederIdleCard
          onCollect={() => setModalOpen(true)}
          disabled={preview.loading}
        />
      ) : null}

      {preview.loading ? (
        <LineFeederPreviewProgress
          percent={preview.progressPercent}
          logs={preview.progressLogs}
        />
      ) : null}

      {errorMessage ? (
        <div className="ppc-state ppc-state--error" role="alert">
          {errorMessage}
        </div>
      ) : null}

      {preview.data && preview.query && !preview.loading ? (
        <LineFeederMaterialsPanel data={preview.data} query={preview.query} />
      ) : null}

      <LineFeederCollectModal
        open={modalOpen}
        branch={branch}
        initial={preview.query}
        submitting={preview.loading}
        onClose={() => setModalOpen(false)}
        onSubmit={(selection) => {
          setModalOpen(false);
          void preview.run(selection);
        }}
      />
    </div>
  );
}
