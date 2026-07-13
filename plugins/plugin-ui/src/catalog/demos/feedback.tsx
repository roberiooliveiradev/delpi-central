import { Activity, Info } from "lucide-react";
import { useState } from "react";

import { PUC_DASHBOARD_ROOT, PUC_PREFIX } from "../../app/bemPrefix";
import {
  ConfirmModalPanel,
  confirmModalBemClasses,
  DrawerShell,
  drawerShellBemClasses,
  EmptyState,
  emptyStatePanelBemClasses,
  InfoStatePanel,
  infoStateBemClasses,
  LoadingActivityCard,
  loadingActivityBemClasses,
  LoadingState,
  loadingStatePanelBemClasses,
  ModalShell,
  modalShellBemClasses,
  StateBanner,
  stateBannerBemClasses,
  StateBoxPanel,
  stateBoxBemClasses,
  StatusBadge,
  statusBadgeBemClasses,
} from "../../components/feedback";
import type { CatalogEntry } from "../types";

const emptyCn = emptyStatePanelBemClasses(PUC_PREFIX);
const loadingCn = loadingStatePanelBemClasses(PUC_PREFIX);
const bannerCn = stateBannerBemClasses(PUC_PREFIX);
const badgeCn = statusBadgeBemClasses(PUC_PREFIX);
const modalCn = modalShellBemClasses(PUC_PREFIX);
const confirmCn = confirmModalBemClasses(PUC_PREFIX);
const drawerCn = drawerShellBemClasses(PUC_PREFIX);
const loadingActivityCn = loadingActivityBemClasses(PUC_PREFIX);
const stateBoxCn = stateBoxBemClasses(PUC_PREFIX);
const infoStateCn = infoStateBemClasses(PUC_PREFIX);

