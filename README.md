# Concurrency Bench

Laboratório didático de programação concorrente em Python para fins acadêmicos e práticos. O objetivo é estudar, medir e comparar o comportamento de diferentes mecanismos de concorrência sob workloads variados (CPU-bound, I/O-bound e concorrência em banco de dados).

---

## 1. Contexto Geral e Funcionamento

O laboratório compara a performance e a segurança de quatro estratégias de execução:
1. **Sequencial**: Sem concorrência, execução síncrona uma tarefa após a outra.
2. **Threads**: Concorrência via `ThreadPoolExecutor`. Indicado para I/O-bound, mas limitado pelo GIL (Global Interpreter Lock) em CPU-bound.
3. **Processos**: Concorrência via `ProcessPoolExecutor`. Execução paralela real em múltiplos núcleos de CPU (contorna o GIL), ideal para CPU-bound.
4. **Programação Assíncrona (Asyncio)**: Concorrência cooperativa de thread única usando corrotinas. Altamente eficiente para alta concorrência I/O-bound.

### Workloads de Simulação
*   **CPU-bound**: Cálculos matemáticos determinísticos pesados de CPU (`cpu_bound_work`).
*   **I/O-bound HTTP**: Acessos a endpoints web, simulados localmente usando um servidor HTTP embutido (`LocalDelayServer`).
*   **Concorrência de Estoque (Stock)**: Simula compras simultâneas para ilustrar problemas clássicos de condições de corrida (Race Conditions) e consistência.

---

## 2. Padrões de Projeto (Design Patterns)

O projeto adota práticas avançadas de engenharia de software e padrões de design:

*   **Clean Architecture (Arquitetura em Camadas)**:
    *   `domain`: Entidades puras e regras independentes de frameworks e bibliotecas (ex: `Product`, `ExperimentResult`).
    *   `application`: Casos de uso de domínio (`PurchaseProduct`, `RunExperiment`) e interfaces abstratas (Ports).
    *   `infrastructure`: Implementações físicas e integrações com banco, servidor HTTP local, monitoramento de hardware (`psutil`) e concorrência de baixo nível.
    *   `presentation`: Pontos de entrada visuais (terminal e dashboard Streamlit).
*   **Strategy Pattern (Padrão Estratégia)**: As estratégias de concorrência (`SequentialStrategy`, `ThreadStrategy`, `ProcessStrategy`, `AsyncStrategy`) são tratadas como peças intercambiáveis que implementam a mesma interface (`ExecutionStrategy` ou `AsyncExecutionStrategy`). O executor de experimentos (`RunExperiment`) não conhece os detalhes de infraestrutura da estratégia escolhida.
*   **Repository Pattern (Repositório)**: Acesso aos dados do estoque abstraído pela interface `ProductRepository`. Isso permite alternar de forma transparente entre o repositório em memória (`InMemoryProductRepository`) e o banco relacional real (`SqlAlchemyProductRepository`).
*   **Use Case / Command Pattern**: Cada operação de negócio principal é modelada como um caso de uso autocontido com responsabilidade única.

---

## 3. Modelo de Dados (Persistência)

### Resultados de Experimentos / Benchmarks (Persistência de Histórico)
Os resultados das execuções e benchmarks são persistidos fisicamente no PostgreSQL. Isso permite acessar e auditar o histórico de experimentos através da aba de "Histórico de Experimentos" no Streamlit sem necessidade de reexecutá-los. O modelo é composto por duas tabelas:

#### Tabela `experiments` (Metadados do Experimento)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do experimento. |
| `name` | `VARCHAR(255)` | Nome do experimento. |
| `experiment_type` | `VARCHAR(50)` | Tipo do experimento (cpu_bound, http, database, etc.). |
| `task_count` | `INTEGER` | Quantidade de tarefas/requisições. |
| `description` | `TEXT` (nullable) | Descrição do cenário. |
| `parameters_json` | `TEXT` | Dicionário de parâmetros de configuração em formato JSON. |
| `created_at` | `TIMESTAMP WITH TIMEZONE` | Data e hora em que o experimento foi gerado. |

