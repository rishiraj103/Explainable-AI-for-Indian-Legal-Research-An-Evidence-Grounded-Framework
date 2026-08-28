FROM pytorch/pytorch:2.5.1-cuda12.4-cudnn9-runtime

RUN pip install --no-cache-dir \
    accelerate==1.0.1 \
    pyarrow==18.1.0 \
    scikit-learn==1.5.2 \
    transformers==4.46.3

WORKDIR /workspace
ENV PYTHONPATH=/workspace/src
ENV HF_HOME=/workspace/artifacts/e2_hf_cache
ENV HF_HUB_DISABLE_TELEMETRY=1
