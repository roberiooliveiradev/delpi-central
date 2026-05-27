import re
import unicodedata


# Ordem importa: padrões mais específicos primeiro.
_TYPO_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    # Fornecedores / clientes
    (r"\bforncedor(es)?\b", r"fornecedor\1"),
    (r"\bfornecedore(s)?\b", r"fornecedor\1"),
    (r"\bfornecdor(es)?\b", r"fornecedor\1"),
    (r"\bforneçedor(es)?\b", r"fornecedor\1"),
    (r"\bfornecedr(es)?\b", r"fornecedor\1"),
    (r"\bclinte(s)?\b", r"cliente\1"),
    (r"\bcleinte(s)?\b", r"cliente\1"),
    (r"\bcliente(s)?\b", r"cliente\1"),
    # Estoque
    (r"\bestoq(u|ue)?\b", r"estoque"),
    (r"\bestq\b", r"estoque"),
    (r"\bestoquee\b", r"estoque"),
    (r"\bestok\b", r"estoque"),
    (r"\bsaldo\b", r"saldo"),
    # Capacidades / perguntas ao assistente
    (r"\bcoonsegue\b", r"consegue"),
    (r"\bconsigue\b", r"consegue"),
    (r"\bconsege\b", r"consegue"),
    # Produto
    (r"\bprodt?\b", r"produto"),
    (r"\bprduto\b", r"produto"),
    (r"\bprouto\b", r"produto"),
    (r"\bproduot\b", r"produto"),
    (r"\bitem\b", r"item"),
    (r"\biten\b", r"item"),
    # Descrição / cadastro
    (r"\bdescriçao\b", r"descricao"),
    (r"\bdescricao\b", r"descricao"),
    (r"\bdescrção\b", r"descricao"),
    (r"\bdescrição\b", r"descricao"),
    (r"\bcadastro\b", r"cadastro"),
    (r"\bcadastr\b", r"cadastro"),
    # Preço / custo
    (r"\bpreço\b", r"preco"),
    (r"\bpreco\b", r"preco"),
    (r"\bpreç\b", r"preco"),
    (r"\bprço\b", r"preco"),
    (r"\bquanto custa\b", r"quanto custa"),
    (r"\bquanto cust\b", r"quanto custa"),
    (r"\bcusto\b", r"custo"),
    (r"\bcust\b", r"custo"),
    (r"\btabela de preco\b", r"tabela de preco"),
    (r"\btabela de preço\b", r"tabela de preco"),
    # Estrutura / BOM
    (r"\bestrutur(a)?\b", r"estrutura"),
    (r"\bestrutur\b", r"estrutura"),
    (r"\bcomposiçao\b", r"composicao"),
    (r"\bcomposicao\b", r"composicao"),
    (r"\bcomponentes\b", r"componentes"),
    (r"\bcomponente\b", r"componente"),
    (r"\bbom\b", r"bom"),
    # Parents / onde é usado
    (r"\bpais\b", r"pais"),
    (r"\bpai\b", r"pai"),
    (r"\bwhere used\b", r"where used"),
    (r"\bonde e usado\b", r"onde e usado"),
    (r"\bonde é usado\b", r"onde e usado"),
    # Roteiro / inspeção
    (r"\brotiero\b", r"roteiro"),
    (r"\broteir\b", r"roteiro"),
    (r"\broteiro\b", r"roteiro"),
    (r"\binspeçao\b", r"inspecao"),
    (r"\binspecao\b", r"inspecao"),
    (r"\binspeção\b", r"inspecao"),
    (r"\binspeç\b", r"inspecao"),
    # Movimentações / notas
    (r"\bmovimentaçao\b", r"movimentacao"),
    (r"\bmovimentaçoes\b", r"movimentacoes"),
    (r"\bmovimentacao\b", r"movimentacao"),
    (r"\bmovimentacoes\b", r"movimentacoes"),
    (r"\bmovimenta\b", r"movimentacao"),
    (r"\bnota fiscal\b", r"nota fiscal"),
    (r"\bnfe\b", r"nfe"),
    (r"\bnota de entrada\b", r"nota de entrada"),
    (r"\bnota de saida\b", r"nota de saida"),
    (r"\bnota de saída\b", r"nota de saida"),
    # Compras / vendas (não usar \bcompr\b — quebra «comparar», «compare», «comprare»)
    (r"\bcompras\b", r"compras"),
    (r"\bcompra\b", r"compra"),
    (r"\bcomprare\b", r"compare"),
    (r"\bvendas\b", r"vendas"),
    (r"\bvenda\b", r"venda"),
    (r"\bfaturamento\b", r"faturamento"),
    (r"\bfaturam\b", r"faturamento"),
    # LMP / engenharia
    (r"\blmps\b", r"lmps"),
    (r"\blmp\b", r"lmp"),
    (r"\bordem de venda\b", r"ordem de venda"),
    (r"\bov\b", r"ov"),
    (r"\bengenharia\b", r"engenharia"),
    # Indicadores suprimentos
    (r"\bgiro de estoque\b", r"giro de estoque"),
    (r"\bgiro\b", r"giro"),
    (r"\bcpv\b", r"cpv"),
    (r"\botd\b", r"otd"),
    (r"\bvalor de estoque\b", r"valor de estoque"),
    (r"\bvalor total de estoque\b", r"valor total de estoque"),
    # Relatório / consulta
    (r"\brelatório\b", r"relatorio"),
    (r"\brelatorio\b", r"relatorio"),
    (r"\brelator\b", r"relatorio"),
    (r"\bconsulta\b", r"consulta"),
    (r"\bconsultar\b", r"consultar"),
    (r"\bbuscar\b", r"buscar"),
    (r"\bbusque\b", r"busque"),
    (r"\bpesquisar\b", r"pesquisar"),
    (r"\bpesquise\b", r"pesquise"),
    (r"\blistar\b", r"listar"),
    (r"\bliste\b", r"liste"),
    (r"\bmostrar\b", r"mostrar"),
    (r"\bmostre\b", r"mostre"),
    # Capacidades / ajuda
    (r"\bcapacidades\b", r"capacidades"),
    (r"\bfuncionalidades\b", r"funcionalidades"),
    (r"\bcomandos\b", r"comandos"),
    (r"\bajuda\b", r"ajuda"),
    # Abreviações comuns
    (r"\bvc\b", r"voce"),
    (r"\btb\b", r"tambem"),
    (r"\bqdo\b", r"quando"),
    (r"\bqd\b", r"quando"),
    (r"\bqnt\b", r"quantidade"),
    (r"\bqtd\b", r"quantidade"),
    (r"\bqt\b", r"quantidade"),
    (r"\bnum\b", r"numero"),
    (r"\bnº\b", r"numero"),
    (r"\bcod\b", r"codigo"),
    (r"\bcód\b", r"codigo"),
)

_TYPO_PATTERNS = [
    (re.compile(pattern, re.IGNORECASE), repl) for pattern, repl in _TYPO_REPLACEMENTS
]


class ChatMessageNormalizationService:
    """Normaliza mensagens do usuário para matching de intenção (acentos, typos)."""

    @staticmethod
    def strip_accents(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", str(value or "").strip().lower())
        return "".join(char for char in normalized if not unicodedata.combining(char))

    @classmethod
    def normalize_for_matching(cls, message: str) -> str:
        text = cls.strip_accents(message)
        text = re.sub(r"\s+", " ", text).strip()

        for pattern, replacement in _TYPO_PATTERNS:
            text = pattern.sub(replacement, text)

        return text

    @classmethod
    def contains_any(cls, message: str, terms: tuple[str, ...] | list[str]) -> bool:
        normalized = cls.normalize_for_matching(message)
        return any(cls.strip_accents(term) in normalized for term in terms)

    @classmethod
    def expand_query_terms(cls, message: str) -> list[str]:
        """Retorna a mensagem normalizada e variantes úteis para busca semântica."""
        base = cls.normalize_for_matching(message)
        variants = {base}
        if base:
            variants.add(base.replace("?", "").strip())
        return [item for item in variants if item]
