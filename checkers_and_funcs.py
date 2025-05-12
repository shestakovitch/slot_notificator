import time
import random
import json

import requests
from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains  # Импортируем для движения мыши
from config import BASE_URL, SERVICES_URL, LOGIN, PASSWORD, USER_NAME
from logger_config import setup_logger

logger = setup_logger(__name__)


def random_sleep(min_seconds=1, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))


def scroll_page(driver):
    """Функция для прокрутки страницы до конца"""
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    random_sleep()


def move_mouse(driver):
    """Функция для эмуляции движения мыши"""
    actions = ActionChains(driver)
    actions.move_to_element(driver.find_element(By.TAG_NAME, "body")).perform()
    random_sleep()


def human_typing(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.1, 0.3))


def login(driver):
    logger.info("Открываем сайт и выполняем логин")
    driver.get(url=BASE_URL)

    try:
        scroll_page(driver)
        move_mouse(driver)

        # Клик по полю email мышью
        email_element = driver.find_element(By.ID, value="login-email")
        ActionChains(driver).move_to_element(email_element).click().perform()
        human_typing(email_element, LOGIN)
        random_sleep(1, 2)

        # Клик по полю password мышью
        password_element = driver.find_element(By.ID, value="login-password")
        ActionChains(driver).move_to_element(password_element).click().perform()
        human_typing(password_element, PASSWORD)
        random_sleep(1, 2)

        # Клик по кнопке входа мышью
        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        ActionChains(driver).move_to_element(login_button).click().perform()
        time.sleep(5)

    except Exception as e:
        logger.error(f"Ошибка при логине: {e}")
        return False


def check_unavailable_or_verification_error(driver):
    """
        Проверяет заголовок страницы и URL на наличие признаков ошибки.
        При обнаружении логирует, завершает драйвер и возвращает True.
        """
    try:
        if "unavailable" in driver.title.lower():
            logger.error(f"Обнаружена ошибка: unavailable")
            driver.quit()
            return True
        if "error" in driver.current_url.lower():
            logger.error(f"Обнаружена ошибка: An error occurred while processing the request")
            driver.quit()
            return True
    except Exception as e:
        logger.error(f"Ошибка при проверке доступности страницы: {e}")
    return False


def check_login(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//figure[@class='main-nav__avatar']//figcaption[contains(text(), '{USER_NAME}')]"))
        )
        return True
    except NoSuchElementException:
        return False
    except TimeoutException:
        logger.warning("⏱️ Истекло время ожидания появления элемента логина.")
        return False


def save_cookies(driver, path="cookies.json"):
    """
    Сохраняет cookies текущей сессии в указанный файл.
    """
    try:
        cookies = driver.get_cookies()
        with open(path, "w") as f:
            json.dump(cookies, f)
        logger.info(f"🍪 Cookies успешно сохранены в файл: {path}")
    except Exception as e:
        logger.error(f"❌ Ошибка при сохранении cookies: {e}")


def load_cookies(path="cookies.json"):
    logger.info(f"📂 Загружаем cookies из {path}")
    try:
        with open(path, "r") as f:
            selenium_cookies = json.load(f)
        requests_cookies = {cookie['name']: cookie['value'] for cookie in selenium_cookies}
        logger.info(f"✅ Загружено {len(requests_cookies)} cookies для requests")
        return requests_cookies
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке cookies: {e}")
        return {}


def check_slots(path="cookies.json", url=SERVICES_URL):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/135.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://prenotami.esteri.it/",
        "Origin": "https://prenotami.esteri.it",
        "Connection": "keep-alive",
    }

    logger.info("🌐 Делаем запрос к %s", url)

    cookies = load_cookies()
    if not cookies:
        logger.error("🚫 Не удалось загрузить cookies, остановка проверки.")
        return

    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("❌ Ошибка запроса: %s", e)
        return

    try:
        data = response.json()
    except json.JSONDecodeError:
        logger.error("❌ Не удалось декодировать JSON. Ответ: %s", response.text[:500])
        return

    target_ids = {1151, 1258}
    excluded_links = {
        "https://vistoperitalia.esteri.it/home/en",
        "https://ambbelgrado.esteri.it/ambasciata_belgrado/sr/informazioni_e_servizi/visti/visto-per-studio/",
    }

    found_links = []

    for service in data:
        if service.get("IdServizioErogato") in target_ids:
            raw_links = service.get("LinkServizioErogato", [])
            # Очищаем от пробелов и фильтруем исключённые
            filtered_links = [
                link.strip() for link in raw_links if link.strip() not in excluded_links
            ]
            found_links.extend(filtered_links)

    if len(found_links) > 0:
        logger.info("✅ Есть слот! Найдены ссылки: %s", found_links)
    else:
        logger.info("🕵️ Слотов нет")

    return found_links
