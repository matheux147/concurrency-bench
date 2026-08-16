# Guia de Execução

## 1. Objetivo

Este projeto é um laboratório didático de programação concorrente em Python.

O objetivo é executar e comparar diferentes estratégias de processamento em cenários com características distintas:

- tarefas CPU-bound;
- tarefas I/O-bound;
- concorrência sobre recursos compartilhados;
- execução sequencial, com threads, processos e programação assíncrona.

Os experimentos permitem observar diferenças de desempenho, uso de recursos e comportamento diante de condições de corrida.

---

## 2. Pré-requisitos

Para executar o projeto, recomenda-se ter instalado:

- Python 3.12 ou superior;
- Git;
- Docker;
- Docker Compose.

O PostgreSQL utilizado pelo projeto é executado por meio de um container Docker.

---

## 3. Preparação do ambiente

Após obter o projeto, abra um terminal na pasta principal do repositório.

### 3.1 Criar o arquivo de ambiente

No Windows PowerShell:

```powershell
Copy-Item .env.example .env

```

Esse comando cria o arquivo `.env` a partir do modelo `.env.example`.

### 3.2 Iniciar o PostgreSQL

Execute:

```powershell
docker compose up -d postgres
```

O Docker iniciará o banco de dados PostgreSQL utilizado pelos experimentos que dependem de persistência.

---

## 4. Criar o ambiente virtual Python

No Windows:

```powershell
py -m venv .venv
```

Depois, ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

O ambiente virtual mantém as dependências do projeto separadas das demais instalações de Python do computador.

---

## 5. Instalar as dependências

Com o ambiente virtual ativado, execute:

```powershell
python -m pip install -e ".[dev]"
```

Esse comando instala o projeto e as dependências necessárias para execução, testes e desenvolvimento.

---

## 6. Executar os experimentos

O projeto possui exemplos específicos para os principais cenários estudados.

### 6.1 Experimento CPU-bound

Execute:

```powershell
python examples/cpu_bound_comparison.py
```

Esse experimento compara estratégias em tarefas que exigem processamento intenso da CPU.

A comparação permite observar o comportamento de:

- execução sequencial;
- threads;
- processos.

Nesse cenário, o uso de processos é especialmente relevante porque permite explorar múltiplos núcleos de CPU.

---

### 6.2 Experimento I/O-bound

Execute:

```powershell
python examples/io_bound_comparison.py
```

Esse experimento simula operações de entrada e saída utilizando requisições HTTP locais.

A comparação envolve principalmente:

- execução sequencial;
- threads;
- programação assíncrona com Asyncio.

O objetivo é observar como a concorrência pode reduzir o tempo ocioso enquanto uma operação aguarda uma resposta externa.

---

### 6.3 Experimento de concorrência de estoque

Execute:

```powershell
python examples/stock_concurrency_comparison.py
```

Esse cenário simula várias operações de compra concorrendo pelo mesmo estoque.

O experimento permite visualizar conceitos como:

- condição de corrida;
- região crítica;
- acesso simultâneo a dados;
- sincronização;
- uso de Lock.

A comparação demonstra a diferença entre permitir acessos concorrentes sem proteção e controlar o acesso ao recurso compartilhado.

---

## 7. Executar a interface Streamlit

Para iniciar a interface gráfica, execute:

```powershell
streamlit run src/concurrency_bench/presentation/streamlit/app.py
```

O Streamlit abrirá uma interface no navegador.

Por meio dela, é possível visualizar e executar os experimentos de forma mais interativa.

---

## 8. Métricas observadas

Os experimentos podem utilizar métricas como:

- tempo total de execução;
- quantidade de tarefas concluídas;
- uso de CPU;
- uso de memória;
- quantidade de workers;
- speedup.

Essas métricas auxiliam na comparação entre as estratégias de concorrência.

---

## 9. Executar os testes

Para verificar o funcionamento do projeto, execute:

```powershell
python -m pytest
```

Os testes ajudam a verificar se os componentes continuam funcionando corretamente após alterações no projeto.

---

## 10. Sequência recomendada para demonstração

Para a apresentação do projeto, recomenda-se executar os experimentos na seguinte ordem:

1. I/O-bound;
2. CPU-bound;
3. concorrência de estoque;
4. dashboard Streamlit.

Essa sequência facilita a compreensão das diferenças entre os cenários e das estratégias utilizadas.

---

## 11. Resumo

A execução dos experimentos permite observar que não existe uma única estratégia de concorrência adequada para todas as situações.

De forma geral:

- tarefas I/O-bound podem se beneficiar de Threads ou Asyncio;
- tarefas CPU-bound podem se beneficiar de Processos;
- recursos compartilhados exigem mecanismos de sincronização;
- a escolha da estratégia deve considerar o tipo de carga de trabalho e os recursos utilizados.
