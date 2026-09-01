import { SI_HELP } from "../../content/helpTooltips";
import "./GoalScopeBadges.css";

type GoalScopeBadgesProps = {
  /** Escopo selecionado no formulário: vazio = Consolidado. */
  selectedScope?: string;
  className?: string;
};

/** Badges C / 01 / 02 — preview do escopo da meta (admin). */
export function GoalScopeBadges({
  selectedScope = "",
  className,
}: GoalScopeBadgesProps) {
  const consolidated = selectedScope === "" || selectedScope === "consolidated";
  const branch01 = selectedScope === "01";
  const branch02 = selectedScope === "02";

  return (
    <span
      className={["si-goal-scope-badges", className].filter(Boolean).join(" ")}
      aria-label="Escopo da meta"
    >
      <span
        className={consolidated ? "is-on" : "is-off"}
        title={SI_HELP.badges.goalScopeConsolidated}
      >
        C
      </span>
      <span className={branch01 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope01}>
        01
      </span>
      <span className={branch02 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope02}>
        02
      </span>
    </span>
  );
}

/** Cobertura de metas ativas por escopo (validação estrutural). */
export function GoalScopeCoverageBadges({
  consolidated,
  branch01,
  branch02,
}: {
  consolidated: boolean;
  branch01: boolean;
  branch02: boolean;
}) {
  return (
    <span className="si-goal-scope-badges">
      <span
        className={consolidated ? "is-on" : "is-off"}
        title={SI_HELP.badges.goalScopeConsolidated}
      >
        C
      </span>
      <span className={branch01 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope01}>
        01
      </span>
      <span className={branch02 ? "is-on" : "is-off"} title={SI_HELP.badges.goalScope02}>
        02
      </span>
    </span>
  );
}
