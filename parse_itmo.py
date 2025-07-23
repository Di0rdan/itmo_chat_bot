#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import argparse
import requests
import os


def parse_itmo_program(html_file_path: str) -> Dict[str, Any]:
    """
    Парсит HTML страницу магистерской программы ИТМО и извлекает структурированную информацию
    """
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Структура данных для JSON
    program_data = {
        "university": "ИТМО",
        "program_type": "магистратура",
        "year": 2025
    }
    
    # Основная информация о программе
    program_data["basic_info"] = extract_basic_info(soup)
    
    # Менеджер программы
    program_data["program_manager"] = extract_program_manager(soup)
    
    # Социальные сети
    program_data["social_networks"] = extract_social_networks(soup)
    
    # Направления подготовки
    program_data["study_directions"] = extract_study_directions(soup)
    
    # Описание программы
    program_data["program_description"] = extract_program_description(soup)
    
    # Партнеры
    program_data["partners"] = extract_partners(soup)
    
    # Команда программы
    program_data["team"] = extract_team_info(soup)
    
    # Карьерные возможности
    program_data["career"] = extract_career_info(soup)
    
    # Компании-работодатели
    program_data["employers"] = extract_employers(soup)
    
    # Отзывы выпускников
    program_data["alumni_reviews"] = extract_alumni_reviews(soup)
    
    # Достижения студентов
    program_data["achievements"] = extract_achievements(soup)
    
    # Поступление
    program_data["admission"] = extract_admission_info(soup)
    
    # Стипендии
    program_data["scholarships"] = extract_scholarships(soup)
    
    # Международные возможности
    program_data["international_opportunities"] = extract_international_opportunities(soup)
    
    # FAQ
    program_data["faq"] = extract_faq(soup)
    
    # Похожие программы
    program_data["similar_programs"] = extract_similar_programs(soup)
    
    return program_data

def extract_basic_info(soup: BeautifulSoup) -> Dict[str, Any]:
    """Извлекает основную информацию о программе"""
    basic_info = {}
    
    # Название программы
    title_elem = soup.find('h1', class_='Information_information__header__fab3I')
    if title_elem:
        basic_info["title"] = title_elem.get_text(strip=True)
    
    # Институт
    institute_elem = soup.find('div', class_='Information_information__link__cfN2l')
    if institute_elem:
        basic_info["institute"] = institute_elem.get_text(strip=True)
    
    # Параметры программы из карточек
    cards = soup.find_all('div', class_='Information_card__rshys')
    for card in cards:
        header = card.find('div', class_='Information_card__header__6PpVf')
        text = card.find('div', class_='Information_card__text__txwcx')
        
        if header and text:
            header_text = header.get_text(strip=True).lower()
            value = text.get_text(strip=True)
            
            if 'форма обучения' in header_text:
                basic_info["study_form"] = value
            elif 'длительность' in header_text:
                basic_info["duration"] = value
            elif 'язык обучения' in header_text:
                basic_info["language"] = value
            elif 'стоимость' in header_text:
                basic_info["cost_per_year"] = value
            elif 'общежитие' in header_text:
                basic_info["dormitory"] = value == "да"
            elif 'военный учебный центр' in header_text:
                basic_info["military_center"] = value == "да"
            elif 'гос. аккредитация' in header_text:
                basic_info["state_accreditation"] = value == "да"
            elif 'дополнительные возможности' in header_text:
                basic_info["additional_opportunities"] = value
    
    return basic_info

def extract_program_manager(soup: BeautifulSoup) -> Dict[str, str]:
    """Извлекает информацию о менеджере программы"""
    manager_info = {}
    
    manager_section = soup.find('div', class_='Information_manager__XZOI3')
    if manager_section:
        # Имя
        name_elem = manager_section.find('div', class_='Information_manager__name__ecPmn')
        if name_elem:
            name_text = name_elem.get_text(strip=True)
            # Убираем первую часть, которая может быть alt текстом изображения
            name_parts = name_text.split('\n')
            manager_info["name"] = name_parts[-1] if name_parts else name_text
        
        # Контакты
        contacts = manager_section.find_all('div', class_='Information_manager__contact__1fPAH')
        for contact in contacts:
            link = contact.find('a')
            if link:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                if href.startswith('mailto:'):
                    manager_info["email"] = text
                elif href.startswith('tel:'):
                    manager_info["phone"] = text
        
        # Фото
        photo_elem = manager_section.find('img')
        if photo_elem:
            manager_info["photo_url"] = photo_elem.get('src', '')
    
    return manager_info

