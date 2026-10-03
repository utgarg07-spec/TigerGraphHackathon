import os
import logging
from common.llm_services import LLM_Model
from common.logs.log import req_id_cv
from common.logs.logwriter import LogWriter

logger = logging.getLogger(__name__)


class Groq(LLM_Model):
    def __init__(self, config):
        super().__init__(config)
        for auth_detail in config.get("authentication_configuration", {}).keys():
            os.environ[auth_detail] = config["authentication_configuration"][
                auth_detail
            ]
        from langchain_groq import ChatGroq

        model_name = config["llm_model"]
        reasoning_effort = config.get("reasoning_effort", "low")
        model_kwargs = config.get("model_kwargs", {})
        temperature = model_kwargs.get("temperature", 0)
        max_tokens = config.get("max_tokens", model_kwargs.get("max_tokens", 512))

        groq_api_key = config.get("authentication_configuration", {}).get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        self.llm = ChatGroq(
            temperature=temperature,
            model_name=model_name,
            reasoning_effort=reasoning_effort,
            max_tokens=max_tokens,
            max_retries=0,
            groq_api_key=groq_api_key,
        )
        self.prompt_path = config["prompt_path"]
        LogWriter.info(
            f"request_id={req_id_cv.get()} instantiated Groq model_name={model_name} reasoning_effort={reasoning_effort}"
        )

        # Build fallback LLM providers (Active chain: Groq -> OpenRouter)
        self.fallback_llms = []
        auth_cfg = config.get("authentication_configuration", {})

        # OpenRouter (Secondary fallback)
        openrouter_key = auth_cfg.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if openrouter_key:
            try:
                from langchain_openai import ChatOpenAI
                openrouter_llm = ChatOpenAI(
                    model_name="qwen/qwen-2.5-coder-32b-instruct",
                    openai_api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_body={"max_tokens": max_tokens},
                    max_retries=0,
                )
                self.fallback_llms.append(("openrouter", openrouter_llm))
                LogWriter.info("Configured OpenRouter Qwen-2.5-Coder-32B as secondary fallback LLM provider")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenRouter fallback: {e}")

        # FreeLLMAPI (Tertiary fallback)
        openai_key = auth_cfg.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if openai_key:
            try:
                from langchain_openai import ChatOpenAI
                freellm_llm = ChatOpenAI(
                    model_name="openai/auto",
                    openai_api_key=openai_key,
                    base_url="https://api.freellmapi.com/v1",
                    temperature=temperature,
                    max_tokens=max_tokens,
                    extra_body={"max_tokens": max_tokens},
                    max_retries=0,
                    timeout=15,
                )
                self.fallback_llms.append(("freellmapi", freellm_llm))
                LogWriter.info("Configured FreeLLMAPI as tertiary fallback LLM provider")
            except Exception as e:
                logger.warning(f"Failed to initialize FreeLLMAPI fallback: {e}")










