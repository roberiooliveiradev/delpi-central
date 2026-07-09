import { useState } from "react";

import {
  compareAdminGuidelineVersions,
  listAdminGuidelineVersions,
  restoreAdminGuidelineVersion,
} from "../../../../data/api/adminApi";
import type {
  AdminGuideline,
  AdminGuidelineVersion,
  AdminGuidelineVersionComparison,
} from "../../../../data/api/adminTypes";
import { useConfirmDialog } from "../../shared";
import {
  ChatAdminNativeSelectField,
} from "../shared/chatAdminFormFields";

import "./GuidelineVersionPanel.css";

type GuidelineVersionPanelProps = {
  guidelines: AdminGuideline[];
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onRestored?: () => Promise<void>;
  canCreateGuidelines: boolean;
};

export function GuidelineVersionPanel({
  guidelines,
  getAccessToken,
  onRestored,
  canCreateGuidelines,
}: GuidelineVersionPanelProps) {
  const { confirm, dialog: confirmDialog } = useConfirmDialog();
  const [selectedGuidelineId, setSelectedGuidelineId] = useState("");
  const [versions, setVersions] = useState<AdminGuidelineVersion[]>([]);
  const [fromVersion, setFromVersion] = useState("");
  const [toVersion, setToVersion] = useState("");
  const [comparison, setComparison] =
    useState<AdminGuidelineVersionComparison | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLoadVersions(guidelineId: string) {
    setSelectedGuidelineId(guidelineId);
    setVersions([]);
    setComparison(null);
    setFromVersion("");
    setToVersion("");
    setError(null);

    if (!guidelineId) {
      return;
    }

    setIsLoading(true);

    try {
      const response = await listAdminGuidelineVersions(guidelineId, {
        getAccessToken,
      });
      setVersions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar versões.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleCompareVersions() {
    if (!selectedGuidelineId || !fromVersion || !toVersion || isComparing) {
      return;
    }

    setIsComparing(true);
    setComparison(null);
    setError(null);

    try {
      const response = await compareAdminGuidelineVersions(
        selectedGuidelineId,
        Number(fromVersion),
        Number(toVersion),
        { getAccessToken },
      );
      setComparison(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao comparar versões.");
    } finally {
      setIsComparing(false);
    }
  }

  async function handleRestoreVersion(version: number) {
    if (!selectedGuidelineId || isRestoring) {
      return;
    }

    const confirmed = await confirm({
      title: "Restaurar versão",
      description: `Restaurar a versão ${version} como novo rascunho?`,
      confirmLabel: "Restaurar",
      cancelLabel: "Cancelar",
      danger: true,
    });

    if (!confirmed) {
      return;
    }

    setIsRestoring(true);
    setError(null);

    try {
      await restoreAdminGuidelineVersion(selectedGuidelineId, version, {
        getAccessToken,
      });

      await handleLoadVersions(selectedGuidelineId);
      await onRestored?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao restaurar versão.");
    } finally {
      setIsRestoring(false);
    }
  }

  return (
    <article className="mdc-guideline-version-panel">
      {confirmDialog}
      <div>
        <p className="mdc-chat-eyebrow">Versionamento</p>
        <h2>Histórico de diretrizes</h2>
      </div>

      <p className="mdc-chat-muted">
        Consulte versões, compare mudanças e restaure versões anteriores como novo rascunho.
      </p>

      <ChatAdminNativeSelectField
        id="guideline-version-guideline"
        label="Diretriz"
        span={false}
        value={selectedGuidelineId}
        placeholderOption="Selecione uma diretriz"
        options={guidelines.map((guideline) => ({
          value: guideline.id,
          label: guideline.title,
        }))}
        onChange={(value) => {
          void handleLoadVersions(value);
        }}
      />

      {versions.length >= 2 ? (
        <section className="mdc-guideline-version-panel__compare">
          <h3>Comparar versões</h3>

          <div>
            <ChatAdminNativeSelectField
              id="guideline-version-from"
              label="De"
              span={false}
              value={fromVersion}
              placeholderOption="Versão"
              options={versions.map((version) => ({
                value: String(version.version),
                label: `v${version.version}`,
              }))}
              onChange={setFromVersion}
            />

            <ChatAdminNativeSelectField
              id="guideline-version-to"
              label="Para"
              span={false}
              value={toVersion}
              placeholderOption="Versão"
              options={versions.map((version) => ({
                value: String(version.version),
                label: `v${version.version}`,
              }))}
              onChange={setToVersion}
            />

            <button
              type="button"
              disabled={!fromVersion || !toVersion || isComparing}
              onClick={() => {
                void handleCompareVersions();
              }}
            >
              {isComparing ? "Comparando..." : "Comparar"}
            </button>
          </div>
        </section>
      ) : null}

      {comparison ? (
        <section className="mdc-guideline-version-panel__diff">
          <h3>
            v{comparison.fromVersion.version} → v{comparison.toVersion.version}
          </h3>

          {comparison.changes.length === 0 ? (
            <p>Nenhuma diferença encontrada entre as versões.</p>
          ) : (
            <ul>
              {comparison.changes.map((change) => (
                <li key={change.field}>
                  <strong>{change.field}</strong>
                  <div>
                    <span>Antes</span>
                    <p>{change.from || "—"}</p>
                  </div>
                  <div>
                    <span>Depois</span>
                    <p>{change.to || "—"}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      ) : null}

      {error ? (
        <div className="mdc-guideline-version-panel__error" role="alert">
          {error}
        </div>
      ) : null}

      {isLoading ? <p className="mdc-chat-muted">Carregando versões...</p> : null}

      {!isLoading && selectedGuidelineId && versions.length === 0 ? (
        <div className="mdc-guideline-version-panel__empty">
          Nenhuma versão registrada para esta diretriz.
        </div>
      ) : null}

      {versions.length > 0 ? (
        <div className="mdc-guideline-version-panel__list">
          {versions.map((version) => (
            <section key={version.id}>
              <div>
                <strong>v{version.version}</strong>
                <span>{version.event}</span>
              </div>

              <h3>{version.title}</h3>
              <p>{version.description || version.content}</p>

              <footer>
                <small>
                  {version.status} · {version.createdAt ?? "sem data"}
                </small>

                <button
                  type="button"
                  disabled={isRestoring || !canCreateGuidelines}
                  title={
                    canCreateGuidelines
                      ? "Restaurar versão como rascunho"
                      : "Você não tem permissão para restaurar diretrizes."
                  }
                  onClick={() => {
                    void handleRestoreVersion(version.version);
                  }}
                >
                  Restaurar
                </button>
              </footer>
            </section>
          ))}
        </div>
      ) : null}
    </article>
  );
}
