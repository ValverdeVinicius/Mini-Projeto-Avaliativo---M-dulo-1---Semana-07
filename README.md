# Festa em Cena — Análise de Pedidos de Halloween

## 1. Descrição do projeto

A **Festa em Cena** é uma rede fictícia que vende fantasias e acessórios de Halloween por três canais: **Mercado** (caixas de supermercados parceiros), **Loja física** (lojas próprias) e **Web** (pedidos pelo site). A gestão precisava organizar os registros e entender como os pedidos variam por canal e por período antes de comparar os anos.

A base `halloween_vendas.csv` contém **1.500 pedidos distintos**, de agosto a novembro de 2024 e de 2025. Ela foi criada para a atividade e inclui problemas intencionais: categorias vazias, pontuação e espaçamento irregulares, canais escritos de formas diferentes, quantidades inválidas, preços ausentes e datas inválidas. Os dados são fictícios e não representam o mercado real.

**Uma linha representa um pedido de um único produto**, que pode conter várias unidades. Portanto, a linha não é o total de um carrinho com vários produtos e as contagens abaixo são de **pedidos registrados**, não de receita ou de vendas concluídas.

### Quatro colunas escolhidas

| Coluna | Significado | Uso neste projeto |
|---|---|---|
| `pedido_id` | Identificador único do pedido. | Contagem de pedidos e identificação de exemplos. |
| `data_venda` | Data e hora locais de São Paulo, sem fuso explícito, no formato texto `AAAA-MM-DD HH:MM:SS`. | Conversão para data, extração de ano/mês/dia/hora e contagem por ano-mês. |
| `canal_venda` | Canal em que o pedido foi registrado: Mercado, Loja física ou Web. | Padronização e contagem de pedidos por canal. |
| `quantidade` | Quantidade de unidades do produto naquele pedido. | Validação: precisa ser inteiro maior que zero. |

Outras colunas usadas nas regras são `preco_unitario` (preço por unidade), `status_pedido` (Cancelado, Concluído ou Devolvido) e `data_entrega` (data prevista/real de entrega, que pode estar vazia). As colunas de custo e desconto existem no CSV, mas não são usadas para calcular receita neste projeto.

## 2. Objetivo e escopo

O programa foi desenvolvido para:

- ler o CSV com Pandas, preservando o arquivo original;
- revisar células vazias e padronizar categorias e canais;
- validar quantidade e preço sem inventar valores;
- converter datas com `datetime.strptime()` e marcar datas inválidas;
- investigar a relação entre data de entrega vazia e status Cancelado;
- produzir um relatório manual no terminal com contagens por canal e por ano-mês;
- apresentar duas descobertas com evidência numérica, interpretação e limitação.

O projeto é de **análise exploratória**. Não há treinamento de modelo, cálculo de receita ou previsão.

## 3. Regras de leitura e tratamento

### 3.1 Leitura do CSV

A leitura é feita com:

```python
pd.read_csv(caminho, sep=",", encoding="utf-8", dtype=str, keep_default_na=False)
```

Decisões:

- `dtype=str`: todos os campos são lidos como texto, como pede o enunciado; números e datas são convertidos apenas quando usados.
- `keep_default_na=False`: células vazias continuam como `""` em vez de virarem `NaN` automaticamente. Assim os problemas ficam visíveis e não há imputação silenciosa.
- `sep=","` e `encoding="utf-8"`: separador e codificação especificados.
- O arquivo é apenas lido. Nenhuma escrita é feita em `halloween_vendas.csv`.
- Antes das transformações, os textos originais de `categoria`, `canal_venda`, `data_venda` e `data_entrega` são copiados para colunas `*_original`, permitindo auditoria e preservação do dado recebido.

A revisão inicial encontrou 18 células vazias em `categoria`, 12 em `preco_unitario`, 7 em `custo_unitario` e 143 em `data_entrega`, totalizando 180 células vazias. As demais colunas não tinham vazios.

### 3.2 Categorias

A função `normalizar_categoria()` executa, nesta ordem:

1. `.strip()` e `.lower()`;
2. `re.sub()` para remover pontuação, dígitos e símbolos, preservando letras e espaços;
3. `re.sub(r"\s+", " ", ...)` para reduzir espaços repetidos a um;
4. se o resultado ficar vazio, usa a string **`"sem categoria"`**.

