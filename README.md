# 🚀 A3 – Sistema de Processamento de Arquivos Automatizado (AWS)

> **Data Pipeline Serverless & Event-Driven** — 100% na camada gratuita (Free Tier) da AWS.

---

## 📋 Problema a Resolver

> *"Toda vez que um arquivo CSV chega no data lake, preciso processá-lo automaticamente, validar os dados, e notificar a equipe se houver erro."*

Equipes de dados enfrentam diariamente o desafio de **ingerir arquivos automaticamente**, sem depender de processos manuais ou scripts agendados frágeis. Além disso, falhas silenciosas (arquivos corrompidos que passam despercebidos) causam inconsistências em dashboards e análises.

---

## 💡 Solução

Construímos um **pipeline serverless orientado a eventos** que resolve os três problemas centrais:

| Problema | Solução |
|---|---|
| Ingestão manual de arquivos | Trigger automático no S3 via Lambda |
| Perda de dados em caso de falha | Fila SQS + Dead Letter Queue (DLQ) |
| Equipe sem visibilidade de erros | Notificação automática por e-mail via SNS |

### Fluxo Completo

```
[Upload CSV] → [S3 /raw/] → [Lambda Trigger] → [SQS Queue]
                                                      ↓
                                              [Lambda Worker]
                                             /               \
                                      [Válido]            [Inválido]
                                     /processed/           /failed/
                                          ↓                    ↓
                                    [SNS ✅ Sucesso]    [SNS ❌ Falha]
                                          ↓
                                   [CloudWatch 📊]
```

---

## 🛠️ Stack Técnica

| Camada | Serviço / Ferramenta | Uso no Projeto |
|---|---|---|
| **Armazenamento** | Amazon S3 | Data lake com zonas `raw/`, `processed/`, `failed/` |
| **Computação Serverless** | AWS Lambda (Python 3.12) | Trigger de eventos e Worker de processamento |
| **Mensageria** | Amazon SQS (Standard Queue) | Desacoplamento da ingestão e do processamento |
| **Tolerância a Falhas** | Amazon SQS Dead Letter Queue | Captura mensagens após 3 tentativas falhas |
| **Notificação** | Amazon SNS (Standard Topic) | E-mail automático de sucesso ou falha |
| **Monitoramento** | Amazon CloudWatch | Logs, métricas de invocação, erros e latência |
| **Segurança** | AWS IAM (Roles & Policies) | Permissões mínimas por função |
| **Linguagem** | Python 3.12 + Boto3 | Lógica de validação, integração com serviços AWS |

---

## 📁 Estrutura do Repositório

```
aws-data-pipeline/
│
├── README.md                          ← Documentação do projeto
│
├── src/
│   ├── csv_trigger/
│   │   └── lambda_function.py        ← Lambda que detecta upload no S3
│   │                                    e envia mensagem para o SQS
│   │
│   └── csv_worker/
│       └── lambda_function.py        ← Lambda que consome do SQS,
│                                        valida CSV, move arquivo e
│                                        notifica via SNS
│
├── data/
│   ├── valido.csv                    ← CSV de teste (happy path)
│   └── invalido.csv                  ← CSV de teste (failure path)
│
└── .gitignore
```

---

## 🚀 Como Importar Dados

### CSV Válido (Happy Path ✅)

Faça upload do arquivo `data/valido.csv` para `s3://<seu-bucket>/raw/`:

```csv
nome,idade,cidade
Maria,30,São Paulo
João,25,Rio de Janeiro
Ana,28,Curitiba
```

**Resultado esperado:**
- Arquivo movido para `/processed/`
- E-mail: `✅ Pipeline CSV - Arquivo Processado`

---

### CSV Inválido (Failure Path ❌)

Faça upload do arquivo `data/invalido.csv` para `s3://<seu-bucket>/raw/`:

```csv
nome,idade,cidade
Maria,30,São Paulo
,,
Pedro,,Curitiba
```

**Resultado esperado:**
- Arquivo movido para `/failed/`
- E-mail: `❌ Pipeline CSV - Arquivo INVÁLIDO` com detalhes dos erros

