FROM python:3.12-slim
LABEL authors="Quyen"

WORKDIR /onpremEM
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt
RUN playwright install chromium
RUN playwright install-deps chromium
RUN mkdir ./report
COPY tests ./tests

CMD ["pytest", "--html=report/report.html", "-v", "tests/EM_GUI_tests.py"]
#CMD ["sleep", "600"]