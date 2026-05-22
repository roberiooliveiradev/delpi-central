import { useMemo, useState } from "react";
import { InfoState } from "./InfoState";
import { LoadingActivityInline } from "./LoadingActivityInline";
import { useCatalogStructureValidation } from "../../state/hooks/useCatalogStructureValidation";
import type { ValidationSeverity } from "../../domain/catalogStructureValidation";
import {
  getAggregationModeLabel,
  getScopeTypeLabel,
} from "../presentation/labels";
import "./CatalogStructureValidationWorkspace.css";

type CatalogStructureValidationWorkspaceProps = {
  getAccessToken?: () => string | undefined;
};

const SEVERITY_LABEL: Record<ValidationSeverity, string> = {
  ok: "OK",
  info: "Info",
  warning: "Atenção",
  error: "Erro",
};

function GoalScopeBadges({
  consolidated,
  branch01,
  branch02,
}: {
  consolidated: boolean;
  branch01: boolean;
  branch02: boolean;
}) {
  return (
    <span className="si-catalog-validation__scopes">
      <span className={consolidated ? "is-on" : "is-off"} title="Meta consolidada">
        C
      </span>
      <span className={branch01 ? "is-on" : "is-off"} title="Meta filial 01">
        01
      </span>
      <span className={branch02 ? "is-on" : "is-off"} title="Meta filial 02">
        02
      </span>
    </span>
  );
}

