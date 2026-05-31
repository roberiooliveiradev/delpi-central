import { ChatIntelligenceSettingsPanel } from "../metrics-tab/ChatIntelligenceSettingsPanel";

type AdminPlatformIntelligenceTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function AdminPlatformIntelligenceTab({
  getAccessToken,
}: AdminPlatformIntelligenceTabProps) {
  return (
    <section className="mdc-admin-platform-intelligence">
      <header className="mdc-admin-section-intro">
        <h2>Inteligência do chat</h2>
        <p>
          Toggles do pipeline base (fast path, agentic, RAG). Alterações afetam todos os
          agentes que herdam a plataforma.
        </p>
      </header>
      <ChatIntelligenceSettingsPanel getAccessToken={getAccessToken} />
    </section>
  );
}
