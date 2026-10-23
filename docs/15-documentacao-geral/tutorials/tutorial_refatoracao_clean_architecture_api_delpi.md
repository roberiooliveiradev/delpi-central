# Manual Oficial de Refatoração Completa para Clean Architecture
## Projeto: api-delpi

---

# 1. Propósito deste documento

Este manual existe para servir como **guia definitivo de refatoração da api-delpi** para um modelo de **Clean Architecture real**, completo e consistente.

Ele foi escrito com um objetivo muito específico:

> mostrar, de forma detalhada, todos os arquivos, conceitos, responsabilidades e etapas necessárias para refatorar uma rota sem esquecer nenhuma peça arquitetural.

Este não é um resumo.
Este não é um guia superficial.
Este é um documento para ser usado como **playbook de execução**.

Ele explica:

- o que é Clean Architecture
- por que usar
- quando usar cada conceito
- como as camadas se relacionam
- quais arquivos compõem uma feature
- como refatorar cada tipo de rota
- como testar
- como evitar erros comuns
- como migrar sem quebrar o projeto

---

# 2. Problema que este manual resolve

APIs que crescem rápido costumam seguir um fluxo parecido com este:

```text
Route → Service → Repository
```

Esse modelo funciona no início, mas costuma degradar com o tempo.

Os sintomas aparecem assim:

- arquivos de service com centenas de linhas
- repositories fazendo mais do que acesso a dados
- rotas conhecendo detalhes demais
- dependências sendo criadas em qualquer lugar
- dificuldade de testar casos de uso isoladamente
- regra de negócio espalhada por múltiplas camadas

Quando isso acontece, o sistema passa a sofrer com:

- alto acoplamento
- baixa previsibilidade
- medo de refatorar
- duplicação de lógica
- testes frágeis
- manutenção lenta

A Clean Architecture existe para combater exatamente esses problemas.

---

# 3. O que é Clean Architecture

Clean Architecture é um modelo de organização de software que separa o sistema em camadas com responsabilidades muito claras.

A ideia central é simples:

> o núcleo do sistema deve conter a regra de negócio,
> e os detalhes técnicos devem ficar nas bordas.

Detalhes técnicos incluem:

- framework web
- banco de dados
- ORM
- arquivos Excel
- APIs externas
- TOTVS
- filas
- cache
- autenticação concreta

A regra de negócio não deve depender desses detalhes.

---

# 4. Regra central: direção das dependências

A principal regra da Clean Architecture é:

> dependências sempre apontam para dentro.

Em termos práticos:

```text
Interfaces / Infrastructure → Application → Domain
```

O que isso significa:

- `domain` não conhece ninguém
- `application` conhece o `domain`
- `infrastructure` conhece `application` e `domain`
- `interfaces` conhece `application`

O banco não manda no sistema.
O framework não manda no sistema.
A rota não manda no sistema.

O centro do sistema é o domínio e os casos de uso.

---

# 5. Benefícios concretos da Clean Architecture

Ao aplicar corretamente, você ganha:

## 5.1 Testabilidade

Você testa o caso de uso sem subir FastAPI, Flask, banco ou TOTVS.

## 5.2 Baixo acoplamento

Trocar SQL Server por outro mecanismo não obriga mudança no use case.

## 5.3 Evolução segura

A rota pode mudar sem quebrar a regra de negócio.

## 5.4 Responsabilidades claras

Cada arquivo tem um papel explícito.

## 5.5 Menos medo de mexer

Quando a arquitetura está clara, refatorar deixa de ser uma operação arriscada.

---

# 6. Conceitos principais que você precisa dominar

Esta seção explica os conceitos mais importantes da Clean Architecture e quando usar cada um.

---

## 6.1 Entity

Entity representa algo central do negócio.

Ela modela um conceito que existe independentemente de framework, HTTP ou banco.

Exemplos possíveis na api-delpi:

- Product
- ProductStructure
- Supplier
- Customer
- Pricing
- StockPosition

### Quando usar

Use entity quando o objeto representa uma coisa real do domínio.

### Quando não usar

Não use entity para payloads temporários de HTTP ou parâmetros de query string.

### Exemplo

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    code: str
    description: str
    group_code: Optional[str] = None
    unit: Optional[str] = None
    type: Optional[str] = None
