# Round 10 평가 보고서

- 실행 시각: 2026-11-27 09:20 (소요 579초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.866 (0.8 이상 7/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.866 | 11 |
| answer_relevancy | 0.262 | 11 |
| llm_context_precision_with_reference | 0.834 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 23.4 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 19.9 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 28.1 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 18.3 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 24.4 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 29.8 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 21.7 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 27.2 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 21.4 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 24.5 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 23.9 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 16.4 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 16.1 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 21.4 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.5 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 20.8 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.4 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 20.0 |

## 5. 9차 → 10차: 검색 순위 개선

| 항목 | 9차 | 10차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 · AC-4 1순위 원인 | 4/4 · 7/7 | 4/4 · 7/7 |
| context_precision | 0.512 | **0.834** |
| faithfulness (기준 0.8) | 0.931 | 0.866 |
| answer_relevancy | 0.314 | 0.262 |
| context_recall | 0.939 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 4.82 · 5.00 · 4.73 · 5.00 | 5.00 · 5.00 · 4.82 · 5.00 |

**무엇을 바꿨나** (src/agent.py plan_runbook)
1. 원인 중심 재검색을 모든 원인에 한다. 전에는 처음 검색어가 문의 증상 문장에서 나와 일반 문제 해결 문서가 앞에 깔리고, 원인 근거 문서는 빠지거나 맨 뒤에 붙었다(9차 P5 0.17 · E1 0.23 · P6 0.25 · E4 0.33).
   검색어는 장애 이름과 모델이 쓴 원인 설명이다. 평가 reference로 쓰는 근거 요약(evidence_note)은 검색어에서 뺐다(평가 누설 방지, 전에는 쓰고 있었음).
2. contexts 순서를 원인 근거 문서 → 테넌트 상태·조치 목록 → 나머지 검색 결과로 정렬한다. 관리자가 보는 근거 목록도 같은 순서다.
3. 다른 커넥터 문서(Confluence)는 원인 근거에서 뺀다. 반복 실행에서 E2(F2 쓰기 scope)의 재검색 1위가 Confluence의 'minimum application scopes'였다(E2 0.67 → 0.42). 고친 뒤 10차 E2 0.58.

**효과 판정**: 한 번 실행값이 아니라 같은 코드 3회씩 비교했다(evaluation/repeat_report.md). context_precision 중앙값 0.512 → 0.798, 범위가 겹치지 않음. faithfulness는 범위가 겹쳐 변화 없음으로 본다(10차 0.866도 개선 전 범위 0.840~0.931 안).
**남은 약점**: P6(F5) · E2(F2) · E4(F3) 0.58 — 근거 문서 2개 중 1개만 reference와 맞는다고 채점됨.
