import "./App.css";

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
};

export default function App({ pathname }: AppProps) {
  return (
    <main className="minha-delpi-chat">
      <section className="minha-delpi-chat__card">
        <p className="minha-delpi-chat__eyebrow">Plugin oficial</p>
        <h1>Minha DELPI Chat</h1>
        <p>
          Plugin carregado com sucesso. A implementação do chat será feita nas
          próximas etapas do roadmap.
        </p>
        <small>Rota atual: {pathname ?? "/apps/minha-delpi-chat"}</small>
      </section>
    </main>
  );
}
