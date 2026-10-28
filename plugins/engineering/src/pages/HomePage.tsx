import { useCallback, useEffect, useRef, useState } from "react";
import { TaskItemsTable } from "@delpi/plugin-ui/index";

import { getEngineeringHome } from "../api/engineeringHomeApi";
import { HomeApiError } from "../api/httpClient";
import {
  buildSectionView,
  CONTINUITY_SECTIONS,
  partialBannerMessage,
  WORK_SECTIONS,
  type HomeSectionSpec,
  type SectionView,
} from "../features/home/homeViewModel";
import type { HomeResponse, HomeSection } from "../types/home";
import {
  ENG_PORTAL_SCOPE,
  EngineeringEmptyState,
  EngineeringLoadingState,
  EngineeringPageHeader,
  EngineeringSectionCard,
  EngineeringStateBanner,
} from "../ui/engineeringUi";

type LoadState =
  | { phase: "loading" }
  | { phase: "error"; error: HomeApiError }
  | { phase: "ready"; home: HomeResponse };

function openItemRoute(route: string | null | undefined) {
  // Navegação pelo host: href oficial devolvido pela engineering-api.
  if (route) window.location.assign(route);
}

function SectionBody({ view }: { view: SectionView }) {
  if (view.kind === "items") {
    return (
      <>
        <TaskItemsTable
          items={view.items}
          onOpen={(item) => openItemRoute(item.route)}
        />
        {view.totalLabel ? (
          <p className="engineering-section-total">{view.totalLabel}</p>
        ) : null}
      </>
    );
  }
  if (view.kind === "empty") {
    return <EngineeringEmptyState message={view.message} />;
  }
  if (view.kind === "forbidden") {
    return (
      <div className="engineering-section-notice" role="status">
        {view.message}
      </div>
    );
  }
  if (view.kind === "not_implemented") {
    return (
      <div className="engineering-section-notice engineering-section-notice--muted" role="status">
        {view.message}
      </div>
    );
  }
  return (
    <EngineeringStateBanner variant="error">{view.message}</EngineeringStateBanner>
  );
}

function HomeSectionCard({
  spec,
  section,
}: {
  spec: HomeSectionSpec;
  section: HomeSection;
}) {
  const view = buildSectionView(section);
  return (
    <EngineeringSectionCard title={spec.title} subtitle={spec.subtitle}>
      <SectionBody view={view} />
    </EngineeringSectionCard>
  );
}

export function HomePage() {
  const [state, setState] = useState<LoadState>({ phase: "loading" });
  const [refreshing, setRefreshing] = useState(false);
  const requestSeq = useRef(0);

  const load = useCallback(async (isRefresh: boolean) => {
    const seq = ++requestSeq.current;
    const controller = new AbortController();
    if (!isRefresh) setState({ phase: "loading" });
    setRefreshing(true);
    try {
      const home = await getEngineeringHome(controller.signal);
      if (seq !== requestSeq.current) return;
      setState({ phase: "ready", home });
    } catch (error) {
      if (seq !== requestSeq.current) return;
      setState({
        phase: "error",
        error:
          error instanceof HomeApiError
            ? error
            : new HomeApiError(
                "network_error",
                "Falha ao carregar a área de trabalho.",
              ),
      });
    } finally {
      if (seq === requestSeq.current) setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    const pending = queueMicrotask(() => void load(false));
    return () => {
      void pending;
      requestSeq.current += 1;
    };
  }, [load]);

  const partial =
    state.phase === "ready" ? partialBannerMessage(state.home.status) : null;

  return (
    <div className={`${ENG_PORTAL_SCOPE} engineering-page`}>
      <EngineeringPageHeader
        title="Portal Engenharia"
        subtitle="Sua área de trabalho — demandas, solicitações e LMPs autorizadas."
        onRefresh={() => void load(true)}
        refreshing={refreshing}
      />

      {state.phase === "loading" ? <EngineeringLoadingState /> : null}

      {state.phase === "error" ? (
        <EngineeringStateBanner variant="error">
          {state.error.message}
        </EngineeringStateBanner>
      ) : null}

      {state.phase === "ready" ? (
        <>
          {partial ? (
            <EngineeringStateBanner variant="default">{partial}</EngineeringStateBanner>
          ) : null}
          <div className="engineering-sections-grid">
            {WORK_SECTIONS.map((spec) => (
              <HomeSectionCard
                key={spec.key}
                spec={spec}
                section={state.home.sections[spec.key]}
              />
            ))}
          </div>
          <div className="engineering-sections-grid engineering-sections-grid--continuity">
            {CONTINUITY_SECTIONS.map((spec) => (
              <HomeSectionCard
                key={spec.key}
                spec={spec}
                section={state.home.sections[spec.key]}
              />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
