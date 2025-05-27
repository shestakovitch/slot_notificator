import requests
from config import BOT_TOKEN, CHAT_ID
from logger_config import setup_logger

logger = setup_logger(__name__)


def _post_to_telegram(method, data=None, files=None):
    """
    Универсальная функция для отправки запросов в Telegram Bot API.
    """
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    try:
        res = requests.post(url, data=data, files=files, timeout=10)
        res.raise_for_status()
        logger.info("✅ Успешно отправлено в Telegram: %s", method)
    except requests.exceptions.HTTPError as http_err:
        logger.error("❌ HTTP ошибка при отправке в Telegram: %s | Ответ: %s", http_err, res.text)
        return None
    except requests.exceptions.RequestException as req_err:
        logger.error("❌ Ошибка соединения при отправке в Telegram: %s", req_err)
        return None
    except Exception as e:
        logger.error("❌ Непредвиденная ошибка при отправке в Telegram: %s", e)
        return None

    return res


def send_message(message):
    """
    Отправляет текстовое сообщение в Telegram.
    """
    return _post_to_telegram("sendMessage", data={
        "chat_id": CHAT_ID,
        "text": message
    })


def send_pic(pic_path):
    """
    Отправляет фото в Telegram.
    """
    with open(pic_path, "rb") as photo:
        return _post_to_telegram("sendPhoto", data={
            "chat_id": CHAT_ID
        }, files={
            "photo": photo
        })
