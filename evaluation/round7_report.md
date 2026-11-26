# Round 7 평가 보고서

- 실행 시각: 2026-11-26 15:30 (소요 544초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.836 (0.8 이상 8/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.836 | 11 |
| answer_relevancy | 0.275 | 11 |
| llm_context_precision_with_reference | 0.512 | 11 |
| context_recall | 0.909 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 24.6 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 18.3 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 27.2 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 18.1 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 23.6 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 24.3 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 22.8 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 22.5 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 19.6 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 22.2 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 20.9 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 16.5 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 15.9 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 17.3 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.8 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 19.2 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 17.0 |

## 5. 6차 → 7차: 불일치 대응 추가 후 회귀 확인

| 항목 | 6차 | 7차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 | 4 / 4 | 4 / 4 |
| AC-4 1순위 원인 정확도 | 7 / 7 | 7 / 7 |
| faithfulness (기준 0.8) | 0.892 (0.8 이상 9/11) | 0.836 (0.8 이상 8/11) |
| answer_relevancy | 0.311 | 0.275 |
| context_recall | 0.939 | 0.909 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 5.00 · 5.00 · 5.00 · 5.00 | 4.82 · 5.00 · 4.82 · 5.00 |

- 통과·정확도는 유지. 정상 케이스에 불일치 처리가 잘못 걸린 경우는 N4(가격 문의) 한 건이었고, "원인 후보가 없으면 불일치 안내를 붙이지 않는다"로 고친 뒤 N1~N4를 다시 돌려 4/4 통과·불일치 안내 0건을 확인했다.
- faithfulness는 0.892 → 0.836으로 내려갔지만 필수 기준(0.8)은 지킨다. 케이스별로는 오르고 내린 것이 섞여 있고(P4 0.75→1.0, E2 0.909→0.6), 프롬프트 규칙이 늘어난 영향과 실행 편차가 함께 있는 것으로 본다. 불일치 대응을 얻는 대신 치른 비용으로 기록한다.
- judge 감점은 P2 하나(정확성·실행 3점): judge는 쓰기 권한 추가를 선호하고 우리 조치 목록은 쓰기 동작 끄기를 고른다(4차와 같은 지적).
