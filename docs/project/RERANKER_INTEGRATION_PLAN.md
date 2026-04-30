# Plano de Integração: Cerebro Reranker

## Objetivo
Integrar o serviço `cerebro-reranker` (FastAPI + Rust Core) ao ecossistema `cerebro` (Phantom), substituindo a implementação local atual baseada apenas em `sentence-transformers`.

## Status Atual
- **Phantom (`src/phantom/core/rerank.py`)**: Implementação síncrona simples usando `CrossEncoder` local. Sem cache, sem fallback, bloqueante.
- **Cerebro Reranker (`../cerebro-reranker`)**: Microsserviço robusto com:
    - Core em Rust (`libscorer`) via FFI para performance.
    - API FastAPI assíncrona.
    - Cache distribuído (IPFS/Redis).
    - Suporte a modelos híbridos (Fast/Accurate) e Fallback para Nuvem.

## Estratégia de Integração: "Sidecar Service"
Para manter o `cerebro` leve e desacoplado, integraremos o `cerebro-reranker` como um serviço paralelo (sidecar), em vez de uma biblioteca direta. Isso evita conflitos de dependência (Python/Rust) e permite escalar o reranker independentemente.

### 1. Camada de Cliente (Phantom)
Criar um adaptador robusto em `src/phantom/core/rerank_client.py` que:
- Tenta conectar ao serviço `cerebro-reranker` via HTTP.
- Implementa o padrão **Circuit Breaker**: se o serviço falhar, degrada graciosamente para a implementação local (`CrossEncoder`) ou retorna erro (configurável).
- Mantém a assinatura da função `rerank()` atual para compatibilidade com o CLI existente.

### 2. Gerenciamento de Serviço
Atualizar o script de inicialização `start_cerebro.sh` para:
- Verificar a presença do diretório `../cerebro-reranker`.
- Se presente, iniciar o serviço em background usando `nix run`.
- Gerenciar o ciclo de vida (PID) para encerrar junto com o `cerebro`.

### 3. Configuração
Adicionar variáveis de ambiente/configuração:
- `CEREBRO_RERANKER_URL`: URL do serviço (default: `http://localhost:8090`).
- `CEREBRO_RERANKER_MODE`: `service` (preferido), `local` (legado), `hybrid` (tenta serviço, falha para local).

## Roadmap de Execução

### Fase 1: Adaptação do Código (Phantom)
1.  **Criar Cliente**: Implementar `CerebroRerankerClient` em `src/phantom/core/rerank_client.py` usando `requests` (para compatibilidade síncrona) ou `httpx`.
2.  **Atualizar Facade**: Modificar `src/phantom/core/rerank.py` para instanciar o cliente.
    - Manter a classe `CrossEncoderReranker` como "LocalFallback".
    - A função `rerank()` principal orquestra a chamada.

### Fase 2: Infraestrutura e Scripts
3.  **Script de Start**: Editar `start_cerebro.sh`.
    - Adicionar função `start_reranker()`.
    - Logs unificados.
4.  **Dependências**: Verificar se `requests` ou `httpx` estão disponíveis no ambiente `flake.nix`.

### Fase 3: Validação
5.  **Teste de Integração**: Criar script `scripts/test_reranker.py` que:
    - Sobe o serviço (se não estiver rodando).
    - Envia documentos para rerank.
    - Compara resultados com a versão local.
6.  **CLI Check**: Verificar se `cerebro rag rerank` funciona transparentemente.

## Rollback Plan
Caso o serviço apresente instabilidade:
- Definir `CEREBRO_RERANKER_MODE=local` força o uso da implementação antiga (que será mantida no código como fallback).
- O código será desenhado para "falhar seguro" (fail-open) para a versão local se o serviço não responder em X ms.
