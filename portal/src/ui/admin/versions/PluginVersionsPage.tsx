// src/ui/admin/versions/PluginVersionsPage.tsx

import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import type { PluginVersion, PluginVersionDetail } from "../../../data/adminApi";
import { useAdminApi } from "../../../hooks/useAdminApi";
import { ConfirmDialog } from "../../../components/ConfirmDialog";
import { useAppAlert } from "../../../components/ConfirmDialogProvider";
import {
  Alert,
  Badge,
  Button,
  DenseTable,
  PageChrome,
  Radio,
  Spinner,
} from "../../../ui-kit";
import { diffManifest, type ManifestDiff } from "../manifest/manifestUtils";

import "./PluginVersionsPage.css";

const formatBrazilDateTime = (value?: string | null) => {
  if (!value) return "—";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Data inválida";

  return new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
};

const DiffSection = ({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "added" | "removed" | "changed";
}) => {
  if (items.length === 0) return null;

  return (
    <div className={`plugin-versions-diff-section plugin-versions-diff-section--${tone}`}>
      <h5>
        {title} <span>({items.length})</span>
      </h5>
      <ul>
        {items.map((item) => (
          <li key={item}>
            <code>{item}</code>
          </li>
        ))}
      </ul>
    </div>
  );
};

export const PluginVersionsPage = () => {
  const { appId = "" } = useParams<{ appId: string }>();
  const navigate = useNavigate();
  const showAlert = useAppAlert();
  const api = useAdminApi();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [appName, setAppName] = useState(appId);
  const [currentVersion, setCurrentVersion] = useState<string | null>(null);
  const [versions, setVersions] = useState<PluginVersion[]>([]);

  const [versionA, setVersionA] = useState<string>("");
  const [versionB, setVersionB] = useState<string>("");
  const [comparing, setComparing] = useState(false);
  const [diff, setDiff] = useState<ManifestDiff | null>(null);
  const [manifestA, setManifestA] = useState<Record<string, unknown> | null>(null);
  const [manifestB, setManifestB] = useState<Record<string, unknown> | null>(null);

  const backToManifest = () =>
    navigate(`/admin/apps/${encodeURIComponent(appId)}/manifest`);

  const [rollbackTarget, setRollbackTarget] = useState<string | null>(null);
  const [rollbackRemovedCodes, setRollbackRemovedCodes] = useState<string[]>([]);
  const [rollbackLoading, setRollbackLoading] = useState(false);

  const load = useCallback(async () => {
    if (!appId) return;

    setLoading(true);
    setError(null);

    try {
      const [versionsRes, manifest, appsRes] = await Promise.all([
        api.listPluginVersions(appId),
        api.getPluginManifest(appId).catch(() => null),
        api.listApps({ page: 1, pageSize: 999, q: appId }),
      ]);

      const list = Array.isArray(versionsRes) ? versionsRes : [];
      setVersions(list);

      const fromManifest =
        manifest && typeof manifest === "object" && typeof manifest.version === "string"
          ? manifest.version
          : null;

      const app = (appsRes.data ?? []).find((item) => item.id === appId);
      setAppName(app?.name?.trim() || appId);
      setCurrentVersion(fromManifest || app?.version || null);

      if (list.length > 0) {
        setVersionA((prev) => prev || fromManifest || list[0].version);
        setVersionB((prev) => {
          if (prev) return prev;
          const other = list.find((v) => v.version !== (fromManifest || list[0].version));
          return other?.version || list[0].version;
        });
      }
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Não foi possível carregar o histórico de versões.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [api, appId]);

  useEffect(() => {
    void load();
  }, [load]);

  const runCompare = async () => {
    if (!appId || !versionA || !versionB) return;

    setComparing(true);
    setDiff(null);

    try {
      const [detailA, detailB] = await Promise.all([
        api.getPluginVersion(appId, versionA),
        api.getPluginVersion(appId, versionB),
      ]);

      const aManifest = (detailA as PluginVersionDetail).manifest ?? {};
      const bManifest = (detailB as PluginVersionDetail).manifest ?? {};

      setManifestA(aManifest);
      setManifestB(bManifest);
      setDiff(diffManifest(aManifest, bManifest));
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Não foi possível comparar as versões.";
      await showAlert({ title: "Erro", message });
    } finally {
      setComparing(false);
    }
  };

  const openRollbackConfirm = async (targetVersion: string) => {
    if (!appId || targetVersion === currentVersion) return;

    setRollbackLoading(true);

    try {
      const [currentManifest, targetDetail] = await Promise.all([
        api.getPluginManifest(appId),
        api.getPluginVersion(appId, targetVersion),
      ]);

      const targetManifest =
        (targetDetail as PluginVersionDetail).manifest ?? {};
      const preview = diffManifest(currentManifest ?? {}, targetManifest);
      setRollbackRemovedCodes(preview.permissions.removed);
      setRollbackTarget(targetVersion);
    } catch (e: unknown) {
      const message =
        e instanceof Error
          ? e.message
          : "Não foi possível preparar a restauração.";
      await showAlert({ title: "Erro", message });
    } finally {
      setRollbackLoading(false);
    }
  };

  const confirmRollback = async () => {
    if (!appId || !rollbackTarget) return;

    setRollbackLoading(true);

    try {
      await api.rollbackPlugin(appId, rollbackTarget);
      setRollbackTarget(null);
      setDiff(null);
      setManifestA(null);
      setManifestB(null);
      await showAlert({
        title: "Versão restaurada",
        message: `O plugin foi restaurado para a versão ${rollbackTarget}.`,
      });
      await load();
    } catch (e: unknown) {
      const message =
        e instanceof Error ? e.message : "Falha ao restaurar a versão.";
      await showAlert({ title: "Erro", message });
    } finally {
      setRollbackLoading(false);
    }
  };

  const rollbackMessage = useMemo(() => {
    if (!rollbackTarget) return "";

    let message = `Deseja restaurar o plugin para a versão ${rollbackTarget}? A versão atual será substituída pelo snapshot histórico selecionado.`;

    if (rollbackRemovedCodes.length > 0) {
      message += ` Atenção: ${rollbackRemovedCodes.length} código(s) de permissão serão removidos do manifesto vigente (${rollbackRemovedCodes.join(", ")}). Papéis que dependem só desses codes podem perder acesso.`;
    }

    return message;
  }, [rollbackRemovedCodes, rollbackTarget]);

  const hasDiffContent =
    !!diff &&
    (diff.permissions.added.length > 0 ||
      diff.permissions.removed.length > 0 ||
      diff.permissions.changed.length > 0 ||
      diff.routes.added.length > 0 ||
      diff.routes.removed.length > 0 ||
      diff.routes.changed.length > 0 ||
      diff.meta.changed.length > 0);

  return (
    <PageChrome
      className="plugin-versions-page"
      breadcrumb={[
        { label: "Admin", onClick: () => navigate("/admin") },
        { label: "Aplicações", onClick: () => navigate("/admin?tab=apps") },
        { label: "Manifesto", onClick: backToManifest },
        { label: "Histórico de versões" },
      ]}
      title={appName}
      subtitle={
        <>
          App <code>{appId}</code>
          {currentVersion ? (
            <>
              {" "}
              · versão atual <strong>{currentVersion}</strong>
            </>
          ) : null}
        </>
      }
      actions={
        <Button variant="secondary" size="sm" onClick={backToManifest}>
          Voltar ao manifesto
        </Button>
      }
    >
      {loading && <Spinner label="Carregando versões…" />}
      {error && <Alert tone="danger">{error}</Alert>}

      {!loading && !error && (
        <>
          <section className="plugin-versions-panel">
            <div className="plugin-versions-panel-header">
              <div>
                <h2>Histórico</h2>
                <p className="hint">
                  {versions.length} versão(ões) publicadas. Selecione A e B para
                  comparar, ou restaure um snapshot.
                </p>
              </div>
            </div>

            {versions.length === 0 ? (
              <Alert tone="info">Nenhuma versão publicada ainda.</Alert>
            ) : (
              <DenseTable wrapTable>
                <thead>
                  <tr>
                    <th>Versão</th>
                    <th>Checksum</th>
                    <th>Criada em</th>
                    <th>A</th>
                    <th>B</th>
                    <th>Ações</th>
                  </tr>
                </thead>
                <tbody>
                  {versions.map((item) => {
                    const isCurrent = item.version === currentVersion;

                    return (
                      <tr
                        key={item.version}
                        className={isCurrent ? "is-current" : undefined}
                      >
                        <td>
                          <code>{item.version}</code>
                          {isCurrent ? (
                            <Badge tone="primary">Atual</Badge>
                          ) : null}
                        </td>
                        <td>
                          <code className="plugin-versions-checksum">
                            {item.checksum?.slice(0, 12) || "—"}
                            {item.checksum && item.checksum.length > 12
                              ? "…"
                              : ""}
                          </code>
                        </td>
                        <td>{formatBrazilDateTime(item.created_at)}</td>
                        <td>
                          <Radio
                            name="version-a"
                            checked={versionA === item.version}
                            onChange={() => setVersionA(item.version)}
                            aria-label={`Comparar A = ${item.version}`}
                          />
                        </td>
                        <td>
                          <Radio
                            name="version-b"
                            checked={versionB === item.version}
                            onChange={() => setVersionB(item.version)}
                            aria-label={`Comparar B = ${item.version}`}
                          />
                        </td>
                        <td>
                          <Button
                            variant="secondary"
                            size="sm"
                            disabled={isCurrent || rollbackLoading}
                            onClick={() => void openRollbackConfirm(item.version)}
                          >
                            Restaurar
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </DenseTable>
            )}

            <div className="plugin-versions-compare-bar">
              <span className="hint">
                A: <strong>{versionA || "—"}</strong>
                {" → "}
                B: <strong>{versionB || "—"}</strong>
              </span>
              <Button
                variant="primary"
                size="sm"
                disabled={!versionA || !versionB || comparing}
                loading={comparing}
                onClick={() => void runCompare()}
              >
                {comparing ? "Comparando…" : "Comparar"}
              </Button>
            </div>
          </section>

          {diff && (
            <section className="plugin-versions-panel">
              <div className="plugin-versions-panel-header">
                <div>
                  <h2>Diff de manifesto</h2>
                  <p className="hint">
                    Comparando <code>{versionA}</code> (base) →{" "}
                    <code>{versionB}</code> (alvo)
                  </p>
                </div>
              </div>

              {!hasDiffContent ? (
                <Alert tone="success">
                  Nenhuma diferença estrutural entre as versões selecionadas.
                </Alert>
              ) : (
                <div className="plugin-versions-diff-grid">
                  <DiffSection
                    title="Permissões adicionadas"
                    items={diff.permissions.added}
                    tone="added"
                  />
                  <DiffSection
                    title="Permissões removidas"
                    items={diff.permissions.removed}
                    tone="removed"
                  />
                  <DiffSection
                    title="Permissões alteradas"
                    items={diff.permissions.changed}
                    tone="changed"
                  />
                  <DiffSection
                    title="Rotas adicionadas"
                    items={diff.routes.added}
                    tone="added"
                  />
                  <DiffSection
                    title="Rotas removidas"
                    items={diff.routes.removed}
                    tone="removed"
                  />
                  <DiffSection
                    title="Rotas alteradas"
                    items={diff.routes.changed}
                    tone="changed"
                  />
                  <DiffSection
                    title="Metadados alterados"
                    items={diff.meta.changed}
                    tone="changed"
                  />
                </div>
              )}

              {manifestA && manifestB ? (
                <details className="plugin-versions-raw">
                  <summary>Ver JSON dos snapshots</summary>
                  <div className="plugin-versions-raw-grid">
                    <pre>{JSON.stringify(manifestA, null, 2)}</pre>
                    <pre>{JSON.stringify(manifestB, null, 2)}</pre>
                  </div>
                </details>
              ) : null}
            </section>
          )}
        </>
      )}

      <ConfirmDialog
        open={!!rollbackTarget}
        title="Restaurar versão"
        message={rollbackMessage}
        confirmText="Restaurar"
        danger
        size="md"
        loading={rollbackLoading}
        onCancel={() => {
          if (!rollbackLoading) setRollbackTarget(null);
        }}
        onConfirm={confirmRollback}
      />
    </PageChrome>
  );
};
