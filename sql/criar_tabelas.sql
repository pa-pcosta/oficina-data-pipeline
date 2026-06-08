-- ─────────────────────────────────────────────────────────────────────────────
-- Tabelas de dimensão
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE dim_data (
    sk_data          INT           PRIMARY KEY, -- formato YYYYMMDD ex: 20260128
    dt_data_completa DATE          NOT NULL,
    nr_dia           INT           NOT NULL,
    nr_mes           INT           NOT NULL,
    nr_ano           INT           NOT NULL,
    nr_trimestre     INT           NOT NULL,
    nr_semana_ano    INT           NOT NULL,
    nm_mes           VARCHAR(20)   NOT NULL,
    nm_dia_semana    VARCHAR(20)   NOT NULL,
    fl_fim_semana    BOOLEAN       NOT NULL,
    fl_feriado       BOOLEAN
);

CREATE TABLE dim_cliente (
    sk_cliente       BIGSERIAL     PRIMARY KEY,
    nk_cliente       INT           UNIQUE NOT NULL,
    nome             VARCHAR(255),
    bairro           VARCHAR(100),
    cidade           VARCHAR(100),
    uf               VARCHAR(2),
    fl_tipo_pessoa   VARCHAR(2), -- 'PF' ou 'PJ'
    cpf              VARCHAR(14),
    cnpj             VARCHAR(18),
    dt_cadastro      DATE,
    dt_nascimento    DATE
);

CREATE TABLE dim_motocicleta (
    sk_motocicleta   BIGSERIAL     PRIMARY KEY,
    nk_motocicleta   INT           UNIQUE NOT NULL,
    placa            VARCHAR(10),
    marca            VARCHAR(100),
    modelo           VARCHAR(100),
    versao           VARCHAR(100),
    cor              VARCHAR(50),
    ano              VARCHAR(4),
    chassi           VARCHAR(50)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- Tabelas FATO
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE fact_ordem_de_servico (
    sk_ordem_de_servico  BIGSERIAL     PRIMARY KEY,
    nk_ordem_de_servico  INT,                                              -- chave degenerada, sem FK
    valor_total          NUMERIC(10,2),
    valor_desconto       NUMERIC(10,2),
    km_motocicleta       INT,
    data_inclusao        INT           NOT NULL REFERENCES dim_data(sk_data),
    data_saida           INT                    REFERENCES dim_data(sk_data),
    sk_cliente           BIGINT        NOT NULL REFERENCES dim_cliente(sk_cliente),
    sk_motocicleta       BIGINT                 REFERENCES dim_motocicleta(sk_motocicleta)
);

CREATE TABLE fact_item_os (
    sk_item_os           BIGSERIAL     PRIMARY KEY,
    sk_ordem_servico     BIGINT        NOT NULL REFERENCES fact_ordem_de_servico(sk_ordem_de_servico),
    nk_ordem_servico     INT,          -- chave degenerada, mesma da fact pai
    tipo                 VARCHAR(10),  -- 'produto', 'servico' ou NULL
    nk_codigo_origem     INT,          -- id do produto/servico na fonte (0 = não cadastrado)
    descricao            VARCHAR(255),
    quantidade           NUMERIC(10,2),
    vl_unitario          NUMERIC(10,2),
    vl_total             NUMERIC(10,2),
    vl_desconto          NUMERIC(10,2),
    fl_aprovado          BOOLEAN
);
