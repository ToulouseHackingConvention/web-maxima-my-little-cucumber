image:
	docker-compose build

build: image

run:
	docker-compose up -d
	sleep 5 && docker-compose exec web python3 initdb.py

logs:
	docker-compose logs

stop:
	docker-compose stop

export:

clean:
	docker-compose down
	rm -rf export

clean-all: clean
	docker-compose down --rmi all

.PHONY: image build run logs stop export clean clean-all
