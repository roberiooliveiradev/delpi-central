import { Check, History, PencilLine, Plus, Rocket, Trash2 } from "lucide-react";

import type { KaizenRevision, KaizenVersionStatus } from "../../types/kaizen";
import { HintAction, TitleWithHelp } from "../ui";
import { KAIZEN_HELP_TOOLTIPS } from "../../content/helpTooltips";

const STATUS_LABELS: Record<KaizenVersionStatus, string> = {
  em_andamento: "Rascunho",
  implantado: "Ativa",
  descontinuado: "Descontinuada",
  cancelado: "Cancelada",
  substituido: "Substituída",
};

function versionStatus(revision: KaizenRevision): KaizenVersionStatus {
  return (revision.version_status as KaizenVersionStatus) ?? "implantado";
}

export type SelectionMode = "active" | "draft" | "readonly";

type Props = {
  revisions: KaizenRevision[];
  selectedRevision: number;
  /** Exibe a lista de versões (pills). Com versão única, só o botão "Nova versão" aparece. */
  showList: boolean;
  onSelect: (revisionNumber: number) => void;
  onCreateVersion: () => void;
  creating: boolean;
  mode: SelectionMode;
  onImplement: () => void;
  implementing: boolean;
  onDelete: () => void;
  deleting: boolean;
};

export function KaizenVersionSwitcher({
  revisions,
  selectedRevision,
  showList,
  onSelect,
  onCreateVersion,
  creating,
  mode,
  onImplement,
  implementing,
  onDelete,
  deleting,
}: Props) {
  const ordered = [...revisions].sort((a, b) => a.revision_number - b.revision_number);
  const selected = ordered.find((r) => r.revision_number === selectedRevision);

  return (
    <section className="kz-card kz-versions">
      <header className="kz-versions__header">
        <div className="kz-versions__heading">
          <h2 className="kz-versions__title">
            <TitleWithHelp
              title="Versões do kaizen"
              hint={KAIZEN_HELP_TOOLTIPS.sections.improvements}
            />
          </h2>
          <span className="kz-versions__count">
            {ordered.length} {ordered.length === 1 ? "versão" : "versões"}
          </span>
        </div>
        <button
          type="button"
          className="kz-primary-btn"
          onClick={onCreateVersion}
          disabled={creating}
        >
          <Plus size={14} aria-hidden="true" />
          {creating ? "Criando cópia…" : "Nova versão"}
        </button>
      </header>

      {showList ? (
      <div className="kz-versions__pills" role="tablist" aria-label="Selecionar versão">
        {ordered.map((revision) => {
          const status = versionStatus(revision);
          const isSelected = revision.revision_number === selectedRevision;
          const classes = [
            "kz-version-pill",
            `kz-version-pill--${status}`,
            isSelected ? "kz-version-pill--selected" : "",
          ]
            .filter(Boolean)
            .join(" ");
          return (
            <button
              key={revision.id}
              type="button"
              role="tab"
              aria-selected={isSelected}
              className={classes}
              onClick={() => onSelect(revision.revision_number)}
            >
              <span className="kz-version-pill__num">v{revision.revision_number}</span>
              <span className="kz-version-pill__status">
                {status === "implantado" ? <Check size={12} aria-hidden="true" /> : null}
                {status === "em_andamento" ? <PencilLine size={12} aria-hidden="true" /> : null}
                {status === "substituido" ? <History size={12} aria-hidden="true" /> : null}
                {STATUS_LABELS[status]}
              </span>
            </button>
          );
        })}
      </div>
      ) : null}

      {showList && mode === "active" ? (
        <p className="kz-versions__banner kz-versions__banner--active">
          <Check size={14} aria-hidden="true" />
          Você está na <strong>versão ativa</strong> (v{selected?.revision_number}) — é ela que
          contabiliza os ganhos. Editar as seções abaixo faz uma <strong>correção</strong> nesta
          versão (não cria uma nova).
        </p>
      ) : null}

      {mode === "draft" ? (
        <div className="kz-versions__banner kz-versions__banner--draft">
          <div className="kz-versions__banner-text">
            <PencilLine size={14} aria-hidden="true" />
            Editando o <strong>rascunho v{selected?.revision_number}</strong> (ainda não ativo). A
            versão ativa segue contabilizando. Ajuste as seções abaixo e, ao final,{" "}
            <strong>salve e torne esta versão ativa</strong>.
          </div>
          <div className="kz-versions__implement">
            <HintAction
              hint={KAIZEN_HELP_TOOLTIPS.improvements.implement}
              ariaLabel="Ajuda: tornar versão ativa"
            >
              <button
                type="button"
                className="kz-primary-btn"
                onClick={onImplement}
                disabled={implementing || deleting}
              >
                <Rocket size={14} aria-hidden="true" />
                {implementing ? "Ativando…" : "Salvar e tornar ativa"}
              </button>
            </HintAction>
            <button
              type="button"
              className="kz-danger-btn"
              onClick={onDelete}
              disabled={implementing || deleting}
            >
              <Trash2 size={14} aria-hidden="true" />
              {deleting ? "Excluindo…" : "Excluir rascunho"}
            </button>
          </div>
        </div>
      ) : null}

      {mode === "readonly" ? (
        <div className="kz-versions__banner kz-versions__banner--history">
          <span className="kz-versions__banner-text">
            <History size={14} aria-hidden="true" />
            Versão histórica v{selected?.revision_number} (
            {STATUS_LABELS[versionStatus(selected!)]}) — somente leitura. Para mudanças, crie uma
            nova versão.
          </span>
          <button
            type="button"
            className="kz-danger-btn"
            onClick={onDelete}
            disabled={deleting}
          >
            <Trash2 size={14} aria-hidden="true" />
            {deleting ? "Excluindo…" : "Excluir versão"}
          </button>
        </div>
      ) : null}
    </section>
  );
}
