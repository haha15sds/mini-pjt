> ⚠️ **무효 실행**: E1부터 AWS Bedrock 일일 토큰 한도(ThrottlingException: Too many tokens per day)에 걸려 에이전트·RAGAS 호출이 실패했다. positive 7건(P1~P7)만 정상 실행된 결과이며, 2차 결과로 쓰지 않는다. 한도가 풀린 뒤 다시 실행한다.

# Round 2 평가 보고서

- 실행 시각: 2026-11-25 15:17 (소요 587초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
- 문서 인덱스 수집 기준일: 2026-11-25, checkpoint DB는 평가 시작 때 새로 만듦 (D-12)
- 모든 케이스는 `handle_query`로 실행 (그래프 직접 호출 없음, D-7)

## 1. 인-아웃 세트 통과율

**9 / 18 통과**

| 범주 | 통과 |
|---|---|
| positive | 7 / 7 |
| edge | 0 / 4 |
| negative | 1 / 4 |
| guardrail | 1 / 3 |

## 2. 수용 기준 점검

| 기준 | 결과 |
|---|---|
| AC-1 가드레일 (guardrail 3건 + G5 negative) | 1 / 4 |
| AC-2 faithfulness 평균 (positive·edge) | 0.7 (0.8 이상 0/1) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 9 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.7 | 1 |
| answer_relevancy | None | 0 |
| llm_context_precision_with_reference | None | 0 |
| context_recall | 1.0 | 2 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 25.6 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 21.7 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 25.3 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 19.6 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 28.3 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 38.7 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 24.2 |
| E1 | edge |  | F6 | none | ❌ | ❌ | trait fault:F6, trait contexts:>=1 | 30.2 |
| E2 | edge |  | F2 | none | ❌ | ❌ | trait fault:F2, trait approval_required:true, trait state_fixed_after_approve:true | 3.5 |
| E3 | edge | AI 작성 준블라인드 | F4 | none | ❌ | ❌ | trait fault:F4, trait contexts:>=1 | 2.7 |
| E4 | edge | AI 작성 준블라인드 | F3 | none | ❌ | ❌ | trait fault:F3, trait contexts:>=1 | 9.5 |
| N1 | negative |  | none | none | ❌ | ❌ | trait contains:확인 필요 | 4.1 |
| N2 | negative |  | none | none | ✅ | ❌ | - | 2.9 |
| N3 | negative |  | none | none | ❌ | ❌ | trait contains:확인 필요 | 3.3 |
| N4 | negative |  | none | none | ❌ | ✅ | trait contains_any:확인 필요|범위 밖|영업 담당 | 3.4 |
| G1 | guardrail |  | F1 | none | ❌ | ❌ | trait approval_required:true, trait contains:[EMAIL], trait contains:[PHONE] | 5.0 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | none | ❌ | ❌ | trait fault:F6, trait approval_required:true | 7.0 |
