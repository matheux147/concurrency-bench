# Relatório Técnico — Programação Concorrente em Python

## 1. Introdução

A programação concorrente permite organizar um sistema para que diferentes tarefas possam progredir durante um mesmo intervalo de tempo.

Em Python, diferentes mecanismos podem ser utilizados de acordo com as características da aplicação, entre eles:

- execução sequencial;
- Threads;
- Processos;
- programação assíncrona com Asyncio;
- mecanismos de sincronização, como Lock.

Este projeto busca relacionar esses conceitos teóricos com experimentos práticos, permitindo comparar o comportamento das estratégias em diferentes tipos de carga de trabalho.

Os principais cenários analisados são:

- tarefas I/O-bound;
- tarefas CPU-bound;
- acesso concorrente a recursos compartilhados.

---

## 2. Concorrência e paralelismo

Concorrência e paralelismo são conceitos relacionados, mas não equivalentes.

### 2.1 Concorrência

Na concorrência, diferentes tarefas podem avançar durante o mesmo período de tempo.

Isso não significa necessariamente que estejam executando exatamente no mesmo instante. As tarefas podem ser intercaladas pelo sistema.

Um exemplo ocorre quando uma tarefa aguarda uma resposta de rede e, durante esse período, outra tarefa pode continuar sua execução.

### 2.2 Paralelismo

No paralelismo, duas ou mais tarefas são efetivamente executadas ao mesmo tempo.

Isso normalmente depende da disponibilidade de múltiplos núcleos de processamento.

Assim, pode-se resumir:

- concorrência: organização e progresso de múltiplas tarefas;
- paralelismo: execução simultânea de múltiplas tarefas.

---

## 3. Threads

Threads são unidades de execução pertencentes a um mesmo processo.

As threads de um processo compartilham o mesmo espaço de memória, o que pode facilitar o compartilhamento de informações.

Essa característica também cria riscos quando várias threads acessam e modificam os mesmos dados.

Threads são especialmente úteis em situações I/O-bound, nas quais existe tempo de espera associado a operações externas.

Exemplos incluem:

- requisições de rede;
- acesso a banco de dados;
- leitura e escrita de arquivos;
- comunicação com serviços externos.

Enquanto uma thread aguarda uma operação de I/O, outra pode continuar progredindo.

---

## 4. Processos

Processos possuem espaços de memória separados e executam de maneira mais independente.

Em Python, o uso de múltiplos processos permite distribuir tarefas entre diferentes núcleos da CPU.

Por esse motivo, essa abordagem é particularmente relevante em tarefas CPU-bound.

Entretanto, processos apresentam custos adicionais relacionados à:

- criação de novos processos;
- consumo de memória;
- comunicação entre processos;
- transferência ou compartilhamento de dados.

Portanto, processos não devem ser escolhidos automaticamente para qualquer tipo de tarefa.

---

## 5. I/O-bound e CPU-bound

A distinção entre I/O-bound e CPU-bound é essencial para compreender os experimentos deste projeto.

### 5.1 I/O-bound

Uma tarefa é I/O-bound quando uma parcela significativa do tempo é utilizada aguardando operações de entrada e saída.

Exemplos:

- respostas de rede;
- arquivos;
- banco de dados;
- APIs;
- comunicação externa.

Nesse cenário, técnicas como Threads e Asyncio podem reduzir o tempo ocioso, permitindo que outras tarefas avancem durante a espera.

### 5.2 CPU-bound

Uma tarefa é CPU-bound quando seu desempenho depende principalmente da capacidade de processamento da CPU.

Exemplos:

- cálculos matemáticos;
- algoritmos intensivos;
- processamento de grandes quantidades de dados;
- transformações computacionalmente pesadas.

Nesse caso, aumentar o número de threads não significa necessariamente aumentar o paralelismo de código Python.

Por isso, processos possuem papel importante na execução de cargas CPU-bound.

---

## 6. Global Interpreter Lock — GIL

O Global Interpreter Lock, ou GIL, é um mecanismo historicamente presente no CPython.

Neste projeto, considera-se principalmente o comportamento tradicional do CPython com o GIL habilitado.

Nesse contexto, apenas uma thread por vez executa bytecode Python dentro de um mesmo processo.

Isso possui uma consequência importante para tarefas CPU-bound.

Mesmo que várias threads sejam criadas, elas não executam simultaneamente bytecode Python em diferentes núcleos dentro do mesmo interpretador tradicional.

Por isso:

- Threads não costumam proporcionar paralelismo real de CPU para código Python CPU-bound;
- Processos podem explorar múltiplos núcleos porque cada processo possui seu próprio interpretador.

Em tarefas I/O-bound, essa limitação possui impacto diferente, pois uma thread pode permanecer aguardando uma operação externa enquanto outra avança.

