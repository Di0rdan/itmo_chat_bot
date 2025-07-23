#!/usr/bin/env python3
"""
Скачивает PDF‑учебный план магистратуры ИТМО через Playwright.
Поддерживает выбор программы через аргумент командной строки.
"""

import asyncio
import argparse
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

# Константы
NAV_TIMEOUT = 60_000      # 60 с
SEL_TIMEOUT = 30_000      # 30 с
LINK_TEXT = "Скачать учебный план"


async def download_curriculum(program: str, output_file: str = None) -> None:
    """
    Скачивает учебный план для указанной программы
    
    Args:
        program: Код программы (например, 'ai', 'deep_learning', 'programming')
        output_file: Путь к выходному файлу (опционально)
    """
    # Формируем URL страницы программы
    page_url = f"https://abit.itmo.ru/program/master/{program}"
    
    # Формируем имя выходного файла, если не указано
    if output_file is None:
        output_file = Path(f"{program}.pdf").expanduser()
    else:
        output_file = Path(output_file).expanduser()
    
    print(f"🎓 Скачивание учебного плана программы: {program.upper()}")
    print(f"🌐 URL: {page_url}")
    print(f"📁 Выходной файл: {output_file}")
    print("-" * 60)
    
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("→ Открываем страницу…")
        try:
            await page.goto(page_url, wait_until="domcontentloaded",
                            timeout=NAV_TIMEOUT)
        except PWTimeout:
            raise RuntimeError(
                f"Не удалось загрузить страницу за {NAV_TIMEOUT/1000:.0f} с.\n"
                f"URL: {page_url}\n"
                "Проверьте подключение, правильность кода программы или увеличьте NAV_TIMEOUT."
            )

        print("→ Ищем кнопку «Скачать учебный план»…")
        try:
            button = await page.wait_for_selector(
                f"text='{LINK_TEXT}'", timeout=SEL_TIMEOUT
            )
        except PWTimeout:
            raise RuntimeError(
                f"Кнопка '{LINK_TEXT}' не появилась на странице.\n"
                f"URL: {page_url}\n"
                "Возможные причины:\n"
                "1. Изменилась вёрстка — проверьте ручным осмотром\n"
                "2. Программа не содержит учебный план\n"
                "3. Учебный план доступен только после авторизации\n"
                "4. Подберите другой селектор или используйте page.locator()"
            )

        print("→ Кликаем и перехватываем загрузку…")
        try:
            async with page.expect_download() as download_info:
                await button.click()
            download = await download_info.value
        except Exception as e:
            raise RuntimeError(
                f"Ошибка при клике на кнопку: {e}\n"
                "Возможно, кнопка не генерирует загрузку файла."
            )

        print(f"→ Сохраняем PDF ({download.suggested_filename})…")
        try:
            await download.save_as(output_file)
        except Exception as e:
            raise RuntimeError(f"Ошибка при сохранении файла: {e}")

        await browser.close()
        print(f"✔ Учебный план успешно сохранён: {output_file.resolve()}")
        
        # Проверяем размер файла
        file_size = output_file.stat().st_size
        print(f"📏 Размер файла: {file_size:,} байт")


def main():
    """Основная функция с поддержкой аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Скачивает PDF-учебный план магистерской программы ИТМО через Playwright',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python load_curriculum.py --program ai
  python load_curriculum.py --program ai --output ai.pdf
  python load_curriculum.py --program ai --output /path/to/programming_curriculum.pdf

Доступные программы:
  ai, ai_product
        """
    )
    
    parser.add_argument(
        "--program", 
        type=str, 
        required=True, 
        help="Код программы (например: ai, deep_learning, programming)"
    )
    
    parser.add_argument(
        "--output", 
        type=str, 
        help="Путь к выходному PDF файлу (опционально)"
    )
    
    args = parser.parse_args()
    
    # Проверяем, что код программы не пустой
    if not args.program.strip():
        print("❌ Ошибка: Код программы не может быть пустым")
        return 1
    
    try:
        # Запускаем асинхронную функцию
        asyncio.run(download_curriculum(args.program, args.output))
        return 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
