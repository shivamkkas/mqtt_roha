# ---------- Stage 1: Builder ----------
FROM python:3.11-slim AS builder

# ARG APP_NAME
# ARG RELEASE_VERSION
# ARG BUILD_TIME

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# RUN pip install pyinstaller

# COPY . .

# RUN pyinstaller --onefile --name ${APP_NAME} main.py

# # ---------- Stage 2: Runtime ----------
# FROM python:3.11-slim

# ARG RELEASE_VERSION
# ARG BUILD_TIME

# ENV RELEASE_VERSION=${RELEASE_VERSION}
# ENV BUILD_TIME=${BUILD_TIME}

# WORKDIR /app

# COPY --from=builder /app/dist/roha-mqtt-point /app/roha-mqtt-point

# ENTRYPOINT ["/app/roha-mqtt-point"]