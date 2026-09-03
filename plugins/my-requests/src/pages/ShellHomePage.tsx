type ShellHomePageProps = {
  canCreate: boolean;
};

export function ShellHomePage({ canCreate }: ShellHomePageProps) {
  return (
    <section className="dashboard-my-requests__panel">
      <h1>Minhas Solicitações</h1>
      <p>
        Shell do módulo. Use as rotas internas <code>/mine</code>,{" "}
        <code>/work-queue</code>, <code>/new</code> e <code>/requests/:id</code>.
      </p>
      <nav className="dashboard-my-requests__nav">
        <a href="/apps/my-requests/mine">Minhas</a>
        <a href="/apps/my-requests/work-queue">Fila de trabalho</a>
        {canCreate ? <a href="/apps/my-requests/new">Nova</a> : null}
      </nav>
    </section>
  );
}
