FROM python:3.13-slim

WORKDIR /app


COPY streamlit_app/requirements.txt ./requirements.txt
COPY pyproject.toml ./

RUN pip install --no-cache-dir -r requirements.txt


RUN pip install --no-cache-dir pyspark==4.2.0


COPY pyspark_jobs/ ./pyspark_jobs/
COPY streamlit_app/ ./streamlit_app/
COPY configs/ ./configs/


RUN pip install --no-cache-dir -e .

EXPOSE 8080

CMD ["streamlit", "run", "streamlit_app/Readmission_vs_Staffing.py", "--server.port=8080", "--server.address=0.0.0.0", "--server.headless=true"]
