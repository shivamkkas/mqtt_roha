APP_NAME = roha-mqtt-point
DOCKER_REPO = infinityshiv/roha-mqtt-point
RELEASE_VERSION := v0.0.1

ifneq (,$(wildcard ./.env))
  include .env
  export
endif

# -------- Run Locally --------
run:
	python3 main.py

# -------- Build Binary --------
build:
	pyinstaller --onefile --name $(APP_NAME) main.py
	mkdir -p bin/linux
	mv dist/$(APP_NAME) bin/linux/$(APP_NAME)

# -------- Windows Build --------
window:
	pyinstaller --onefile --name $(APP_NAME).exe main.py
	mkdir -p bin/window
	mv dist/$(APP_NAME).exe bin/window/

# -------- Docker Build --------
docker:
	docker build -t $(APP_NAME) \
		--platform linux/amd64 \
		--build-arg APP_NAME=$(APP_NAME) \
		--build-arg RELEASE_VERSION=$(RELEASE_VERSION) \
		--build-arg BUILD_TIME=$(shell date -u +%Y-%m-%dT%H:%M:%SZ) \
		.

# -------- Push to Harbor --------
hub:
	docker tag $(APP_NAME) $(DOCKER_REPO):$(RELEASE_VERSION)
	docker push $(DOCKER_REPO):$(RELEASE_VERSION)

# -------- Clean --------
clean:
	rm -rf build dist __pycache__ *.spec bin