A expressão regular preserva letras latinas acentuadas, caso apareçam em outra base, embora as categorias preenchidas deste CSV usem letras sem acento. A regra evita tratar `"FANTASIA!!!"`, `" Fantasia "` e `"Fantasia"` como categorias diferentes.

Resultados nesta base:

- **18 categorias vazias** foram preenchidas com `"sem categoria"`;
- **131 categorias não vazias** tinham espaços ou pontuação e foram alteradas pela limpeza;
- todas as **1.482 categorias não vazias** passaram por `.lower()`; a contagem de 131 destaca apenas as que precisaram de correção de formato;
- contagem final: `fantasia` = 979, `acessorio` = 503, `sem categoria` = 18.

### 3.3 Canais

A função `normalizar_canal()` aplica `.strip()`, `.lower()` e reduz espaços. Em seguida, um dicionário converte as formas reconhecidas para os rótulos oficiais:

- `mercado` → **Mercado**;
- `loja física` ou `loja fisica` → **Loja física**;
- `web` → **Web**.

Foram **45 valores alterados**. Todos os 1.500 registros ficaram com canal reconhecido; não houve canal vazio ou desconhecido nesta base. Se houvesse, o valor não seria inventado: ficaria vazio, seria marcado como não reconhecido e excluído das contagens por canal, com o total de exclusões informado.

### 3.4 Quantidade e preço unitário

As regras foram aplicadas com `pd.to_numeric(..., errors="coerce")`, sem substituir valores:

- **`quantidade`**: deve ser um inteiro maior que zero. Vazia, não numérica, negativa, zero ou fracionária é inválida. Nesta base, **7 pedidos** têm quantidade `-1`; não usamos média, mediana ou qualquer valor inventado para corrigi-los.
- **`preco_unitario`**: deve estar preenchido e ser maior ou igual a zero. Zero é aceito pela regra (pode representar promoção ou cortesia), mas vazio, texto não numérico ou negativo é inválido. Nesta base, **12 pedidos** têm preço vazio; nenhum preço foi imputado.

Cada problema é registrado em uma coluna de flag (`quantidade_invalida`, `preco_invalido` e `problema_numerico`). A contagem por campo é 7 e 12. Como não há sobreposição nesta base, a **união de pedidos afetados é 19**; o código calcula a interseção para não somar o mesmo pedido duas vezes em bases futuras.

### 3.5 Datas de venda

A função `converter_datas()` usa explicitamente:

```python
datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
```

Para cada linha:

- o texto original permanece em `data_venda_original`;
- datas válidas geram `data_venda_dt`, além de `ano`, `mes`, `dia` e `hora`;
- a apresentação brasileira é criada com `strftime("%d/%m/%Y")` na coluna `data_venda_br`;
- datas vazias ou inválidas são marcadas em `data_venda_status` e `data_venda_invalida`, recebem `NaT` e **não são substituídas pela data de hoje** nem por uma data inventada;
- o processamento continua após encontrar uma data inválida.

Nesta base: **1.496 datas válidas**, **4 datas inválidas** (pedidos 740, 370, 1480 e 1110, todos com o texto `data_invalida`) e **0 datas vazias**. Exemplo de preservação: o pedido 844 tem original `"2025-11-21 18:02:35"` e apresentação `21/11/2025`, com ano 2025, mês 11, dia 21 e hora 18.

### 3.6 Data de entrega e status

A hipótese investigada é: **toda linha com `data_entrega` vazia tem `status_pedido` igual a Cancelado**. O status e as datas de entrega não são alterados. Os grupos são contados separadamente:

- pedidos sem data de entrega: **143**;
- desses, cancelados: **109**;
- desses, com outros status: **34**;
- total de cancelados: **109**;
- cancelados com data de entrega: **0**.

Como existem 34 pedidos sem entrega e com outro status, a hipótese é **FALSA** na base. Os três primeiros contraexemplos são os pedidos **1170** (Concluído, Web), **990** (Concluído, Web) e **740** (Concluído, Web; este também tem data de venda inválida). O fato de todos os 109 cancelados estarem sem data de entrega é a relação inversa e não confirma a hipótese testada.

