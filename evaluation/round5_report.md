# Round 5 평가 보고서

- 실행 시각: 2026-11-26 11:53 (소요 536초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.886 (0.8 이상 8/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.886 | 11 |
| answer_relevancy | 0.272 | 11 |
| llm_context_precision_with_reference | 0.512 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 24.0 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 17.8 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 30.1 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 17.6 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 26.0 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 25.1 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 19.4 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 25.6 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 18.0 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 20.1 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 22.1 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 17.3 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 14.2 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 19.2 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.4 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 17.7 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 16.9 |

## 5. 4차 → 5차: 강사 힌트 집중 점검 결과 반영

강사 피드백 유형(값 비교로 갈리는 원인)을 변형 20개로 따로 시험한 결과([stress_hint_report.md](stress_hint_report.md)), 코드로 계산한 비교값만으로는 '권장 구성과 다르기만 한 값'을 원인으로 오진했다(대조군 1/5). 그래서 checks에 코드 규칙 판정 `findings`(실제 문제)와 `not_a_problem`(문제 아님)을 더하고, 원인은 findings에서만 고르게 했다. 변형 20개는 14/20 → **20/20**.

이 변경이 정식 18건을 해치지 않았는지 확인한 것이 5차다.

| 항목 | 4차 | 5차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-4 1순위 원인 정확도 | 7 / 7 | 7 / 7 |
| faithfulness | 0.893 (0.8 이상 10/11) | 0.886 (0.8 이상 8/11) |
| answer_relevancy | 0.312 | 0.272 |
| context_precision | 0.508 | 0.512 |
| context_recall | 0.939 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 4.82 · 5.00 · 4.82 · 5.00 | 5.0 · 5.0 · 4.64 · 4.64 |

- 회귀 없음: 통과·정확도는 그대로이고 faithfulness 평균은 같은 수준(±0.01). 0.8 이상 건수는 10→8건으로 줄어 응답별 편차가 있다.
- judge 감점: P2·P6·P7은 실행 가능성 3~4점(조치 단계가 짧음), E2는 안전성 1점 — 승인 후 응답이라는 사실을 judge에 함께 줬는데도 '조치를 적용했다' 문장을 무단 적용으로 본 경우로, 4차에서는 같은 조건에서 5점이었다. judge 판정도 실행마다 흔들릴 수 있음을 보여 준다.
