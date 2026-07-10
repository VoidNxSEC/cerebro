```mermaid
graph TD
    %% --- Styles ---
    classDef source fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef process fill:#fff3e0,stroke:#ff6f00,stroke-width:2px;
    classDef storage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef consume fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;
    classDef ai fill:#fce4ec,stroke:#c2185b,stroke-width:2px,stroke-dasharray: 5 5;

    %% --- 1. Fontes de Dados (Sources) ---
    subgraph Sources [Fontes de Dados]
        LocalRepos[📂 Local Repositories<br/>(Git/Code)]:::source
        GCPLogs[☁️ GCP Logs<br/>(Billing/Audit)]:::source
        UserQuery[👤 User Queries<br/>(CLI/Chat)]:::source
        ExtAPIs[🌐 External APIs<br/>(GitHub/HN/Web)]:::source
    end

    %% --- 2. Processamento (Processing) ---
    subgraph Processing [Processamento Core]
        %% Knowledge Engine
        Analyzer[🔬 Knowledge Analyzer<br/>(AST/TreeSitter)]:::process
        ETL_Docs[🏭 ETL Pipeline<br/>(Markdown -> JSONL)]:::process
        
        %% RAG Engine
        Chunker[✂️ Text Splitter<br/>(RecursiveCharacter)]:::process
        Embedder[🧠 Embedding Gen<br/>(Vertex AI text-embedding-004)]:::process
        
        %% Orchestration
        Orchestrator[⚙️ Orchestrator<br/>(Scripts/Justfile)]:::process
    end

    %% --- 3. Armazenamento (Storage) ---
    subgraph Storage [Armazenamento & Persistência]
        Artifacts[🗃️ Raw Artifacts<br/>(JSON/JSONL)]:::storage
        VectorDB[(🗄️ ChromaDB<br/>Vector Store)]:::storage
        BigQuery[(📊 BigQuery<br/>Billing/Analytics)]:::storage
        GCS[☁️ Google Cloud Storage<br/>(Ingestion Staging)]:::storage
    end

    %% --- 4. Inteligência (AI Layer) ---
    subgraph AI [Camada de Inteligência]
        VertexLLM[🤖 Vertex AI LLM<br/>(Gemini 1.5 Flash)]:::ai
        VertexSearch[🔎 Vertex AI Search<br/>(Discovery Engine)]:::ai
    end

    %% --- 5. Consumo (Consumption) ---
    subgraph Consumption [Consumo & Interface]
        CLI[💻 Cerebro CLI<br/>(Typer/Rich)]:::consume
        Dashboards[📈 Billing Dashboards<br/>(Looker/Console)]:::consume
        Docs[📄 Documentation<br/>(Markdown/Generated)]:::consume
    end

    %% --- Fluxos (Flows) ---
    
    %% Flow: Knowledge Analysis
    LocalRepos -->|analyze .| Analyzer
    Analyzer -->|extracts| Artifacts
    
    %% Flow: Documentation ETL
    Artifacts -->|generate_docs.py| Docs
    Docs -->|etl_docs.py| ETL_Docs
    ETL_Docs -->|upload| GCS
    GCS -->|index| VertexSearch

    %% Flow: RAG Ingestion
    Artifacts -->|ingest| Chunker
    Chunker -->|batch 20| Embedder
    Embedder -->|vectors| VectorDB

    %% Flow: RAG Query
    UserQuery -->|rag query| CLI
    CLI -->|retrieve| VectorDB
    VectorDB -->|context| VertexLLM
    VertexLLM -->|answer| CLI

    %% Flow: Billing & Monitoring
    GCPLogs -->|export| BigQuery
    BigQuery -->|audit_credits.py| CLI
    BigQuery -->|visualize| Dashboards

    %% Flow: Trend Prediction
    ExtAPIs -->|trend_predictor.py| VertexLLM
    VertexLLM -->|insights| CLI

```