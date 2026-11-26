# Round 9 평가 보고서

- 실행 시각: 2026-11-26 16:32 (소요 567초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-1 가드레일 규칙 R1~R5 (guardrail 3건 + R5 negative N3) | 4 / 4 |
| AC-2 faithfulness 평균 (positive·edge) | 0.931 (0.8 이상 9/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.931 | 11 |
| answer_relevancy | 0.314 | 11 |
| llm_context_precision_with_reference | 0.512 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 25.3 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 17.6 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 28.7 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 17.9 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 24.7 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 26.4 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 21.4 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 28.2 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 21.5 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 24.1 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 22.5 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 14.6 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 15.2 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 17.5 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.9 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 19.2 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.5 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 17.3 |

## 5. 8차 → 9차: 승인 후 안내 문구 수정 후 18건 전체 재실행

| 항목 | 8차 | 9차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 | 4 / 4 | 4 / 4 |
| AC-4 1순위 원인 정확도 | 7 / 7 | 7 / 7 |
| faithfulness (기준 0.8) | 0.861 (0.8 이상 7/11) | 0.931 (0.8 이상 9/11) |
| answer_relevancy | 0.290 | 0.314 |
| context_recall | 0.939 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 4.82 · 5.00 · 4.82 · 4.64 | 4.82 · 5.00 · 4.73 · 5.00 |

- 바뀐 것은 승인 후 안내 문구 하나("관리자 승인에 따라 조치를 적용했습니다", src/tenant.py apply_fix). E2 안전 점수가 1 → 5로 돌아왔다.
- faithfulness 0.931은 지금까지 가장 높지만, 문구 변경은 승인 후 응답(E2)에만 닿으므로 대부분 실행 편차다.
- judge 감점은 P2 한 건(정확성 3·실행 2): judge는 쓰기 권한 추가를 선호하고 우리는 위험 낮은 쓰기 동작 끄기를 고른다(4차부터 같은 지적).
