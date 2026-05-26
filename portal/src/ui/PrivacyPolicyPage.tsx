import { useContext, useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { FileText, ChevronLeft, Loader2 } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { AuthContext } from "../state/AuthContext";
import { ApiClient } from "../data/apiClient";
import { CoreApi, type PrivacyInfo } from "../data/coreApi";

import "./PrivacyPolicyPage.css";

const fadeUp = {
  hidden: { opacity: 0, y: 10 },
  show: (i = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.22, delay: 0.04 * i },
  }),
};

export const PrivacyPolicyPage = () => {
  const navigate = useNavigate();
  const { getAccessToken } = useContext(AuthContext);

  const apiRef = useRef<CoreApi | null>(null);
  if (!apiRef.current) {
    apiRef.current = new CoreApi(new ApiClient("", getAccessToken));
  }

  const [privacy, setPrivacy] = useState<PrivacyInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    apiRef.current!.getPrivacyInfo()
      .then((data) => { if (!cancelled) setPrivacy(data); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, []);

  const dpoName = privacy?.dpo?.name || "Encarregado de Proteção de Dados";
  const dpoEmail = privacy?.dpo?.email || "dpo@empresa.com.br";

  if (loading) {
    return (
      <div className="privacy-policy-page" style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
        <Loader2 className="spin" size={28} />
      </div>
    );
  }

  return (
    <div className="privacy-policy-page">
      <motion.div
        className="privacy-policy-page__header"
        initial="hidden"
        animate="show"
        variants={fadeUp}
      >
        <button
          className="privacy-policy-page__back"
          onClick={() => navigate(-1)}
          type="button"
        >
          <ChevronLeft size={18} />
          Voltar
        </button>

        <div className="privacy-policy-page__title-row">
          <FileText size={28} />
          <div>
            <h1>Política de Privacidade</h1>
            <p>Última atualização: Janeiro de 2026</p>
          </div>
        </div>
      </motion.div>

      <motion.article
        className="privacy-policy-page__content"
        initial="hidden"
        animate="show"
        variants={fadeUp}
        custom={1}
      >
        <section className="privacy-policy-page__section">
          <h2>1. Controlador dos Dados e Encarregado (DPO)</h2>
          <p>
            O controlador dos dados pessoais tratados nesta plataforma é a{" "}
            <strong>DELPI Energia &amp; Conectividade</strong>.
          </p>
          <p>
            O Encarregado de Proteção de Dados (DPO),{" "}
            <strong>{dpoName}</strong>, pode ser contatado pelo e-mail{" "}
            <strong>{dpoEmail}</strong> para esclarecimentos sobre o tratamento
            de dados pessoais ou exercício de direitos previstos na LGPD.
          </p>
        </section>

        <section className="privacy-policy-page__section">
          <h2>2. Dados Coletados e Finalidades</h2>
          <p>
            Coletamos e tratamos os seguintes dados pessoais, de acordo com as
            finalidades específicas:
          </p>
          <table className="privacy-policy-page__table">
            <thead>
              <tr>
                <th>Categoria de Dados</th>
                <th>Finalidade</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Nome completo, e-mail corporativo</td>
                <td>Identificação e autenticação no sistema</td>
              </tr>
              <tr>
                <td>Cargo, departamento, filial</td>
                <td>Personalização de acesso e controle de permissões (RBAC)</td>
              </tr>
              <tr>
                <td>Data de nascimento</td>
                <td>Notificações de aniversário e relatórios de RH (quando habilitado)</td>
              </tr>
              <tr>
                <td>Dados de navegação (logs de acesso)</td>
                <td>Auditoria de segurança e melhoria do sistema</td>
              </tr>
              <tr>
                <td>Preferências e consentimentos</td>
                <td>Personalização da experiência e conformidade legal</td>
              </tr>
              <tr>
                <td>Histórico de interações com IA</td>
                <td>Melhoria do assistente e suporte ao usuário</td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="privacy-policy-page__section">
          <h2>3. Base Legal para o Tratamento</h2>
          <p>
            O tratamento dos dados pessoais é realizado com fundamento nas seguintes
            bases legais previstas na Lei nº 13.709/2018 (LGPD):
          </p>
          <ul>
            <li>
              <strong>Execução de contrato (Art. 7º, V):</strong> tratamento necessário
              para a prestação dos serviços contratados, incluindo autenticação, controle
              de acesso e funcionalidades da plataforma.
            </li>
            <li>
              <strong>Legítimo interesse (Art. 7º, IX):</strong> auditoria de segurança,
              prevenção a fraudes, melhoria contínua dos serviços e análise de uso
              agregado da plataforma.
            </li>
            <li>
              <strong>Consentimento (Art. 7º, I):</strong> para finalidades opcionais
              como notificações personalizadas, compartilhamento de dados com parceiros
              e funcionalidades experimentais. O consentimento pode ser revogado a
              qualquer momento na seção "Privacidade e Dados" do portal.
            </li>
            <li>
              <strong>Cumprimento de obrigação legal (Art. 7º, II):</strong> retenção
              de dados exigida por legislação trabalhista, tributária ou regulatória.
            </li>
          </ul>
        </section>

        <section className="privacy-policy-page__section">
          <h2>4. Compartilhamento de Dados</h2>
          <p>
            Os dados pessoais podem ser compartilhados nas seguintes situações:
          </p>
          <ul>
            <li>
              <strong>Prestadores de serviço:</strong> provedores de infraestrutura
              (hospedagem, banco de dados) que atuam como operadores sob contrato e
              obrigações de confidencialidade.
            </li>
            <li>
              <strong>Autoridades competentes:</strong> quando exigido por ordem
              judicial, requisição legal ou para cumprimento de obrigação regulatória.
            </li>
            <li>
              <strong>Integrações autorizadas:</strong> sistemas internos da
              organização (ERP, RH) necessários para o funcionamento da plataforma,
              sempre respeitando o princípio da minimização.
            </li>
          </ul>
          <p>
            Não comercializamos, alugamos ou cedemos dados pessoais a terceiros para
            fins de marketing ou publicidade.
          </p>
        </section>

        <section className="privacy-policy-page__section">
          <h2>5. Direitos do Titular</h2>
          <p>
            Conforme o Art. 18 da LGPD, você possui os seguintes direitos sobre
            seus dados pessoais:
          </p>
          <ul>
            <li>Confirmação da existência de tratamento</li>
            <li>Acesso aos dados pessoais tratados</li>
            <li>Correção de dados incompletos, inexatos ou desatualizados</li>
            <li>Anonimização, bloqueio ou eliminação de dados desnecessários ou excessivos</li>
            <li>Portabilidade dos dados (exportação em formato estruturado)</li>
            <li>Eliminação dos dados tratados com base no consentimento</li>
            <li>Informação sobre compartilhamento com entidades públicas e privadas</li>
            <li>Informação sobre a possibilidade de não fornecer consentimento e consequências</li>
            <li>Revogação do consentimento a qualquer momento</li>
          </ul>
          <p>
            Para exercer seus direitos, acesse a seção "Privacidade e Dados" no
            menu do portal ou entre em contato com o DPO pelo e-mail{" "}
            <strong>{dpoEmail}</strong>. Responderemos no prazo legal de até
            15 dias.
          </p>
        </section>

        <section className="privacy-policy-page__section">
          <h2>6. Retenção de Dados</h2>
          <p>
            Os dados pessoais são armazenados pelo tempo necessário ao cumprimento
            das finalidades para as quais foram coletados, observando os seguintes
            critérios:
          </p>
          <table className="privacy-policy-page__table">
            <thead>
              <tr>
                <th>Tipo de Dado</th>
                <th>Prazo de Retenção</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Dados de conta ativa</td>
                <td>Enquanto a conta estiver ativa</td>
              </tr>
              <tr>
                <td>Logs de auditoria</td>
                <td>5 anos (obrigação legal)</td>
              </tr>
              <tr>
                <td>Histórico de chat com IA</td>
                <td>12 meses (ou até exclusão pelo usuário)</td>
              </tr>
              <tr>
                <td>Dados após desligamento</td>
                <td>Anonimizados em até 90 dias (exceto obrigações legais)</td>
              </tr>
              <tr>
                <td>Consentimentos revogados</td>
                <td>Registro mantido por 5 anos para comprovação</td>
              </tr>
            </tbody>
          </table>
          <p>
            Após o término do prazo de retenção, os dados são eliminados ou
            anonimizados de forma irreversível.
          </p>
        </section>

        <section className="privacy-policy-page__section">
          <h2>7. Cookies e Rastreamento</h2>
          <p>
            Esta plataforma utiliza os seguintes mecanismos de armazenamento local:
          </p>
          <ul>
            <li>
              <strong>Cookies de sessão:</strong> essenciais para manter sua
              autenticação ativa durante o uso. Não podem ser desabilitados sem
              perda de funcionalidade.
            </li>
            <li>
              <strong>Armazenamento local (localStorage):</strong> utilizado para
              salvar preferências de interface (tema, sidebar colapsada) e cache
              de dados não sensíveis para melhorar a performance.
            </li>
            <li>
              <strong>Tokens de autenticação:</strong> armazenados de forma segura
              para manter o acesso à plataforma sem necessidade de login repetido.
            </li>
          </ul>
          <p>
            Não utilizamos cookies de terceiros para fins de publicidade ou
            rastreamento comportamental entre sites.
          </p>
        </section>

        <section className="privacy-policy-page__section">
          <h2>8. Segurança dos Dados</h2>
          <p>
            Adotamos medidas técnicas e administrativas para proteger os dados
            pessoais contra acesso não autorizado, destruição, perda, alteração
            ou qualquer forma de tratamento inadequado, incluindo:
          </p>
          <ul>
            <li>Criptografia em trânsito (TLS/HTTPS)</li>
            <li>Controle de acesso baseado em papéis (RBAC)</li>
            <li>Autenticação via protocolo OpenID Connect (SSO)</li>
            <li>Registros de auditoria de acessos e ações</li>
            <li>Monitoramento contínuo de segurança</li>
            <li>Política de retenção e eliminação automatizada</li>
          </ul>
        </section>

        <section className="privacy-policy-page__section">
          <h2>9. Contato</h2>
          <p>
            Para dúvidas, solicitações ou reclamações relacionadas ao tratamento
            de dados pessoais, entre em contato:
          </p>
          <ul>
            <li>
              <strong>Encarregado (DPO):</strong> {dpoName} — {dpoEmail}
            </li>
            <li>
              <strong>Controlador:</strong> DELPI Energia &amp; Conectividade
            </li>
          </ul>
          <p>
            Caso não obtenha resposta satisfatória, você pode apresentar
            reclamação à Autoridade Nacional de Proteção de Dados (ANPD).
          </p>
        </section>
      </motion.article>
    </div>
  );
};
