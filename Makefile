.PHONY: clean

# build the ethereum-testnet-bootstrapper docker.
build-bootstrapper:
	docker build -t ethereum-testnet-bootstrapper -f Dockerfile .

# build all of the docker files we currently use
build-dockers:
	cd deps/dockers && ./build_dockers.sh

# init the testnet dirs and all files needed to later bootstrap the testnet.
init-testnet:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --init-testnet

# after an init this runs the bootstrapper and start up the testnet.
run-bootstrapper:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --bootstrap-mode

clean:
	docker run -it -v $(shell pwd)/:/source/ -v $(shell pwd)/data/:/data ethereum-testnet-bootstrapper --config $(config) --clear-last-run