## 4. Como executar

### Requisitos da aplicação

- Python 3.10 ou superior (testado com Python 3.14.10);
- Pandas (testado com 3.1.1);
- o arquivo `halloween_vendas.csv` na raiz do projeto.

### Estrutura

```text
sctech/
├── main.py
├── halloween_vendas.csv
├── requirements.txt
├── README.md
└── report.md
```

### Passo a passo

No terminal, a partir do diretório do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

O script procura `halloween_vendas.csv` na mesma pasta do `main.py`. Também é possível informar outro caminho:

```bash
python main.py {qualquer_caminho}/halloween_vendas.csv
```

Para ver as opções:

```bash
python main.py --help
```

A saída é impressa no terminal e organizada em seções: leitura e nulos, padronização, validação numérica, datas, regra de entrega, pedidos por canal, pedidos por ano-mês e duas descobertas. Se quiser salvar o relatório:

```bash
python main.py > resultados.txt
```

O CSV original não é modificado.

## 5. Resultados obtidos

### 5.1 Resumo da qualidade

| Métrica | Resultado |
|---|---:|
| Linhas lidas | 1.500 |
| Colunas originais | 14 |
| Categorias vazias preenchidas com `"sem categoria"` | 18 |
| Categorias não vazias com espaços/pontuação corrigidos | 131 |
| Canais padronizados | 45 |
| Canais não reconhecidos | 0 |
| Quantidade inválida | 7 |
| Preço unitário inválido | 12 |
| Pedidos com problema numérico (união) | 19 |
| Datas de venda válidas | 1.496 |
| Datas de venda inválidas | 4 |
| Datas de venda vazias | 0 |
| Pedidos cancelados | 109 |
| Pedidos sem data de entrega | 143 |
| Sem entrega e cancelados | 109 |
| Sem entrega e outros status | 34 |
| Cancelados com data de entrega | 0 |

### 5.2 Categorias após padronização

| Categoria | Pedidos |
|---|---:|
| `fantasia` | 979 |
| `acessorio` | 503 |
| `sem categoria` | 18 |

### 5.3 Pedidos por canal

Contagem com todos os status e apenas canais reconhecidos; exclusões: 0.

| Canal | Pedidos | Percentual |
|---|---:|---:|
| Web | 666 | 44,4% |
| Loja física | 551 | 36,7% |
| Mercado | 283 | 18,9% |
| **Total** | **1.500** | **100,0%** |

### 5.4 Pedidos por ano-mês

Contagem com todos os status e apenas datas de venda válidas; exclusões por data inválida/vazia: 4. O agrupamento é por **ano e mês**, não apenas por mês, para não misturar 2024 e 2025.

| Ano-mês | Pedidos | Percentual |
|---|---:|---:|
| 2024-08 | 77 | 5,1% |
| 2024-09 | 104 | 7,0% |
| 2024-10 | 393 | 26,3% |
| 2024-11 | 174 | 11,6% |
| 2025-08 | 62 | 4,1% |
| 2025-09 | 94 | 6,3% |
| 2025-10 | 410 | 27,4% |
| 2025-11 | 182 | 12,2% |
| **Total** | **1.496** | **100,0%** |

### 5.5 Conclusão sobre entrega sem data

A hipótese de que toda entrega vazia pertence a um pedido cancelado **não se sustenta**: 34 pedidos sem data de entrega têm status Concluído. Por outro lado, os 109 cancelados não têm data de entrega. Isso mostra uma associação parcial, mas não a regra testada. Nenhum status foi alterado e nenhuma data de entrega foi inventada.

## 6. Duas descobertas

### 6.1 Por canal

**Evidência:** Web concentra **666 de 1.500 pedidos (44,4%)**, contra 551 na Loja física (36,7%) e 283 no Mercado (18,9%). Todos os 1.500 pedidos tinham canal reconhecido após a padronização.

**Interpretação:** nesta base fictícia, o site é o principal ponto de registro de pedidos. Isso pode orientar atenção comercial, comunicação e planejamento de estoque para o canal Web.

