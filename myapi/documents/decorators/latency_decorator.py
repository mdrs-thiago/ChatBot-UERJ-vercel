import logging
import time

from documents.models import LatencyLLM

logger = logging.getLogger(__name__)


def collect_latency(provider_arg_name="provider"):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            latency = time.time() - start
            provider = None
            if args and hasattr(args[0], provider_arg_name):
                provider = getattr(args[0], provider_arg_name)
            elif provider_arg_name in kwargs:
                provider = kwargs[provider_arg_name]
            try:
                LatencyLLM.objects.create(provider=provider, latency=latency)
            except Exception as e:
                logger.warning(f"Erro ao salvar latência no banco: {e}")
            logger.info(f"[latency][{provider}] {latency:.3f}s")
            answer = {
                "metrics": {
                    "latency": latency,
                },
                "answer": result,
            }
            return answer

        return wrapper

    return decorator
