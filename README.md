# Concurrency Bench

## Programação Concorrente com Threads e Processos em Python

**Universidade Federal do Cariri — UFCA**  
**Centro de Ciência e Tecnologia — CCT**  
**Curso:** Bacharelado em Engenharia de Software  
**Disciplina:** Paradigmas de Programação — ES0012  
**Professor:** Rafael Will Macedo de Araujo  

### Integrantes

- Ana Aisha Tomaz de Morais
- Elilúcio Teixeira Félix Filho
- Grazielly Bibiano do Nascimento
- Icaro Cavalcante de Carvalho Pinheiro
- Matheus Rennan Freire Veras Teotonio
- Natalina de Freitas Oliveira
- Samuel Jackson Mesquita Lima

---

Laboratório didático de programação concorrente em Python para fins acadêmicos e práticos. O objetivo é estudar, medir e comparar o comportamento de diferentes mecanismos de concorrência sob workloads variados, incluindo cenários CPU-bound, I/O-bound e concorrência em banco de dados.

---

## 1. Contexto Geral e Funcionamento

O laboratório compara a performance e a segurança de quatro estratégias de execução:

1. **Sequencial:** sem concorrência, com execução síncrona de uma tarefa após a outra.
2. **Threads:** concorrência via `ThreadPoolExecutor`. Indicada principalmente para tarefas I/O-bound, mas limitada pelo GIL (Global Interpreter Lock) em tarefas CPU-bound no CPython tradicional.
3. **Processos:** concorrência via `ProcessPoolExecutor`. Permite paralelismo em múltiplos núcleos de CPU e contorna a limitação do GIL entre os diferentes processos, sendo adequada para tarefas CPU-bound.
4. **Programação Assíncrona (Asyncio):** concorrência cooperativa utilizando corrotinas e event loop, especialmente eficiente em cenários com grande quantidade de operações I/O-bound.

### Workloads de Simulação

- **CPU-bound:** cálculos matemáticos determinísticos que utilizam intensamente a CPU (`cpu_bound_work`).
- **I/O-bound HTTP:** acessos a endpoints web simulados localmente utilizando um servidor HTTP embutido (`LocalDelayServer`).
- **Concorrência de Estoque (Stock):** simula compras simultâneas para ilustrar problemas clássicos de condição de corrida (Race Condition), região crítica, sincronização e consistência.

---

## 2. Padrões de Projeto (Design Patterns)

O projeto adota práticas de engenharia de software e diferentes padrões de projeto.

### Clean Architecture — Arquitetura em Camadas

- `domain`: entidades e regras independentes de frameworks e bibliotecas, como `Product` e `ExperimentResult`.
- `application`: casos de uso de domínio, como `PurchaseProduct` e `RunExperiment`, além das interfaces abstratas (Ports).
- `infrastructure`: implementações físicas e integrações com banco de dados, servidor HTTP local, monitoramento de hardware com `psutil` e mecanismos de concorrência.
- `presentation`: pontos de entrada visuais, incluindo terminal e dashboard Streamlit.

### Strategy Pattern — Padrão Estratégia

As estratégias de concorrência:

- `SequentialStrategy`;
- `ThreadStrategy`;
- `ProcessStrategy`;
- `AsyncStrategy`;

são tratadas como componentes intercambiáveis que implementam uma mesma interface, como `ExecutionStrategy` ou `AsyncExecutionStrategy`.

O executor de experimentos (`RunExperiment`) não precisa conhecer os detalhes internos da implementação da estratégia utilizada.

### Repository Pattern — Padrão Repositório

O acesso aos dados do estoque é abstraído por meio da interface `ProductRepository`.

Isso permite alternar entre diferentes implementações, como:

- `InMemoryProductRepository`;
- `SqlAlchemyProductRepository`.

### Use Case / Command Pattern

Cada operação principal de negócio é modelada como um caso de uso autocontido e com responsabilidade específica.

---

## 3. Modelo de Dados (Persistência)

### Resultados de Experimentos / Benchmarks

Os resultados das execuções e benchmarks são persistidos no PostgreSQL.

