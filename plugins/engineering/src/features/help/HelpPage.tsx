import { BookOpen } from "lucide-react";

import {
  buildEngineeringPath,
  navigateEngineeringView,
} from "../../app/engineeringRoutes";
import {
  EngineeringActionButton,
  EngineeringPageHero,
  EngineeringPagePath,
  EngineeringSectionCard,
  EngineeringUserManual,
} from "../../ui/engineeringUi";

type HelpPageProps = {
  basePath: string;
};

function scrollToSection(id: string) {
  const el = document.getElementById(`manual-${id}`);
  el?.scrollIntoView({ behavior: "smooth", block: "start" });
}

/** Ajuda — manual de uso do Portal Engenharia no componente oficial
 * `UserManual` do plugin-ui. Documenta somente o que está implementado:
 * EVA e colaboração aparecem como limitações/capacidades futuras. */
export function HelpPage({ basePath }: HelpPageProps) {
  const Manual = EngineeringUserManual;
  const homeHref = buildEngineeringPath("home", basePath);

  const sections = [
    { id: "start", title: "Página Início" },
    { id: "overview", title: "Visão geral" },
    { id: "nonconformities", title: "Não conformidades" },
    { id: "paths", title: "Caminhos e funcionalidades" },
    { id: "search", title: "Busca e favoritos" },
    { id: "states", title: "Estados das informações" },
    { id: "permissions", title: "Permissões" },
    { id: "limits", title: "Limitações atuais" },
  ];

  return (
    <Manual.Frame className="engineering-manual">
      <EngineeringPagePath
        back={{
          label: "Início",
          href: homeHref,
          onNavigate: (event) => {
            event.preventDefault();
            navigateEngineeringView("home", { basePath });
          },
        }}
        items={[]}
        current="Ajuda"
      />

      <EngineeringPageHero
        eyebrow={
          <Manual.Eyebrow>
            <BookOpen size={16} strokeWidth={1.75} aria-hidden="true" />
            Ajuda
          </Manual.Eyebrow>
        }
        title="Ajuda do Portal Engenharia"
        description="Como usar a sua área de trabalho, os caminhos, a busca e os favoritos."
        actions={
          <EngineeringActionButton
            variant="ghost"
            onClick={() => navigateEngineeringView("home", { basePath })}
          >
            Voltar ao Início
          </EngineeringActionButton>
        }
      />

      <Manual.Scope>
        O Portal Engenharia reúne sua área de trabalho na Minha DELPI.
        Ele mostra somente informações que você tem permissão de ver —
        as permissões são controladas pela plataforma, não pelo portal.
      </Manual.Scope>

      <Manual.Layout
        title="Nesta página"
        aria-label="Sumário da ajuda"
        items={sections.map((section) => ({
          id: section.id,
          label: section.title,
          onSelect: () => scrollToSection(section.id),
        }))}
      >
        <Manual.Section id="manual-start">
          <EngineeringSectionCard title="Página Início">
            <Manual.Concepts
              items={[
                {
                  term: "Saudação",
                  meaning:
                    "No topo, o portal apresenta uma saudação com seu nome e um resumo das suas fontes autorizadas: tarefas, solicitações e LMPs.",
                },
                {
                  term: "Eventos e interações",
                  meaning:
                    "Lista os itens que pedem sua atenção — tarefas atribuídas e solicitações abertas — com atalho para abrir cada um no aplicativo oficial.",
                },
                {
                  term: "Caminhos e funcionalidades",
                  meaning:
                    "Catálogo dos acessos oficiais de Engenharia, organizados por categoria: Trabalho, Análises e Suporte.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-overview">
          <EngineeringSectionCard title="Visão geral">
            <Manual.Concepts
              items={[
                {
                  term: "Indicadores",
                  meaning:
                    "Seis indicadores oficiais da Engenharia: % LMP dentro do prazo, lead time médio e total de propostas (LMP); ganhos brutos, soluções implementadas e ROI médio (TRANSFORMA+). Metas e Nota IDD aparecem somente nos dois indicadores estratégicos (% LMP dentro do prazo e ganhos brutos), quando os sistemas oficiais as fornecem — os demais cards exibem apenas valor, período e escopo.",
                },
                {
                  term: "Filtros",
                  meaning:
                    "Período rápido, datas inicial e final, competência e unidade. Mudar a competência ajusta as datas do mês; datas que cruzam meses limpam a competência. Os filtros ficam refletidos no endereço da página.",
                },
                {
                  term: "Unidade e escopo",
                  meaning:
                    "Selecionar uma unidade filtra os indicadores operacionais que suportam esse recorte. Indicadores estratégicos consolidados continuam consolidados — o escopo de cada cartão aparece abaixo do valor.",
                },
                {
                  term: "Estados",
                  meaning:
                    "Quando uma fonte falha ou não é autorizada, o cartão informa o estado real — os demais indicadores continuam exibidos. Nenhum valor é substituído por zero.",
                },
                {
                  term: "Aprofundamento",
                  meaning:
                    "O atalho para o Portal TRANSFORMA+ aparece somente quando você tem permissão. O acompanhamento detalhado de LMPs está disponível em LMPs — filtros, indicadores, gráficos, tabela e detalhe por proposta.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-nonconformities">
          <EngineeringSectionCard title="Não conformidades">
            <Manual.Concepts
              items={[
                {
                  term: "Listagem",
                  meaning:
                    "Registros oficiais da Engineering API com busca por status, OV, LMP, cliente, produto, problema identificado e período de ocorrência. Toque em uma linha para abrir o detalhe.",
                },
                {
                  term: "Produtos na listagem",
                  meaning:
                    "A coluna Produtos associados mostra os itens vinculados a cada NC — os primeiros aparecem na célula e o contador indica os demais; a lista completa fica no detalhe.",
                },
                {
                  term: "Indicadores",
                  meaning:
                    "Dias consecutivos sem não conformidade e recorde histórico aparecem dentro do cabeçalho da página — valores oficiais calculados pela Engineering API.",
                },
                {
                  term: "Ajuda nos rótulos",
                  meaning:
                    "Passe o mouse, toque ou navegue com Tab sobre o texto de qualquer rótulo para ver a explicação do campo — não há ícone de ajuda separado.",
                },
                {
                  term: "Cadastro e edição",
                  meaning:
                    "Crie ou edite registros pelo botão Nova não conformidade ou Editar. Toda alteração grava histórico de auditoria com o seu usuário.",
                },
                {
                  term: "Histórico",
                  meaning:
                    "Linha do tempo de auditoria do registro: criação e cada atualização com autor, data e campos alterados.",
                },
                {
                  term: "Contexto da proposta",
                  meaning:
                    "No detalhe, a situação da OV vinculada e a estrutura dos produtos associados chegam dos fatos oficiais TOTVS via Engineering API — quando uma fonte está indisponível, o estado real aparece no cartão.",
                },
                {
                  term: "Exportar e importar",
                  meaning:
                    "Exportar baixa o acervo em JSON. Importar substitui todo o acervo e exige dry-run e confirmação explícita — a mesma semântica do registro legado.",
                },
                {
                  term: "Registro legado",
                  meaning:
                    "O aplicativo legado de não conformidades permanece operacional durante a migração governada — o acesso fica disponível na própria área de LMPs.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-paths">
          <EngineeringSectionCard title="Caminhos e funcionalidades">
            <p>
              Cada cartão agrupa funcionalidades de uma categoria. Itens
              marcados como "Em breve" representam capacidades previstas e
              ainda não executáveis — eles não abrem nenhuma página.
            </p>
            <p>
              Os destinos externos (como Minhas solicitações) abrem os
              aplicativos oficiais correspondentes. Funcionalidades
              internas, como LMPs, abrem páginas do próprio Portal. Se
              você não tiver a permissão exigida, o atalho não aparece.
            </p>
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-search">
          <EngineeringSectionCard title="Busca e favoritos">
            <Manual.Concepts
              items={[
                {
                  term: "Busca",
                  meaning:
                    "Use o campo na barra superior (ou Ctrl+K) para pesquisar funcionalidades por nome, descrição ou palavra-chave.",
                },
                {
                  term: "Favoritos",
                  meaning:
                    "Toque na estrela de um caminho para fixá-lo na barra superior. Favoritos ficam salvos neste navegador, na sua conta — eles não são compartilhados entre dispositivos.",
                },
                {
                  term: "Últimos acessos",
                  meaning:
                    "Os caminhos abertos recentemente aparecem em destaque para retomada rápida.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-states">
          <EngineeringSectionCard title="Estados das informações">
            <Manual.Concepts
              items={[
                {
                  term: "Disponível",
                  meaning: "A fonte oficial respondeu e há itens para mostrar.",
                },
                {
                  term: "Sem itens",
                  meaning:
                    "A fonte respondeu e, no momento, não há pendências — não é um erro.",
                },
                {
                  term: "Indisponível",
                  meaning:
                    "A fonte oficial falhou ou está fora do ar. Tente atualizar; as demais partes da página continuam funcionando.",
                },
                {
                  term: "Acesso negado",
                  meaning:
                    "Você não tem permissão para ver essa informação. Se precisar, solicite a permissão ao administrador.",
                },
                {
                  term: "Capacidade futura",
                  meaning:
                    "Funcionalidade prevista no portal que ainda não foi liberada.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-permissions">
          <EngineeringSectionCard title="Permissões">
            <p>
              As permissões são definidas e concedidas pela plataforma Minha
              DELPI (Core). O Portal Engenharia apenas apresenta o que o seu
              acesso autoriza — não existe permissão especial criada pelo
              portal.
            </p>
          </EngineeringSectionCard>
        </Manual.Section>

        <Manual.Section id="manual-limits">
          <EngineeringSectionCard title="Limitações atuais">
            <Manual.Concepts
              items={[
                {
                  term: "Assistente EVA",
                  meaning:
                    "Capacidade de inteligência assistiva prevista para uma próxima etapa — ainda não está operacional.",
                },
                {
                  term: "Colaboração",
                  meaning:
                    "Espaços de trabalho compartilhados ainda não possuem fonte oficial neste portal.",
                },
                {
                  term: "Favoritos e últimos acessos",
                  meaning:
                    "Ficam salvos localmente neste navegador e não são sincronizados entre dispositivos.",
                },
              ]}
            />
          </EngineeringSectionCard>
        </Manual.Section>
      </Manual.Layout>
    </Manual.Frame>
  );
}