export function CatalogStructureValidationWorkspace({
  getAccessToken,
}: CatalogStructureValidationWorkspaceProps) {
  const validation = useCatalogStructureValidation({ getAccessToken });
  const [onlyIssues, setOnlyIssues] = useState(true);
  const [departmentFilter, setDepartmentFilter] = useState("");

  const departmentOptions = useMemo(() => {
    const seen = new Map<string, string>();
    for (const row of validation.rows) {
      if (!seen.has(row.departmentId)) {
        seen.set(row.departmentId, row.departmentShortName || row.departmentName);
      }
    }
    return [...seen.entries()].map(([id, label]) => ({ id, label }));
  }, [validation.rows]);

  const filteredRows = useMemo(() => {
    return validation.rows.filter((row) => {
      if (departmentFilter && row.departmentId !== departmentFilter) return false;
      if (onlyIssues && row.worstSeverity === "ok") return false;
      return true;
    });
  }, [validation.rows, departmentFilter, onlyIssues]);

  const yearOptions = useMemo(() => {
    const current = new Date().getFullYear();
    return [current + 1, current, current - 1];
  }, []);

  if (validation.loading && validation.rows.length === 0) {
    return (
      <LoadingActivityInline
        title="Carregando catálogo"
        description="Departamentos, indicadores e metas do ano selecionado."
        variant="panel"
        tone="info"
      />
    );
  }

  if (validation.error) {
    return (
      <InfoState
        title="Validação indisponível"
        description={validation.error}
        actionLabel="Tentar novamente"
        onAction={() => void validation.reload()}
      />
    );
  }

  return (
    <div className="si-catalog-validation">
      <div className="si-catalog-validation__toolbar">
        <p className="si-catalog-validation__hint">
          Cruza agregação do departamento, escopo do indicador e cobertura de metas ativas
          no ano. Use para detectar inconsistências antes de fechar o ciclo ou publicar o painel.
        </p>
        <button
          type="button"
          className="si-btn si-btn--secondary"
          onClick={() => void validation.reload()}
        >
          Atualizar
        </button>
      </div>

      <div className="si-catalog-validation__summary">
        <article className="si-catalog-validation__stat">
          <span>Indicadores</span>
          <strong>{validation.summary.totalRows}</strong>
        </article>
        <article className="si-catalog-validation__stat is-error">
          <span>Erros</span>
          <strong>{validation.summary.errors}</strong>
        </article>
        <article className="si-catalog-validation__stat is-warning">
          <span>Atenções</span>
          <strong>{validation.summary.warnings}</strong>
        </article>
        <article className="si-catalog-validation__stat is-info">
          <span>Informativos</span>
          <strong>{validation.summary.infos}</strong>
        </article>
        <article className="si-catalog-validation__stat is-ok">
          <span>Sem apontamento</span>
          <strong>{validation.summary.ok}</strong>
        </article>
      </div>

      {validation.departmentWeightIssues.length > 0 ? (
        <div className="si-catalog-validation__weight-banner" role="status">
          <strong>Pesos dos indicadores por departamento</strong>
          <ul>
            {validation.departmentWeightIssues.map((item) => (
              <li key={item.departmentId}>
                {item.shortName || item.departmentName}: soma{" "}
                <strong>{item.totalWeight}%</strong> (esperado 100%)
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="si-catalog-validation__filters">
        <label className="si-admin-form-field">
          <span>Ano das metas</span>
          <select
            value={validation.goalYear}
            onChange={(event) => validation.setGoalYear(Number(event.target.value))}
          >
            {yearOptions.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>

        <label className="si-admin-form-field">
          <span>Departamento</span>
          <select
            value={departmentFilter}
            onChange={(event) => setDepartmentFilter(event.target.value)}
          >
            <option value="">Todos</option>
            {departmentOptions.map((option) => (
              <option key={option.id} value={option.id}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label className="si-catalog-validation__checkbox">
          <input
            type="checkbox"
            checked={onlyIssues}
            onChange={(event) => setOnlyIssues(event.target.checked)}
          />
          Mostrar só linhas com apontamento
        </label>
      </div>

      {filteredRows.length === 0 ? (
        <InfoState
          title="Nenhuma linha neste filtro"
          description={
            onlyIssues
              ? "Não há inconsistências para o ano e filtros atuais."
              : "Não há registros para exibir."
          }
        />
      ) : (
        <div className="si-catalog-validation__table">
          <div className="si-catalog-validation__table-head">
            <span>Departamento</span>
            <span>Agregação</span>
            <span>Indicador</span>
            <span>Escopo</span>
            <span>Metas</span>
            <span>Status</span>
            <span>Validação</span>
          </div>

          {filteredRows.map((row) => {
            const rowKey =
              row.indicatorId === "—"
                ? `dept-${row.departmentId}`
                : `${row.departmentId}-${row.indicatorId}`;

            return (
              <div
                key={rowKey}
                className={`si-catalog-validation__table-row severity-${row.worstSeverity}`}
              >
                <div>
                  <strong>{row.departmentShortName || row.departmentName}</strong>
                  {!row.departmentActive ? (
                    <small className="is-muted">Inativo</small>
                  ) : null}
                </div>

                <div>
                  <strong>{getAggregationModeLabel(row.departmentAggregation)}</strong>
                  <small>{row.departmentWeightPct}% no IGD</small>
                </div>

                <div>
                  <strong>{row.indicatorName}</strong>
                  {row.indicatorId !== "—" ? (
                    <small>
                      {row.indicatorId}
                      {!row.indicatorActive ? " · inativo" : ` · ${row.indicatorWeightPct}%`}
                    </small>
                  ) : null}
                </div>

                <div>
                  {row.indicatorId === "—" ? (
                    <span className="is-muted">—</span>
                  ) : (
                    <strong>{getScopeTypeLabel(row.scopeType)}</strong>
                  )}
                </div>

                <div>
                  <GoalScopeBadges
                    consolidated={row.goalCoverage.consolidated}
                    branch01={row.goalCoverage.branch01}
                    branch02={row.goalCoverage.branch02}
                  />
                  <small>{row.goalCoverage.activeCount} meta(s) ativa(s)</small>
                </div>

                <div>
                  <span
                    className={`si-catalog-validation__badge severity-${row.worstSeverity}`}
                  >
                    {SEVERITY_LABEL[row.worstSeverity]}
                  </span>
                </div>

                <div className="si-catalog-validation__messages">
                  {row.issues.length === 0 ? (
                    <span className="is-muted">Alinhado ao modelo esperado.</span>
                  ) : (
                    <ul>
                      {row.issues.map((issue) => (
                        <li
                          key={`${rowKey}-${issue.code}`}
                          className={`severity-${issue.severity}`}
                        >
                          {issue.message}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
