import { useCallback, useEffect, useState } from "react";

import {
  getAdminSecurityConfig,
  getAdminSecuritySummary,
  listAdminSecurityEvents,
  scanAdminSecurityInput,
} from "../../../../data/api/adminApi";
import type {
  AdminSecurityConfig,
  AdminSecurityEventsResponse,
  AdminSecurityScanResponse,
  AdminSecuritySummary,
} from "../../../../data/api/adminTypes";

import type { AdminNavState } from "../../../../navigation/adminNavigation";
import { AdminSectionLinks } from "../shared/AdminSectionLinks";

import "./AdminSecurityTab.css";

type AdminSecurityTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
  onNavigate?: (nav: Partial<AdminNavState>) => void;
};

export function AdminSecurityTab({ getAccessToken, onNavigate }: AdminSecurityTabProps) {
  const [config, setConfig] = useState<AdminSecurityConfig | null>(null);
  const [summary, setSummary] = useState<AdminSecuritySummary | null>(null);
  const [events, setEvents] = useState<AdminSecurityEventsResponse | null>(null);
  const [scanMessage, setScanMessage] = useState("");
  const [scanResult, setScanResult] = useState<AdminSecurityScanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [configResponse, summaryResponse, eventsResponse] = await Promise.all([
        getAdminSecurityConfig({ getAccessToken }),
        getAdminSecuritySummary(24, { getAccessToken }),
        listAdminSecurityEvents({ limit: 25, offset: 0 }, { getAccessToken }),
      ]);

      setConfig(configResponse);
      setSummary(summaryResponse);
      setEvents(eventsResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar segurança operacional.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    void loadData();
  }, [loadData]);

  async function handleScan() {
    if (!scanMessage.trim()) {
      return;
    }

    setIsScanning(true);
    setError(null);

    try {
      const result = await scanAdminSecurityInput({ message: scanMessage }, { getAccessToken });
      setScanResult(result);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao analisar mensagem.");
    } finally {
      setIsScanning(false);
    }
  }

  return (
    <section className="mdc-admin-security">
      <AdminSectionLinks
        items={
          onNavigate
            ? [
                {
                  label: "Ver trilha de auditoria",
                  onClick: () => onNavigate({ section: "governance", subTab: "audit" }),
                },
              ]
            : []
        }
      />

      <article className="mdc-admin-panel">
        <header className="mdc-admin-tab-header">
          <div className="mdc-admin-panel__intro">
            <p className="mdc-chat-eyebrow">Segurança</p>
            <h2>Segurança operacional</h2>
            <p>
              Anti prompt-injection, sanitização, limites e auditoria de tentativas suspeitas.
            </p>
          </div>
          <button
            type="button"
            className="mdc-admin-btn"
            disabled={isLoading}
            onClick={() => void loadData()}
          >
            {isLoading ? "Carregando..." : "Atualizar"}
          </button>
        </header>
      </article>

      {error ? <p className="mdc-admin-security__error">{error}</p> : null}

      <div className="mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Bloqueios (24h)</h3>
          <strong>{summary?.blockedCount ?? 0}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Sinalizados (24h)</h3>
          <strong>{summary?.flaggedCount ?? 0}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Scans admin (24h)</h3>
          <strong>{summary?.scannedCount ?? 0}</strong>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Total eventos</h3>
          <strong>{summary?.totalEvents ?? 0}</strong>
        </article>
      </div>

      <div className="mdc-admin-security__layout mdc-admin-split">
        <article className="mdc-admin-split__aside mdc-admin-panel mdc-admin-security__scan">
          <h3>Testar mensagem</h3>
          <label className="mdc-admin-field">
            <span>Mensagem</span>
            <textarea
            value={scanMessage}
            onChange={(event) => setScanMessage(event.target.value)}
              placeholder="Cole uma mensagem para avaliar risco de prompt injection..."
            />
          </label>
          <button
            type="button"
            className="mdc-admin-btn mdc-admin-btn--primary"
            disabled={isScanning}
            onClick={() => void handleScan()}
          >
            {isScanning ? "Analisando..." : "Analisar"}
          </button>

          {scanResult ? (
            <div className="mdc-admin-security__scan-result">
              <strong>
                Risco {scanResult.analysis.riskLevel} ({Math.round(scanResult.analysis.riskScore * 100)}%)
              </strong>
              <span>
                {scanResult.wouldBlock
                  ? "Seria bloqueada no chat"
                  : scanResult.wouldFlag
                    ? "Seria sinalizada na auditoria"
                    : "Passaria sem bloqueio"}
              </span>
              {scanResult.analysis.flags.length ? (
                <div className="mdc-admin-security__flags">
                  {scanResult.analysis.flags.map((flag) => (
                    <span key={flag}>{flag}</span>
                  ))}
                </div>
              ) : (
                <span className="mdc-chat-muted">Nenhum indicador detectado.</span>
              )}
            </div>
          ) : null}
        </article>

        <article className="mdc-admin-split__main mdc-admin-panel mdc-admin-security__config">
          <h3>Configuração ativa</h3>
          {config ? (
            <dl>
              <div>
                <dt>Proteção</dt>
                <dd>{config.enabled ? "Ativa" : "Desativada"}</dd>
              </div>
              <div>
                <dt>Modo</dt>
                <dd>{config.mode}</dd>
              </div>
              <div>
                <dt>Tamanho máximo</dt>
                <dd>{config.messageMaxChars} caracteres</dd>
              </div>
              <div>
                <dt>Bloqueio ≥</dt>
                <dd>{config.blockThreshold}</dd>
              </div>
              <div>
                <dt>Sinalização ≥</dt>
                <dd>{config.flagThreshold}</dd>
              </div>
              <div>
                <dt>Regras injection</dt>
                <dd>{config.injectionRuleCount}</dd>
              </div>
              <div>
                <dt>Rate limit chat</dt>
                <dd>
                  {config.rateLimits.chatMessagesPerWindow}/{config.rateLimits.windowSeconds}s
                </dd>
              </div>
            </dl>
          ) : (
            <p className="mdc-chat-muted">Carregando configuração...</p>
          )}

          {summary?.flagDistribution?.length ? (
            <>
              <h3>Indicadores frequentes (24h)</h3>
              <ul>
                {summary.flagDistribution.map((item) => (
                  <li key={item.flag}>
                    {item.flag} ({item.count})
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      </div>

      <article className="mdc-admin-panel mdc-admin-security__events">
        <h3>Eventos recentes</h3>
        <table>
          <thead>
            <tr>
              <th>Quando</th>
              <th>Ação</th>
              <th>Risco</th>
              <th>Flags</th>
            </tr>
          </thead>
          <tbody>
            {(events?.items ?? []).map((event) => (
              <tr key={event.id}>
                <td>{new Date(event.createdAt).toLocaleString("pt-BR")}</td>
                <td>{event.action}</td>
                <td>{String(event.metadata?.riskScore ?? "—")}</td>
                <td>{((event.metadata?.flags as string[]) ?? []).join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </article>
    </section>
  );
}