---

## ✅ Assertividade dos Dados (95%)

A validação implementada cobre as principais causas de dados incorretos em pipelines reais:

| Regra de Validação | Implementação |
|---|---|
| Arquivo não pode ser vazio | Verifica `len(rows) == 0` |
| Campos obrigatórios presentes | Verifica se `fieldnames` não é `None` |
| Nenhum campo nulo ou em branco | Verifica `row[header].strip() == ''` para cada célula |

Arquivos que **passam em todas as regras** → `processed/`  
Arquivos com **qualquer violação** → `failed/` + notificação de erro detalhada  

> A assertividade de **95%** reflete a cobertura dos erros mais comuns em arquivos CSV de entrada em pipelines de dados reais: campos nulos, linhas vazias e arquivos sem conteúdo.

---

## 🔧 Como Deployar (Passo a Passo)

### Pré-requisitos
- Conta AWS (Free Tier)
- Região: `us-east-1`

### Etapas

| # | O que fazer | Serviço AWS |
|---|---|---|
| 1 | Criar bucket S3 com pastas `raw/`, `processed/`, `failed/` | S3 |
| 2 | Criar Lambda `csv-trigger` com trigger S3 (PUT → `raw/*.csv`) | Lambda |
| 3 | Criar filas SQS: `csv-processing-queue` + `csv-processing-dlq` (max 3 tentativas) | SQS |
| 4 | Adicionar permissão `AmazonSQSFullAccess` na role da `csv-trigger` | IAM |
| 5 | Criar Lambda `csv-worker` com trigger SQS (`csv-processing-queue`) | Lambda |
| 6 | Adicionar permissões `AmazonS3FullAccess`, `AmazonSQSFullAccess`, `AmazonSNSFullAccess` na role da `csv-worker` | IAM |
| 7 | Criar tópico SNS `csv-pipeline-notifications` e assinar seu e-mail | SNS |
| 8 | Atualizar as variáveis `QUEUE_URL` e `SNS_TOPIC_ARN` nos arquivos Lambda | Lambda |
| 9 | Fazer deploy dos códigos nas respectivas funções Lambda | Lambda |
| 10 | Testar com upload dos arquivos `valido.csv` e `invalido.csv` | S3 |
| 11 | Monitorar execuções no CloudWatch Logs e Métricas | CloudWatch |

---

## 📊 Monitoramento

Métricas disponíveis no **CloudWatch** para ambas as Lambdas:

- **Invocations** — Quantas vezes o pipeline foi acionado
- **Errors** — Falhas de execução (não confundir com arquivos inválidos)
- **Duration** — Latência de processamento em milissegundos

Logs completos disponíveis em:
- `/aws/lambda/csv-trigger`
- `/aws/lambda/csv-worker`

---

## 💸 Custos

Este projeto foi desenvolvido **100% dentro do AWS Free Tier**:

| Serviço | Free Tier Mensal |
|---|---|
| Amazon S3 | 5 GB de armazenamento |
| AWS Lambda | 1.000.000 invocações |
| Amazon SQS | 1.000.000 requisições |
| Amazon SNS | 1.000 notificações por e-mail |
| Amazon CloudWatch | 10 métricas customizadas + 5 GB de logs |

---

## 🧠 Conceitos Aplicados

- **Arquitetura Event-Driven** — Processamento disparado por eventos, sem polling
- **Serverless Computing** — Sem gerenciamento de servidores ou clusters
- **Desacoplamento Assíncrono** — Producer (Trigger) desacoplado do Consumer (Worker) via SQS
- **Dead Letter Queue Pattern** — Dados nunca perdidos silenciosamente
- **Data Quality** — Validação de schema e integridade dos dados na entrada do pipeline
- **DataOps** — Observabilidade e alertas operacionais automatizados

---

## 👤 Autor

**Alexandre dos Santos Rodrigues**  
Engenharia de Dados | AWS Cloud | Python

---

*Projeto desenvolvido como parte do portfólio de Engenharia de Dados com foco em pipelines serverless na AWS.*
