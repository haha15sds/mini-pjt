#!/usr/bin/env bash
# 실행 스크립트 (과제 규약 3-1, 선택). 저장소 루트에서 실행한다.
#   ./run.sh setup         가상환경 만들고 패키지 설치 (.env.example → .env 복사 후 키 입력)
#   ./run.sh api           FastAPI 서버 (POST /query, 포트 8000)
#   ./run.sh ui            Streamlit 화면 (포트 8501, '샘플 응답으로 보기'는 키 없이 동작)
#   ./run.sh eval [N]      인-아웃 세트 18건 + RAGAS (채점 모델 Haiku), 결과는 evaluation/roundN_*
#   ./run.sh docker        Docker 이미지 빌드 후 API 실행 (--env-file .env)
set -euo pipefail
cd "$(dirname "$0")"

if [ -x .venv/bin/python ]; then PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then PY=.venv/Scripts/python.exe   # Windows Git Bash
else PY=python3; fi

case "${1:-}" in
  setup)
    python3 -m venv .venv
    if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY=.venv/Scripts/python.exe; fi
    "$PY" -m pip install -r requirements.txt
    [ -f .env ] || cp .env.example .env
    echo "완료: .env 에 AWS Bedrock 키를 넣으세요." ;;
  api)    "$PY" -X utf8 -m uvicorn src.api.server:app --port 8000 ;;
  ui)     "$PY" -X utf8 -m streamlit run src/ui/app.py --server.port 8501 ;;
  eval)   "$PY" -X utf8 src/evaluation/run_eval.py --round "${2:-11}" --ragas-model haiku ;;
  docker) docker build -t mini-pjt . && docker run --rm -p 8000:8000 --env-file .env mini-pjt ;;
  *) sed -n '2,8p' "$0"; exit 1 ;;
esac