#### Tabela `experiment_results` (Métricas de Execução)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do registro de métrica. |
| `experiment_id` | `UUID` (Foreign Key) | Referência para o experimento (`experiments.id`, cascade). |
| `strategy` | `VARCHAR(50)` | Estratégia de concorrência utilizada (threads, processes, async, etc.). |
| `completed_task_count` | `INTEGER` | Quantidade de tarefas concluídas com sucesso. |
| `total_time_seconds` | `DOUBLE PRECISION` | Tempo total de execução do benchmark. |
| `cpu_usage_percent` | `DOUBLE PRECISION` (nullable) | Uso médio de CPU em porcentagem. |
| `memory_usage_mb` | `DOUBLE PRECISION` (nullable) | Uso médio de memória em MB. |
| `workers_used` | `INTEGER` (nullable) | Quantidade de workers simultâneos configurados. |
| `speedup` | `DOUBLE PRECISION` (nullable) | Fator de speedup medido contra o baseline. |
| `metadata_json` | `TEXT` | Dicionário de metadados específicos de execução (como estoque final ou lista de resultados individuais) em JSON. |

### Estoque e Compras (PostgreSQL)
Para o cenário de consistência transacional concorrente, o banco de dados armazena o inventário de produtos e os logs de pedidos. O modelo de dados (mapeado via SQLAlchemy em `infrastructure/database/models.py`) é estruturado em duas tabelas:

#### Tabela `products` (Produtos em estoque)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único do produto. |
| `name` | `VARCHAR(255)` | Nome do produto. |
| `stock` | `INTEGER` | Quantidade atualizada disponível em estoque. |

#### Tabela `purchases` (Histórico de compras aprovadas)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `id` | `UUID` (Primary Key) | Identificador único da transação de compra (gerado automaticamente). |
| `product_id` | `UUID` (Foreign Key) | Referência ao produto comprado (`products.id`, deleção em cascata). |
| `created_at` | `TIMESTAMP WITH TIMEZONE` | Data e hora em que a transação de compra foi registrada. |

> [!NOTE]
> O `SqlAlchemyProductRepository` suporta dois modos de operação para fins didáticos:
> 1. **PostgreSQL sem Lock**: Realiza o decremento diretamente sem bloqueio pessimista de linha e introduz um pequeno delay (tempo de interleave) entre a leitura e a gravação. Sob concorrência múltipla, isso leva a condições de corrida severas no banco de dados (gerando atualizações perdidas e permitindo estoque negativo/inconsistência na tabela `products`).
> 2. **PostgreSQL com transação e lock de linha**: Utiliza bloqueio pessimista de linha (`SELECT FOR UPDATE`), garantindo consistência estrita: apenas uma transação por vez lê e decrementa o estoque daquele registro, impedindo qualquer inconsistência.

---

## 4. Tecnologias Utilizadas

*   **Python 3.12+**
*   **SQLAlchemy 2.0 & psycopg3** (ORMs e conexões PostgreSQL)
*   **Httpx** (Requisições HTTP síncronas e assíncronas)
*   **Psutil** (Aferição de consumo de recursos de CPU e memória do processo)
*   **Streamlit** (Interface gráfica interativa)
*   **Matplotlib** (Geração de gráficos comparativos especializados para exportação)
*   **Pytest** (Testes de unidade e integração)
*   **PostgreSQL** (Rodando em container via Docker)

---

## 5. Como Executar o Projeto

### Pré-requisitos (PostgreSQL local)
Crie o arquivo de configuração de ambiente a partir do modelo e inicie o serviço do banco de dados:
```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

### Instalação de Dependências
Crie um ambiente virtual Python e instale o pacote em modo editável com as dependências de desenvolvimento:
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Executar Exemplos via Terminal
```powershell
python examples/cpu_bound_comparison.py
python examples/io_bound_comparison.py
python examples/stock_concurrency_comparison.py
```

### Executar Dashboard Streamlit
```powershell
streamlit run src/concurrency_bench/presentation/streamlit/app.py
```

### Rodar os Testes
```bash
python -m pytest
```
