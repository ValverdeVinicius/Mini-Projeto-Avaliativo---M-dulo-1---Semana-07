# Relatório — Festa em Cena

## Escopo

A análise cobre **1.500 pedidos registrados** de agosto a novembro de 2024 e 2025, nos canais Mercado, Loja física e Web. Uma linha representa um pedido de um único produto, com uma ou mais unidades. As contagens abaixo são de pedidos, não de receita ou vendas concluídas.

## Qualidade dos dados

A leitura com Pandas preservou o CSV original e tratou os campos como texto. Foram preenchidas **18 categorias vazias** com `"sem categoria"`; **131 categorias não vazias** precisaram de correção de espaços ou pontuação, e todas as 1.482 não vazias passaram por padronização de caixa. Nos canais, **45 valores** foram ajustados; os 1.500 registros ficaram reconhecíveis.

Na validação numérica, **7 pedidos** têm quantidade inválida (`-1`) e **12** têm preço unitário vazio. Como não há sobreposição, **19 pedidos** são afetados. Nenhum valor foi imputado. Quatro datas de venda são inválidas e foram excluídas das contagens temporais; nenhuma foi substituída pela data atual.

## Regra de entrega

Há **143 pedidos sem data de entrega**: 109 são Cancelados e **34 têm outros status**. Portanto, a hipótese "toda `data_entrega` vazia implica Cancelado" é **falsa**; os pedidos 1170, 990 e 740 são contraexemplos (todos Concluídos). Todos os 109 cancelados estão sem data de entrega, mas essa é a relação inversa e não confirma a hipótese. Status e datas não foram alterados.

## Descobertas

**Canal.** Web concentra **666 dos 1.500 pedidos (44,4%)**, contra 551 na Loja física (36,7%) e 283 no Mercado (18,9%). A leitura sugere prioridade de atenção ao canal Web, mas contar pedidos não mede receita, ticket ou conversão; 19 registros têm problemas numéricos e a base é fictícia.

**Período.** Outubro reúne **803 dos 1.496 pedidos com data válida (53,7%)**, sendo 393 em 2024-10 e 410 em 2025-10; agosto tem 139 (9,3%). O padrão é compatível com a sazonalidade do Halloween nos dois anos. A limitação é que a base cobre apenas agosto a novembro, exclui 4 datas inválidas e inclui todos os status; não permite inferir causalidade nem representar o mercado real.

## Conclusão

Os dados são majoritariamente utilizáveis após padronização, mas as falhas encontradas exigem cautela: nenhuma contagem foi corrigida por imputação. A concentração em Web e outubro é um sinal exploratório para planejamento comercial e de estoque. Para Machine Learning, limpeza é necessária, porém insuficiente: representatividade, escolha do modelo e validação temporal são essenciais para evitar overfitting ou underfitting.