export const feedbackCatalogEntries: CatalogEntry[] = [
  {
    id: "feedback.EmptyState",
    family: "feedback",
    exportName: "EmptyState",
    title: "EmptyState",
    description: "Estado vazio com título e mensagem.",
    docAnchor: "emptystate",
    propsSummary: ["title", "message", "classNames"],
    demos: [
      {
        id: "default",
        label: "Com título",
        render: () => (
          <EmptyState
            title="Sem dados"
            message="Nenhum registro encontrado para o filtro."
            classNames={emptyCn}
            defaultMessage="Sem itens."
          />
        ),
      },
    ],
  },
  {
    id: "feedback.LoadingState",
    family: "feedback",
    exportName: "LoadingState",
    title: "LoadingState",
    description: "Estado de carregamento.",
    docAnchor: "loadingstate",
    propsSummary: ["message", "classNames"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <LoadingState
            message="Carregando indicadores…"
            classNames={loadingCn}
            defaultMessage="Carregando…"
          />
        ),
      },
    ],
  },
  {
    id: "feedback.StateBanner",
    family: "feedback",
    exportName: "StateBanner",
    title: "StateBanner",
    description: "Banner de status (default / error / success).",
    docAnchor: "statebanner",
    propsSummary: ["variant", "children"],
    demos: [
      {
        id: "variants",
        label: "Variantes",
        render: () => (
          <div className="puc-stack">
            <StateBanner classNames={bannerCn}>Informação neutra.</StateBanner>
            <StateBanner classNames={bannerCn} variant="success">
              Operação concluída.
            </StateBanner>
            <StateBanner classNames={bannerCn} variant="error">
              Falha ao carregar.
            </StateBanner>
          </div>
        ),
      },
    ],
  },
  {
    id: "feedback.StatusBadge",
    family: "feedback",
    exportName: "StatusBadge",
    title: "StatusBadge",
    description: "Badge de status semântico.",
    docAnchor: "statusbadge",
    propsSummary: ["label", "variant"],
    demos: [
      {
        id: "variants",
        label: "Variantes",
        render: () => (
          <div className="puc-badge-row">
            <StatusBadge label="Neutro" classNames={badgeCn} />
            <StatusBadge label="Info" variant="info" classNames={badgeCn} />
            <StatusBadge label="Sucesso" variant="success" classNames={badgeCn} />
            <StatusBadge label="Atenção" variant="warning" classNames={badgeCn} />
            <StatusBadge label="Risco" variant="danger" classNames={badgeCn} />
          </div>
        ),
      },
    ],
  },
  {
    id: "feedback.ModalShell",
    family: "feedback",
    exportName: "ModalShell",
    title: "ModalShell",
    description: "Shell de modal com portal (escopo do MFE).",
    docAnchor: "modalshell",
    propsSummary: ["open", "title", "onClose", "portalScopeClassName"],
    demos: [
      {
        id: "default",
        label: "Abrir",
        render: () => <ModalShellDemo />,
      },
    ],
  },
  {
    id: "feedback.ConfirmModalPanel",
    family: "feedback",
    exportName: "ConfirmModalPanel",
    title: "ConfirmModalPanel",
    description: "Painel de confirmação (mensagem + ações).",
    docAnchor: "confirmmodalpanel",
    propsSummary: ["message", "onConfirm", "onCancel", "variant"],
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <div className="puc-card puc-confirm-preview">
            <ConfirmModalPanel
              message="Deseja remover este registro?"
              onConfirm={() => undefined}
              onCancel={() => undefined}
              classNames={confirmCn}
            />
          </div>
        ),
      },
    ],
  },
  {
    id: "feedback.LoadingActivityCard",
    family: "feedback",
    exportName: "LoadingActivityCard",
    title: "LoadingActivityCard",
    demos: [
      {
        id: "default",
        label: "Com progresso",
        render: () => (
          <LoadingActivityCard
            title="Carregando dashboard…"
            description="Consultando APIs operacionais."
            progressPercent={42}
            classNames={loadingActivityCn}
            labels={{
              progressRemaining: (n) => `Faltam ${n}%`,
              progressAriaDeterminate: (n) => `Progresso, faltam ${n}%`,
              progressAriaIndeterminate: "Carregando",
            }}
          />
        ),
      },
    ],
  },
  {
    id: "feedback.DrawerShell",
    family: "feedback",
    exportName: "DrawerShell",
    title: "DrawerShell",
    demos: [
      {
        id: "default",
        label: "Abrir",
        render: () => <DrawerShellDemo />,
      },
    ],
  },
  {
    id: "feedback.StateBoxPanel",
    family: "feedback",
    exportName: "StateBoxPanel",
    title: "StateBoxPanel",
    demos: [
      {
        id: "empty",
        label: "Empty",
        render: () => (
          <StateBoxPanel
            variant="empty"
            title="Sem resultados"
            message="Ajuste os filtros e tente novamente."
            icon={<Info size={22} />}
            classNames={stateBoxCn}
          />
        ),
      },
    ],
  },
  {
    id: "feedback.InfoStatePanel",
    family: "feedback",
    exportName: "InfoStatePanel",
    title: "InfoStatePanel",
    demos: [
      {
        id: "default",
        label: "Padrão",
        render: () => (
          <InfoStatePanel
            title="Nenhuma seleção"
            description="Escolha um item na lista para ver detalhes."
            actionLabel="Limpar filtros"
            onAction={() => undefined}
            icon={<Activity size={22} />}
            classNames={infoStateCn}
          />
        ),
      },
    ],
  },
];

function ModalShellDemo() {
  const [open, setOpen] = useState(false);

  return (
    <div className="puc-stack">
      <button type="button" className="puc-primary-btn" onClick={() => setOpen(true)}>
        Abrir modal
      </button>
      <ModalShell
        open={open}
        title="Exemplo de modal"
        description="Conteúdo ilustrativo do catálogo."
        onClose={() => setOpen(false)}
        classNames={modalCn}
        portalScopeClassName={PUC_DASHBOARD_ROOT}
      >
        <p className="puc-muted">Corpo do diálogo.</p>
      </ModalShell>
    </div>
  );
}

function DrawerShellDemo() {
  const [open, setOpen] = useState(false);

  return (
    <div className="puc-stack">
      <button type="button" className="puc-primary-btn" onClick={() => setOpen(true)}>
        Abrir drawer
      </button>
      <DrawerShell
        open={open}
        title="Painel lateral"
        description="Exemplo de drawer."
        onClose={() => setOpen(false)}
        classNames={drawerCn}
      >
        <p className="puc-muted">Conteúdo do drawer.</p>
      </DrawerShell>
    </div>
  );
}