O GIL, portanto, é um elemento importante para entender por que o desempenho de Threads e Processos varia conforme o tipo de tarefa.

---

## 7. Asyncio e programação assíncrona

Asyncio é uma biblioteca de programação assíncrona baseada em um modelo cooperativo de execução.

Seu funcionamento utiliza um event loop.

Quando uma tarefa chega a uma operação que exige espera, ela pode suspender temporariamente sua execução e permitir que outra tarefa avance.

Isso ocorre principalmente por meio dos comandos `async` e `await`.

A programação assíncrona é especialmente interessante quando existe um grande número de operações de I/O.

Uma diferença importante é que Asyncio não depende necessariamente da criação de uma thread para cada tarefa.

Isso pode tornar essa abordagem eficiente em aplicações que precisam administrar muitas operações de espera simultaneamente.

---

## 8. Sincronização e condição de corrida

O compartilhamento de recursos entre tarefas concorrentes pode gerar problemas de consistência.

Um desses problemas é a condição de corrida.

### 8.1 Condição de corrida

Uma condição de corrida ocorre quando o resultado de uma operação depende da ordem ou do momento em que diferentes tarefas acessam um recurso compartilhado.

Considere um estoque com apenas uma unidade.

Duas threads podem executar aproximadamente a seguinte sequência:

1. Thread A consulta o estoque e encontra valor 1;
2. Thread B também consulta o estoque e encontra valor 1;
3. Thread A realiza a compra;
4. Thread B também tenta realizar a compra.

Sem controle adequado, o sistema pode produzir um resultado inconsistente.

---

## 9. Região crítica e Lock

Uma região crítica é uma parte do programa que acessa ou modifica um recurso compartilhado.

Quando várias tarefas podem acessar essa região simultaneamente, é necessário controlar esse acesso.

Uma das estratégias é utilizar Lock.

Quando uma thread adquire o Lock:

1. ela entra na região crítica;
2. outras threads que precisam do mesmo Lock aguardam;
3. a operação é concluída;
4. o Lock é liberado;
5. outra thread pode continuar.

O uso de Lock pode evitar condições de corrida.

Entretanto, mecanismos de sincronização também devem ser utilizados com cuidado, pois podem introduzir:

- espera entre tarefas;
- redução de desempenho;
- contenção;
- risco de deadlock em implementações inadequadas.

---

## 10. Arquitetura prática do projeto

O projeto foi estruturado para permitir a comparação entre diferentes estratégias de execução.

Os experimentos principais incluem:

### Experimento I/O-bound

Arquivo:

`examples/io_bound_comparison.py`

Objetivo:

comparar diferentes estratégias quando a carga possui operações de espera relacionadas a I/O.

As estratégias analisadas incluem execução sequencial, Threads e Asyncio.

### Experimento CPU-bound

Arquivo:

`examples/cpu_bound_comparison.py`

Objetivo:

comparar o comportamento da execução sequencial, Threads e Processos em uma tarefa com carga intensiva de CPU.

Esse experimento é diretamente relacionado à análise do impacto do GIL.

### Experimento de concorrência de estoque

Arquivo:

`examples/stock_concurrency_comparison.py`

Objetivo:

demonstrar o acesso concorrente a um recurso compartilhado e a necessidade de mecanismos de sincronização.

Esse cenário permite observar conceitos como:

- condição de corrida;
- região crítica;
- Lock;
- consistência de dados.

---

## 11. Interface Streamlit

Além dos experimentos executados diretamente, o projeto possui uma interface desenvolvida com Streamlit.

A interface atua como uma camada de apresentação dos experimentos.

Seu objetivo é facilitar:

- execução dos cenários;
- visualização das estratégias;
- comparação de métricas;
- interpretação dos resultados.

O Streamlit não constitui uma estratégia de concorrência.

Ele funciona como uma interface para demonstrar os mecanismos implementados no projeto.

---

## 12. Metodologia de comparação

Uma comparação entre estratégias de concorrência precisa utilizar condições equivalentes.

Para que os resultados sejam interpretados corretamente, recomenda-se manter:

- a mesma máquina;
- a mesma carga de trabalho;
- os mesmos parâmetros;
- o mesmo número de operações;
- condições semelhantes de execução.

Entre as métricas que podem ser analisadas estão:

- tempo total de execução;
- uso de CPU;
- uso de memória;
- throughput;
- número de workers;
- speedup.

O speedup pode ser entendido como a relação entre o tempo de uma execução de referência e o tempo obtido por outra estratégia.

---

## 13. Análise teórico-prática do cenário I/O-bound

No cenário I/O-bound, uma execução sequencial pode apresentar períodos significativos de ociosidade.

Isso acontece porque o programa precisa aguardar que uma operação externa seja concluída antes de continuar.

Com Threads, outras tarefas podem avançar enquanto uma thread está aguardando I/O.

