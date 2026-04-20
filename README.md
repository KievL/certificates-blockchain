# Distributed Certificates Blockchain

Este projeto é uma implementação de uma blockchain distribuída para gestão de certificados, desenvolvida como requisito para a disciplina de **Sistemas Distribuídos** no **Departamento de Computação e Automação (DCA)** da **Universidade Federal do Rio Grande do Norte (UFRN)**.

O sistema utiliza uma arquitetura baseada em eventos para comunicação entre nós, implementando conceitos fundamentais de sistemas distribuídos como consenso, tolerância a falhas (via regra da cadeia mais longa) e sincronização.

## 📝 O que é?

A **Certificates Blockchain** é uma rede descentralizada onde "certificados" (representados como transações) são registrados em blocos imutáveis. O objetivo é garantir a integridade e a auditabilidade de certificados emitidos de forma distribuída, sem a necessidade de uma autoridade central única, utilizando o algoritmo de **Proof of Work (PoW)** para segurança.

## 🏗️ Arquitetura do Projeto

O projeto segue os princípios de **Clean Architecture** e **Domain-Driven Design (DDD)**, garantindo separação de preocupações e facilidade de manutenção.

### Estrutura de Camadas:
- **Domain**: Entidades (Block, Transaction) e regras de negócio puras.
- **Application/Use Cases**: Lógica de aplicação (receber bloco, processar transação).
- **Ports/Interfaces**: Definição de como o sistema interage com o mundo externo.
- **Adapters/Infrastructure**: Implementações concretas (Kafka, FastAPI, Repositórios em memória).

### Fluxo de Comunicação:
O sistema é desacoplado através do **Apache Kafka**, que atua como o backbone de eventos. Os nós não se comunicam diretamente por HTTP para troca de blocos/transações, mas sim através de tópicos:
1. `transactions`: Novas transações enviadas para a mempool.
2. `mining_jobs`: Notificações para os mineradores de que há trabalho disponível.
3. `found_blocks`: Blocos minerados que devem ser validados pela rede.

## 🛠️ Serviços

A solução é composta por quatro componentes principais:

| Serviço | Tecnologia | Função |
| :--- | :--- | :--- |
| **Blockchain Node** | Python (FastAPI) | Mantém a chain, gerencia a mempool, valida blocos e resolve forks. |
| **Miner** | Python (Asyncio) | Escuta por jobs de mineração e realiza o esforço computacional (PoW). |
| **Message Broker** | Kafka (KRaft mode) | Garante a entrega de mensagens e eventos entre todos os nós e mineradores. |
| **Web UI** | Streamlit (Modern Glassmorphism Design) | Interface premium para visualizar a blockchain, enviar transações, verificar certificados e simular ataques. |
| **Kafka UI** | Provectus UI | Monitoramento técnico dos tópicos e mensagens trafegando no broker. |

## 🚀 Como Executar

### Pré-requisitos
- Docker e Docker Compose instalados.

### Passo a Passo

1. **Configuração de Ambiente**:
   Crie um arquivo `.env` na raiz do projeto (ou copie o `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. **Subir a Infraestrutura**:
   Utilize o Docker Compose para subir 3 nós de blockchain, 3 mineradores e a infraestrutura Kafka (KRaft):
   ```bash
   docker compose up --build
   ```

3. **Acessar as Interfaces**:
   - **Streamlit UI**: Execute localmente com `streamlit run ui/app.py` (acessível em `http://localhost:8501`).
   - **FastAPI Docs**: `http://localhost:8001/docs` (Node 1), `8002` (Node 2), etc.
   - **Kafka UI**: `http://localhost:8080` (verificação de mensagens).

## 🛡️ Funcionalidades de Teste e Simulação

O projeto inclui ferramentas avançadas para testar a resiliência e o comportamento da rede em cenários adversos:

### 🔍 Verificação de Certificados
Uma aba dedicada permite consultar qualquer nó da rede por um ID/Hash de transação, retornando o status em tempo real (Confirmado em Bloco ou Pendente na Mempool) e os dados detalhados do certificado.

### 💥 Simulação de Ataque (Injeção Direta de Blocos)
Esta ferramenta permite que a UI atue como um "minerador malicioso":
1.  Busca o estado atual da chain de um nó alvo.
2.  Gera transações arbitrárias (falsas).
3.  Realiza o esforço computacional (PoW) diretamente no navegador.
4.  Injeta o bloco minerado via endpoint HTTP, testando a capacidade do nó de validar e propagar blocos que não vieram do pipeline padrão do Kafka.
5.  **Force Accept**: Opção para testar o comportamento do nó ignorando validações de assinatura (modo debug).

### 🎲 Gerador de Transações Aleatórias
Permite enviar lotes de transações para a rede com dados gerados aleatoriamente. Utiliza um **SEED de aleatoriedade** para garantir que os testes sejam reproduzíveis.

## ⚙️ Detalhes Técnicos

- **Consenso**: Proof of Work com dificuldade variável configurada via variável de ambiente (`DIFFICULTY`).
- **Resolução de Conflitos**: Regra da Cadeia Mais Longa (*Longest Chain Rule*). Em caso de empate, um protocolo de consenso aleatório é acionado consultando outros nós.
- **Estratégia de Mineração**:
    - **Batching**: Blocos são criados ao atingir `BATCH_SIZE` transações ou um `TIMEOUT`.
    - **Jitter Strategy**: Adição de atraso aleatório antes da publicação para reduzir colisões e forks e simular condições reais de rede.
    - **Validação Rigorosa**: Verificação de hashes anteriores, timestamps, nonces e assinaturas criptográficas Ed25519.
- **Segurança**: Assinaturas de transação validadas em cada etapa. Blocos injetados com `force_accept=True` são aceitos apenas se a lógica do nó permitir explicitamente (útil para simulações de "ataque de 51%" ou "by-pass").

---
*Desenvolvido como trabalho acadêmico para a disciplina de Sistemas Distribuídos - DCA/UFRN.*