Isso permite acessar e consultar o histórico de experimentos através da aba de **Histórico de Experimentos** no Streamlit, sem necessidade de reexecutar os testes anteriores.

O modelo é composto por duas tabelas principais.

### Tabela `experiments` — Metadados do Experimento

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do experimento. |
| `name` | `VARCHAR(255)` | Nome do experimento. |
| `experiment_type` | `VARCHAR(50)` | Tipo do experimento, como cpu_bound, http ou database. |
| `task_count` | `INTEGER` | Quantidade de tarefas ou requisições. |
| `description` | `TEXT` (nullable) | Descrição do cenário. |
| `parameters_json` | `TEXT` | Parâmetros de configuração em formato JSON. |
| `created_at` | `TIMESTAMP WITH TIMEZONE` | Data e hora em que o experimento foi gerado. |

### Tabela `experiment_results` — Métricas de Execução

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do registro. |
| `experiment_id` | `UUID` (Foreign Key) | Referência ao experimento. |
| `strategy` | `VARCHAR(50)` | Estratégia de concorrência utilizada. |
| `completed_task_count` | `INTEGER` | Quantidade de tarefas concluídas com sucesso. |
| `total_time_seconds` | `DOUBLE PRECISION` | Tempo total de execução do benchmark. |
| `cpu_usage_percent` | `DOUBLE PRECISION` (nullable) | Uso médio de CPU em porcentagem. |
| `memory_usage_mb` | `DOUBLE PRECISION` (nullable) | Uso médio de memória em MB. |
| `workers_used` | `INTEGER` (nullable) | Quantidade de workers configurados. |
| `speedup` | `DOUBLE PRECISION` (nullable) | Fator de speedup medido contra o baseline. |
| `metadata_json` | `TEXT` | Metadados específicos de execução em JSON. |

### Estoque e Compras — PostgreSQL

Para o cenário de consistência transacional concorrente, o banco de dados armazena o inventário dos produtos e os registros de pedidos.

O modelo é mapeado via SQLAlchemy em:

`infrastructure/database/models.py`

### Tabela `products` — Produtos em Estoque

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do produto. |
| `name` | `VARCHAR(255)` | Nome do produto. |
| `stock` | `INTEGER` | Quantidade atualizada disponível em estoque. |

### Tabela `purchases` — Histórico de Compras Aprovadas

| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único da transação. |
| `product_id` | `UUID` (Foreign Key) | Referência ao produto comprado. |
| `created_at` | `TIMESTAMP WITH TIMEZONE` | Data e hora em que a compra foi registrada. |

> [!NOTE]
> O `SqlAlchemyProductRepository` suporta dois modos de operação para fins didáticos:
>
> 1. **PostgreSQL sem Lock:** realiza o decremento sem bloqueio pessimista de linha e introduz um pequeno intervalo entre leitura e gravação. Sob concorrência, podem ocorrer condições de corrida, atualizações perdidas e inconsistências.
> 2. **PostgreSQL com transação e Lock de linha:** utiliza bloqueio pessimista por meio de `SELECT FOR UPDATE`, garantindo que apenas uma transação por vez modifique aquele registro durante a região crítica.

---

## 4. Conceitos de Concorrência Estudados

### Concorrência x Paralelismo

Concorrência significa permitir que diferentes tarefas progridam durante o mesmo intervalo de tempo.

Paralelismo ocorre quando duas ou mais tarefas são efetivamente executadas simultaneamente, normalmente utilizando diferentes núcleos da CPU.

### I/O-bound

Tarefas I/O-bound passam grande parte do tempo aguardando operações externas, como:

- requisições de rede;
- leitura e escrita de arquivos;
- banco de dados;
- APIs.

Threads e Asyncio são estratégias especialmente relevantes para esse cenário.

### CPU-bound

Tarefas CPU-bound utilizam intensamente a capacidade de processamento.

Exemplos incluem:

- cálculos matemáticos;
- processamento intensivo;
- algoritmos computacionalmente pesados.