def extract_social_networks(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает ссылки на социальные сети программы"""
    social_networks = []
    
    social_section = soup.find('div', class_='Information_socials__JpNII')
    if social_section:
        links = social_section.find_all('a', class_='Information_socials__link___eN3E')
        for link in links:
            social_networks.append({
                "name": link.get_text(strip=True),
                "url": link.get('href', '')
            })
    
    return social_networks

def extract_study_directions(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Извлекает направления подготовки"""
    directions = []
    
    direction_items = soup.find_all('div', class_='Directions_table__item__206L0')
    for item in direction_items:
        direction = {}
        
        # Код и название направления
        header = item.find('div', class_='Directions_table__header__qV8_J')
        if header:
            code_elem = header.find('p')
            name_elem = header.find('h5')
            if code_elem:
                direction["code"] = code_elem.get_text(strip=True)
            if name_elem:
                direction["name"] = name_elem.get_text(strip=True)
        
        # Места
        places_info = item.find('div', class_='Directions_table__info__HQR4Y')
        if places_info:
            places = places_info.find_all('div', class_='Directions_table__places__RWYBT')
            direction["places"] = {}
            
            for place in places:
                span = place.find('span')
                p = place.find('p')
                if span and p:
                    place_type = p.get_text(strip=True)
                    place_count = span.get_text(strip=True)
                    
                    if 'бюджетных' in place_type:
                        direction["places"]["budget"] = int(place_count)
                    elif 'целевая' in place_type:
                        direction["places"]["targeted"] = int(place_count)
                    elif 'контрактных' in place_type:
                        direction["places"]["contract"] = int(place_count)
        
        directions.append(direction)
    
    return directions

def extract_program_description(soup: BeautifulSoup) -> Dict[str, str]:
    """Извлекает описание программы"""
    description = {}
    
    about_section = soup.find('div', class_='AboutProgram_aboutProgram__textBlock__LpASa')
    if about_section:
        # Краткое описание
        lead_elem = about_section.find('span', class_='AboutProgram_aboutProgram__lead__SBgI1')
        if lead_elem:
            description["summary"] = lead_elem.get_text(strip=True)
        
        # Полное описание
        desc_elem = about_section.find('span', class_='AboutProgram_aboutProgram__description__Bf9LA')
        if desc_elem:
            description["full_description"] = desc_elem.get_text(strip=True)
    
    return description

def extract_partners(soup: BeautifulSoup) -> List[str]:
    """Извлекает список партнеров программы"""
    partners = []
    
    partner_cards = soup.find_all('div', class_='Partners_partners__card__STOzK')
    for card in partner_cards:
        img = card.find('img')
        if img:
            alt_text = img.get('alt', '')
            src = img.get('src', '')
            if src:
                # Извлекаем название партнера из пути к изображению
                filename = src.split('/')[-1].split('.')[0]
                partners.append(filename.replace('_', ' ').title())
    
    return partners

def extract_team_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Извлекает информацию о команде"""
    team_section = soup.find('div', class_='Team_team__bXtHu')
    if team_section:
        title_elem = team_section.find('h2')
        if title_elem:
            return {"section_title": title_elem.get_text(strip=True)}
    return {}

def extract_career_info(soup: BeautifulSoup) -> Dict[str, str]:
    """Извлекает информацию о карьерных возможностях"""
    career = {}
    
    career_section = soup.find('div', class_='Career_career__Fc883')
    if career_section:
        h5_elem = career_section.find('h5')
        if h5_elem:
            career["description"] = h5_elem.get_text(strip=True)
    
    return career

def extract_employers(soup: BeautifulSoup) -> List[str]:
    """Извлекает список компаний-работодателей"""
    employers = []
    
    job_cards = soup.find_all('div', class_='Job_job__card__lGEpQ')
    for card in job_cards:
        img = card.find('img')
        if img:
            src = img.get('src', '')
            if src:
                filename = src.split('/')[-1].split('.')[0]
                # Очищаем и форматируем название
                company_name = filename.replace('_', ' ').replace('1', '').replace('2', '').title()
                employers.append(company_name)
    
    return employers

def extract_alumni_reviews(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает отзывы выпускников"""
    reviews = []
    
    review_items = soup.find_all('li', class_='Slider_slider__item__DCIiq')
    for item in review_items:
        review = {}
        
        # Текст отзыва
        text_elem = item.find('div', class_='Slider_slider__textForDesktop__ar2Q4')
        if text_elem:
            review["text"] = text_elem.get_text(strip=True)
        
        # Информация о выпускнике
        name_elem = item.find('p', class_='Slider_slider__name__K8ZO_')
        year_elem = item.find('span', class_='Slider_slider__position__jv528')
        
        if name_elem:
            review["name"] = name_elem.get_text(strip=True)
        if year_elem:
            review["graduation_year"] = year_elem.get_text(strip=True)
        
        if review:
            reviews.append(review)
    
    return reviews

def extract_achievements(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает достижения студентов"""
    achievements = []
    
    achievement_cards = soup.find_all('div', class_='Achievements_achievements__card__yolZ5')
    for card in achievement_cards:
        achievement = {}
        
        # Заголовок
        h5_elem = card.find('h5')
        if h5_elem:
            achievement["title"] = h5_elem.get_text(strip=True)
        
        # Ссылка на подробности
        link_elem = card.find('a')
        if link_elem:
            achievement["url"] = link_elem.get('href', '')
        
        # Изображение
        img_elem = card.find('img')
        if img_elem:
            achievement["image_url"] = img_elem.get('src', '')
        
        achievements.append(achievement)
    
    return achievements

def extract_admission_info(soup: BeautifulSoup) -> Dict[str, List[Dict[str, str]]]:
    """Извлекает информацию о поступлении"""
    admission = {"ways_to_apply": []}
    
    accordion_items = soup.find_all('div', class_='Accordion_accordion__item__A6W5t')
    for item in accordion_items:
        way = {}
        
        # Название способа поступления
        title_elem = item.find('h5')
        if title_elem:
            way["name"] = title_elem.get_text(strip=True)
        
        # Описание
        info_elem = item.find('div', class_='Accordion_accordion__info__wkCQC')
        if info_elem:
            # Получаем только текст, исключая ссылки
            desc_div = info_elem.find('div')
            if desc_div:
                way["description"] = desc_div.get_text(strip=True)
            
            # Ссылка на подробности
            link_elem = info_elem.find('a')
            if link_elem:
                way["details_url"] = link_elem.get('href', '')
        
        if way.get("name"):
            admission["ways_to_apply"].append(way)
    
    return admission

def extract_scholarships(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает информацию о стипендиях"""
    scholarships = []
    
    scholarship_items = soup.find_all('a', class_='Scholarship_item__cowlU')
    for item in scholarship_items:
        scholarship = {}
        
        # Название стипендии
        h5_elem = item.find('h5')
        if h5_elem:
            scholarship["name"] = h5_elem.get_text(strip=True)
        
        # Сумма
        h4_elem = item.find('h4')
        if h4_elem:
            scholarship["amount"] = h4_elem.get_text(strip=True)
        
        # Ссылка
        scholarship["url"] = item.get('href', '')
        
        scholarships.append(scholarship)
    
    return scholarships

def extract_international_opportunities(soup: BeautifulSoup) -> Dict[str, Any]:
    """Извлекает информацию о международных возможностях"""
    opportunities = {}
    
    opp_section = soup.find('div', class_='Opportunities_opportunities__P3Pj8')
    if opp_section:
        # Основное описание
        text_elem = opp_section.find('p', class_='Opportunities_opportunities__text__axjuV')
        if text_elem:
            opportunities["description"] = text_elem.get_text(strip=True)
        
        # Конкретные возможности из аккордеона
        opportunities["programs"] = []
        accordion_items = opp_section.find_all('div', class_='Accordion_accordion__item__A6W5t')
        
        for item in accordion_items:
            program = {}
            
            title_elem = item.find('h5')
            if title_elem:
                program["name"] = title_elem.get_text(strip=True)
            
            desc_elem = item.find('div', class_='Accordion_accordion__info__wkCQC')
            if desc_elem:
                desc_div = desc_elem.find('div')
                if desc_div:
                    program["description"] = desc_div.get_text(strip=True)
            
            if program.get("name"):
                opportunities["programs"].append(program)
    
    return opportunities

def extract_faq(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает часто задаваемые вопросы"""
    faq_list = []
    
    # Ищем FAQ секцию
    faq_section = soup.find('h2', class_='Faq_title__aGKyL')
    if faq_section:
        parent = faq_section.find_parent()
        if parent:
            accordion_items = parent.find_all('div', class_='Accordion_accordion__item__A6W5t')
            
            for item in accordion_items:
                faq_item = {}
                
                # Вопрос
                question_elem = item.find('h5')
                if question_elem:
                    faq_item["question"] = question_elem.get_text(strip=True)
                
                # Ответ
                answer_elem = item.find('div', class_='Accordion_accordion__info__wkCQC')
                if answer_elem:
                    answer_div = answer_elem.find('div')
                    if answer_div:
                        faq_item["answer"] = answer_div.get_text(strip=True)
                
                if faq_item.get("question"):
                    faq_list.append(faq_item)
    
    return faq_list

def extract_similar_programs(soup: BeautifulSoup) -> List[Dict[str, str]]:
    """Извлекает похожие программы"""
    similar_programs = []
    
    program_items = soup.find_all('a', class_='SimilarPrograms_programs__item__u2gRI')
    for item in program_items:
        program = {}
        
        # Название программы
        h5_elem = item.find('h5')
        if h5_elem:
            program["name"] = h5_elem.get_text(strip=True)
        
        # Направление подготовки
        direction_elem = item.find('p')
        if direction_elem:
            program["direction"] = direction_elem.get_text(strip=True)
        
        # Ссылка
        program["url"] = item.get('href', '')
        
        similar_programs.append(program)
    
    return similar_programs


def load_html_repr(program: str, output_file: str) -> str:
    """Загружает HTML представление программы"""

    url = f'https://abit.itmo.ru/program/master/{program}'
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        # Удалим ненужные теги
        for tag in soup(['script', 'style', 'svg', 'noscript', 'iframe', 'meta', 'link']):
            tag.decompose()

        # Удалим скрытые элементы по стилю
        for tag in soup.find_all(style=True):
            if 'display:none' in tag['style'] or 'visibility:hidden' in tag['style']:
                tag.decompose()

        # Удалим скрытые классы (опционально)
        hidden_classes = ['sr-only', 'visually-hidden']
        for cls in hidden_classes:
            for tag in soup.select(f'.{cls}'):
                tag.decompose()

        # Сохраняем очищенный HTML
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(str(soup.prettify()))

        print(f"Очищенная HTML-страница сохранена в '{output_file}'")
    else:
        print(f"Ошибка загрузки: {response.status_code}")


def main(program: str):
    """Основная функция"""
    html_file = f"clean_page_{program}.html"
    output_file = f"itmo_{program}_program.json"

    load_html_repr(program, html_file)

    try:
        # Парсим HTML файл
        program_data = parse_itmo_program(html_file)
        
        # Сохраняем в JSON файл
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(program_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Данные успешно извлечены и сохранены в {output_file}")
        print(f"📊 Извлечено:")
        print(f"   - Основная информация о программе")
        print(f"   - {len(program_data.get('study_directions', []))} направления подготовки")
        print(f"   - {len(program_data.get('partners', []))} партнеров")
        print(f"   - {len(program_data.get('employers', []))} компаний-работодателей")
        print(f"   - {len(program_data.get('scholarships', []))} видов стипендий")
        print(f"   - {len(program_data.get('faq', []))} вопросов FAQ")
        print(f"   - {len(program_data.get('admission', {}).get('ways_to_apply', []))} способов поступления")

        os.remove(html_file)

    except FileNotFoundError:
        print(f"❌ Файл {html_file} не найден!")
    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Парсит HTML страницу магистерской программы ИТМО')
    parser.add_argument("--program", type=str, required=True, help="ai/ai_product")
    program = parser.parse_args().program
    main(program)
