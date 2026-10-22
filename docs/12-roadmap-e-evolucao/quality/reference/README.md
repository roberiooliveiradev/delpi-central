# Referência visual — Relatório metalográfico

Arquivo íntegro: `Modelo_Relatorio_Metalografico_Delpi_Editavel.html`.

SHA-256: `13ba5eb7033afa616bf542ac6f7a6df5c67a0d318d2ea898caa4fb368220b820`.

Origem: arquivo entregue pelo solicitante do chamado #1400. A cópia neste diretório é byte a byte.

O HTML incorpora a fonte Delpi Sans (OpenType CFF, pesos 400 e 700), o logotipo e o esquema de cotas. Esses recursos foram extraídos para o MFE `metalography` para reproduzir o mesmo documento. A família CSS publicada é `DelpiSans`, sem espaço, porque o minificador do build descarta aspas e partiria o nome `Delpi Sans`. Os arquivos são os mesmos. O script pdf-lib incluído no arquivo está sob Apache License 2.0 e permanece apenas nesta referência; o MFE não o executa.

A folha vazia e a folha preenchida com o mesmo conjunto de dados foram capturadas no Chrome, janela 1100×1750. Na região da barra e da folha (y 0–1214) a diferença de pixel entre o HTML e o CSS publicado do MFE foi zero. A área abaixo da folha não entra na comparação: no HTML ela é o fundo da página; no Portal ela pertence ao host.

A impressão do MFE não usa `window.print()` da janela do Portal. O botão Imprimir monta a folha corrente num iframe oculto, com `@page` A4 e margem zero, para a navegação do host não entrar na prévia. O tema claro ou escuro da tela não entra nesse documento: `@media print` devolve a paleta do HTML original. O arquivo HTML de referência não é alterado.

O PDF continua na API DELPI, desenhado nas coordenadas em milímetros do exportador do próprio HTML. A página não recebe marca d'água; o status funcional do relatório continua rascunho. Diferenças residuais em relação à tela: o PDF usa o traço de confirmação do exportador HTML, e a fonte foi convertida de CFF para TrueType para o ReportLab. As observações usam as três linhas já desenhadas na folha; o que não cabe termina com `...`, para o corte não ficar invisível.
