FROM gcr.io/prysmaticlabs/build-agent AS builder

WORKDIR /git

RUN git clone --branch evil-shapella \
    --recurse-submodules \
    --depth 1 \
    https://github.com/prysmaticlabs/prysm

WORKDIR /git/prysm
# Build binaries for minimal configuration.
RUN bazel build --config=minimal \
  //cmd/beacon-chain:beacon-chain \
  //cmd/validator:validator



FROM scratch

COPY --from=builder /git/prysm/bazel-bin/cmd/beacon-chain/beacon-chain_/beacon-chain /usr/local/bin/
COPY --from=builder /git/prysm/bazel-bin/cmd/validator/validator_/validator /usr/local/bin/

#
##FROM scratch
##
#COPY --from=builder /build/beacon-chain /usr/local/bin/
#COPY --from=builder /build/validator /usr/local/bin/
#COPY --from=builder /git/src/github.com/prysmaticlabs/prysm_instrumented/symbols/* /opt/antithesis/symbols/
#COPY --from=builder /prysm.version /prysm.version
#COPY --from=builder /git/src/github.com/prysmaticlabs/* /git/src/github.com/prysmaticlabs/