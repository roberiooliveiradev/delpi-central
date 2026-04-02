export type AppProps = {
  getAccessToken?: () => string | undefined;
};

export default function App({ getAccessToken }: AppProps) {
  void getAccessToken;

  return (
    <div className="strategic-indicators-app">
      <div className="strategic-indicators-shell">
        <header className="strategic-indicators-header">
          <p className="strategic-indicators-eyebrow">MinhaDelpi</p>
          <h1>Strategic Indicators</h1>
          <span className="strategic-indicators-badge">Plugin em fundação</span>
        </header>

        <main className="strategic-indicators-content">
          <section className="strategic-indicators-card">
            <h2>Microfrontend carregado com sucesso</h2>
            <p>
              A fundação técnica do plugin está ativa. O próximo passo será
              construir a visão executiva do dashboard.
            </p>
          </section>
        </main>
      </div>
    </div>
  );
}