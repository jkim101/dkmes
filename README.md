<p align="center">
  <img src="https://img.shields.io/badge/Status-Active%20Development-brightgreen" alt="Status"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-blue" alt="Version"/>
</p>

<h1 align="center">🧠 DKMES</h1>
<h3 align="center">Data Knowledge Management Eco-System</h3>

<p align="center">
  <strong>조직의 암묵적 지식을 발견하고, 연결하고, 활용하는 지능형 지식 관리 플랫폼</strong>
</p>

---

## 🎯 What is DKMES?

DKMES는 **조직 내 흩어진 데이터와 지식을 하나로 연결**하는 지능형 플랫폼입니다.

기존의 지식 관리 시스템은 문서를 저장하고 검색하는 데 그쳤습니다. 하지만 진정한 지식은 단순한 문서가 아니라 **데이터 간의 관계**, **숨겨진 패턴**, **암묵적 전문성** 속에 존재합니다.

DKMES는 이러한 **보이지 않는 지식**을 발견하고, 필요한 사람에게 적시에 전달합니다.

---

## ✨ Key Features

### 📚 Hybrid RAG (Retrieval-Augmented Generation)
- **Vector Search**: 의미 기반 유사성 검색으로 관련 정보 발견
- **Graph Search**: 개념과 개념 사이의 관계를 따라 탐색
- **Hybrid**: 두 방식을 결합하여 최적의 컨텍스트 제공

### 🕸️ Knowledge Graph
- 문서에서 자동으로 **개념(Entity)**과 **관계(Relationship)** 추출
- 3D 시각화로 지식의 연결 구조를 직관적으로 탐색
- 숨겨진 지식 패턴과 지식 공백 발견

### 🤖 Multi-Agent Collaboration
- 서로 다른 전문 도메인을 가진 AI 에이전트들이 협력
- 에이전트 간 **지식 교환 프로토콜(KEP)**로 분산 지식 활용
- 하나의 에이전트로 해결할 수 없는 복합 질문도 처리

### 📊 RAG Evaluation Studio
- Vector, Graph, Hybrid 전략의 성능을 **실시간 비교**
- RAGAS 기반 평가 메트릭 (Faithfulness, Relevance, Recall)
- 배치 평가로 대규모 품질 검증

### 🔍 Trace Inspector
- 모든 RAG 파이프라인의 **동작 과정을 투명하게 추적**
- 검색 → 컨텍스트 → 답변 생성의 전체 흐름 시각화
- 디버깅과 최적화를 위한 인사이트 제공

---

## 🌟 Why DKMES?

| 기존 방식 | DKMES |
|----------|-------|
| 키워드 검색에 의존 | 의미 기반 + 관계 기반 하이브리드 검색 |
| 문서 저장만 가능 | 문서에서 지식 그래프 자동 구축 |
| 단일 관점의 답변 | 다중 에이전트 협업으로 풍부한 인사이트 |
| 블랙박스 AI | 투명한 추론 과정과 평가 지표 제공 |

---

## 🚀 Getting Started

```bash
# 1. 저장소 클론
git clone https://github.com/jkim101/dkmes.git
cd dkmes

# 2. Docker로 Graph DB 시작
docker-compose up -d

# 3. 백엔드 실행
cd backend
poetry install
poetry run uvicorn main:app --reload --port 8000

# 4. 프론트엔드 실행 (새 터미널)
cd frontend
npm install
npm run dev
```

**접속**: http://localhost:5174

---

## 🎯 Use Cases

- **기업 지식 관리**: 흩어진 사내 문서, 위키, 노트에서 통합 지식 검색
- **연구 자료 분석**: 논문과 리포트에서 핵심 개념 관계 시각화
- **고객 지원 향상**: 과거 사례와 해결책을 지능적으로 연결
- **온보딩 가속화**: 신입 직원이 조직의 암묵지에 빠르게 접근

---

## 📬 Contact

**Jihoon Kim** - jkim101@github

---

<p align="center">
  <i>"지식은 연결될 때 비로소 힘을 발휘합니다."</i>
</p>