Para esse cenário, múltiplos processos podem permitir melhor aproveitamento dos núcleos da CPU.

### GIL — Global Interpreter Lock

No CPython tradicional com o GIL habilitado, apenas uma thread por vez executa bytecode Python dentro de um mesmo processo.

Isso ajuda a explicar por que a utilização de múltiplas threads não garante paralelismo para tarefas CPU-bound.

Processos possuem interpretadores separados e podem explorar diferentes núcleos da CPU.

### Race Condition

Uma condição de corrida ocorre quando o resultado de uma operação depende da ordem em que diferentes tarefas concorrentes acessam ou modificam um mesmo recurso.

### Região Crítica e Lock

Uma região crítica corresponde a uma parte do programa que manipula um recurso compartilhado.

O `Lock` é um mecanismo utilizado para controlar o acesso a essa região e impedir que múltiplas threads realizem modificações inadequadas simultaneamente.

---

## 5. Tecnologias Utilizadas

- **Python 3.12+**
- **SQLAlchemy 2.0**
- **psycopg3**
- **Httpx**
- **Psutil**
- **Streamlit**
- **Matplotlib**
- **Pytest**
- **PostgreSQL**
- **Docker**

---

## 6. Como Executar o Projeto

### Pré-requisitos

É recomendado possuir:

- Python 3.12 ou superior;
- Git;
- Docker;
- Docker Compose.

### Instalação das Dependências

Crie um ambiente virtual Python:

```powershell
py -m venv .venv
```

Ative o ambiente:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale o projeto e as dependências:

```powershell
python -m pip install -e ".[dev]"
```

### Preparação do PostgreSQL

Crie o arquivo de configuração de ambiente a partir do modelo:

```powershell
Copy-Item .env.example .env
```

Inicie o PostgreSQL:

```powershell
docker compose up -d postgres
```

---

## 7. Executar os Experimentos

### Experimento CPU-bound

```powershell
python examples/cpu_bound_comparison.py
```

Compara principalmente:

- Sequencial;
- Threads;
- Processos.

O objetivo é observar o comportamento das estratégias diante de uma carga intensiva de processamento.

### Experimento I/O-bound

```powershell
python examples/io_bound_comparison.py
```

Compara estratégias em operações que envolvem espera de I/O.

O cenário permite analisar principalmente:

- Sequencial;
- Threads;
- Asyncio.

### Experimento de Concorrência de Estoque

```powershell
python examples/stock_concurrency_comparison.py
```

Permite visualizar:

- condição de corrida;
- inconsistência de dados;
- região crítica;
- sincronização;
- Lock.

### Experimento de Otimização e Concorrência de Cache

```powershell
python examples/cache_concurrency_comparison.py
```

Permite analisar:

- Cache Stampede (Thundering Herd);
- Otimização de I/O em memória;
- Cache Frio (vazio) vs. Cache Quente (preenchido);
- Cache sem Lock (múltiplas consultas redundantes);
- Cache com Lock (sincronização de recursos).

---

## 8. Dashboard Streamlit

Para iniciar a interface gráfica:

```powershell
streamlit run src/concurrency_bench/presentation/streamlit/app.py
```

O dashboard permite executar e visualizar os experimentos de maneira mais interativa.

A interface auxilia na análise de:

- tempo de execução;
- utilização de CPU;
- uso de memória;
- throughput;
- quantidade de workers;
- speedup;
- histórico dos experimentos.

O Streamlit atua como camada de apresentação e não como estratégia de concorrência.

---

## 9. Métricas de Comparação

Os experimentos podem avaliar métricas como:

| Métrica | Finalidade |
| --- | --- |
| Tempo total | Verificar quanto tempo cada estratégia necessita para finalizar a carga. |
| CPU | Avaliar utilização do processador. |
| Memória | Observar consumo de memória. |
| Throughput | Medir quantas tarefas são concluídas em determinado intervalo de tempo. |
| Workers | Registrar quantidade de unidades de execução configuradas. |
| Speedup | Comparar o ganho de desempenho em relação a uma estratégia de referência. |

