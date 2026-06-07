# Contexto do Data Warehouse — Oficina Integrada

## Objetivo

Criar as tabelas do Data Warehouse no Supabase usando DDL (PostgreSQL). O modelo é um star schema centrado na `fact_ordem_de_servico`, com uma segunda fact table (`fact_item_os`) no grain do item.

---

## Instruções técnicas importantes

### Tipos de PK e FK

Existem dois tipos de PK nesse modelo e é essencial que as FKs batam com o tipo correto:

- As dimensões `dim_cliente` e `dim_motocicleta` usam `BIGSERIAL` como PK. As FKs que apontam para essas dimensões devem ser `BIGINT`.
- A `dim_data` usa `INT` como PK (formato `YYYYMMDD`, ex: `20260128`). As FKs que apontam para ela devem ser `INT`, não `BIGINT`. Se houver divergência de tipo o banco rejeita a constraint.
- A `fact_ordem_de_servico` usa `BIGSERIAL` como PK. A FK em `fact_item_os` que aponta para ela deve ser `BIGINT`.

### Surrogate Key (SK) vs Natural Key (NK)

Todas as dimensões (exceto `dim_data`) possuem dois tipos de chave:

- `sk_` (Surrogate Key): chave artificial gerada pelo próprio DW, sem significado de negócio. É um `BIGSERIAL` auto-incrementado. É a chave usada nas FKs e em todos os joins.
- `nk_` (Natural Key): chave original vinda do sistema fonte (Oficina Integrada). Guardada como coluna separada com `UNIQUE` constraint. Usada pelo pipeline de carga para localizar o registro correto na dimensão antes de inserir na fact.

As fact tables armazenam **apenas SKs** como FKs — nunca NKs. As NKs aparecem nas facts apenas como chaves degeneradas para rastreabilidade ao sistema fonte, sem constraint de FK.

A `dim_data` é exceção: sua PK é o próprio inteiro `YYYYMMDD`, que já é estável e sem risco de colisão entre fontes. Não tem NK separada.

### Chaves degeneradas nas facts

- `nk_ordem_de_servico` na `fact_ordem_de_servico`: número original da OS no sistema fonte.
- `nk_ordem_servico` na `fact_item_os`: mesmo número, replicado para rastreabilidade e validação de carga.
- `nk_codigo_origem` na `fact_item_os`: id do produto ou serviço na fonte (0 = item não cadastrado).

Nenhuma dessas colunas tem constraint de FK.

### Convenção de nomenclatura

| Prefixo | Significado | Tipo usual |
|---|---|---|
| `sk_` | Surrogate Key | BIGSERIAL / INT |
| `nk_` | Natural Key | INT / VARCHAR |
| `fl_` | Flag (booleano) | BOOLEAN / VARCHAR |
| `dt_` | Data | DATE / TIMESTAMP |
| `vl_` | Valor monetário | NUMERIC(10,2) |

Os prefixos `nr_` e `nm_` são usados apenas quando há ambiguidade real — dois atributos do mesmo conceito em tipos diferentes. Por exemplo `nr_dia` (INT) e `nm_dia_semana` (VARCHAR) na `dim_data`. Fora desses casos, o nome do atributo é direto sem prefixo.

---

## Estrutura das tabelas

### dim_data

```sql
sk_data            INT           PRIMARY KEY   -- formato YYYYMMDD ex: 20260128
dt_data_completa   DATE
nr_dia             INT
nr_mes             INT
nr_ano             INT
nr_trimestre       INT
nr_semana_ano      INT
nm_mes             VARCHAR                     -- 'janeiro' (par textual de nr_mes)
nm_dia_semana      VARCHAR                     -- 'quarta-feira' (par textual de nr_dia)
fl_fim_semana      BOOLEAN
fl_feriado         BOOLEAN                     -- não obrigatório no MVP
```

### dim_cliente

```sql
sk_cliente         BIGSERIAL     PRIMARY KEY
nk_cliente         INT           UNIQUE NOT NULL   -- id_cliente do sistema fonte
nome               VARCHAR
bairro             VARCHAR
cidade             VARCHAR
uf                 VARCHAR
fl_tipo_pessoa     VARCHAR                         -- 'PF' ou 'PJ'
cpf                VARCHAR
cnpj               VARCHAR
dt_cadastro        DATE
```

### dim_motocicleta

```sql
sk_motocicleta     BIGSERIAL     PRIMARY KEY
nk_motocicleta     INT           UNIQUE NOT NULL   -- id_veiculo do sistema fonte
placa              VARCHAR
marca              VARCHAR
modelo             VARCHAR
versao             VARCHAR
cor                VARCHAR
ano                VARCHAR
chassi             VARCHAR
```

### fact_ordem_de_servico

```sql
sk_ordem_de_servico  BIGSERIAL   PRIMARY KEY
nk_ordem_de_servico  INT                           -- chave degenerada, sem FK
valor_total          NUMERIC(10,2)
valor_desconto       NUMERIC(10,2)
km_motocicleta       INT
data_inclusao        INT         NOT NULL REFERENCES dim_data(sk_data)
data_saida           INT                  REFERENCES dim_data(sk_data)
sk_cliente           BIGINT      NOT NULL REFERENCES dim_cliente(sk_cliente)
sk_motocicleta       BIGINT               REFERENCES dim_motocicleta(sk_motocicleta)
```

### fact_item_os

```sql
sk_item_os         BIGSERIAL     PRIMARY KEY
sk_ordem_servico   BIGINT        NOT NULL REFERENCES fact_ordem_de_servico(sk_ordem_de_servico)
nk_ordem_servico   INT                             -- chave degenerada, mesma da fact pai
tipo               VARCHAR                         -- 'produto', 'servico' ou NULL
nk_codigo_origem   INT                             -- id do produto/servico na fonte (0 = não cadastrado)
descricao          VARCHAR                         -- texto que veio na OS
quantidade         NUMERIC(10,2)
vl_unitario        NUMERIC(10,2)
vl_total           NUMERIC(10,2)
vl_desconto        NUMERIC(10,2)
fl_aprovado        BOOLEAN                         -- item orçado foi aprovado pelo cliente
```

---

## Lógica de transformação para fact_item_os

O campo `tipo` é resolvido na etapa de transformação do pipeline. O CSV de itens da OS possui `Codigo Produtos Servicos` que pode referenciar um produto ou um serviço, sem indicador de tipo. A lógica de resolução:

1. Buscar o código + descrição na tabela de produtos → se encontrar, `tipo = 'produto'`
2. Se não encontrou, buscar na tabela de serviços → se encontrar, `tipo = 'servico'`
3. Se não encontrou em nenhuma (ou código = 0) → `tipo = NULL`, `nk_codigo_origem = 0`

A descrição é sempre preservada independentemente da resolução do tipo.

---

## Observações de carga

- `dim_data` deve ser populada uma única vez antes de qualquer carga de fatos, com um script Python que gera todas as datas de um intervalo (ex: 2020 até 2030).
- `data_saida` é nullable na fact porque uma OS pode estar aberta sem data de saída definida.
- `sk_motocicleta` é nullable porque no sistema fonte a ligação entre OS e moto pode estar incompleta.
- `fact_item_os` depende de `fact_ordem_de_servico` — a carga da fact pai deve ocorrer antes da carga dos itens.
