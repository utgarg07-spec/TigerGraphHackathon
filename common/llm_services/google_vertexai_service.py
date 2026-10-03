import logging
from common.llm_services import LLM_Model
from common.logs.log import req_id_cv
from common.logs.logwriter import LogWriter

logger = logging.getLogger(__name__)


class GoogleVertexAI(LLM_Model):
    def __init__(self, config):
        super().__init__(config)
        from langchain_google_vertexai import VertexAI

        model_name = config["llm_model"]
        self.llm = VertexAI(
            model=model_name, max_output_tokens=1000, **config["model_kwargs"]
        )

        self.prompt_path = config["prompt_path"]
        LogWriter.info(
            f"request_id={req_id_cv.get()} instantiated GoogleVertexAI model_name={model_name}"
        )

