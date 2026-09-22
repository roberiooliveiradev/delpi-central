import { useMemo, useState, type ReactNode } from "react";
import { Copy, MessagesSquare, MoreHorizontal, Trash2 } from "lucide-react";
import type { PageHeroHighlight } from "@delpi/plugin-ui/index";

import { TmPageHero, TmPagePath, TmStatusBadge, TmUnderlineNav } from "../../components/tmChromeUi";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import type { Processo, ProcessoInstancia, Revisao } from "../../data/api/transformometroApi";
import { computeProcessoListCompletion } from "../../utils/processoCompletion";
import { revisaoDisplayLabel } from "../../utils/revisaoLabels";
import {
  buildInstanciaSectionHref,
  buildProcessoSectionHref,
  buildRevisaoSectionHref,
  instanciaNavLabel,
  INSTANCIA_WORKSPACE_SECTIONS,
  PROCESSO_WORKSPACE_SECTIONS,
  revisaoSectionsForCenario,
  type InstanciaWorkspaceSectionId,
  type ProcessoWorkspaceSectionId,
  type RevisaoWorkspaceSectionId,
} from "./processWorkspaceNav";
import { buildInstanciaPath } from "../../utils/routeParser";

type View = "processo" | "instancia" | "revisao";

type Props = {
  view: View;
  processo: Processo | null;
  instancias: ProcessoInstancia[];
  revisoes: Revisao[];
  processoId: string;
  instanciaId?: string;
  revisaoId?: string;
  activeProcessoSection: ProcessoWorkspaceSectionId;
  activeInstanciaSection: InstanciaWorkspaceSectionId;
  activeRevisaoSection: RevisaoWorkspaceSectionId;
  onNavigate: (href: string) => void;
  onBack: () => void;
  onOpenRoom: () => void;
  openingRoom: boolean;
  roomError: string | null;
  treePartialError: string | null;
  onDuplicate: () => void;
  onDelete: () => void;
};

function processHighlights(
  processo: Processo,
  instancias: ProcessoInstancia[],
  revisoes: Revisao[],
): PageHeroHighlight[] {
  const completion = computeProcessoListCompletion(processo);
  const diagramNodes = processo.setup_stats?.diagram_node_count ?? 0;
  return [
    {
      id: "preenchimento",
      label: "Preenchimento",
      value: `${completion.percent}%`,
      description: `${completion.done} de ${completion.total}`,
    },
    {
      id: "melhorias",
      label: "Melhorias",
      value: String(instancias.length),
    },
    {
      id: "revisoes",
      label: "Revisões",
      value: String(revisoes.length),
    },
    {
      id: "diagrama",
      label: "Diagrama",
      value: diagramNodes > 0 ? `${diagramNodes} nós` : "—",
    },
  ];
}

