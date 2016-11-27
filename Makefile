build: Dockerfile
	docker build -t web-maxima-my-little-cucumber:1.0 .

run:
	docker run -p 5000:5000 web-maxima-my-little-cucumber:1.0
