import unittest
from unittest.mock import Mock, patch

from agent.services.weather_service import fetch_weather


class WeatherServiceTest(unittest.TestCase):
    @patch("agent.services.weather_service.requests.get")
    def test_fetch_weather_uses_open_meteo_geocoding_and_forecast(self, mock_get):
        geo_response = Mock()
        geo_response.json.return_value = {
            "results": [{"latitude": 22.54, "longitude": 114.05}]
        }
        geo_response.raise_for_status.return_value = None

        weather_response = Mock()
        weather_response.json.return_value = {
            "current": {
                "temperature_2m": 26,
                "relative_humidity_2m": 72,
                "precipitation": 0.2,
                "wind_speed_10m": 9,
            }
        }
        weather_response.raise_for_status.return_value = None
        mock_get.side_effect = [geo_response, weather_response]

        result = fetch_weather("深圳")

        self.assertIn("城市深圳实时天气", result)
        self.assertIn("气温26°C", result)
        self.assertIn("空气湿度72%", result)
        self.assertIn("当前降水量0.2mm", result)
        self.assertIn("风速9km/h", result)

    @patch("agent.services.weather_service.requests.get")
    def test_fetch_weather_reports_unknown_city(self, mock_get):
        geo_response = Mock()
        geo_response.json.return_value = {}
        geo_response.raise_for_status.return_value = None
        mock_get.return_value = geo_response

        self.assertEqual(fetch_weather("不存在城市"), "未找到城市：不存在城市，请确认城市名称")


if __name__ == "__main__":
    unittest.main()
