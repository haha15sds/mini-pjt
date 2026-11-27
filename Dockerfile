# Gemini Enterprise 설정 지원 에이전트 — 클린 환경 재현용 이미지
#
# 빌드:  docker build -t mini-pjt .
# API :  docker run --rm -p 8000:8000 --env-file .env mini-pjt
# 화면:  docker run --rm -p 8501:8501 --env-file .env mini-pjt \
#          streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
# 평가:  docker run --rm --env-file .env -v "$PWD/evaluation:/app/evaluation" mini-pjt \
#          python src/evaluation/run_eval.py --round 11 --ragas-model haiku
#
# .env(AWS Bedrock 키)는 이미지에 넣지 않고 실행할 때 --env-file 로 준다(.dockerignore).
# 검색 인덱스(chroma_db)도 이미지에 넣지 않는다. 컨테이너가 처음 뜰 때 Bedrock 임베딩으로 만든다(약 1분).
FROM python:3.14-slim

ENV PYTHONUTF8=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# ragas 가 쓰는 scikit-network 는 리눅스 Python 3.14용 wheel 이 없어 소스에서 빌드한다 → C++ 컴파일러가 필요하다
# (GitHub Actions 첫 빌드에서 "/usr/bin/g++ 없음"으로 실패해 추가)
RUN apt-get update \
 && apt-get install -y --no-install-recommends g++ \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000 8501
CMD ["uvicorn", "src.api.server:app", "--host", "0.0.0.0", "--port", "8000"]
