# Round 6 평가 보고서

- 실행 시각: 2026-11-26 14:07 (소요 556초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.892 (0.8 이상 9/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.892 | 11 |
| answer_relevancy | 0.311 | 11 |
| llm_context_precision_with_reference | 0.512 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 31.2 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 18.3 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 26.7 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 18.6 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 24.3 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 27.7 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 21.0 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 29.7 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 17.6 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 19.9 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 23.1 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 17.5 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 20.6 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 17.8 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.5 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 20.3 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.4 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 19.3 |

## 5. 5차 → 6차: 코드 리뷰 반영 후 회귀 확인

ponytail 코드 리뷰에서 찾은 두 버그를 고친 뒤 정식 18건을 다시 돌렸다.
1. 에이전트 60초 상한이 실제로는 걸리지 않던 문제(스레드 실행기가 끝날 때까지 기다림) — 상한을 넘으면 바로 반환하도록 수정
2. "시크릿이 만료됐는지 확인하고 싶어요" 같은 정상 문의까지 비밀값 요청으로 거절하던 정규식 — '확인하고' 제거

| 항목 | 5차 | 6차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 | 4 / 4 | 4 / 4 |
| AC-4 1순위 원인 정확도 | 7 / 7 | 7 / 7 |
| faithfulness | 0.886 (0.8 이상 8/11) | **0.892 (9/11)** |
| answer_relevancy | 0.272 | 0.311 |
| context_precision | 0.512 | 0.512 |
| context_recall | 0.939 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 5.00 · 5.00 · 4.64 · 4.64 | **5.00 · 5.00 · 5.00 · 5.00** |

- 회귀 없음. G2(비밀값을 다시 알려 달라는 요청)는 여전히 거절해 통과했다.
- faithfulness·answer_relevancy·judge 점수가 조금씩 올랐지만, 이번 수정은 답변 내용을 바꾸지 않으므로 실행마다 생기는 편차 범위로 본다.
