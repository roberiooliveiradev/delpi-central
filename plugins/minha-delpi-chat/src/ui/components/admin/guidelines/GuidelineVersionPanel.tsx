import { useState } from "react";

import { listAdminGuidelineVersions } from "../../../../data/api/adminApi";
import type { AdminGuideline, AdminGuidelineVersion } from "../../../../data/api/adminTypes";

import "./GuidelineVersionPanel.css";

type GuidelineVersionPanelProps = {
  guidelines: AdminGuideline[];
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function GuidelineVersionPanel({
  guidelines,
  getAccessToken,
}: GuidelineVersionPanelProps) {
  const [selectedGuidelineId, setSelectedGuidelineId] = useState("");
  const [versions, setVersions] = useState<AdminGuidelineVersion[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleLoadVersions(guidelineId: string) {
    setSelectedGuidelineId(guidelineId);
    setVersions([]);
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

  return (
    <article className="mdc-guideline-version-panel">
      <div>
        <p className="mdc-chat-eyebrow">Versionamento</p>
        <h2>Histórico de diretrizes</h2>
      </div>

      <p className="mdc-chat-muted">
        Consulte versões geradas automaticamente ao salvar, publicar ou arquivar diretrizes.
      </p>

      <label>
        <span>Diretriz</span>
        <select
          value={selectedGuidelineId}
          onChange={(event) => {
            void handleLoadVersions(event.target.value);
          }}
        >
          <option value="">Selecione uma diretriz</option>
          {guidelines.map((guideline) => (
            <option key={guideline.id} value={guideline.id}>
              {guideline.title}
            </option>
          ))}
        </select>
      </label>

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

              <small>
                {version.status} · {version.createdAt ?? "sem data"}
              </small>
            </section>
          ))}
        </div>
      ) : null}
    </article>
  );
}
