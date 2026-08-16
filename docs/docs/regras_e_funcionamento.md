# Regras e Funcionamento do Projeto

## 1. Visão geral

O projeto compara diferentes formas de executar tarefas em Python, analisando quando cada estratégia de concorrência apresenta vantagens ou limitações.

As principais abordagens estudadas são:

- execução sequencial;
- Threads;
- Processos;
- Asyncio;
- sincronização com Lock.

A escolha da estratégia depende principalmente do tipo de tarefa executada.

---

## 2. Execução sequencial

Na execução sequencial, uma tarefa é concluída antes que a próxima seja iniciada.

Exemplo:

Tarefa A → Tarefa B → Tarefa C

Essa abordagem apresenta um fluxo simples e previsível, mas pode desperdiçar tempo quando uma tarefa precisa aguardar operações externas.

---

## 3. Threads

Threads são fluxos de execução que pertencem ao mesmo processo.

Elas compartilham recursos e memória, o que facilita a comunicação entre as tarefas, mas também exige cuidado quando várias threads acessam e modificam o mesmo dado.

Threads são especialmente úteis em tarefas I/O-bound.

Exemplos:

- requisições de rede;
- leitura e escrita de arquivos;
- acesso a banco de dados;
- espera por respostas de serviços externos.

Enquanto uma thread aguarda uma operação de entrada ou saída, outra pode continuar trabalhando.

---

## 4. Processos

Processos possuem espaços de memória separados e seus próprios interpretadores Python.

Eles apresentam maior custo de criação e comunicação quando comparados às threads, mas podem executar tarefas simultaneamente em diferentes núcleos da CPU.

Por isso, processos são especialmente relevantes em tarefas CPU-bound.

Exemplos:

- cálculos matemáticos intensivos;
- processamento de grandes volumes de dados;
- algoritmos que utilizam intensamente a CPU.

---

## 5. Asyncio

Asyncio é uma abordagem de programação assíncrona baseada em um event loop.

Em vez de criar várias threads, uma tarefa pode liberar temporariamente a execução enquanto aguarda uma operação de I/O.

Nesse período, o event loop pode permitir que outra tarefa avance.

Asyncio é indicado principalmente quando existem muitas operações de I/O sendo executadas concorrentemente.

---

## 6. I/O-bound e CPU-bound

A identificação do tipo de tarefa é fundamental para escolher a estratégia adequada.

### I/O-bound

Uma tarefa é considerada I/O-bound quando grande parte do tempo é utilizada aguardando operações externas.

Exemplos:

- rede;
- arquivos;
- banco de dados;
- APIs.

Nesses casos, Threads e Asyncio podem apresentar vantagens.

### CPU-bound

Uma tarefa é considerada CPU-bound quando a maior parte do tempo é utilizada em cálculos e processamento.

Exemplos:

- operações matemáticas;
- processamento intensivo;
- algoritmos computacionalmente pesados.

Nesse cenário, o uso de Processos pode permitir melhor aproveitamento de múltiplos núcleos da CPU.

---

## 7. GIL

O GIL, ou Global Interpreter Lock, é um mecanismo presente no CPython tradicional.

Ele permite que apenas uma thread execute bytecode Python por vez dentro de um mesmo processo.

Por esse motivo, adicionar várias threads a uma tarefa CPU-bound não significa necessariamente executar código Python simultaneamente em vários núcleos.

Isso ajuda a explicar por que:

- Threads são adequadas para muitos cenários I/O-bound;
- Processos são mais adequados para explorar paralelismo em tarefas CPU-bound.

Cada processo possui seu próprio interpretador e, consequentemente, seu próprio GIL.

---

## 8. Concorrência e paralelismo

Concorrência e paralelismo são conceitos relacionados, mas diferentes.

### Concorrência

Na concorrência, várias tarefas podem progredir durante o mesmo intervalo de tempo.

Elas não precisam estar sendo executadas exatamente no mesmo instante.

### Paralelismo

No paralelismo, duas ou mais tarefas são efetivamente executadas ao mesmo tempo, normalmente utilizando diferentes núcleos de processamento.

Assim:

- concorrência está relacionada à organização de várias tarefas;
- paralelismo está relacionado à execução simultânea.

---

## 9. Condição de corrida

Uma condição de corrida pode acontecer quando duas ou mais tarefas acessam e modificam um mesmo recurso compartilhado concorrentemente.

O resultado pode depender da ordem em que as operações acontecem.

Exemplo:

Estoque inicial = 1

Thread A lê estoque = 1.

Thread B também lê estoque = 1.

As duas podem tentar concluir uma compra, mesmo existindo apenas uma unidade disponível.

Esse comportamento pode produzir inconsistências.

---

## 10. Região crítica

Região crítica é a parte do código que acessa ou modifica um recurso compartilhado e que precisa ser protegida contra acessos concorrentes inadequados.

No exemplo do estoque, a verificação e a atualização da quantidade disponível formam uma região crítica.

---

## 11. Lock

Lock é um mecanismo de sincronização utilizado para controlar o acesso a uma região crítica.

Quando uma thread adquire o Lock, as outras precisam esperar até que ele seja liberado.

Exemplo:

Thread A → adquire Lock → consulta estoque → realiza operação → libera Lock.

Thread B → aguarda → adquire Lock → consulta estoque atualizado.

Dessa forma, o Lock ajuda a evitar condições de corrida e inconsistências em recursos compartilhados.

---

## 12. Comparação entre as estratégias

De forma geral:

| Cenário | Estratégia mais adequada |
| --- | --- |
| Fluxo simples | Sequencial |
| Espera de rede, arquivos ou banco | Threads |
| Muitas operações assíncronas de I/O | Asyncio |
| Processamento intensivo de CPU | Processos |
| Recurso compartilhado | Sincronização com Lock |

Essa relação não deve ser interpretada como uma regra absoluta. A estratégia adequada depende das características específicas da aplicação.

---

## 13. Regras para os experimentos

Para que as comparações sejam coerentes, os experimentos devem utilizar condições equivalentes sempre que possível.

Isso inclui:

- executar o mesmo tipo de tarefa;
- utilizar a mesma máquina;
- manter parâmetros equivalentes;
- comparar as mesmas métricas;
- evitar alterar a carga de trabalho entre estratégias.

As principais métricas observadas podem incluir:

- tempo de execução;
- throughput;
- uso de CPU;
- uso de memória;
- speedup.

---

## 14. Regra principal do projeto

A principal ideia demonstrada pelo projeto é que não existe uma única estratégia de concorrência que seja melhor em todos os cenários.

A escolha depende da natureza da tarefa:

- I/O-bound → Threads ou Asyncio;
- CPU-bound → Processos;
- recurso compartilhado → mecanismos de sincronização, como Lock.