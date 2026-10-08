import { createDashboardUserManual } from "@delpi/plugin-ui/index";
import { ArrowLeft } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { HttpRequestError } from "../api/httpClient";
import {
  fetchProductGuideHelp,
  type ProductGuideHelpTopic,
} from "../api/tvDashboardApi";
import {
  HELP_AUTH_NOTE,
  HELP_CONFIG_NOTE,
  HELP_UNAVAILABLE_NOTE,
  indexTopicsById,
  mergeManualWithGuides,
  relatedSectionsFor,
} from "../content/helpGuideContent";
import { USER_MANUAL_CONTENT } from "../content/userManualContent";
import { TvLibraryPageLayout } from "../layout/TvLibraryPageLayout";
import { TvPageHeader, TvSectionCard } from "../layout/tvUi";

const Manual = createDashboardUserManual({ prefix: "td" });

type Props = {
  onNavigate: (path: string) => void;
  onBack: () => void;
};

type GuideState =
  | { status: "loading"; topicsById: Map<string, ProductGuideHelpTopic> | null; note: string | null }
  | { status: "ready"; topicsById: Map<string, ProductGuideHelpTopic>; note: string | null }
  | { status: "failed"; topicsById: null; note: string };

function scrollToSection(id: string) {
  document
    .getElementById(`manual-${id}`)
    ?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function noteForFailure(err: unknown): string {
  if (err instanceof HttpRequestError) {
    if (err.status === 401 || err.status === 403) return HELP_AUTH_NOTE;
    if (err.status === 404 || err.status === 422) return HELP_CONFIG_NOTE;
  }
  return HELP_UNAVAILABLE_NOTE;
}

export function HelpPage({ onNavigate, onBack }: Props) {
  const manual = USER_MANUAL_CONTENT;
  const [guide, setGuide] = useState<GuideState>({
    status: "loading",
    topicsById: null,
    note: null,
  });

  const load = useCallback((signal?: AbortSignal) => {
    fetchProductGuideHelp({ signal })
      .then((payload) => {
        if (signal?.aborted) return;
        const topics = payload.topics ?? [];
        if (!topics.length) {
          setGuide({ status: "failed", topicsById: null, note: HELP_CONFIG_NOTE });
          return;
        }
        setGuide({ status: "ready", topicsById: indexTopicsById(topics), note: null });
      })
      .catch((err) => {
        if (signal?.aborted) return;
        setGuide({ status: "failed", topicsById: null, note: noteForFailure(err) });
      });
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    load(controller.signal);
    return () => controller.abort();
  }, [load]);

  function retry() {
    setGuide({ status: "loading", topicsById: null, note: null });
    load();
  }

  const loading = guide.status === "loading";
  const sections = useMemo(
    () =>
      mergeManualWithGuides(manual.sections, guide.topicsById, {
        loading,
        unavailableNote: guide.note ?? undefined,
      }),
    [guide.note, guide.topicsById, loading, manual.sections],
  );

  const relatedBySection = useMemo(() => {
    const map = new Map<string, readonly { sectionId: string; topicId: string }[]>();
    for (const section of manual.sections) {
      map.set(section.id, relatedSectionsFor(section.id, guide.topicsById));
    }
    return map;
  }, [guide.topicsById, manual.sections]);

  return (
    <TvLibraryPageLayout
      header={
        <TvPageHeader
          eyebrow="Operações · Displays"
          nav={
            <button type="button" className="td-page-back" onClick={onBack}>
              <ArrowLeft size={16} aria-hidden="true" />
              Voltar
            </button>
          }
          title="Ajuda"
          subtitle={manual.scopeNote}
        />
      }
    >
      <Manual.Frame>
        {guide.status === "failed" && guide.note === HELP_UNAVAILABLE_NOTE ? (
          <p className={Manual.classNames.scope} role="status">
            {guide.note}{" "}
            <button type="button" className="td-page-back" onClick={retry}>
              Tentar novamente
            </button>
          </p>
        ) : null}
        <Manual.Layout
          title={manual.tocTitle}
          aria-label={manual.tocAriaLabel}
          items={sections.map((section) => ({
            id: section.id,
            label: section.title,
            onSelect: () => scrollToSection(section.id),
          }))}
        >
          {sections.map((section) => {
            const related = relatedBySection.get(section.id) ?? [];
            return (
              <Manual.Section key={section.id} id={`manual-${section.id}`}>
                <TvSectionCard title={section.title}>
                  {section.intro ? (
                    <p className={Manual.classNames.intro}>{section.intro}</p>
                  ) : null}
                  {section.bullets && section.bullets.length > 0 ? (
                    <ul className={Manual.classNames.list}>
                      {section.bullets.map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  ) : null}
                  {section.links && section.links.length > 0 ? (
                    <Manual.GuideTable
                      rows={section.links.map((link) => ({
                        want: link.want,
                        where: link.path ? (
                          <button
                            type="button"
                            className={Manual.classNames.where}
                            onClick={() => onNavigate(link.path!)}
                          >
                            {link.where}
                          </button>
                        ) : (
                          link.where
                        ),
                        how: link.how,
                      }))}
                    />
                  ) : null}
                  {related.length > 0 ? (
                    <p className={Manual.classNames.intro}>
                      Veja também:{" "}
                      {related.map((item, index) => (
                        <span key={item.topicId}>
                          {index > 0 ? " · " : ""}
                          <button
                            type="button"
                            className={Manual.classNames.where}
                            onClick={() => scrollToSection(item.sectionId)}
                          >
                            {manual.sections.find((s) => s.id === item.sectionId)?.title ??
                              item.topicId}
                          </button>
                        </span>
                      ))}
                    </p>
                  ) : null}
                </TvSectionCard>
              </Manual.Section>
            );
          })}
        </Manual.Layout>
      </Manual.Frame>
    </TvLibraryPageLayout>
  );
}
