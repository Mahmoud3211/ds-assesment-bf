FROM python:3.9.21

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


COPY . .
EXPOSE 8501

CMD ["sh", "-c", "cd ./src && streamlit run dashboard.py --server.port 8501"]