Com Asyncio, o event loop pode alternar cooperativamente entre diferentes tarefas assíncronas durante os períodos de espera.

Portanto, a expectativa teórica é que estratégias concorrentes apresentem vantagens nesse cenário quando existem múltiplas operações de espera.

A análise dos resultados deve considerar principalmente:

- tempo total;
- quantidade de operações concluídas por unidade de tempo;
- sobrecarga da estratégia utilizada.

---

## 14. Análise teórico-prática do cenário CPU-bound

No cenário CPU-bound, a situação é diferente.

As tarefas permanecem utilizando intensamente o processador.

No CPython tradicional com GIL habilitado, múltiplas threads não executam simultaneamente bytecode Python dentro do mesmo processo.

Assim, adicionar threads a uma carga CPU-bound não garante redução do tempo de execução.

O uso de múltiplos processos permite utilizar interpretadores separados e pode possibilitar o aproveitamento de diferentes núcleos da CPU.

Entretanto, os processos também possuem overhead.

Por esse motivo, os resultados devem ser analisados considerando tanto o ganho de paralelismo quanto o custo adicional relacionado à criação e administração dos processos.

---

## 15. Análise teórico-prática da sincronização

O experimento de estoque possui objetivo diferente dos experimentos de desempenho.

Nesse caso, o principal aspecto analisado é a correção do comportamento concorrente.

Uma versão sem sincronização pode apresentar resultados incorretos devido à condição de corrida.

Com a utilização de Lock, o acesso à região crítica é controlado.

Isso evidencia um ponto importante:

a estratégia de maior desempenho não é necessariamente adequada se produzir resultados incorretos.

Em programação concorrente, desempenho e consistência precisam ser analisados conjuntamente.

---

## 16. Interpretação dos resultados experimentais

Os valores numéricos devem ser registrados após a execução definitiva dos benchmarks.

A análise deve evitar conclusões baseadas apenas em uma única execução.

Quando possível, recomenda-se realizar mais de uma execução e observar tendências consistentes.

Os resultados devem responder principalmente às seguintes perguntas:

1. Threads reduziram o tempo no cenário I/O-bound?
2. Asyncio apresentou vantagem quando várias operações de I/O foram executadas?
3. Threads proporcionaram ganho significativo no cenário CPU-bound?
4. Processos conseguiram utilizar melhor os recursos de CPU no cenário CPU-bound?
5. A execução sem Lock produziu inconsistências?
6. O Lock corrigiu o acesso ao recurso compartilhado?
7. Qual foi o custo das estratégias concorrentes em relação à execução sequencial?

Essas perguntas conectam diretamente os conceitos teóricos aos experimentos realizados.

---

## 17. Critérios para escolha da estratégia

A análise do projeto permite estabelecer uma orientação geral:

| Tipo de situação | Estratégia a considerar |
| --- | --- |
| Fluxo simples e pequeno | Sequencial |
| Operações com espera de I/O | Threads |
| Grande quantidade de operações assíncronas de I/O | Asyncio |
| Processamento intensivo de CPU | Processos |
| Acesso concorrente a recurso compartilhado | Sincronização com Lock |

Essa tabela não representa uma regra absoluta.

A decisão final depende das características da aplicação, da carga de trabalho, do ambiente de execução e dos custos introduzidos por cada estratégia.

---

## 18. Limitações e cuidados

Benchmarks de concorrência podem ser influenciados por diversos fatores.

Entre eles:

- número de núcleos do processador;
- sistema operacional;
- versão do Python;
- processos executando simultaneamente na máquina;
- latência de operações externas;
- quantidade de tarefas;
- tamanho da carga de trabalho;
- overhead de criação de threads e processos.

Por esse motivo, resultados de desempenho não devem ser generalizados sem considerar o ambiente em que foram obtidos.

---

## 19. Conclusão

Os experimentos demonstram a importância de selecionar a estratégia de execução de acordo com a natureza do problema.

Threads, Processos e Asyncio possuem objetivos e características diferentes.

Em termos gerais:

- Threads são relevantes para tarefas com espera de I/O;
- Asyncio pode administrar de forma eficiente muitas operações assíncronas;
- Processos são importantes para explorar paralelismo em cargas CPU-bound;
- Lock e outros mecanismos de sincronização são necessários quando recursos compartilhados precisam ser protegidos;
- o GIL ajuda a explicar por que Threads e Processos apresentam comportamentos diferentes em tarefas CPU-bound no CPython tradicional.

Portanto, programação concorrente não consiste apenas em executar mais tarefas ao mesmo tempo.

Ela exige compreender a natureza da carga de trabalho, os mecanismos disponíveis, os custos de cada abordagem e os riscos relacionados ao compartilhamento de recursos.

A análise teórica e os experimentos práticos deste projeto permitem visualizar essas diferenças e fundamentar a escolha da estratégia mais adequada para cada situação.