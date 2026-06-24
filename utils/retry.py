"""通用重试工具。

为什么需要：外部 API（Open-Meteo 天气、ip-api 定位）偶尔会超时或瞬时网络抖动，
直接失败会让 Agent 拿不到关键信息（如天气）从而给出错误建议。
加一层轻量重试 + 指数退避，可覆盖大部分瞬时故障，且不引入 tenacity 等额外依赖。
"""
import time
from functools import wraps
from typing import Callable, Iterable, Type

from utils.logger_handler import logger


def with_retry(
    retries: int = 2,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
):
    """同步函数重试装饰器。

    Args:
        retries: 额外重试次数（不含首次调用），总调用次数 = retries + 1
        delay: 首次重试前等待秒数
        backoff: 每次重试等待时间的倍数（指数退避）
        exceptions: 触发重试的异常类型

    只对「瞬时性」异常重试；被调函数返回正常值或抛出非匹配异常时不重试。
    """
    exc_tuple = tuple(exceptions)

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exc = None
            for attempt in range(retries + 1):
                try:
                    return func(*args, **kwargs)
                except exc_tuple as e:
                    last_exc = e
                    if attempt >= retries:
                        logger.warning(
                            f"[with_retry]{func.__name__} 第{attempt + 1}次调用失败且已达重试上限：{e}"
                        )
                        raise
                    logger.info(
                        f"[with_retry]{func.__name__} 第{attempt + 1}次调用失败（{e}），"
                        f"{current_delay:.1f}s 后重试（剩余 {retries - attempt} 次）"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            # 理论上不会走到这里
            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator
