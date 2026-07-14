import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Info } from "lucide-react";

import {
  fetchCatalog,
  publishCatalog,
  type CatalogData,
} from "../api/audit5sApi";
import { AuditCatalogEditor } from "../components/AuditCatalogEditor";
import { AuditCatalogPublishBar } from "../components/AuditCatalogPublishBar";
import { useAudit5sAdminPermission } from "../hooks/useAudit5sAdminPermission";
import {
  addCriterionToSenso,
  buildPublishPayload,
  catalogsAreEquivalent,
  computeCatalogDiff,
  criteriaFromCatalog,
  groupCriteriaBySenso,
  removeCriterion,
  resolveSensoName,
  updateCriterion,
  validateDraftCriteria,
  type EditableCriterion,
} from "../utils/catalogEditor";

type Props = {
  branch: string;
  pathname?: string;
  onPublished?: () => void;
  onDenied?: () => void;
};

export function AuditCatalogPage({
  branch,
  pathname,
  onPublished,
  onDenied,
}: Props) {
  const { canAdmin, loading: adminLoading } = useAudit5sAdminPermission(
    branch,
    pathname,
  );
  const onDeniedRef = useRef(onDenied);
  onDeniedRef.current = onDenied;

  const [catalog, setCatalog] = useState<CatalogData | null>(null);
  const [baseline, setBaseline] = useState<EditableCriterion[]>([]);
  const [draft, setDraft] = useState<EditableCriterion[]>([]);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchCatalog(branch);
      const editable = criteriaFromCatalog(data.criteria);
      setCatalog(data);
      setBaseline(editable);
      setDraft(editable);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar catálogo.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  useEffect(() => {
    if (adminLoading) return;
    if (!canAdmin) {
      onDeniedRef.current?.();
      return;
    }
    void loadCatalog();
  }, [adminLoading, canAdmin, loadCatalog]);

  const grouped = useMemo(() => groupCriteriaBySenso(draft), [draft]);
  const diff = useMemo(() => computeCatalogDiff(baseline, draft), [baseline, draft]);

  const handleAdd = (sensoOrder: number) => {
    setDraft((prev) => addCriterionToSenso(prev, sensoOrder));
    setSuccess(null);
  };

  const handleChange = (
    clientId: string,
    patch: Partial<Pick<EditableCriterion, "code" | "description" | "sort_order">>,
  ) => {
    setDraft((prev) => updateCriterion(prev, clientId, patch));
    setSuccess(null);
  };

  const handleRemove = (clientId: string) => {
    setDraft((prev) => removeCriterion(prev, clientId));
    setSuccess(null);
  };

  const handlePublish = async () => {
    const validationError = validateDraftCriteria(draft);
    if (validationError) {
      setError(validationError);
      return;
    }
    if (catalogsAreEquivalent(baseline, draft)) {
      setError("Nenhuma alteração detectada.");
      return;
    }

    setPublishing(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await publishCatalog(buildPublishPayload(branch, draft));
      setSuccess(
        `Catálogo publicado na versão ${result.catalog_version} com ${result.criteria_count} critérios.`,
      );
      await loadCatalog();
      onPublished?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao publicar catálogo.");
    } finally {
      setPublishing(false);
    }
  };

  if (adminLoading || !canAdmin) {
    return <p className="a5s-catalog-loading">Verificando permissão administrativa…</p>;
  }

  if (loading && !catalog) {
    return <p className="a5s-catalog-loading">Carregando catálogo de critérios…</p>;
  }

  return (
    <div className="a5s-catalog">
      <div className="a5s-catalog__intro">
        <div>
          <h2 className="a5s-catalog__title">Critérios da auditoria 5S</h2>
          <p className="a5s-catalog__subtitle">
            Edite o formulário de critérios da filial {branch}. Cada publicação gera uma nova versão
            do catálogo.
          </p>
        </div>
      </div>

      <div className="a5s-catalog__notice" role="note">
        <Info size={18} aria-hidden />
        <p>
          Alterações valerão apenas para auditorias criadas após a publicação. Auditorias já
          avaliadas ou em andamento não serão modificadas.
        </p>
      </div>

      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
      {success ? <div className="a5s-alert a5s-alert--success">{success}</div> : null}

      {catalog ? (
        <AuditCatalogPublishBar
          catalogVersion={catalog.catalog_version}
          diff={diff}
          publishing={publishing}
          onPublish={handlePublish}
        />
      ) : null}

      <div className="a5s-catalog__grid">
        {[1, 2, 3, 4, 5].map((sensoOrder) => (
          <AuditCatalogEditor
            key={sensoOrder}
            sensoOrder={sensoOrder}
            sensoName={resolveSensoName(
              sensoOrder,
              catalog?.criteria ?? [],
              catalog?.senso_names ?? [],
            )}
            criteria={grouped.get(sensoOrder) ?? []}
            onAdd={handleAdd}
            onChange={handleChange}
            onRemove={handleRemove}
          />
        ))}
      </div>
    </div>
  );
}
