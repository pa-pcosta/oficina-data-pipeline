# Script de Extração Automatizada — `extract_clientes.py`

## O que este script faz

O script acessa automaticamente o sistema de gestão da oficina via navegador, faz login, navega até o relatório de clientes e dispara o download do arquivo CSV — sem nenhuma interação manual. O arquivo baixado é renomeado com a data de execução e salvo em um diretório estruturado.

---

## Por que Selenium?

O sistema da oficina não oferece uma API de integração. Os dados só são acessíveis pela interface web, exigindo uma abordagem de **automação de navegador**. O Selenium WebDriver controla o Chrome programaticamente, simulando exatamente o que um usuário faria manualmente: abrir o navegador, preencher campos, clicar em botões e aguardar downloads.

---

## Tecnologias utilizadas

| Biblioteca | Função |
|---|---|
| `selenium` | Controla o navegador Chrome |
| `webdriver-manager` | Baixa e gerencia o ChromeDriver automaticamente |
| `python-dotenv` | Lê credenciais e configurações do arquivo `.env` |

---

## Separação de configuração e código — o arquivo `.env`

As credenciais e caminhos de sistema ficam num arquivo `.env` separado do código, nunca versionado no Git. O script lê esse arquivo ao iniciar:

```
SISTEMA_BASE_URL=https://sistema.oficinaintegrada.com.br
SISTEMA_LOGIN_URL=${SISTEMA_BASE_URL}/login.asp
SISTEMA_ID_OFICINA=...
SISTEMA_USUARIO=...
SISTEMA_SENHA=...
DOWNLOAD_BASE=/caminho/para/os/dados
```

O `python-dotenv` suporta interpolação de variáveis (`${VAR}`), então `SISTEMA_LOGIN_URL` é montado automaticamente a partir de `SISTEMA_BASE_URL`. Isso evita repetição e facilita trocar o ambiente (desenvolvimento, produção).

```python
load_dotenv(Path(__file__).parent.parent / ".env")
```

O caminho explícito garante que o `.env` seja encontrado independente de onde o script for executado — relevante quando for integrado ao Airflow futuramente.

---

## Fluxo de execução

```
1. Carregar variáveis do .env
2. Configurar o Chrome (diretório de download)
3. Login no sistema
4. Navegar até o relatório de clientes
5. Disparar o download via JavaScript
6. Aguardar o arquivo aparecer no diretório
7. Renomear o arquivo com a data de hoje
8. Encerrar o navegador
```

---

## Configuração do Chrome

Antes de abrir o navegador, o script instrui o Chrome a salvar downloads automaticamente num diretório específico, sem exibir caixas de diálogo:

```python
options.add_experimental_option("prefs", {
    "download.default_directory": os.path.abspath(download_dir),
    "download.prompt_for_download": False,
    ...
})
```

O diretório é criado automaticamente se não existir (`os.makedirs(..., exist_ok=True)`).

---

## Login

O formulário de login do sistema tem três campos obrigatórios identificados por inspeção do HTML:

| Campo HTML (`id`) | Valor |
|---|---|
| `chave` | ID da oficina (identifica o tenant no sistema) |
| `usuario` | Nome de usuário |
| `senha` | Senha |

O botão de login (`id="btnLogar"`) é uma tag `<a>` que dispara uma função JavaScript — o Selenium clica nele normalmente.

Após o clique, o script aguarda a URL mudar (sair da página `/login.asp`) antes de prosseguir, garantindo que o login foi concluído:

```python
wait.until(lambda d: "login" not in d.current_url.lower())
```

---

## Download do CSV — decisão de implementação

O botão de exportação no sistema é um **dropdown ativado por hover** (mouse sobre o botão abre o menu). Isso apresentou um desafio:

- Forçar o estado `:hover` via DevTools **não funciona** porque o dropdown é controlado por um listener JavaScript (`mouseenter`), não por CSS puro.
- Clicar no botão também não abre o menu, pois ele foi projetado para hover.

**Solução adotada:** chamar diretamente a função JavaScript responsável pelo download, sem passar pela interface do dropdown:

```python
driver.execute_script("exportarCSV();")
```

Isso é possível porque o Selenium permite executar JavaScript arbitrário no contexto da página. A abordagem é mais robusta que tentar simular interações de mouse, pois não depende do estado visual da interface.

---

## Aguardar e renomear o arquivo

O sistema gera o arquivo com um nome genérico. O script monitora o diretório de download até o arquivo aparecer, ignora arquivos `.crdownload` (download ainda em progresso do Chrome) e renomeia para o padrão `AAAA-MM-DD.csv`:

```python
# Aguarda até um .csv completo aparecer no diretório
arquivos = [f for f in glob.glob("*.csv") if not f.endswith(".crdownload")]

# Seleciona o mais recente e renomeia
arquivo_baixado = max(arquivos, key=os.path.getctime)
shutil.move(arquivo_baixado, destino)
```

O resultado é um arquivo como `2026-06-06.csv` dentro de `data/raw/clientes/`.

---

## Estrutura de diretórios gerada

```
data/raw/
└── clientes/
    ├── 2026-06-01.csv
    └── 2026-06-06.csv
```

Cada execução gera um novo arquivo com a data do dia. Execuções repetidas no mesmo dia sobrescrevem o arquivo existente.

---

## Tratamento de falhas

O driver do Chrome é sempre encerrado ao final, mesmo em caso de erro:

```python
try:
    ...  # toda a lógica de extração
finally:
    driver.quit()  # executado mesmo se ocorrer exceção
```

Sem isso, processos do Chrome ficariam abertos em segundo plano após falhas.

---

## Evolução futura — integração com Airflow

Atualmente o script é executado manualmente. Na próxima etapa do pipeline, ele será integrado ao **Apache Airflow**, que fará o agendamento e rerrodará execuções passadas em caso de falha. As únicas mudanças necessárias no script serão:

1. Substituir `os.environ["..."]` por `Variable.get("...")` (variáveis do Airflow)
2. Receber a data de referência via `context["logical_date"]` em vez de `date.today()`
3. Adicionar `**context` na assinatura de `run_extraction()`

O restante da lógica — login, navegação, download, renomeação — permanece idêntico.
