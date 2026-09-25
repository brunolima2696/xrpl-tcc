# Capítulo 4 — Especificação de Requisitos

## Descrição

O capítulo traduz a fundamentação teórica em requisitos verificáveis para o framework e para a Prova de Conceito. São especificados os papéis dos participantes, as políticas distintas para Depositantes e Tomadores, as extensões do *Single Asset Vault* e de `LoanSet`, as restrições do XRPL e os critérios gerais de validação.

## Sumário

### 4.1 Escopo, Atores e Premissas

Delimita a solução, seus participantes e a separação entre *underwriting* off-chain e autorização on-chain.

#### 4.1.1 Atores e Responsabilidades

Define as funções dos participantes do framework.

#### 4.1.2 Fronteiras e Premissas

Delimita o que ocorre dentro e fora da solução.

### 4.2 Requisitos Funcionais (RF)

Especifica identidade, credenciais, políticas de acesso, configuração do *Vault* e ciclo do empréstimo.

#### 4.2.1 Identidade e Credentials

Abrange identificação, emissão, aceite e revogação.

#### 4.2.2 Políticas de Acesso e Vault

Define os domínios e sua associação ao *Vault*.

#### 4.2.3 Ciclo do Empréstimo

Abrange autorização, assinatura, pagamento e encerramento.

### 4.3 Requisitos Não-Funcionais (RNF)

Define privacidade, determinismo, auditabilidade, compatibilidade e reprodutibilidade.

#### 4.3.1 Privacidade

Estabelece a minimização dos dados registrados no ledger.

#### 4.3.2 Determinismo, Integridade e Auditabilidade

Estabelece validações determinísticas e referências consistentes.

#### 4.3.3 Compatibilidade e Reprodutibilidade

Preserva os fluxos já existentes no ledger e permite reproduzir os experimentos.

### 4.4 Restrições e Decisões de Projeto

Distingue restrições herdadas do XRPL, decisões introduzidas pela extensão e limitações do ambiente.

#### 4.4.1 Restrições Herdadas do XRP Ledger

Apresenta os limites das primitivas utilizadas.

#### 4.4.2 Decisões da Extensão

Justifica a separação das políticas e a vinculação pelo *Vault*.

#### 4.4.3 Limitações da Prova de Conceito

Delimita o alcance dos resultados experimentais.

### 4.5 Prova de Conceito e Validação

Define o ambiente local, os cenários positivos e negativos e as evidências de atendimento aos requisitos.

#### 4.5.1 Ambiente Local

Descreve a infraestrutura utilizada nos experimentos.

#### 4.5.2 Cenários de Validação

Define os fluxos positivos e negativos.

#### 4.5.3 Aceitação e Rastreabilidade

Relaciona requisitos, resultados esperados e evidências.

## Requisitos Funcionais

| ID | Requisito | Descrição |
|---|---|---|
| RF01 | Gestão de Identidade | Permitir que os participantes associem suas contas a DIDs nativos do XRPL. |
| RF02 | Emissão de Credenciais Verificáveis | Permitir que o Emissor de Credenciais produza VCs off-chain. |
| RF03 | Ancoragem On-Chain | Registrar a atestação por meio de `CredentialCreate`. |
| RF04 | Consentimento do Titular | Exigir `CredentialAccept` antes da utilização da *Credential*. |
| RF05 | Ciclo de Vida da Credential | Considerar emissão, aceite, expiração e revogação. |
| RF06 | Definição das Políticas | Manter políticas distintas para Depositantes e Tomadores. |
| RF07 | Gestão dos Permissioned Domains | Criar e atualizar um domínio para cada papel. |
| RF08 | Configuração do Vault Privado | Associar `DomainID` e `BorrowerDomainID` ao *Vault*. |
| RF09 | Autorização do Depositante | Validar a *Credential* do Depositante em `VaultDeposit`. |
| RF10 | Associação do Loan Broker | Associar o Loan Broker ao *Vault* por meio de `LoanBrokerSet`. |
| RF11 | Originação Conjunta | Exigir as assinaturas do Loan Broker e do Tomador em `LoanSet`. |
| RF12 | Identificação do Vault em LoanSet | Receber `VaultID` e validar sua relação com `LoanBrokerID`. |
| RF13 | Autorização do Tomador | Consultar `BorrowerDomainID` e validar on-chain a *Credential* do Tomador. |
| RF14 | Ciclo de Vida do Empréstimo | Permitir pagamento e encerramento por `LoanPay` e `LoanDelete`. |

## Requisitos Não-Funcionais

| ID | Requisito | Descrição |
|---|---|---|
| RNF01 | Privacidade | Não armazenar dados pessoais, institucionais ou financeiros brutos no ledger. |
| RNF02 | Determinismo | Produzir resultados de autorização consistentes a partir do estado do ledger. |
| RNF03 | Auditabilidade | Permitir a consulta dos objetos e resultados registrados no ledger. |
| RNF04 | Integridade  | Garantir a consistência entre `VaultID`, `BorrowerDomainID` e `LoanBrokerID`. |
| RNF05 | Compatibilidade | Preservar o comportamento dos fluxos nativos. |
| RNF06 | Reprodutibilidade | Permitir a construção e a execução local do protótipo. |
| RNF07 | Persistência | Preservar o estado do  ledger entre execuções. |
| RNF08 | Rastreabilidade | Registrar identificadores, hashes e resultados das transações. |

## Restrições e Decisões de Projeto

| ID | Restrição | Descrição |
|---|---|---|
| RST01 | Critérios alternativos | Um *Permissioned Domain* exige ao menos um par aceito de emissor e `CredentialType`. |
| RST02 | Correspondência Exata | Emissor e `CredentialType` devem corresponder exatamente ao critério definido. |
| RST03 | Limites de Representação | `CredentialType` possui até 64 bytes e o domínio aceita até dez combinações. |
| RST04 | Propriedade do Vault | O Loan Broker e o proprietário do *Vault* correspondem à mesma conta. |

| ID | Decisão | Descrição |
|---|---|---|
| DP01 | Separação das Políticas | `DomainID` controla Depositantes e `BorrowerDomainID` controla Tomadores. |
| DP02 | Vinculação da Política | `LoanSet` recebe `VaultID` e obtém a política do Tomador a partir do *Vault*. |


## Requisitos para a Prova de Conceito

| ID | Requisito | Descrição |
|---|---|---|
| RPC01 | Rede Local | Executar um nó `rippled` compilado a partir do código-fonte do projeto. |
| RPC02 | Orquestração e Persistência | Executar o ambiente e preservar seus dados por meio de containers. |
| RPC03 | Identidade Institucional | Demonstrar DID, VC e *Credential* com dados institucionais genéricos. |
| RPC04 | Configuração das Políticas | Representar regras de Depositantes e Tomadores com múltiplos emissores e tipos. |
| RPC05 | Configuração Permissionada | Criar dois domínios e um *Vault* com `DomainID` e `BorrowerDomainID`. |
| RPC06 | Validação do Depositante | Demonstrar aceitação e rejeição de `VaultDeposit`. |
| RPC07 | Validação do Tomador | Demonstrar aceitação e rejeição de `LoanSet`. |
| RPC08 | Ciclo Completo | Executar emissão, aceite, depósito, pagamento e encerramento. |
| RPC09 | Testes da Extensão | Verificar referências inválidas e *Credentials* ausentes, inválidas ou revogadas. |
| RPC10 | Evidências do Experimento | Registrar os elementos necessários para reprodução e auditoria. |