**Limitação:** contar pedidos não é medir receita, ticket médio, conversão ou vendas concluídas. A contagem inclui cancelados e devolvidos; além disso, 19 pedidos têm problema numérico e a base é fictícia, sem representatividade do mercado real.

### 6.2 Por período

**Evidência:** outubro soma **803 dos 1.496 pedidos com data válida (53,7%)**, com 393 em 2024-10 e 410 em 2025-10. O maior mês isolado é 2025-10, com 410 pedidos. Agosto soma 139 pedidos (9,3%) e setembro, 198 (13,2%); novembro soma 356 (23,8%).

**Interpretação:** há concentração em outubro nos dois anos, compatível com a sazonalidade do Halloween. O padrão sugere que o planejamento de estoque e de campanhas precisa considerar esse pico.

**Limitação:** a base cobre apenas agosto a novembro; 4 datas inválidas foram excluídas; todos os status estão incluídos, então o resultado não representa receita nem vendas concluídas. O padrão é descritivo e não prova causalidade.

## 7. Reflexão sobre qualidade de dados e Machine Learning

A limpeza realizada é necessária, mas **não garante** bom desempenho em Machine Learning. Valores ausentes, rótulos inconsistentes e datas inválidas podem distorcer estatísticas e features: neste projeto, 18 categorias foram recuperadas, 131 rótulos precisaram de limpeza, 7 quantidades eram inválidas, 12 preços estavam vazios e 4 datas eram inválidas. Se esses problemas fossem ignorados, contagens por categoria, canal ou período poderiam ficar enviesadas.

Além da limpeza, importam a **representatividade** e a **avaliação**. A base é fictícia, tem 1.500 pedidos, apenas quatro meses por ano, três canais e seis produtos; ela não representa o mercado real e não sustenta generalizações. Em um projeto de ML, seria necessário separar treino e teste respeitando o tempo (por exemplo, treinar com 2024 e testar com 2025), evitar vazamento de informação, documentar a estratégia para valores ausentes e escolher métricas adequadas. A escolha do modelo, a regularização e a validação também influenciam o resultado: **limpeza sozinha não evita overfitting nem underfitting**.

Neste trabalho não há treinamento de modelo. O objetivo é demonstrar que a qualidade dos dados e a transparência das regras são a base para qualquer análise ou modelo posterior.

## 8. Limitações e próximos passos

- As contagens são de **pedidos registrados**, não de receita ou vendas concluídas.
- 19 pedidos têm problema numérico: 7 com quantidade inválida e 12 com preço vazio.
- 4 pedidos têm data de venda inválida e 143 não têm data de entrega.
- Todos os status entram nas contagens por canal e por ano-mês; isso é intencional, mas deve ser considerado na interpretação.
- A base é fictícia e cobre apenas agosto a novembro de 2024 e 2025; não é possível generalizar para o mercado real.
- Próximos passos: validar as regras com a área de negócio, recuperar preços e datas com as fontes originais, testar as funções com dados sintéticos e, se houver modelagem, usar validação temporal e métricas adequadas.

## 9. Organização do código e versionamento

O código está em `main.py`, com funções de responsabilidade única:

- `carregar_dados()`: leitura, validação de colunas e revisão de nulos;
- `normalizar_categoria()`, `normalizar_canal()` e `padronizar_textos()`: limpeza e padronização;
- `validar_numeros()`: regras de quantidade e preço, com flags e contagens;
- `converter_datas()`: `strptime()`, partes da data e apresentação brasileira;
- `analisar_entregas()`: investigação da hipótese de entrega;
- `contar_por_canal()` e `contar_por_ano_mes()`: agregações;
- `imprimir_relatorio()`: relatório manual, descobertas e limitações;
- `main()` e `cli()`: orquestração, argumentos e tratamento de erros.

O repositório foi organizado com a branch `main` para a versão estável, a branch `feat/analise` para a implementação do código e a branch `docs/entrega` para a documentação. Os commits registram a evolução em etapas compreensíveis.

## 10. Fonte dos dados

A base `halloween_vendas.csv` foi disponibilizada na atividade:

<https://github.com/Machine-Learning-Visao-Computacional-T5/python_exercises/tree/main/data_analysis/arquivo_mini_projeto>
