# Round 4 평가 보고서

- 실행 시각: 2026-11-26 09:46 (소요 639초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.893 (0.8 이상 10/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.893 | 11 |
| answer_relevancy | 0.312 | 11 |
| llm_context_precision_with_reference | 0.508 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 50.7 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 37.6 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 38.6 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 20.1 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 22.0 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 25.2 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 22.7 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 26.5 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 20.7 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 22.0 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 25.2 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 15.6 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 16.5 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 15.2 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 10.9 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 21.4 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.4 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 20.3 |

## 5. 강사 피드백 반영 결과 (3차 → 4차)

**피드백**: F4(대소문자)·F5(그룹 클레임 한도)처럼 값 비교로 갈리는 원인을 LLM이 check_tenant_state 원본만 보고 찾으면 1순위 정확도가 흔들릴 수 있다 → 권장 구성과 달라진 필드·그룹 개수를 코드로 계산해 함께 돌려줄 것.

**반영**: check_tenant_state가 `{checks, state}`를 돌려준다. checks는 코드로 계산한 비교 결과(권장 구성 대비 차이, 그룹 수와 토큰 한도, 이메일·UPN·식별자 대소문자 비교, subject 매핑, 권한 없는 사이트, Entra 앱 점검)이며 장애 ID·이름은 넣지 않는다(D-15).

| 항목 | 3차 | 4차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 | 7 / 7 |
| faithfulness (기준 0.8) | 0.853 (0.8 이상 9/11) | **0.893 (10/11)** |
| P6 faithfulness (F5 그룹 한도) | 0.611 | **0.800** |
| E4 faithfulness (F3, 준블라인드) | 0.565 | **0.846** |
| answer_relevancy | 0.338 | 0.312 |
| context_precision (with reference) | 0.524 | 0.508 |
| context_recall | 0.909 | 0.939 |

**흔들림 측정 (반복 실행)**: positive·edge 11건을 같은 조건으로 한 번 더 실행(`round4_repeat_results.json`).
- 1순위 원인이 두 번 실행에서 같은 비율: **11 / 11**, 두 번 모두 정답: **11 / 11** (F4: P3·E3, F5: P6, 복합 E1 포함)
- 한계: 3차 이전에는 반복 실행을 하지 않아 '반영 전 흔들림'과 직접 비교할 수는 없다. 반영 후 2회 실행에서 흔들림이 없었다는 것까지만 말할 수 있다.

**해석**: 값 비교를 코드로 옮기자 LLM이 숫자·대소문자를 해석하며 덧붙이던 근거 없는 문장이 줄어 faithfulness가 올랐다(특히 F5 P6, F3 E4). answer_relevancy는 계속 낮아지는 추세로, 답변이 '상태값 + 문서 근거' 나열 위주라 질문 문장과의 유사도가 낮은 탓으로 본다.
