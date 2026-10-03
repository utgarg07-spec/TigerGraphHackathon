import logging
from common.llm_services import LLM_Model
from common.logs.log import req_id_cv
from common.logs.logwriter import LogWriter

logger = logging.getLogger(__name__)


class Ollama(LLM_Model):
    def __init__(self, config):
        super().__init__(config)
        from langchain_openai import ChatOpenAI

        model_name = config["llm_model"]
        base_url = config.get("base_url", "http://host.docker.internal:11434/v1")
        if not base_url.endswith("/v1") and not base_url.endswith("/v1/"):
            base_url = base_url.rstrip("/") + "/v1"

        temp = config.get("model_kwargs", {}).get("temperature", 0)
        self.llm = ChatOpenAI(
            base_url=base_url,
            api_key="ollama",
            model=model_name,
            temperature=temp,
        )
        self.prompt_path = config["prompt_path"]
        LogWriter.info(
            f"request_id={req_id_cv.get()} instantiated Ollama model_name={model_name} via {base_url}"
        )
