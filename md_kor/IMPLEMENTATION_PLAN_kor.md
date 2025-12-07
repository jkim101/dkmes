# DKMES 상세 구현 계획 (Detailed Implementation Plan)

## 1단계: 기초 및 Google Cloud 설정
**목표**: Google Cloud 연동을 포함한 프로젝트 초기화 및 "Walking Skeleton" 구축.
- [x] **프로젝트 초기화**
    - [x] Git 저장소 및 디렉토리 구조 생성 (`/backend`, `/frontend`, `/lib`).
    - [x] **Backend**: Python Poetry 프로젝트 설정 (`fastapi`, `google-cloud-aiplatform`, `uvicorn` 포함).
    - [x] **Frontend**: React + Vite + TypeScript 프로젝트 설정.
- [x] **Google Vertex AI 연동**
    - [x] GCP 자격 증명(Service Account) 설정.
    - [x] Gemini Pro API 호출을 처리할 `GeminiClient` 래퍼 구현.
    - [x] Gemini 연결 확인을 위한 간단한 테스트 스크립트 작성.
- [x] **기본 API 및 UI**
    - [x] `POST /api/v1/evaluate` 구현 (Mock 응답).
    - [x] 이 API를 호출하는 "Hello World" React 페이지 제작.

## 2단계: 지식 코어 (The "Brain")
**목표**: `hybrid-rag-system`을 참조하여 모듈형 지식 시스템 구현.
- [x] **Hybrid RAG 분석**
    - [x] `hybrid-rag-system` 로직 분석 및 벤치마킹.
    - [x] 핵심 로직 추출:
        - 그래프 구축 (노드/엣지).
        - 하이브리드 검색 전략 (벡터 + 그래프).
- [x] **지식 매니저 (Knowledge Manager) 구현**
    - [x] `KnowledgeProvider` 인터페이스 정의.
    - [x] **Vector 모듈**: `ChromaDB` (로컬) 또는 `Vertex AI Vector Search` 활용 구현.
    - [x] **Graph 모듈**: **FalkorDB** (초저지연 그래프 DB) 활용 구현.
        - 참조: [FalkorDB 웹사이트](https://www.falkordb.com/)
        - **[x]**: **LLM 기반 그래프 구축 로직** 구현 (기존 룰 기반 대체).
            - Gemini를 사용하여 비정형 텍스트/스키마에서 엔티티와 관계를 추출.
    - [x] **라우터**: 모듈 간 선택 또는 결합 로직 구현.

## 3단계: 평가 엔진 (The "Teacher")
**목표**: Gemini를 활용한 채점 시스템 구축.
- [x] **LLM 심판 (Gemini)**
    - [x] Gemini가 "엄격한 데이터 엔지니어"처럼 행동하도록 시스템 프롬프트 설계.
    - [x] `JudgeService` 구현: (사용자 답안, 정답, 맥락)을 입력받아 점수 + 피드백 반환.
- [x] **벤치마킹 스위트**
    - [x] 테스트 케이스 스키마 정의 (`json` 또는 `yaml`).
    - [x] `hybrid-rag-system`의 평가 지표/로직 이식.
    - [x] 배치(Batch)로 테스트 케이스를 실행하고 종합 점수를 계산하는 러너 구현.

## 4단계: 관측성 및 웹 포털
**목표**: 프로세스 시각화.
- [x] **트레이스 로깅 (Trace Logging)**
    - [x] 모든 요청/응답/LLM 호출을 캡처하는 미들웨어.
    - [x] 경량 DB(SQLite 또는 Firestore)에 트레이스 저장.
- [x] **상호작용 검사기 (Interaction Inspector) UI**
    - [x] **트레이스 목록**: 최근 에이전트 상호작용을 보여주는 테이블.
    - [x] **상세 뷰**:
        - Gemini에게 보낸 정확한 프롬프트 표시.
        - 검색된 맥락 청크(Context Chunks) 표시.
        - 반환된 JSON 피드백 표시.

## 5단계: 파일럿 및 개선
- [ ] **파일럿 데이터 수집**
    - [x] 샘플 "커넥티드 카" 데이터셋 스키마를 그래프에 주입.
    - [x] 샘플 문서를 벡터 저장소에 업로드.
- [x] **엔드투엔드 테스트**
    - [x] 외부 에이전트가 질문하는 상황 시뮬레이션.
    - [x] DKMES가 맥락을 검색하고, 답안을 채점하며, 피드백을 반환하는지 검증.

## 6단계: 배포 및 패키징 (Future)
**목표**: 프로덕션 배포를 위한 애플리케이션 패키징.
- [ ] **Dockerization (컨테이너화)**
    - [ ] Backend (FastAPI)용 `Dockerfile` 작성.
    - [ ] Frontend (Nginx/React)용 `Dockerfile` 작성.
    - [ ] 전체 서비스(App, DB)를 통합 관리할 `docker-compose.yml` 업데이트.
- [ ] **CI/CD**
    - [ ] 자동화된 테스트 및 빌드를 위한 GitHub Actions 설정.
