FROM --platform=linux/amd64 rust:1-bookworm AS sim
WORKDIR /build
COPY sim ./sim
RUN cargo build --release --manifest-path sim/Cargo.toml \
    && strip sim/target/release/npb_sim

FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.12
COPY lambda/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt --target "${LAMBDA_TASK_ROOT}"
COPY scripts "${LAMBDA_TASK_ROOT}/scripts"
COPY lambda/handler.py "${LAMBDA_TASK_ROOT}/handler.py"
COPY --from=sim /build/sim/target/release/npb_sim "${LAMBDA_TASK_ROOT}/bin/npb_sim"
RUN chmod +x "${LAMBDA_TASK_ROOT}/bin/npb_sim"
CMD ["handler.handler"]