Para uma comparação adequada, os experimentos devem utilizar cargas equivalentes e condições semelhantes.

---

## 10. Executar os Testes

Para executar os testes automatizados:

```bash
python -m pytest
```

Os testes auxiliam na validação do funcionamento dos componentes do projeto.

---

## 11. Documentação Técnica

A documentação complementar do projeto está disponível na pasta `docs`.

### Guia de Execução

[`docs/guia.md`](docs/guia.md)

Apresenta:

- preparação do ambiente;
- instalação;
- execução dos experimentos;
- execução do Streamlit;
- validação com Pytest.

### Regras e Funcionamento

[`docs/regras_e_funcionamento.md`](docs/regras_e_funcionamento.md)

Apresenta os principais conceitos e regras relacionados a:

- execução sequencial;
- Threads;
- Processos;
- Asyncio;
- I/O-bound;
- CPU-bound;
- GIL;
- condição de corrida;
- região crítica;
- Lock.

### Relatório Técnico

[`docs/relatorio.md`](docs/relatorio.md)

Apresenta:

- fundamentação teórica;
- relação entre teoria e implementação;
- metodologia experimental;
- análise de I/O-bound;
- análise de CPU-bound;
- análise do GIL;
- sincronização;
- limitações;
- critérios para escolha da estratégia.

---

## 12. Síntese das Estratégias

| Cenário | Estratégia a considerar |
| --- | --- |
| Execução pequena e linear | Sequencial |
| Operações com espera de I/O | Threads |
| Muitas operações assíncronas de I/O | Asyncio |
| Processamento intensivo de CPU | Processos |
| Acesso concorrente a recurso compartilhado | Sincronização com Lock |

Essa classificação funciona como orientação geral.

A escolha adequada depende das características do problema, da carga de trabalho, do ambiente de execução e do custo introduzido por cada mecanismo.

---

## 13. Conclusão

O projeto demonstra que diferentes mecanismos de concorrência apresentam comportamentos distintos conforme o tipo de carga de trabalho.

Em tarefas I/O-bound, Threads e Asyncio podem aproveitar os períodos de espera para permitir o progresso de outras tarefas.

Em tarefas CPU-bound, o comportamento tradicional do GIL limita o paralelismo de bytecode Python entre threads de um mesmo processo. A utilização de múltiplos processos permite explorar diferentes núcleos da CPU.

Quando existe compartilhamento de recursos, mecanismos de sincronização tornam-se essenciais para evitar condições de corrida e preservar a consistência.

Assim, o objetivo não é determinar uma única estratégia como superior, mas compreender em quais situações cada mecanismo é mais adequado.

---

## 14. Referências

- PYTHON SOFTWARE FOUNDATION. **Python Documentation — threading: Thread-based parallelism.**  
  https://docs.python.org/3/library/threading.html

- PYTHON SOFTWARE FOUNDATION. **Python Documentation — multiprocessing: Process-based parallelism.**  
  https://docs.python.org/3/library/multiprocessing.html

- PYTHON SOFTWARE FOUNDATION. **Python Documentation — asyncio: Asynchronous I/O.**  
  https://docs.python.org/3/library/asyncio.html

- PYTHON SOFTWARE FOUNDATION. **Python Documentation — concurrent.futures.**  
  https://docs.python.org/3/library/concurrent.futures.html

- PYTHON SOFTWARE FOUNDATION. **Python Documentation — Global Interpreter Lock.**  
  https://docs.python.org/3/glossary.html#term-global-interpreter-lock

- STREAMLIT. **Streamlit Documentation.**  
  https://docs.streamlit.io/

- SQLALCHEMY. **SQLAlchemy Documentation.**  
  https://docs.sqlalchemy.org/

- BEAZLEY, David; JONES, Brian K. **Python Cookbook.** 3. ed. O'Reilly Media, 2013.

- LUTZ, Mark. **Learning Python.** 5. ed. O'Reilly Media, 2013.

- RAMALHO, Luciano. **Fluent Python.** 2. ed. O'Reilly Media, 2022.
