import requests
from unittest.mock import patch, MagicMock
from src.alerting import send_telegram_message


@patch("src.alerting.requests.post")
def test_send_message_success(mock_post):
    mock_post.return_value = MagicMock(status_code=200)
    result = send_telegram_message("Test")
    assert result is True
    mock_post.assert_called_once()


@patch("src.alerting.requests.post")
def test_send_message_failure(mock_post):
    mock_post.side_effect = requests.RequestException("Network error")
    result = send_telegram_message("Test")
    assert result is False


@patch("src.alerting.TELEGRAM_BOT_TOKEN", None)
def test_send_message_no_token():
    result = send_telegram_message("Test")
    assert result is False