export function ProcessWorkspaceChrome({
  view,
  processo,
  instancias,
  revisoes,
  processoId,
  instanciaId,
  revisaoId,
  activeProcessoSection,
  activeInstanciaSection,
  activeRevisaoSection,
  onNavigate,
  onBack,
  onOpenRoom,
  openingRoom,
  roomError,
  treePartialError,
  onDuplicate,
  onDelete,
}: Props) {
  const [moreOpen, setMoreOpen] = useState(false);
  const processesHref = TRANSFORMOMETRO_ROUTES.processes;
  const processoHref = `${TRANSFORMOMETRO_ROUTES.processes}/${processoId}`;

  const activeInstancia = useMemo(
    () => instancias.find((row) => row.instancia_id === instanciaId) ?? null,
    [instanciaId, instancias],
  );
  const activeRevisao = useMemo(
    () => revisoes.find((row) => row.revisao_id === revisaoId) ?? null,
    [revisaoId, revisoes],
  );

  const currentLabel =
    view === "revisao" && activeRevisao
      ? revisaoDisplayLabel(activeRevisao)
      : view === "instancia" && activeInstancia
        ? instanciaNavLabel(activeInstancia)
        : processo?.nome_processo ?? "Processo";

  const pathItems = useMemo(() => {
    const items: Array<{ id: string; label: string; href: string }> = [];
    if (view === "instancia" || view === "revisao") {
      items.push({
        id: "processo",
        label: processo?.codigo_processo ?? "Processo",
        href: processoHref,
      });
    }
    if (view === "revisao" && activeInstancia && instanciaId) {
      items.push({
        id: "instancia",
        label: instanciaNavLabel(activeInstancia),
        href: buildInstanciaPath(processoId, instanciaId),
      });
    }
    return items;
  }, [activeInstancia, instanciaId, processo?.codigo_processo, processoHref, view]);

  const nav: ReactNode =
    view === "processo" ? (
      <TmUnderlineNav
        mode="navigation"
        layout="wrap"
        density="compact"
        aria-label="Seções do processo"
        activeId={activeProcessoSection}
        items={PROCESSO_WORKSPACE_SECTIONS.map((section) => ({
          id: section.id,
          label: section.label,
          onSelect: () => onNavigate(buildProcessoSectionHref(processoId, section.id)),
        }))}
      />
    ) : view === "instancia" && instanciaId ? (
      <TmUnderlineNav
        mode="navigation"
        layout="wrap"
        density="compact"
        aria-label="Seções da melhoria"
        activeId={activeInstanciaSection}
        items={INSTANCIA_WORKSPACE_SECTIONS.map((section) => ({
          id: section.id,
          label: section.label,
          onSelect: () =>
            onNavigate(buildInstanciaSectionHref(processoId, instanciaId, section.id)),
        }))}
      />
    ) : view === "revisao" && instanciaId && revisaoId ? (
      <TmUnderlineNav
        mode="navigation"
        layout="wrap"
        density="compact"
        aria-label="Seções da revisão"
        activeId={activeRevisaoSection}
        items={revisaoSectionsForCenario(activeRevisao?.cenario_tipo).map((section) => ({
          id: section.id,
          label: section.label,
          onSelect: () =>
            onNavigate(
              buildRevisaoSectionHref(
                processoId,
                instanciaId,
                revisaoId,
                section.id,
                activeRevisao?.cenario_tipo,
              ),
            ),
        }))}
      />
    ) : null;

  const highlights =
    view === "processo" && processo
      ? processHighlights(processo, instancias, revisoes)
      : undefined;

  return (
    <div className="tm-processo-workspace-chrome">
      <TmPagePath
        back={{
          label: "Meus processos",
          href: processesHref,
          onNavigate: (event) => {
            event.preventDefault();
            onBack();
          },
        }}
        items={pathItems.map((item) => ({
          ...item,
          onNavigate: (event) => {
            event.preventDefault();
            onNavigate(item.href);
          },
        }))}
        current={currentLabel}
      />

      <TmPageHero
        density="compact"
        aria-label={view === "processo" ? "Processo" : view === "instancia" ? "Melhoria" : "Revisão"}
        eyebrow={view === "processo" ? "Processo" : view === "instancia" ? "Melhoria" : "Revisão"}
        title={
          view === "processo"
            ? processo?.nome_processo ?? "Processo"
            : currentLabel
        }
        description={
          view === "processo" && processo
            ? [
                processo.codigo_processo,
                processo.familia_processo ? `família ${processo.familia_processo}` : null,
              ]
                .filter(Boolean)
                .join(" · ")
            : processo
              ? `${processo.codigo_processo} · ${processo.nome_processo}`
              : undefined
        }
        badge={
          view === "processo" && processo?.status_processo ? (
            <TmStatusBadge label={processo.status_processo} variant="neutral" />
          ) : undefined
        }
        highlights={highlights}
        actions={
          view === "processo" ? (
            <div className="tm-processo-workspace-chrome__actions">
              <button
                type="button"
                className="ds-primary-btn"
                disabled={!processo || openingRoom}
                onClick={onOpenRoom}
              >
                <MessagesSquare size={16} aria-hidden />
                {openingRoom ? "Abrindo sala…" : "Sala de interação"}
              </button>
              <button
                type="button"
                className={DS_GHOST_BTN}
                disabled={!processo}
                onClick={onDuplicate}
              >
                <Copy size={16} aria-hidden />
                Duplicar
              </button>
              <div className="tm-processo-workspace-chrome__more">
                <button
                  type="button"
                  className={DS_GHOST_BTN}
                  aria-expanded={moreOpen}
                  aria-haspopup="menu"
                  disabled={!processo}
                  onClick={() => setMoreOpen((open) => !open)}
                >
                  <MoreHorizontal size={16} aria-hidden />
                  Mais
                </button>
                {moreOpen ? (
                  <div className="tm-processo-workspace-chrome__more-menu" role="menu">
                    <button
                      type="button"
                      role="menuitem"
                      className={dsGhostBtn("danger")}
                      onClick={() => {
                        setMoreOpen(false);
                        onDelete();
                      }}
                    >
                      <Trash2 size={16} aria-hidden />
                      Excluir processo
                    </button>
                  </div>
                ) : null}
              </div>
            </div>
          ) : undefined
        }
      />

      {roomError || treePartialError ? (
        <div className="tm-processo-workspace-chrome__notices" role="status">
          {roomError ? <p role="alert">{roomError}</p> : null}
          {treePartialError ? <p>{treePartialError}</p> : null}
        </div>
      ) : null}

      {nav}
    </div>
  );
}
