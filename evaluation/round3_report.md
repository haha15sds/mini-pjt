# Round 3 평가 보고서

- 실행 시각: 2026-11-25 16:53 (소요 685초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
- RAGAS 채점 모델: us.anthropic.claude-haiku-4-5-20251001-v1:0
- 문서 인덱스 수집 기준일: 2026-11-25, checkpoint DB는 평가 시작 때 새로 만듦 (D-12)
- 모든 케이스는 `handle_query`로 실행 (그래프 직접 호출 없음, D-7)

## 1. 인-아웃 세트 통과율

**18 / 18 통과**

| 범주 | 통과 |
|---|---|
| positive | 7 / 7 |
| edge | 4 / 4 |
| negative | 4 / 4 |
| guardrail | 3 / 3 |

## 2. 수용 기준 점검

| 기준 | 결과 |
|---|---|
| AC-1 가드레일 (guardrail 3건 + G5 negative) | 4 / 4 |
| AC-2 faithfulness 평균 (positive·edge) | 0.853 (0.8 이상 9/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.853 | 11 |
| answer_relevancy | 0.338 | 11 |
| llm_context_precision_with_reference | 0.524 | 11 |
| context_recall | 0.909 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 25.6 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 28.0 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 35.9 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 27.6 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 42.3 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 35.3 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 32.3 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 36.6 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 28.5 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 31.4 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 35.7 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 20.1 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 23.0 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 24.2 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 18.1 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 24.4 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 20.5 |

## 5. 1차 → 2차 → 3차 비교

RAGAS는 모두 같은 채점 모델(Claude Haiku 4.5) 기준. 1차는 저장된 답변을 다시 채점한 값.

| 항목 | 1차 | 2차 | 3차 |
|---|---|---|---|
| 인-아웃 세트 통과 | 14 / 18 | 18 / 18 | **18 / 18** |
| AC-1 가드레일 | 2 / 4 | 4 / 4 | 4 / 4 |
| AC-2 faithfulness (기준 0.8) | 0.241 | 0.734 | **0.853 ✅** (0.8 이상 9/11) |
| answer_relevancy | 0.447 | 0.388 | 0.338 |
| context_precision (with reference) | 0.600 | 0.503 | 0.524 |
| context_recall | 0.667 | 0.909 | 0.909 |

3차 개선 내용: 0.8 미만이던 6건의 RAGAS 문장별 판정을 열어 본 결과에 맞춰
- 요약을 '테넌트 상태: 관찰값'과 '문서: 요구사항'을 나란히 쓰는 형태로 바꾸고 인과 추론 문장을 줄임
- 조치는 문서·조치 목록 문장을 거의 그대로, 번호 대신 목록(순서는 diagnosis.steps)
- 출처는 근거로 검색한 공식 문서 전체를 적음
- 계획 단계에서 고른 조치도 '승인 후 적용' 근거 항목을 contexts에 보장

남은 약점: P6(0.611)·E4(0.565)는 아직 0.8 미만. answer_relevancy는 라운드마다 내려갔다 — 답변이 근거 나열 위주로 바뀌어 질문과의 문장 유사도가 낮아진 것으로 보이며, 이번 프로젝트는 근거성(faithfulness)을 우선했다.
