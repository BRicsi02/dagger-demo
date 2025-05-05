# backend/Dockerfile
FROM python:3.10-slim
WORKDIR /app

# A projekt gyökeréből érkező context miatt IDE azt kell megadni, ahonnan másol:
COPY backend/app.py     ./app.py
COPY frontend/          ./frontend/

RUN pip install flask
EXPOSE 5000
CMD ["python", "app.py"]
