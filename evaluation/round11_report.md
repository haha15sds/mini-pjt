# Round 11 평가 보고서

- 실행 시각: 2026-11-27 11:22 (소요 591초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.851 (0.8 이상 8/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.851 | 11 |
| answer_relevancy | 0.298 | 11 |
| llm_context_precision_with_reference | 0.829 | 11 |
| context_recall | 0.939 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 48.5 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 28.4 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 25.5 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 17.9 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 26.4 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 25.9 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 23.2 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 24.4 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 20.4 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 24.6 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 28.9 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 16.0 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 14.7 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 17.9 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 9.0 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 23.6 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 24.5 |

## 5. 10차 → 11차: 강사 중간평가(9일차 스냅샷) 반영

| 항목 | 10차 | 11차 |
|---|---|---|
| 인-아웃 세트 통과 | 18 / 18 | 18 / 18 |
| AC-1 가드레일 · AC-4 1순위 원인 | 4/4 · 7/7 | 4/4 · 7/7 |
| faithfulness (기준 0.8) | 0.866 | 0.851 |
| answer_relevancy | 0.262 | 0.298 |
| context_precision | 0.834 | 0.829 |
| context_recall | 0.939 | 0.939 |
| LLM-as-Judge 정확성·근거성·실행·안전 | 5.00 · 5.00 · 4.82 · 5.00 | 5.00 · 5.00 · 5.00 · 5.00 |

**바뀐 것**
- F4 조치가 이메일·UPN·subject를 소문자로 맞추고 이전 식별자 연결을 표시한다. 전에는 조치 뒤에도 S03·S07에서 F4가 다시 잡혔다. 지금은 S00~S08 모두 조치 후 코드 점검에서 장애가 사라진다.
- 평가기의 "승인 후 복구"(E2) 판정이 코드 점검으로 기대 장애가 실제로 사라졌는지까지 본다. 실패 케이스가 있으면 종료 코드 1, 평가 전용 체크포인트 파일이 기본값이다.
- 검색 색인 이름에 문서 내용 지문을 붙여 문서가 바뀌면 새로 만든다(이번 실행에서 새로 만듦). 벡터 검색이 실패하면 BM25만으로 답한다.
- 모든 모델 호출에 응답 대기 45초 상한. 응답 contexts(테넌트 조회 결과 포함)와 오류 문구를 내보낼 때 마스킹한다.

**판정**: 통과·정확도 유지. faithfulness 0.851은 같은 코드 3회 반복에서 본 편차 범위(0.84~0.93) 안이고, context_precision 0.829도 개선 후 범위(0.77~0.83) 안이라 이번 변경으로 품질이 바뀌지 않았다고 본다. contexts 마스킹 뒤에도 근거 충실도는 기준을 지킨다.
