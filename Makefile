IMAGE = web-maxima-my-little-cucumber:1.1
CONTAINER = my-little-cucumber

image: Dockerfile
	docker build -t $(IMAGE) .

run:
	docker run -d -p 80:80 --name $(CONTAINER) $(IMAGE)

logs:
	-docker logs $(CONTAINER)

stop:
	-docker stop $(CONTAINER)

export:

clean: stop
	-docker rm $(CONTAINER)
	rm -rf export

clean-all: clean
	-docker rmi $(IMAGE)

.PHONY: image run logs stop export clean clean-all
