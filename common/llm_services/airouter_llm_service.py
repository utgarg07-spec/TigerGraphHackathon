import os
import logging
from common.llm_services import LLM_Model
from common.logs.log import req_id_cv
from common.logs.logwriter import LogWriter

logger = logging.getLogger(__name__)


class AIRouter(LLM_Model):
    def __init__(self, config):
        super().__init__(config)

        auth_cfg = config.get("authentication_configuration", {})
        for auth_detail, val in auth_cfg.items():
            if val:
                os.environ[auth_detail] = val

        api_key = os.environ.get("AIROUTER_API_KEY") or auth_cfg.get("AIROUTER_API_KEY")
        if not api_key:
            raise ValueError(
                "AIROUTER_API_KEY environment variable is missing or empty."
            )

        model_name = config.get("llm_model", "openai/gpt-oss-20b")
        base_url = config.get("base_url", "https://api.airouter.in/v1")
        model_kwargs = dict(config.get("model_kwargs", {}))
        
        temperature = model_kwargs.pop("temperature", 0)
        reasoning_effort = config.get("reasoning_effort", model_kwargs.pop("reasoning_effort", "low"))
        max_tokens = config.get("max_tokens", model_kwargs.pop("max_tokens", 2048))
        request_timeout = config.get("request_timeout", model_kwargs.pop("request_timeout", 180.0))

        from langchain_openai import ChatOpenAI
        import httpx

        timeout_sec = float(request_timeout)
        custom_http_client = httpx.Client(
            timeout=httpx.Timeout(timeout_sec, connect=60.0, read=timeout_sec, write=60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        custom_async_http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_sec, connect=60.0, read=timeout_sec, write=60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )

        kwargs = {
            "model_name": model_name,
            "openai_api_key": api_key,
            "base_url": base_url,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "timeout": timeout_sec,
            "request_timeout": timeout_sec,
            "reasoning_effort": reasoning_effort,
            "model_kwargs": model_kwargs,
            "max_retries": 0,
            "http_client": custom_http_client,
            "http_async_client": custom_async_http_client,
        }

        self.llm = ChatOpenAI(**kwargs)
        self.prompt_path = config.get("prompt_path", "./common/prompts/openai_gpt4/")
        self.provider_name = "airouter"
        
        # Controlled Experiment Constraint: NO fallbacks to FreeLLMAPI or Groq
        self.fallback_llms = []

        LogWriter.info(
            f"request_id={req_id_cv.get()} instantiated AIRouter model_name={model_name} via base_url={base_url}"
        )
