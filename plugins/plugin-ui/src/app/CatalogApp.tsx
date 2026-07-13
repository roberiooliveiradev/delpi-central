import { useEffect, useMemo, useState } from "react";

import { PUC_DASHBOARD_ROOT } from "./bemPrefix";
import {
  CATALOG_ENTRIES,
  CATALOG_FAMILY_LABELS,
  CATALOG_LIFECYCLE_LABELS,
  filterCatalogEntries,
  formatCatalogDatePtBr,
  getCatalogEntryById,
  listCatalogFamilies,
} from "../catalog/componentRegistry";
import type { CatalogFamily, CatalogLifecycleFilter } from "../catalog/types";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function CatalogApp(_props: AppProps = {}) {
  const families = useMemo(() => listCatalogFamilies(), []);
  const [query, setQuery] = useState("");
  const [familyFilter, setFamilyFilter] = useState<CatalogFamily | "all">("all");
  const [lifecycleFilter, setLifecycleFilter] = useState<CatalogLifecycleFilter>("all");
  const [selectedId, setSelectedId] = useState(CATALOG_ENTRIES[0]?.id ?? "");
  const [demoId, setDemoId] = useState(CATALOG_ENTRIES[0]?.demos[0]?.id ?? "");

  const filtered = useMemo(
    () => filterCatalogEntries(query, familyFilter, lifecycleFilter),
    [query, familyFilter, lifecycleFilter],
  );

  const selected = getCatalogEntryById(selectedId) ?? filtered[0] ?? CATALOG_ENTRIES[0];

  useEffect(() => {
    if (!selected) return;
    if (!filtered.some((e) => e.id === selected.id) && filtered[0]) {
      setSelectedId(filtered[0].id);
      setDemoId(filtered[0].demos[0]?.id ?? "");
    }
  }, [filtered, selected]);

  useEffect(() => {
    if (!selected) return;
    if (!selected.demos.some((d) => d.id === demoId)) {
      setDemoId(selected.demos[0]?.id ?? "");
    }
  }, [selected, demoId]);

  const activeDemo = selected?.demos.find((d) => d.id === demoId) ?? selected?.demos[0];

  return (
    <div className={`${PUC_DASHBOARD_ROOT} dashboard-page`}>
      <div className="puc-app-shell">
        <header className="puc-app-header">
          <div>
            <p className="puc-eyebrow">@delpi/plugin-ui</p>
            <h1 className="puc-app-title">Catálogo de componentes</h1>
            <p className="puc-app-subtitle">
              Listagem e prévia de todos os componentes visuais. Tema claro/escuro segue
              o portal (`data-theme`). Busque por <code>DataTable</code> para o visual
              estilo dashboards LMPS.
            </p>
          </div>
          <label className="puc-search">
            <span className="puc-search__label">Buscar</span>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nome, família, descrição…"
              className="puc-input"
            />
          </label>
        </header>

        <div className="puc-layout">
          <aside className="puc-sidebar" aria-label="Componentes">
            <div className="puc-family-filters" role="group" aria-label="Famílias">
              <button
                type="button"
                className={
                  familyFilter === "all" && lifecycleFilter === "all"
                    ? "puc-chip puc-chip--active"
                    : "puc-chip"
                }
                onClick={() => {
                  setFamilyFilter("all");
                  setLifecycleFilter("all");
                }}
              >
                Todas
              </button>
              {families.map((family) => (
                <button
                  key={family}
                  type="button"
                  className={
                    familyFilter === family && lifecycleFilter === "all"
                      ? "puc-chip puc-chip--active"
                      : "puc-chip"
                  }
                  onClick={() => {
                    setFamilyFilter(family);
                    setLifecycleFilter("all");
                  }}
                >
                  {CATALOG_FAMILY_LABELS[family]}
                </button>
              ))}
            </div>

            <div className="puc-lifecycle-filters" role="group" aria-label="Recência">
              <button
                type="button"
                className={
                  lifecycleFilter === "new" ? "puc-chip puc-chip--active" : "puc-chip"
                }
                onClick={() => {
                  setLifecycleFilter("new");
                  setFamilyFilter("all");
                }}
              >
                Recentes
              </button>
              <button
                type="button"
                className={
                  lifecycleFilter === "updated" ? "puc-chip puc-chip--active" : "puc-chip"
                }
                onClick={() => {
                  setLifecycleFilter("updated");
                  setFamilyFilter("all");
                }}
              >
                Atualizados
              </button>
            </div>

            <ul className="puc-entry-list">
              {filtered.map((entry) => (
                <li key={entry.id}>
                  <button
                    type="button"
                    className={
                      selected?.id === entry.id
                        ? "puc-entry-btn puc-entry-btn--active"
                        : "puc-entry-btn"
                    }
                    onClick={() => {
                      setSelectedId(entry.id);
                      setDemoId(entry.demos[0]?.id ?? "");
                    }}
                  >
                    <span className="puc-entry-btn__row">
                      <span className="puc-entry-btn__name">{entry.title}</span>
                      {entry.lifecycle !== "stable" ? (
                        <span
                          className={`puc-lifecycle-badge puc-lifecycle-badge--${entry.lifecycle}`}
                        >
                          {CATALOG_LIFECYCLE_LABELS[entry.lifecycle]}
                        </span>
                      ) : null}
                    </span>
                    <span className="puc-entry-btn__family">
                      {CATALOG_FAMILY_LABELS[entry.family]}
                    </span>
                  </button>
                </li>
              ))}
              {filtered.length === 0 ? (
                <li className="puc-empty-list">Nenhum componente encontrado.</li>
              ) : null}
            </ul>
          </aside>

          <main className="puc-main">
            {selected ? (
              <>
                <div className="puc-meta">
                  <div>
                    <p className="puc-meta__family">
                      {CATALOG_FAMILY_LABELS[selected.family]}
                      {selected.lifecycle !== "stable" ? (
                        <>
                          {" · "}
                          <span
                            className={`puc-lifecycle-badge puc-lifecycle-badge--${selected.lifecycle}`}
                          >
                            {CATALOG_LIFECYCLE_LABELS[selected.lifecycle]}
                          </span>
                        </>
                      ) : null}
                    </p>
                    <h2 className="puc-meta__title">{selected.title}</h2>
                    {selected.description ? (
                      <p className="puc-meta__desc">{selected.description}</p>
                    ) : null}
                  </div>
                  <dl className="puc-meta__facts">
                    <div>
                      <dt>Export</dt>
                      <dd>
                        <code>{selected.exportName}</code>
                      </dd>
                    </div>
                    {selected.propsSummary?.length ? (
                      <div>
                        <dt>Props</dt>
                        <dd>{selected.propsSummary.join(", ")}</dd>
                      </div>
                    ) : null}
                    {selected.docAnchor ? (
                      <div>
                        <dt>Doc</dt>
                        <dd>
                          <code>docs/component-catalog.md#{selected.docAnchor}</code>
                        </dd>
                      </div>
                    ) : null}
                    <div>
                      <dt>Adicionado</dt>
                      <dd>{formatCatalogDatePtBr(selected.addedAt)}</dd>
                    </div>
                    <div>
                      <dt>Última alteração</dt>
                      <dd>{formatCatalogDatePtBr(selected.updatedAt)}</dd>
                    </div>
                    {selected.changeNote ? (
                      <div>
                        <dt>Nota</dt>
                        <dd>{selected.changeNote}</dd>
                      </div>
                    ) : null}
                  </dl>
                </div>

                {selected.demos.length > 1 ? (
                  <div className="puc-demo-tabs" role="tablist" aria-label="Variantes">
                    {selected.demos.map((demo) => (
                      <button
                        key={demo.id}
                        type="button"
                        role="tab"
                        aria-selected={activeDemo?.id === demo.id}
                        className={
                          activeDemo?.id === demo.id
                            ? "puc-chip puc-chip--active"
                            : "puc-chip"
                        }
                        onClick={() => setDemoId(demo.id)}
                      >
                        {demo.label}
                      </button>
                    ))}
                  </div>
                ) : null}

                <section className="puc-preview" aria-label="Prévia">
                  <div className="puc-preview__canvas">
                    {activeDemo ? activeDemo.render() : null}
                  </div>
                </section>
              </>
            ) : (
              <p className="puc-muted">Selecione um componente na lista.</p>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
