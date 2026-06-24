"""天气服务：通过 Open-Meteo 免费 API 获取真实天气数据，无需 API Key。

从 agent_tools.py 抽出来的原因：
- @tool 装饰器包装的函数难以直接单测（会触发整个 agent 模块加载）；
- 把纯 HTTP 调用逻辑独立成 fetch_weather(city)，便于 mock requests 做单测，
  也让 agent_tools 的 get_weather 只负责「工具声明 + 委托」。

数据流：城市名 → geocoding 拿经纬度 → forecast 拿实时天气。

注意：Open-Meteo 的 current 接口支持 precipitation（最近1小时降水量 mm），
但不支持 precipitation_probability（那是 hourly 字段）。
原实现误用 precipitation_probability 实际会拿到「未知」，这里改用 precipitation 更准确。
"""
import requests

from utils.logger_handler import logger

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = 5  # 秒，避免外部 API 卡死阻塞 Agent


def fetch_weather(city: str) -> str:
    """获取指定城市的实时天气，返回纯字符串。

    失败时返回用户可读的提示字符串（不抛异常），保证 Agent 调用安全。
    """
    try:
        # 步骤1：城市名 → 经纬度（geocoding）
        geo_resp = requests.get(
            GEOCODING_URL,
            params={"name": city, "count": 1, "language": "zh"},
            timeout=TIMEOUT,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()

        if not geo_data.get("results"):
            return f"未找到城市：{city}，请确认城市名称"

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        # 步骤2：经纬度 → 实时天气
        weather_resp = requests.get(
            FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "timezone": "auto",
            },
            timeout=TIMEOUT,
        )
        weather_resp.raise_for_status()
        current = weather_resp.json().get("current", {})

        temp = current.get("temperature_2m", "未知")
        humidity = current.get("relative_humidity_2m", "未知")
        precip = current.get("precipitation", "未知")
        wind = current.get("wind_speed_10m", "未知")

        return (f"城市{city}实时天气：气温{temp}°C，空气湿度{humidity}%，"
                f"当前降水量{precip}mm，风速{wind}km/h")
    except requests.exceptions.Timeout:
        logger.warning(f"[fetch_weather]查询城市{city}天气超时")
        return f"查询{city}天气超时，请稍后重试"
    except requests.exceptions.RequestException as e:
        logger.error(f"[fetch_weather]查询城市{city}天气失败：{e}")
        return f"查询{city}天气失败：{str(e)}"
    except Exception as e:
        logger.error(f"[fetch_weather]未知错误：{e}", exc_info=True)
        return f"获取{city}天气时发生未知错误"
