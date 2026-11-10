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
  { id: "networks", label: "Redes" },
  { id: "integrations", label: "Integrações" },
  { id: "relationships", label: "Tipos de relação" },
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
              Inventário manual da infraestrutura DELPI: servidores, serviços e aplicações, instâncias de bancos de dados,
              redes, integrações e os relacionamentos entre eles, com notas técnicas, planos de ação e histórico auditado.
              Todas as informações são gravadas no banco do portal e ficam disponíveis após recarregar a página.
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
                    "Monitoramento, descoberta automática, varredura de rede, agentes, integração com GLPI ou Zabbix, mapa visual de dependências, análise de impacto, notificações e anexos ainda não estão disponíveis.",
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

          <Manual.Section id="itp-manual-networks">
            <Manual.Eyebrow>Redes</Manual.Eyebrow>
            <h2>Cadastrar redes e conectar servidores</h2>
            <Manual.GuideTable
              rows={[
                {
                  want: "Cadastrar uma rede",
                  where: "Redes",
                  how: "«Cadastrar rede», informe nome, CIDR (ex.: 10.0.1.0/24), unidade, ambiente, escopo, criticidade e responsável.",
                },
                {
                  want: "Dizer que um servidor está em uma rede",
                  where: "Detalhe do servidor (seção Redes) ou da rede",
                  how: "«Vincular rede» ou «Vincular servidor». O IP informado precisa estar dentro do CIDR.",
                },
                {
                  want: "Ver os servidores de uma rede",
                  where: "Detalhe da rede",
                  how: "Seção «Servidores conectados».",
                },
              ]}
            />
            <Manual.Concepts
              items={[
                {
                  term: "Rede corporativa",
                  meaning:
                    "Sub-rede da infraestrutura, como a VLAN dos servidores. O mesmo CIDR não pode ser cadastrado duas vezes na mesma unidade.",
                },
                {
                  term: "Rede interna de containers",
                  meaning:
                    "Rede criada pelo Docker ou outro runtime. Só cadastre quando confirmada, e sempre com este escopo — ela não vira rede corporativa.",
                },
              ]}
            />
            <Manual.Scope>
              O portal valida o formato do CIDR, do gateway e dos IPs, mas não faz varredura nem descoberta automática: as
              redes são cadastradas pela equipe de TI. Alterar o CIDR é recusado se algum servidor vinculado ficar com IP fora
              da nova faixa.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-integrations">
            <Manual.Eyebrow>Integrações</Manual.Eyebrow>
            <h2>Registrar integrações entre sistemas</h2>
            <Manual.GuideTable
              rows={[
                {
                  want: "Cadastrar uma integração",
                  where: "Integrações ou detalhe do serviço",
                  how: "«Cadastrar integração», escolha a origem e o destino, o protocolo, a direção, a criticidade e o responsável.",
                },
                {
                  want: "Registrar um sistema de fora",
                  where: "Formulário da integração",
                  how: "Em uma das pontas, escolha «Sistema externo» e informe o nome (ex.: SEFAZ). A outra ponta precisa ser um serviço cadastrado.",
                },
                {
                  want: "Ver as integrações de um servidor",
                  where: "Detalhe do servidor",
                  how: "Seção «Integrações dos serviços hospedados», calculada a partir dos serviços que executam ali.",
                },
              ]}
            />
            <Manual.Scope>
              Registre apenas integrações que existem de fato — não cadastre aplicações fictícias. Nunca informe
              credenciais, tokens, URLs com senha ou exemplos de payload. O uso de bancos de dados continua sendo
              registrado no vínculo serviço–banco.
            </Manual.Scope>
          </Manual.Section>

          <Manual.Section id="itp-manual-relationships">
            <Manual.Eyebrow>Tipos de relação</Manual.Eyebrow>
            <h2>Diferença entre hospedagem, conectividade, consumo e dependência</h2>
            <Manual.Concepts
              items={[
                { term: "Hospedagem", meaning: "Onde o serviço executa: vínculo serviço–servidor." },
                { term: "Conectividade", meaning: "Em quais redes o servidor está: vínculo servidor–rede." },
                {
                  term: "Consumo",
                  meaning: "Troca de dados: vínculo serviço–banco ou integração entre serviços ou com sistemas externos.",
                },
                {
                  term: "Dependência operacional",
                  meaning:
                    "Um serviço deixa de funcionar sem o outro. Registrada no detalhe do serviço, seção «Dependências operacionais». O portal nunca presume dependências.",
                },
              ]}
            />
            <Manual.Scope>
              Todas as relações aparecem nas páginas dos dois lados e podem ser removidas sem apagar os cadastros. O portal
              recusa relações com cadastros inexistentes ou arquivados, relações repetidas e um recurso relacionado a ele
              mesmo. O mapa visual e a análise de impacto chegam em uma etapa futura.
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
              requisição. Ao gravar, o servidor confere suas permissões atuais na hora: uma permissão retirada deixa de
              valer imediatamente. Botões que você não pode usar não aparecem.
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
                {
                  term: "Ver redes",
                  meaning: "Consultar redes, os servidores conectados e o histórico. Exige também ver servidores.",
                },
                {
                  term: "Gerenciar redes",
                  meaning: "Cadastrar, editar, arquivar e restaurar redes e vincular ou desvincular servidores.",
                },
                {
                  term: "Ver integrações",
                  meaning: "Consultar integrações e o histórico. Exige também ver servidores e ver serviços.",
                },
                {
                  term: "Gerenciar integrações",
                  meaning: "Cadastrar, editar, arquivar e restaurar integrações.",
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
                  q: "Por que o CIDR foi recusado?",
                  a: "Informe o endereço da rede com o prefixo, como 10.0.1.0/24. Um endereço de host (10.0.1.5/24) não é aceito como CIDR.",
                },
                {
                  q: "Posso cadastrar uma integração entre dois sistemas externos?",
                  a: "Não. Pelo menos uma ponta precisa ser um serviço cadastrado no Portal de TI.",
                },
                {
                  q: "Quem pode registrar dependências operacionais?",
                  a: "Quem gerencia serviços e aplicações. A dependência é registrada no detalhe do serviço.",
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
