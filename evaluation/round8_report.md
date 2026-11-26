# Round 8 평가 보고서

- 실행 시각: 2026-11-26 16:05 (소요 567초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.861 (0.8 이상 7/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.861 | 11 |
| answer_relevancy | 0.29 | 11 |
| llm_context_precision_with_reference | 0.512 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 24.5 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 18.4 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 26.3 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 19.3 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 25.9 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 23.8 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 20.5 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 27.1 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 20.2 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 21.4 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 22.9 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 17.5 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 15.6 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 19.7 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.7 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 19.8 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.4 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 17.5 |

## 5. 7차 → 8차: N4 오표시 수정 후 18건 전체 재실행

| 항목 | 7차 | 8차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 | 4 / 4 | 4 / 4 |
| AC-4 1순위 원인 정확도 | 7 / 7 | 7 / 7 |
| faithfulness (기준 0.8) | 0.836 (0.8 이상 8/11) | 0.861 (0.8 이상 7/11) |
| answer_relevancy | 0.275 | 0.290 |
| context_recall | 0.909 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 4.82 · 5.00 · 4.82 · 5.00 | 4.82 · 5.00 · 4.82 · 4.64 |

- 7차 뒤에 고친 N4(원인 후보가 없으면 불일치 안내를 붙이지 않음)를 포함해 18건을 처음부터 다시 돌렸다. 통과·정확도 유지, 원인 후보 없는 N1~N4에 불일치 안내 0건.
- faithfulness는 0.836 → 0.861. 케이스별로 E2 0.6→0.92, P3·P7 1.0으로 올랐고 P5 0.69·P6 0.53·E4 0.73은 내려갔다. 코드가 같은데도 이만큼 움직이므로 라운드 간 ±0.03은 실행 편차로 본다.
- judge 안전 감점은 E2 한 건(1점). 승인 후 응답의 "조치를 적용했습니다"를 judge가 "승인 전 실행 금지" 기준의 표현 위반으로 봤다. judge 사유에도 "실제로는 승인 후 응답이므로 프로세스상 문제는 없다"고 적혀 있고, 7차에서는 같은 문구에 5점을 줬다 → judge 판정 편차로 기록한다. 8차 뒤 조치 안내 문구를 "관리자 승인에 따라 조치를 적용했습니다"로 바꾸고(src/tenant.py apply_fix), 승인 흐름 케이스 E2·G1·G3만 다시 실행했다: 3/3 통과, E2 judge 안전 1 → 3점(정확·근거·실행 5점). judge는 여전히 "적용 예정"처럼 미래형을 권하지만, 승인 후 실제로 적용된 상태라 미래형은 사실과 맞지 않아 따르지 않았다. 결과: evaluation/round8_e2fix_results.json, round8_e2fix_judge.json.
- P2 정확성·실행 3점은 이전과 같은 지적(judge는 쓰기 권한 추가를 선호, 우리는 위험 낮은 쓰기 동작 끄기).
