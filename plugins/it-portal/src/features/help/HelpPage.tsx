import { ItpPageHero, ItpUserManual as Manual } from "../../app/itPortalUi";
import { SECRET_WARNING } from "../../content/labels";

const SECTIONS = [
  { id: "overview", label: "Visão geral" },
  { id: "servers", label: "Servidores" },
  { id: "notes", label: "Notas técnicas" },
  { id: "action-plans", label: "Planos de ação" },
  { id: "permissions", label: "Permissões" },
  { id: "faq", label: "Dúvidas frequentes" },
] as const;

function scrollToSection(id: string) {
  document.getElementById(`itp-manual-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function HelpPage() {
  return (
    <>
      <ItpPageHero aria-label="Ajuda" eyebrow="Ajuda" title="Como usar o Portal de TI" />
      <Manual.Frame>
        <Manual.Layout
          title="Nesta página"
          aria-label="Seções da ajuda"
          items={SECTIONS.map((section) => ({ ...section, onSelect: () => scrollToSection(section.id) }))}
        >
          <Manual.Section id="itp-manual-overview">
            <Manual.Eyebrow>Visão geral</Manual.Eyebrow>
            <h2>O que é o Portal de TI</h2>
            <Manual.Scope>
              Inventário manual dos servidores da infraestrutura DELPI, com notas técnicas, planos de ação e histórico
              auditado. Todas as informações são gravadas no banco do portal e ficam disponíveis após recarregar a
              página.
            </Manual.Scope>
            <Manual.Concepts
              items={[
                {
                  term: "Início",
                  meaning:
                    "Indicadores calculados a partir do inventário: servidores ativos, criticidade alta/crítica, ações abertas e atrasadas.",
                },
                {
                  term: "Situação administrativa",
                  meaning:
                    "Informada manualmente pela equipe (planejado, em operação, em manutenção, em desativação). Não há monitoramento nem medição de disponibilidade nesta etapa.",
                },
                {
                  term: "Fora desta etapa",
                  meaning:
                    "Monitoramento, descoberta automática, agentes, integração com GLPI, notificações e anexos ainda não estão disponíveis.",
                },
              ]}
            />
          </Manual.Section>

          <Manual.Section id="itp-manual-servers">
            <Manual.Eyebrow>Servidores</Manual.Eyebrow>
            <h2>Cadastrar e manter servidores</h2>
            <Manual.GuideTable
              rows={[
                {
                  want: "Cadastrar um servidor",
                  where: "Servidores ou Início",
                  how: "«Cadastrar servidor», preencha os campos obrigatórios e salve.",
                },
                {
                  want: "Encontrar um servidor",
                  where: "Servidores",
                  how: "Busque por nome ou hostname e filtre por unidade, ambiente e criticidade.",
                },
                {
                  want: "Editar o cadastro",
                  where: "Detalhe do servidor",
                  how: "«Editar». Se outra pessoa salvou antes, recarregue e repita a alteração.",
                },
                {
                  want: "Tirar do inventário ativo",
                  where: "Detalhe do servidor",
                  how: "«Arquivar». Nada é excluído; é possível restaurar depois. Feche os planos abertos antes.",
                },
              ]}
            />
            <Manual.Scope>
              O hostname é único por unidade e ambiente: o mesmo hostname pode existir em Produção e Homologação, mas não
              duas vezes no mesmo ambiente da mesma unidade.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-notes">
            <Manual.Eyebrow>Notas técnicas</Manual.Eyebrow>
            <h2>Registrar observações</h2>
            <Manual.Scope>
              Notas ficam em ordem cronológica com o autor real e não podem ser editadas nem excluídas. {SECRET_WARNING}{" "}
              O portal recusa textos que pareçam conter senhas ou tokens.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-action-plans">
            <Manual.Eyebrow>Planos de ação</Manual.Eyebrow>
            <h2>Planejar e acompanhar ações</h2>
            <Manual.Concepts
              items={[
                { term: "Criar", meaning: "No detalhe do servidor, seção Planos de ação, «Novo plano»." },
                {
                  term: "Status",
                  meaning:
                    "Pendente → Em andamento → Concluído, ou Cancelado. Um plano concluído pode ser reaberto para Em andamento; um cancelado volta para Pendente.",
                },
                {
                  term: "Atrasado",
                  meaning: "Plano pendente ou em andamento com prazo anterior à data de hoje (horário de Brasília).",
                },
              ]}
            />
          </Manual.Section>

          <Manual.Section id="itp-manual-permissions">
            <Manual.Eyebrow>Permissões</Manual.Eyebrow>
            <h2>Quem pode fazer o quê</h2>
            <Manual.Scope>
              As permissões são concedidas pela administração da Minha DELPI e verificadas pelo servidor a cada
              requisição. Botões que você não pode usar não aparecem.
            </Manual.Scope>
            <Manual.Glossary
              items={[
                { term: "Acessar o Portal de TI", meaning: "Abrir o portal." },
                { term: "Ver servidores", meaning: "Consultar inventário, detalhe, notas e histórico." },
                { term: "Gerenciar servidores", meaning: "Cadastrar, editar, arquivar e restaurar." },
                { term: "Registrar notas", meaning: "Adicionar notas técnicas." },
                { term: "Ver planos de ação", meaning: "Consultar planos de ação." },
                { term: "Gerenciar planos de ação", meaning: "Criar, editar e alterar o status de planos." },
              ]}
            />
          </Manual.Section>

          <Manual.Section id="itp-manual-faq">
            <Manual.Eyebrow>Dúvidas frequentes</Manual.Eyebrow>
            <h2>Dúvidas frequentes</h2>
            <Manual.Faq
              items={[
                {
                  q: "Por que não consigo arquivar um servidor?",
                  a: "Ele ainda tem planos de ação pendentes ou em andamento. Conclua ou cancele-os primeiro.",
                },
                {
                  q: "Apareceu «foi alterado por outra pessoa». O que faço?",
                  a: "Feche o formulário, recarregue a página e refaça a alteração sobre a versão atual.",
                },
                {
                  q: "O portal mostra disponibilidade ou uptime?",
                  a: "Não. Nesta etapa só há informações cadastradas manualmente.",
                },
              ]}
            />
          </Manual.Section>
        </Manual.Layout>
      </Manual.Frame>
    </>
  );
}
