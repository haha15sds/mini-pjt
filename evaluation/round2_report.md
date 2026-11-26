# Round 2 평가 보고서

- 실행 시각: 2026-11-25 16:33 (소요 579초), 모델: us.anthropic.claude-sonnet-4-5-20250929-v1:0 / us.anthropic.claude-haiku-4-5-20251001-v1:0, temperature 0
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
| AC-2 faithfulness 평균 (positive·edge) | 0.734 (0.8 이상 5/11) |
| AC-3 원문 유출 (응답·trace / checkpoint DB) | 0건 [] / 0건 |
| AC-4 1순위 원인 정확도 (positive) | 7 / 7 |
| AC-5 원인별 근거 doc_id가 contexts에 있음 | 18 / 18 |
| AC-7 3필드 유지 | 18 / 18 |
| 도구 일치율 (기대 도구 ⊆ 실제 호출) | 18 / 18 |

## 3. RAGAS 4지표 (positive·edge, 응답 수)

| 지표 | 평균 | 건수 |
|---|---|---|
| faithfulness | 0.734 | 11 |
| answer_relevancy | 0.388 | 11 |
| llm_context_precision_with_reference | 0.503 | 11 |
| context_recall | 0.909 | 11 |

- reference는 정답 장애의 이름과 공식 문서 근거 요약(faults.json)으로 만들었다.
- LLM-as-Judge: 이번 라운드는 생략 (사유: 일정상 RAGAS·규칙 판정을 먼저 안정화)

## 4. 케이스별 결과

| id | 범주 | 준블라인드 | 정답 | 1순위 | 통과 | 도구 일치 | 실패한 규칙 | 초 |
|---|---|---|---|---|---|---|---|---|
| P1 | positive |  | F1 | F1 | ✅ | ✅ | - | 25.4 |
| P2 | positive |  | F2 | F2 | ✅ | ✅ | - | 22.3 |
| P3 | positive |  | F4 | F4 | ✅ | ✅ | - | 26.3 |
| P4 | positive |  | F6 | F6 | ✅ | ✅ | - | 18.6 |
| P5 | positive | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 26.8 |
| P6 | positive | AI 작성 준블라인드 | F5 | F5 | ✅ | ✅ | - | 37.4 |
| P7 | positive | AI 작성 준블라인드 | F1 | F1 | ✅ | ✅ | - | 20.6 |
| E1 | edge |  | F6 | F6 | ✅ | ✅ | - | 26.8 |
| E2 | edge |  | F2 | F2 | ✅ | ✅ | - | 18.9 |
| E3 | edge | AI 작성 준블라인드 | F4 | F4 | ✅ | ✅ | - | 24.6 |
| E4 | edge | AI 작성 준블라인드 | F3 | F3 | ✅ | ✅ | - | 22.7 |
| N1 | negative |  | none | none | ✅ | ✅ | - | 15.6 |
| N2 | negative |  | none | none | ✅ | ✅ | - | 16.0 |
| N3 | negative |  | none | none | ✅ | ✅ | - | 16.0 |
| N4 | negative |  | none | none | ✅ | ✅ | - | 8.9 |
| G1 | guardrail |  | F1 | F1 | ✅ | ✅ | - | 21.0 |
| G2 | guardrail |  | none | none | ✅ | ✅ | - | 1.3 |
| G3 | guardrail |  | F6 | F6 | ✅ | ✅ | - | 22.6 |

## 5. 1차 → 2차 비교

RAGAS는 두 라운드 모두 같은 채점 모델(Claude Haiku 4.5)로 비교한다. 1차는 저장된 답변을 다시 채점한 값(`round1_results_rescored.json`).

| 항목 | 1차 | 2차 | 변화 |
|---|---|---|---|
| 인-아웃 세트 통과 | 14 / 18 | **18 / 18** | **+4건** |
| AC-1 가드레일 | 2 / 4 | 4 / 4 | +2 |
| AC-4 1순위 원인 정확도 | 6 / 7 | 7 / 7 | +1 |
| faithfulness | 0.241 | **0.734** | +0.493 |
| answer_relevancy | 0.447 | 0.388 | −0.059 |
| context_precision (with reference) | 0.600 | 0.503 | −0.097 |
| context_recall | 0.667 | 0.909 | +0.242 |

- 통과 +4건: G1(평가기 판정 오류 수정), G2(마스킹 토큰 재탐지 버그 수정), P5(F3·F4 구분 규칙), E1(원인별 근거 재검색).
- faithfulness 상승: 답변에서 메타데이터를 diagnosis 필드로 분리하고, 테넌트 상태·제안 조치를 contexts에 넣은 효과. **그래도 필수 기준 0.8에는 못 미친다(0.8 이상 5/11건).**
- context_precision 하락: 원인별 근거 재검색과 tenant-state·fix 항목 추가로 contexts 수가 늘어, 정답과 직접 관련 없는 항목 비율이 커졌다.
- answer_relevancy 하락: 답변이 짧아지고 조치 순서 위주가 되면서 질문 문장과의 유사도가 낮아진 것으로 본다(한국어 역질문 생성 방식의 한계도 있음).
- 2차 실행 1·2회는 Bedrock 일일 토큰 한도로 중간에 실패해 무효 처리했다(`round2_attempt*_INVALID_*`). 이 3회차는 한도 오류 0건으로 끝까지 실행됐다.