```

A entity não deve saber:

- de banco
- de FastAPI
- de JSONResponse
- de SQL

---

## 6.2 Port

Port é uma abstração que define um contrato.

Em geral, na api-delpi, isso aparece como:

- porta de repositório
- porta de exporter
- porta de gateway externo

### Por que usar

Porque o use case deve depender de abstrações, não de implementações.

Isso é o princípio DIP.

### Exemplo

```python
from abc import ABC, abstractmethod
from typing import Optional


class ProductQueryRepositoryPort(ABC):

    @abstractmethod
    def get_product_by_code(self, code: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def search_products(
        self,
        code: Optional[str],
        group: Optional[str],
        description: Optional[str],
        page: int,
        page_size: int,
    ) -> dict:
        raise NotImplementedError
```

---

## 6.3 Repository

Repository é a implementação concreta que acessa os dados.

No seu projeto, normalmente ele vai falar com:

- TOTVS
- SQL Server
- tabelas Protheus

### O que ele faz

- monta consulta
- executa query
- retorna dados

### O que ele não deve fazer

- decidir fluxo de negócio
- saber de HTTP
- construir JSONResponse
- aplicar regras de autorização

### Exemplo

```python
class ProductRepository(ProductQueryRepositoryPort):

    def get_product_by_code(self, code: str) -> dict:
        sql = "SELECT B1_COD AS code, B1_DESC AS description FROM SB1010 WHERE B1_COD = ?"
        return self.execute_one(sql, (code,))
```

---

## 6.4 Use Case

Use case representa uma ação do sistema.

Exemplos:

- buscar um produto
- listar produtos
- consultar estrutura
- exportar estrutura
- montar análise consolidada

### Regra fundamental

Use case coordena a regra da aplicação.

Ele não conhece:

- banco concreto
- framework web
- JSONResponse
- Query do FastAPI

### Exemplo

```python
class GetProductUseCase:

    def __init__(self, repository: ProductQueryRepositoryPort):
        self._repository = repository

    def execute(self, code: str) -> Product:
        raw = self._repository.get_product_by_code(code)
        return Product(
            code=raw["code"],
            description=raw["description"],
            group_code=raw.get("group_code"),
        )
```

---

## 6.5 Composer

Composer é a camada que monta dependências.

Ele cria objetos concretos e os conecta.

### O que ele resolve

A pergunta:

> quem cria o repository e injeta no use case?

### Exemplo

```python
from app.application.use_cases.products.get_product_use_case import GetProductUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository


def build_get_product_use_case() -> GetProductUseCase:
    repository = ProductRepository()
    return GetProductUseCase(repository)
```

### Regra prática

Se existe injeção de dependência, o composer deve existir.

---

## 6.6 Controller / Route

A rota é a borda HTTP do sistema.

Ela deve fazer apenas:

- receber request
- validar parâmetros HTTP
- chamar o use case
- traduzir o retorno para resposta HTTP

### O que a rota não deve fazer

- abrir transação
- montar SQL
- instanciar repositório em massa
- decidir regra de negócio
- construir árvore de domínio

### Exemplo

```python
@router.get("/{code}")
def get_product_route(code: str):
    use_case = build_get_product_use_case()
    product = use_case.execute(code)
    return success_response(data={"product": product.__dict__})
```

---

## 6.7 DTO / Schema

DTOs e schemas servem para entrada e saída.

Eles não são entidades de domínio.

Use quando precisar:

- validar request
- serializar resposta
- transportar dados entre camadas

### Exemplo

```python
from pydantic import BaseModel
from typing import Optional


class SearchProductsRequest(BaseModel):
    code: Optional[str] = None
    group: Optional[str] = None
    description: Optional[str] = None
    page: int = 1
    page_size: int = 50
```

---

## 6.8 Exporter

Exporter é uma peça de infraestrutura usada quando um caso de uso gera um artefato.

Exemplos:

- Excel
- CSV
- PDF

Ele não deve morar dentro do use case.

O correto é:

```text
UseCase → Exporter
```

---

## 6.9 Unit of Work

Unit of Work controla transações.

Na api-delpi, muitas rotas são de leitura e não precisam disso.

Mas quando houver fluxo com várias escritas coordenadas, ele passa a ser importante.

### Quando usar

- múltiplos repositories de escrita
- persistência transacional
- necessidade de commit / rollback

### Quando não usar

- consultas simples
- consultas paginadas
- exportações somente leitura

---

# 7. Estrutura completa recomendada do projeto

Abaixo está uma estrutura detalhada e escalável para a api-delpi.

```text
app/
  domain/
    entities/
      product.py
      supplier.py
      stock_position.py
      pricing.py
      structure_node.py
    repositories/
      product_query_repository_port.py
      stock_query_repository_port.py
      pricing_query_repository_port.py
    services/
      # opcional: regras puras de domínio

  application/
    dto/
      products/
        search_products_request.py
        list_products_request.py
        structure_request.py
    use_cases/
      products/
        get_product_use_case.py
        list_products_use_case.py
        search_products_use_case.py
        search_products_by_description_use_case.py
        get_product_structure_use_case.py
        get_product_parents_use_case.py
        get_product_guide_use_case.py
        get_product_inspection_use_case.py
        get_product_stock_use_case.py
        get_product_suppliers_use_case.py
        get_product_customers_use_case.py
        get_product_purchases_use_case.py
        get_product_pricing_use_case.py
        get_sales_summary_use_case.py
        get_sales_open_orders_use_case.py
        get_sales_billing_use_case.py
        get_internal_movements_use_case.py
        export_structure_excel_use_case.py
        get_product_analyser_use_case.py

  infrastructure/
    persistence/
      totvs/
        product_repository.py
        stock_repository.py
        pricing_repository.py
    exporters/
      structure_excel_exporter.py
    mappers/
      product_mapper.py
      structure_mapper.py

  interfaces/
    http/
      routes/
        product_routes.py
      presenters/
        # opcional: formatação de resposta

  composition/
    product_composer.py
```

---

# 8. O que compõe uma chamada de rota completa

Esta é a parte mais importante do documento.

A seguir, você verá **todos os arquivos que compõem uma chamada completa**, para que não falte nenhuma peça na implementação.

---

# 9. Exemplo completo de uma rota simples
## Caso: GET /products/{code}

Objetivo:

- receber um código via HTTP
- executar um caso de uso
- consultar o repositório
- mapear para entity
- devolver resposta HTTP

---

## 9.1 Arquivos envolvidos

```text
app/
  domain/
    entities/
      product.py
    repositories/
      product_query_repository_port.py

  application/
    use_cases/
      products/
        get_product_use_case.py

  infrastructure/
    persistence/
      totvs/
        product_repository.py

  composition/
    product_composer.py

  interfaces/
    http/
      routes/
        product_routes.py
```

---

## 9.2 Entity
### app/domain/entities/product.py

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    code: str
    description: str
    group_code: Optional[str] = None
    unit: Optional[str] = None
    type: Optional[str] = None
```

### Por que existe

Porque o sistema precisa de uma representação estável do conceito de produto.

---

## 9.3 Port
### app/domain/repositories/product_query_repository_port.py

```python
from abc import ABC, abstractmethod


class ProductQueryRepositoryPort(ABC):

    @abstractmethod
    def get_product_by_code(self, code: str) -> dict:
        raise NotImplementedError
```

### Por que existe

Para o use case depender de uma abstração.

---

## 9.4 Use Case
### app/application/use_cases/products/get_product_use_case.py

```python
from app.domain.entities.product import Product
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort


class GetProductUseCase:

    def __init__(self, repository: ProductQueryRepositoryPort):
        self._repository = repository

    def execute(self, code: str) -> Product:
        raw = self._repository.get_product_by_code(code)
        return Product(
            code=raw["code"],
            description=raw["description"],
            group_code=raw.get("group_code"),
            unit=raw.get("unit"),
            type=raw.get("type"),
        )
```

### Por que existe

Porque a ação “obter produto” é um caso de uso da aplicação.

---

## 9.5 Repository concreto
### app/infrastructure/persistence/totvs/product_repository.py

```python
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort


class ProductRepository(ProductQueryRepositoryPort):

    def get_product_by_code(self, code: str) -> dict:
        sql = """
            SELECT
                B1_COD AS code,
                B1_DESC AS description,
                B1_GRUPO AS group_code,
                B1_UM AS unit,
                B1_TIPO AS type
            FROM SB1010
            WHERE D_E_L_E_T_ = ''
              AND B1_COD = ?
        """
        return self.execute_one(sql, (code,))
```

### Por que existe

Porque alguém precisa realmente falar com TOTVS.

---

## 9.6 Composer
### app/composition/product_composer.py

```python
from app.application.use_cases.products.get_product_use_case import GetProductUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository



def build_get_product_use_case() -> GetProductUseCase:
    repository = ProductRepository()
    return GetProductUseCase(repository)
```

### Por que existe

Para centralizar a montagem da dependência.

---

## 9.7 Route
### app/interfaces/http/routes/product_routes.py

```python
from fastapi import APIRouter
from app.composition.product_composer import build_get_product_use_case
from app.core.responses import success_response, error_response
from app.utils.logger import log_error


router = APIRouter()


@router.get("/{code}")
def get_product_route(code: str):
    try:
        use_case = build_get_product_use_case()
        product = use_case.execute(code)
        return success_response(data={"product": product.__dict__})
    except Exception as exc:
        log_error(f"Erro ao consultar produto {code}: {exc}")
        return error_response(str(exc))
```

### Por que existe

Porque a rota é a borda HTTP e não deve carregar a regra principal.

---

# 10. Exemplo completo de uma rota paginada
## Caso: GET /products

---

## 10.1 Arquivos envolvidos

```text
app/
  domain/
    entities/
      product.py
    repositories/
      product_query_repository_port.py
  application/
    dto/
      products/
        list_products_request.py
    use_cases/
      products/
        list_products_use_case.py
  infrastructure/
    persistence/
      totvs/
        product_repository.py
  composition/
    product_composer.py
  interfaces/
    http/
      routes/
        product_routes.py
```

---

## 10.2 DTO de entrada
### app/application/dto/products/list_products_request.py

```python
from dataclasses import dataclass


@dataclass
class ListProductsRequest:
    page: int = 1
    page_size: int = 50
```

### Por que existe

Para não deixar a assinatura do use case crescer de forma desorganizada.

---

## 10.3 Port
### app/domain/repositories/product_query_repository_port.py

```python
from abc import ABC, abstractmethod


class ProductQueryRepositoryPort(ABC):

    @abstractmethod
    def get_products_paginated(self, page: int, page_size: int) -> dict:
        raise NotImplementedError
```

---

## 10.4 Use Case
### app/application/use_cases/products/list_products_use_case.py

```python
from app.application.dto.products.list_products_request import ListProductsRequest
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort


class ListProductsUseCase:

    def __init__(self, repository: ProductQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: ListProductsRequest) -> dict:
        return self._repository.get_products_paginated(
            page=request.page,
            page_size=request.page_size,
        )
```

---

## 10.5 Repository
### app/infrastructure/persistence/totvs/product_repository.py

```python
class ProductRepository(ProductQueryRepositoryPort):

    def get_products_paginated(self, page: int, page_size: int) -> dict:
        offset = (page - 1) * page_size
        sql = "SELECT ... OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        count_sql = "SELECT COUNT(*) AS total FROM SB1010 WHERE D_E_L_E_T_ = ''"
        items = self.execute_query(sql, (offset, page_size))
        total = self.execute_one(count_sql, ())['total']
        return {
            'items': items,
            'page': page,
            'page_size': page_size,
            'total': total,
            'total_pages': (total + page_size - 1) // page_size,
        }
```

---

## 10.6 Composer
### app/composition/product_composer.py

```python
from app.application.use_cases.products.list_products_use_case import ListProductsUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository



def build_list_products_use_case() -> ListProductsUseCase:
    repository = ProductRepository()
    return ListProductsUseCase(repository)
```

---

## 10.7 Route
### app/interfaces/http/routes/product_routes.py

```python
from fastapi import Query
from app.application.dto.products.list_products_request import ListProductsRequest
from app.composition.product_composer import build_list_products_use_case


@router.get("")
def list_products_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
):
    use_case = build_list_products_use_case()
    request = ListProductsRequest(page=page, page_size=page_size)
    result = use_case.execute(request)
    return success_response(data=result)
```

---

# 11. Exemplo completo de uma rota hierárquica
## Caso: GET /products/{code}/structure

Rotas hierárquicas exigem mais atenção porque retornam árvores.

---

## 11.1 Arquivos envolvidos

```text
app/
  domain/
    entities/
      structure_node.py
    repositories/
      product_query_repository_port.py
  application/
    dto/
      products/
        structure_request.py
    use_cases/
      products/
        get_product_structure_use_case.py
  infrastructure/
    persistence/
      totvs/
        product_repository.py
    mappers/
      structure_mapper.py
  composition/
    product_composer.py
  interfaces/
    http/
      routes/
        product_routes.py
```

---

## 11.2 Entity da árvore
### app/domain/entities/structure_node.py

```python
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class StructureNode:
    code: str
    description: Optional[str]
    quantity: float
    type: Optional[str] = None
    unit: Optional[str] = None
    components: List['StructureNode'] = field(default_factory=list)
```

---

## 11.3 DTO de entrada
### app/application/dto/products/structure_request.py

```python
from dataclasses import dataclass


@dataclass
class StructureRequest:
    code: str
    max_depth: int = 10
    page: int = 1
    page_size: int = 100
```

---

## 11.4 Port
### app/domain/repositories/product_query_repository_port.py

```python
from abc import ABC, abstractmethod


class ProductQueryRepositoryPort(ABC):

    @abstractmethod
    def list_structure(
        self,
        code: str,
        max_depth: int,
        page: int,
        page_size: int,
    ) -> dict:
        raise NotImplementedError
```

---

## 11.5 Use Case
### app/application/use_cases/products/get_product_structure_use_case.py

```python
from app.application.dto.products.structure_request import StructureRequest
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort


class GetProductStructureUseCase:

    def __init__(self, repository: ProductQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: StructureRequest) -> dict:
        return self._repository.list_structure(
            code=request.code,
            max_depth=request.max_depth,
            page=request.page,
            page_size=request.page_size,
        )
```

---

## 11.6 Repository
### app/infrastructure/persistence/totvs/product_repository.py

```python
class ProductRepository(ProductQueryRepositoryPort):

    def list_structure(self, code: str, max_depth: int, page: int, page_size: int) -> dict:
        # implementação com CTE recursiva
        # retorna estrutura hierárquica paginada
        ...
```

### Observação importante

Nesta primeira fase de refatoração, a montagem hierárquica pode continuar no repository para reduzir risco.

Mais tarde, se desejar, você pode extrair parte disso para mappers dedicados.

---

## 11.7 Composer
### app/composition/product_composer.py

```python
from app.application.use_cases.products.get_product_structure_use_case import GetProductStructureUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository



def build_get_product_structure_use_case() -> GetProductStructureUseCase:
    repository = ProductRepository()
    return GetProductStructureUseCase(repository)
```

---

## 11.8 Route
### app/interfaces/http/routes/product_routes.py

```python
from fastapi import Query
from app.application.dto.products.structure_request import StructureRequest
from app.composition.product_composer import build_get_product_structure_use_case


@router.get("/{code}/structure")
def structure_route(
    code: str,
    max_depth: int = Query(10, ge=1, le=15),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
):
    use_case = build_get_product_structure_use_case()
    request = StructureRequest(
        code=code,
        max_depth=max_depth,
        page=page,
        page_size=page_size,
    )
    result = use_case.execute(request)
    return success_response(data=result)
```

---

# 12. Exemplo completo de exportação
## Caso: GET /products/{code}/structure/excel

Exportação é um caso especial.

Ela não deve jogar a geração do arquivo dentro da rota nem dentro do repository.

---

## 12.1 Arquivos envolvidos

```text
app/
  domain/
    repositories/
      product_query_repository_port.py
  application/
    use_cases/
      products/
        export_structure_excel_use_case.py
  infrastructure/
    persistence/
      totvs/
        product_repository.py
    exporters/
      structure_excel_exporter.py
  composition/
    product_composer.py
  interfaces/
    http/
      routes/
        product_routes.py
```

---

## 12.2 Port do exporter
### app/domain/repositories/structure_excel_exporter_port.py

```python
from abc import ABC, abstractmethod


class StructureExcelExporterPort(ABC):

    @abstractmethod
    def export(self, structure: dict):
        raise NotImplementedError
```

---

## 12.3 Exporter concreto
### app/infrastructure/exporters/structure_excel_exporter.py

```python
import io
from openpyxl import Workbook
from app.domain.repositories.structure_excel_exporter_port import StructureExcelExporterPort


class StructureExcelExporter(StructureExcelExporterPort):

    def export(self, structure: dict) -> io.BytesIO:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Estrutura'
        sheet.append(['Código', 'Descrição'])

        for item in structure.get('data', {}).get('components', []):
            sheet.append([
                item.get('code'),
                item.get('description'),
            ])

        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return stream
```

---

## 12.4 Use Case
### app/application/use_cases/products/export_structure_excel_use_case.py

```python
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort
from app.domain.repositories.structure_excel_exporter_port import StructureExcelExporterPort


class ExportStructureExcelUseCase:

    def __init__(
        self,
        repository: ProductQueryRepositoryPort,
        exporter: StructureExcelExporterPort,
    ):
        self._repository = repository
        self._exporter = exporter

    def execute(self, code: str):
        structure = self._repository.list_structure(code=code, max_depth=50, page=1, page_size=5000)
        return self._exporter.export(structure)
```

---

## 12.5 Composer
### app/composition/product_composer.py

```python
from app.application.use_cases.products.export_structure_excel_use_case import ExportStructureExcelUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository
from app.infrastructure.exporters.structure_excel_exporter import StructureExcelExporter



def build_export_structure_excel_use_case() -> ExportStructureExcelUseCase:
    repository = ProductRepository()
    exporter = StructureExcelExporter()
    return ExportStructureExcelUseCase(repository, exporter)
```

---

## 12.6 Route
### app/interfaces/http/routes/product_routes.py

```python
from fastapi.responses import StreamingResponse
from app.composition.product_composer import build_export_structure_excel_use_case


@router.get("/{code}/structure/excel")
def structure_excel_route(code: str):
    use_case = build_export_structure_excel_use_case()
    stream = use_case.execute(code)
    filename = f"Estrutura_{code}.xlsx"
    return StreamingResponse(
        stream,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )
```

---

# 13. Exemplo completo de rota composta
## Caso: GET /products/{code}/analyser

Rotas compostas juntam múltiplas consultas.

Nelas, o use case atua como orquestrador.

---

## 13.1 Arquivos envolvidos

```text
app/
  domain/
    repositories/
      product_query_repository_port.py
      stock_query_repository_port.py
      pricing_query_repository_port.py
  application/
    use_cases/
      products/
        get_product_analyser_use_case.py
  infrastructure/
    persistence/
      totvs/
        product_repository.py
        stock_repository.py
        pricing_repository.py
  composition/
    product_composer.py
  interfaces/
    http/
      routes/
        product_routes.py
```

---

## 13.2 Use Case
### app/application/use_cases/products/get_product_analyser_use_case.py

```python
from app.domain.repositories.product_query_repository_port import ProductQueryRepositoryPort
from app.domain.repositories.stock_query_repository_port import StockQueryRepositoryPort
from app.domain.repositories.pricing_query_repository_port import PricingQueryRepositoryPort


class GetProductAnalyserUseCase:

    def __init__(
        self,
        product_repository: ProductQueryRepositoryPort,
        stock_repository: StockQueryRepositoryPort,
        pricing_repository: PricingQueryRepositoryPort,
    ):
        self._product_repository = product_repository
        self._stock_repository = stock_repository
        self._pricing_repository = pricing_repository

    def execute(self, code: str) -> dict:
        product = self._product_repository.get_product_by_code(code)
        stock = self._stock_repository.get_stock(code, page=1, page_size=50, branch=None, location=None)
        pricing = self._pricing_repository.get_product_pricing(code)
        return {
            'product': product,
            'stock': stock,
            'pricing': pricing,
        }
```

---

## 13.3 Composer
### app/composition/product_composer.py

```python
from app.application.use_cases.products.get_product_analyser_use_case import GetProductAnalyserUseCase
from app.infrastructure.persistence.totvs.product_repository import ProductRepository
from app.infrastructure.persistence.totvs.stock_repository import StockRepository
from app.infrastructure.persistence.totvs.pricing_repository import PricingRepository



def build_get_product_analyser_use_case() -> GetProductAnalyserUseCase:
    product_repository = ProductRepository()
    stock_repository = StockRepository()
    pricing_repository = PricingRepository()
    return GetProductAnalyserUseCase(
        product_repository=product_repository,
        stock_repository=stock_repository,
        pricing_repository=pricing_repository,
    )
```

---

## 13.4 Route
### app/interfaces/http/routes/product_routes.py

```python
from app.composition.product_composer import build_get_product_analyser_use_case


@router.get('/{code}/analyser')
def analyser_route(code: str):
    use_case = build_get_product_analyser_use_case()
    result = use_case.execute(code)
    return success_response(data=result)
```

---

# 14. Template oficial para refatorar qualquer rota

Use este processo toda vez.

## Etapa 1 — classificar a rota

Descubra se ela é:

- simples
- paginada
- hierárquica
- exportação
- composta

## Etapa 2 — nomear o use case

Exemplos:

- GetProductUseCase
- ListProductsUseCase
- GetProductStructureUseCase
- ExportStructureExcelUseCase
- GetProductAnalyserUseCase

## Etapa 3 — criar ou atualizar a entity

Se a rota trabalha com um conceito de domínio relevante, modele isso.

## Etapa 4 — criar ou atualizar a port

Defina o contrato que o use case precisa.

## Etapa 5 — criar o use case

Toda regra de aplicação deve entrar aqui.

## Etapa 6 — adaptar o repository concreto

Faça o repositório implementar a port.

## Etapa 7 — criar o composer

Monte as dependências.

## Etapa 8 — atualizar a rota

A rota deve chamar apenas o composer e o use case.

## Etapa 9 — escrever teste unitário do use case

Use fake repository.

## Etapa 10 — validar contrato HTTP

Garanta que o endpoint continua compatível.

---

# 15. Como saber o que cada arquivo deve conter

## Entity

Contém:

- representação do domínio
- atributos do negócio
- eventualmente validações puras

Não contém:

- SQL
- HTTP
- FastAPI

## Port

Contém:

- assinatura do contrato

Não contém:

- implementação

## Use Case

Contém:

- regra de aplicação
- orquestração
- coordenação entre portas

Não contém:

- SQL
- framework
- respostas HTTP

## Repository

Contém:

- implementação concreta de acesso a dados

Não contém:

- regra HTTP
- lógica de menu
- resposta de API

## Composer

Contém:

- montagem de dependências

Não contém:

- regra de negócio

## Route

Contém:

- request
- response
- chamada do use case

Não contém:

- SQL
- regra central

---

# 16. Como testar corretamente

O teste mais importante da Clean Architecture é o teste do use case.

## Exemplo

```python
from app.application.use_cases.products.get_product_use_case import GetProductUseCase


class FakeProductRepository:

    def get_product_by_code(self, code: str) -> dict:
        return {
            'code': '001',
            'description': 'Produto Teste',
            'group_code': 'A',
            'unit': 'PC',
            'type': 'PA',
        }



def test_get_product_use_case():
    repository = FakeProductRepository()
    use_case = GetProductUseCase(repository)
    result = use_case.execute('001')

    assert result.code == '001'
    assert result.description == 'Produto Teste'
```

### Por que isso é importante

Porque prova que a regra da aplicação funciona sem banco nem framework.

---

# 17. Erros comuns que você deve evitar

## Erro 1 — deixar o service antigo entre a rota e o use case

Errado:

```python
class GetProductUseCase:
    def execute(self, code):
        return get_product(code)
```

Isso só renomeia o problema.

## Erro 2 — use case retornando JSONResponse

O use case não deve conhecer HTTP.

## Erro 3 — rota criando múltiplas dependências diretamente

Se existe injeção, o composer deve montar.

## Erro 4 — repository decidindo regra de aplicação

Repository consulta. Use case decide fluxo.

## Erro 5 — não criar port

Sem port, o use case volta a depender do concreto.

---

# 18. Ordem recomendada de migração da api-delpi

## Lote 1 — simples

- GET /products/{code}
- GET /products
- GET /products/search
- GET /products/search/description

## Lote 2 — paginadas

- suppliers
- customers
- purchases
- stock
- internal-movements
- inbound-invoice-items
- outbound-invoice-items

## Lote 3 — hierárquicas

- structure
- parents
- guide
- inspection

## Lote 4 — exportações

- structure/excel

## Lote 5 — compostas

- analyser

---

# 19. Checklist final por rota

Antes de considerar uma rota refatorada, confirme:

- [ ] existe entity quando necessário
- [ ] existe port
- [ ] existe use case
- [ ] repository implementa a port
- [ ] composer monta dependências
- [ ] rota chama o composer
- [ ] rota não contém regra de negócio
- [ ] use case não conhece HTTP
- [ ] repository não conhece response HTTP
- [ ] existe teste unitário do use case

---

# 20. Conclusão

Se você seguir este manual, cada chamada de rota passará a ter uma arquitetura previsível e completa.

O padrão correto será sempre:

```text
Route
 ↓
Composer
 ↓
UseCase
 ↓
Port
 ↓
Repository concreto
 ↓
Banco / TOTVS / Exporter / integração
```

Essa estrutura reduz acoplamento, melhora testabilidade e torna a api-delpi muito mais segura para evoluir.

---

# Fim do manual

