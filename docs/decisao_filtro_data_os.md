# Decisão de Design — Filtro de Data nas Ordens de Serviço

## Contexto

O relatório de Ordens de Serviço (OS) do sistema permite filtrar por três tipos de data:

| Opção | Significado |
|---|---|
| **Entrada** | Data em que a motocicleta deu entrada na oficina |
| **Previsão** | Data estimada de conclusão do serviço |
| **Saída** | Data em que o serviço foi concluído e a moto entregue |

## Decisão

As extrações recorrentes filtram por **data de entrada**.

## Justificativa

Filtrar por data de entrada é a única estratégia que garante a captura completa de todas as OSs abertas no período, independente do seu estado atual.

- Uma OS filtrada por **data de saída** só aparece após a conclusão do serviço. OSs ainda em andamento ficam invisíveis — o que impede análises de backlog, atrasos e fila de trabalho.
- Uma OS filtrada por **data de entrada** aparece desde o momento em que chega na oficina, esteja ela aberta ou fechada. A coluna `data_saida` no próprio CSV indica o estado: preenchida = concluída, vazia = em aberto.

Isso permite que uma única extração alimente múltiplas análises na camada downstream (dbt/SQL):

- **OSs concluídas** → `WHERE data_saida IS NOT NULL` → receita realizada, tempo de ciclo
- **OSs em aberto** → `WHERE data_saida IS NULL` → backlog, priorização por `data_previsao`
- **Atrasos** → `WHERE data_saida IS NULL AND data_previsao < CURRENT_DATE`
- **Demanda** → volume de OSs por data de entrada

## Estratégia de carga

| Tipo | Janela | Quando |
|---|---|---|
| **Carga inicial** | Histórico completo (intervalo amplo) | Uma única vez, manualmente |
| **Extrações recorrentes** | Últimos 7 dias por data de entrada | Execução semanal automatizada |

A janela de 7 dias nas extrações recorrentes garante que OSs abertas há menos de uma semana sejam capturadas. OSs com mais de 7 dias de entrada mas ainda abertas já foram capturadas em execuções anteriores.

## Verificação no script

O sistema já define "Entrada" como opção padrão do filtro. O script verifica isso programaticamente antes de prosseguir:

```python
select = Select(driver.find_element(By.ID, "DATA_TIPO"))
assert select.first_selected_option.text.strip() == "Entrada", \
    "Filtro de data não está em 'Entrada' — verifique o formulário"
```
