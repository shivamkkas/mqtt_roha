APP_NAME := roha-mqtt-point
DOCKER_REPO := infinityshiv/roha-mqtt-point
RELEASE_VERSION := v0.0.2
BUILD_TIME := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

ifneq (,$(wildcard ./.env))
  include .env
  export
endif

# -------- Run Locally --------
run:
	uv run main.py

# -------- Build Binary --------
build:
	uv run pyinstaller --onefile --name $(APP_NAME) main.py
	mkdir -p bin/linux
	mv dist/$(APP_NAME) bin/linux/$(APP_NAME)

window:
	uv run pyinstaller --onefile --name $(APP_NAME).exe main.py
	mkdir -p bin/windows
	mv dist/$(APP_NAME).exe bin/windows/

# -------- Docker Build --------
docker:
	docker build \
		--platform linux/amd64 \
		--build-arg APP_NAME=$(APP_NAME) \
		--build-arg RELEASE_VERSION=$(RELEASE_VERSION) \
		--build-arg BUILD_TIME=$(BUILD_TIME) \
		-t $(APP_NAME) .

# -------- Push to Docker Hub --------
hub:
	docker tag $(APP_NAME) $(DOCKER_REPO):$(RELEASE_VERSION)
	docker push $(DOCKER_REPO):$(RELEASE_VERSION)

# -------- Clean --------
clean:
	rm -rf build  __pycache__ *.spec bin