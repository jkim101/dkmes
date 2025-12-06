# DKMES 시스템 아키텍처

## 상위 레벨 다이어그램 (High-Level Diagram)
```mermaid
graph TD
    subgraph "외부 세상 (External World)"
        EA[외부 에이전트 (External Agent)]
        DE[데이터 엔지니어 (Data Engineer)]
    end

    subgraph "DKMES 코어 (DKMES Core)"
        API[API 게이트웨이 / 인터페이스 계층]
        
        subgraph "지식 코어 (플러그인 방식)"
            KM[지식 매니저 / 라우터]
            KB1[모듈: Standard RAG]
            KB2[모듈: GraphRAG]
            KB3[모듈: LightRAG]
            KB_New[모듈: Future KB...]
        end
        
        subgraph "평가 및 벤치마킹 엔진"
            Judge[LLM 심판 (LLM Judge)]
            Bench[벤치마크 엔진]
        end
        
        subgraph "관리 및 관측 (Management & Observability)"
            TraceDB[(Trace/Log Store)]
            AdminUI[웹 포털 (React)]
        end
    end

    DE -->|설정 (Configures)| KM
    DE -->|실험 실행 (Runs Experiments)| Bench
    DE -->|트레이스 검사 (Inspects)| AdminUI
    
    AdminUI -->|로그 읽기| TraceDB
    
    KM -->|쿼리 라우팅| KB1
    KM -->|쿼리 라우팅| KB2
    KM -->|쿼리 라우팅| KB3

    EA -->|1. 컨텍스트 요청| API
    EA -->|2. 솔루션 제출| API
    
    API -->|상호작용 로그| TraceDB
    API -->|요청 전달| Judge
    
    Judge -->|컨텍스트 검색| KM
    
    Judge -->|평가 (Evaluate)| Bench
    Bench -->|3. 피드백 & 점수| API
    API -->|결과 반환| EA
```

## 컴포넌트 상세 (Component Details)

### 1. 인터페이스 계층 (프로토콜)
- **역할**: 모든 외부 에이전트와 소통하는 표준 채널입니다.
- **기술**: REST API (FastAPI) 또는 GraphQL.
- **핵심 엔드포인트**:
    - `POST /evaluate`: 평가를 위해 쿼리/코드/답변을 제출합니다.
    - `GET /context/{topic}`: 에이전트를 돕기 위해 허가된 도메인 지식을 조회합니다.
    - `GET /feedback/{submission_id}`: 과거 제출물에 대한 상세 피드백을 받습니다.

### 2. 지식 코어 (플러그인 가능한 두뇌)
- **설계 철학**: 모듈화 및 불가지론(Agnostic). 시스템은 다양한 지식 검색 전략을 교체 가능한 플러그인으로 취급합니다.
- **지식 매니저 (Knowledge Manager)**: 주어진 쿼리에 대해 어떤 KB 모듈을 사용할지 결정하는 라우터입니다 (또는 비교를 위해 다수를 사용).
- **지원 모듈 (예시)**:
    - **Standard RAG**: 기본적인 벡터 DB 검색 (Chroma/Pinecone).
    - **GraphRAG**: 지식 그래프 기반 검색 (**FalkorDB**).
    - **LightRAG**: 경량화된 효율적 검색 방법론.
    - **Hybrid**: 위 방법들의 조합.
- **확장성**: 표준 `KnowledgeProvider` 인터페이스를 구현하여 새로운 방법론을 쉽게 추가할 수 있습니다.

### 3. 평가 및 벤치마킹 엔진 (선생님)
- **역할**: 
    1.  **외부 에이전트 대상**: 그들의 답변을 평가합니다 (선생님 역할).
    2.  **내부 모듈 대상**: 서로 다른 KB 모듈 간의 성능을 비교합니다.
- **LLM 심판 (LLM Judge)**: **Google Gemini Pro / Ultra** (Vertex AI 기반).
    - 긴 컨텍스트 윈도우를 활용하여 복잡한 SQL과 문서를 분석합니다.
- **벤치마크 스위트 (Benchmark Suite)**:
    - 참조: `hybrid-rag-system`의 로직을 참고하여 엄격한 평가 로직 구현.
    - "모범 질문-답변 쌍(Golden Q&A Pairs)"의 집합.

### 4. 웹 포털 (Web Portal - React)
- **기술 스택**: React (Frontend), FastAPI (Backend).
- **역할**: 데이터 엔지니어가 에코시스템을 관리하고 관측(Observe)하기 위한 중앙 허브입니다.
- **핵심 기능**:
    - **상호작용 검사기 (Interaction Inspector)**: 외부 에이전트와 DKMES 간에 교환된 정확한 JSON/텍스트 페이로드를 시각화하는 전용 UI입니다.
        - *View 예시*: "에이전트 A가 X를 물었고, DKMES가 맥락 Y를 주었으며, 심판이 점수 Z를 부여함."
    - **지식 큐레이션**: 지식 그래프를 위한 시각적 편집기.
    - **리더보드/통계**: 등록된 모든 에이전트의 성능 지표.
