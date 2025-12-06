# DKMES 통합 검증 체크리스트 (Verification Checklist)

이 문서는 DKMES(Data Knowledge Management Eco-System)의 모든 기능이 정상적으로 구현되었는지 확인하기 위한 테스트 시나리오입니다.

## 1. 데이터 주입 및 처리 (Data Ingestion)
**목표**: 문서가 정상적으로 업로드되고, 벡터 및 그래프 데이터베이스에 저장되는지 확인.

- [ ] **파일 업로드 테스트**
    1. **Data Manager** 메뉴로 이동합니다.
    2. 테스트용 텍스트 파일(`test.txt`) 또는 PDF를 드래그 앤 드롭합니다.
    3. "Upload" 버튼을 클릭합니다.
    4. **결과 확인**:
        - [ ] 화면에 "Upload successful" 메시지가 표시되는가?
        - [ ] "Indexed Knowledge" 목록에 파일명이 추가되는가?
- [ ] **데이터 처리 확인**
    1. **Dashboard** 메뉴로 이동합니다.
    2. **결과 확인**:
        - [ ] `VECTOR CHUNKS` 숫자가 증가했는가?
        - [ ] `GRAPH NODES` 및 `RELATIONSHIPS` 숫자가 증가했는가?

## 2. 그래프 시각화 (Graph Visualization)
**목표**: 구축된 지식 그래프가 시각적으로 올바르게 표현되는지 확인.

- [ ] **그래프 탐색 테스트**
    1. **Graph Explorer** 메뉴로 이동합니다.
    2. "Refresh Graph" 버튼을 클릭합니다 (또는 자동 로딩).
    3. **결과 확인**:
        - [ ] 화면 중앙에 노드(Node)와 엣지(Edge)들이 나타나는가?
        - [ ] 노드를 드래그하거나 줌인/줌아웃이 부드럽게 작동하는가?
        - [ ] 노드에 마우스를 올렸을 때 라벨(이름)이 보이는가?

## 3. 하이브리드 채팅 (Hybrid Chat)
**목표**: 벡터 검색과 그래프 검색이 결합되어 질의응답이 수행되는지 확인.

- [ ] **질의응답 테스트**
    1. **Playground** 메뉴로 이동합니다.
    2. 업로드한 문서 내용과 관련된 질문을 입력합니다 (예: "이 문서의 핵심 내용은 뭐야?").
    3. "Send" 버튼을 클릭합니다.
    4. **결과 확인**:
        - [ ] 에이전트가 "Typing..." 상태를 거쳐 답변을 출력하는가?
        - [ ] 답변 내용이 업로드한 문서를 기반으로 정확하게 작성되었는가?
        - [ ] (선택) 답변이 "I don't have enough information"이 아닌 유의미한 내용인가?

## 4. 관측성 및 디버깅 (Observability)
**목표**: 시스템 내부 동작(검색 과정, 프롬프트 등)이 투명하게 기록되는지 확인.

- [ ] **트레이스 검사 테스트**
    1. Playground에서 질문을 한 직후, **Inspector** 메뉴로 이동합니다.
    2. 왼쪽 "Recent Traces" 목록의 최상단 항목(방금 한 질문)을 클릭합니다.
    3. **결과 확인**:
        - [ ] **Timeline**에 `Retrieval Start`, `Context Retrieved`, `Generation End` 단계가 보이는가?
        - [ ] **Retrieval Details**를 클릭했을 때, `Vector Retrieval`과 `Graph Retrieval` 결과가 각각 보이는가?
        - [ ] **LLM Prompt**를 클릭했을 때, 실제로 Gemini에게 보낸 프롬프트가 보이는가?

## 5. 평가 시스템 (Evaluation Studio)
**목표**: RAG 성능을 정량적으로 평가할 수 있는지 확인.

- [ ] **단건 평가 테스트**
    1. **Evaluation Studio** 메뉴로 이동합니다.
    2. "Run Evaluation" 탭을 선택합니다.
    3. 질문(Query)과 정답(Ground Truth)을 입력하고 "Run Comparison"을 클릭합니다.
    4. **결과 확인**:
        - [ ] **Vector**, **Graph**, **Hybrid** 세 가지 방식의 점수(Score)가 각각 계산되는가?
        - [ ] 각 방식에 대한 "Reasoning"(채점 사유)이 출력되는가?
