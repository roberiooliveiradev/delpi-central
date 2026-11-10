import { ItpPageHero, ItpUserManual as Manual } from "../../app/itPortalUi";
import { SECRET_WARNING } from "../../content/labels";

const SERVICE_KIND_LABEL_HELP = {
  business_application: "O que o usuário final usa para trabalhar, como um portal ou o ERP.",
  platform_service: "Infraestrutura de apoio às aplicações, como proxy reverso, cache, identidade ou mensageria.",
} as const;

const SECTIONS = [
  { id: "overview", label: "Visão geral" },
  { id: "servers", label: "Servidores" },
  { id: "services", label: "Serviços e aplicações" },
  { id: "databases", label: "Bancos de dados" },
  { id: "links", label: "Vínculos" },
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
              Inventário manual da infraestrutura DELPI: servidores, serviços e aplicações, instâncias de bancos de dados
              e os vínculos entre eles, com notas técnicas, planos de ação e histórico auditado. Todas as informações são
              gravadas no banco do portal e ficam disponíveis após recarregar a página.
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
                    "Monitoramento, descoberta automática, agentes, integração com GLPI ou Zabbix, redes, integrações entre sistemas, mapa de dependências, notificações e anexos ainda não estão disponíveis.",
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

          <Manual.Section id="itp-manual-services">
            <Manual.Eyebrow>Serviços e aplicações</Manual.Eyebrow>
            <h2>Cadastrar serviços e aplicações</h2>
            <Manual.Concepts
              items={[
                { term: "Aplicação de negócio", meaning: SERVICE_KIND_LABEL_HELP.business_application },
                { term: "Serviço de plataforma", meaning: SERVICE_KIND_LABEL_HELP.platform_service },
                {
                  term: "Instância em execução",
                  meaning:
                    "É o vínculo do serviço com um servidor: informa como ele roda ali (container, processo, serviço do sistema). Um container não é, por si só, uma aplicação.",
                },
              ]}
            />
            <Manual.GuideTable
              rows={[
                {
                  want: "Cadastrar um serviço",
                  where: "Serviços",
                  how: "«Cadastrar serviço», informe natureza, tipo, ambiente, criticidade e responsável e salve.",
                },
                {
                  want: "Encontrar um serviço",
                  where: "Serviços",
                  how: "Busque por nome ou tecnologia e filtre por natureza, unidade, ambiente e criticidade.",
                },
                {
                  want: "Tirar do inventário ativo",
                  where: "Detalhe do serviço",
                  how: "«Arquivar». Os vínculos e o histórico são preservados; o cadastro fica somente para consulta até ser restaurado.",
                },
              ]}
            />
            <Manual.Scope>
              O nome do serviço é único por unidade e ambiente. Nenhum serviço é criado automaticamente: o inventário
              começa vazio e é preenchido pela equipe de TI.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-databases">
            <Manual.Eyebrow>Bancos de dados</Manual.Eyebrow>
            <h2>Inventariar instâncias de bancos de dados</h2>
            <Manual.GuideTable
              rows={[
                {
                  want: "Cadastrar uma instância",
                  where: "Bancos de dados ou detalhe do servidor",
                  how: "«Cadastrar instância», escolha o SGBD e o servidor hospedeiro, informe criticidade e responsável.",
                },
                {
                  want: "Ver o que roda em um servidor",
                  where: "Detalhe do servidor",
                  how: "Seção «Bancos de dados associados».",
                },
                {
                  want: "Mudar o servidor hospedeiro",
                  where: "Detalhe da instância",
                  how: "«Editar» e escolha outro servidor ativo. A mudança aparece no histórico dos dois servidores.",
                },
              ]}
            />
            <Manual.Scope>
              O inventário é descritivo: nunca informe usuários, senhas, tokens ou strings de conexão. O portal recusa
              textos que pareçam conter credenciais e não se conecta aos bancos cadastrados. O nome da instância é único
              por servidor.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-links">
            <Manual.Eyebrow>Vínculos</Manual.Eyebrow>
            <h2>Ligar serviços, servidores e bancos</h2>
            <Manual.GuideTable
              rows={[
                {
                  want: "Dizer onde um serviço executa",
                  where: "Detalhe do serviço ou do servidor",
                  how: "«Vincular servidor» ou «Vincular serviço». Um serviço pode estar em vários servidores.",
                },
                {
                  want: "Dizer que um serviço usa um banco",
                  where: "Detalhe do serviço ou da instância de banco",
                  how: "«Vincular banco» ou «Vincular serviço».",
                },
                {
                  want: "Desfazer um vínculo",
                  where: "Tabela de vínculos",
                  how: "«Remover vínculo» e confirme. Só a associação é removida; os cadastros continuam existindo.",
                },
              ]}
            />
            <Manual.Scope>
              Cada vínculo criado ou removido fica registrado, com autor e data, no histórico dos dois lados. Só é possível
              vincular cadastros ativos; vínculos de cadastros arquivados permanecem visíveis para consulta.
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
                {
                  term: "Ver serviços e aplicações",
                  meaning: "Consultar serviços, onde executam e o histórico. Exige também ver servidores.",
                },
                {
                  term: "Gerenciar serviços e aplicações",
                  meaning: "Cadastrar, editar, arquivar e restaurar serviços e vincular ou desvincular servidores.",
                },
                {
                  term: "Ver bancos de dados",
                  meaning:
                    "Consultar instâncias de banco e o histórico. Ver quais serviços usam cada banco exige também ver serviços.",
                },
                {
                  term: "Gerenciar bancos de dados",
                  meaning:
                    "Cadastrar, editar, arquivar e restaurar instâncias e vincular ou desvincular serviços consumidores.",
                },
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
                {
                  q: "Remover um vínculo apaga o serviço ou o servidor?",
                  a: "Não. Apenas a associação é desfeita, e a remoção fica no histórico. Para tirar um cadastro do inventário ativo, use «Arquivar».",
                },
                {
                  q: "Por que não consigo vincular um servidor ou serviço?",
                  a: "Só cadastros ativos podem receber vínculos, e o mesmo par não pode ser vinculado duas vezes. Restaure o cadastro arquivado, se for o caso.",
                },
                {
                  q: "Posso guardar a senha do banco no portal?",
                  a: "Não. Registre apenas onde a credencial está guardada no cofre corporativo.",
                },
              ]}
            />
          </Manual.Section>
        </Manual.Layout>
      </Manual.Frame>
    </>
  );
}
