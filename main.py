import threading
import time
from checkers_and_funcs import check_login, check_unavailable_or_verification_error, login, save_cookies, check_slots
from driver_setup import create_driver
from logger_config import setup_logger

logger = setup_logger(__name__)


def update_cookies():
    try:
        logger.info("🔁 Обновляем cookies через Selenium...")
        driver = create_driver()
        logger.info("🚗 Драйвер создан")

        login(driver)

        if not check_unavailable_or_verification_error(driver):
            logger.info("Проверяем логин...")
            if check_login(driver):
                logger.info("🔐Логин выполнен")
            else:
                logger.warning("⚠️ Не удалось найти имя пользователя.")
                driver.quit()
                logger.info("🛑 Драйвер закрыт")
                return

        save_cookies(driver)
        logger.info("✅ Cookies успешно обновлены.")

        driver.quit()
        logger.info("🛑 Драйвер закрыт")
    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении cookies: {e}")


def refresh_cookies():
    while True:
        update_cookies()
        logger.info("🕓 Ждем 20 минут до следующего обновления cookies")
        time.sleep(20 * 60)


def run_check_slots():
    while True:
        try:
            check_slots()
        except Exception as e:
            logger.error(f"❌ Ошибка в check_slots: {e}")
        time.sleep(60)  # Пауза 1 минута



def main():
    logger.info("🚀 Первая инициализация: обновляем cookies через Selenium")
    update_cookies()  # 🔁 Сначала получаем cookies

    logger.info("🚀 Запускаем мониторинг слотов и обновление cookies")

    # Только после обновления запускаем потоки
    threading.Thread(target=refresh_cookies, daemon=True).start()
    threading.Thread(target=run_check_slots, daemon=True).start()

    # Оставляем главный поток живым
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
