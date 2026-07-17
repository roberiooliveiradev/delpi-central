import { useState } from "react";
import { MousePointerClick } from "lucide-react";

import {
  parseContentDispositionFilename,
  triggerBlobDownload,
} from "../../../utils/downloadBlob";
import type { ChatDownloadArtifact } from "../../../data/api/chatTypes";

import "./ChatDownloadArtifacts.css";

type ChatDownloadArtifactsProps = {
  artifacts: ChatDownloadArtifact[];
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

function resolveDownloadUrl(href: string): string {
  const value = String(href || "").trim();

  if (!value) {
    return "";
  }

  if (value.startsWith("http://") || value.startsWith("https://")) {
    return value;
  }

  if (value.startsWith("/apps/api-delpi/")) {
    return value;
  }

  if (value.startsWith("/products/")) {
    return `/apps/api-delpi${value}`;
  }

  if (value.startsWith("/")) {
    return value;
  }

  return `/apps/api-delpi/${value.replace(/^\/+/, "")}`;
}

export function ChatDownloadArtifacts({
  artifacts,
  getAccessToken,
}: ChatDownloadArtifactsProps) {
  const [busyHref, setBusyHref] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!artifacts.length) {
    return null;
  }

  async function handleDownload(artifact: ChatDownloadArtifact) {
    const url = resolveDownloadUrl(artifact.href);

    if (!url) {
      setError("Link de download indisponível.");
      return;
    }

    setBusyHref(artifact.href);
    setError(null);

    try {
      const token = await getAccessToken?.();
      const response = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        throw new Error(`Falha no download (${response.status})`);
      }

      const blob = await response.blob();
      const filename =
        parseContentDispositionFilename(response.headers.get("content-disposition")) ||
        artifact.filename ||
        "download.bin";
      triggerBlobDownload(blob, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Não foi possível baixar o arquivo.");
    } finally {
      setBusyHref(null);
    }
  }

  return (
    <div className="mdc-download-artifacts" data-testid="chat-download-artifacts">
      <ul className="mdc-download-artifacts__list">
        {artifacts.map((artifact) => {
          const key = `${artifact.href}:${artifact.filename}`;
          const busy = busyHref === artifact.href;

          return (
            <li key={key} className="mdc-download-artifacts__item">
              <button
                type="button"
                className="mdc-download-artifacts__button"
                disabled={busy}
                onClick={() => void handleDownload(artifact)}
              >
                <MousePointerClick
                  className="mdc-download-artifacts__click-icon"
                  size={17}
                  aria-hidden="true"
                />
                <span>
                  {busy ? "Baixando…" : artifact.label || `Baixar ${artifact.filename}`}
                </span>
              </button>
              {artifact.filename ? (
                <span className="mdc-download-artifacts__filename">{artifact.filename}</span>
              ) : null}
            </li>
          );
        })}
      </ul>
      {error ? <p className="mdc-download-artifacts__error">{error}</p> : null}
    </div>
  );
}
