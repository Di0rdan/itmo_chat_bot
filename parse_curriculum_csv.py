#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import json
import re
from typing import Dict, List, Any
from pathlib import Path

def parse_curriculum_csv(csv_file_path: str) -> Dict[str, Any]:
    """
    Парсит CSV файл учебного плана и извлекает структурированную информацию
    """
    # Загружаем CSV файл
    df = pd.read_csv(csv_file_path, header=None, encoding='utf-8')
    
    # Очищаем данные
    df = df.fillna('')
    
    # Извлекаем название программы из первой строки
    program_title = df.iloc[0, 0] if len(df) > 0 else "Учебный план"
    
    # Структура для JSON
    curriculum_data = {
        "program_info": {
            "title": program_title,
            "university": "ИТМО",
            "level": "магистратура",
            "total_credits": 0,
            "total_hours": 0
        },
        "blocks": []
    }
    
    current_block = None
    current_module = None
    
    # Проходим по всем строкам
    for index, row in df.iterrows():
        # Пропускаем пустые строки
        if row.isna().all() or (row == '').all():
            continue
            
        # Получаем значения из колонок
        col1 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col2 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col3 = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        col4 = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
        
        # Определяем тип строки и обрабатываем соответственно
        
        # Блок 1-4 (основные блоки) - ищем в колонке 2
        if col1 == "" and "Блок" in col2 and re.match(r"Блок \d+\.", col2):
            if current_block:
                curriculum_data["blocks"].append(current_block)
            
            block_match = re.match(r"Блок (\d+)\. (.+)", col2)
            if block_match:
                block_num = int(block_match.group(1))
                block_name = block_match.group(2)
                
                # Извлекаем зачетные единицы и часы
                try:
                    credits = float(col3) if col3 else 0
                    hours = int(col4) if col4 else 0
                except ValueError:
                    credits = 0
                    hours = 0
                
                current_block = {
                    "block_number": block_num,
                    "block_name": block_name,
                    "total_credits": credits,
                    "total_hours": hours,
                    "modules": []
                }
                current_module = None
                
                # Обновляем общие суммы
                curriculum_data["program_info"]["total_credits"] += credits
                curriculum_data["program_info"]["total_hours"] += hours
        
        # Модули внутри блоков - ищем в колонке 2 (без двоеточия)
        elif col1 == "" and col2 and not col2.startswith("Блок") and not re.match(r"^\d+$", col2) and col3 and col4:
            # Проверяем, что это не дисциплина (нет номера в col1)
            if current_block:
                # Извлекаем зачетные единицы и часы
                try:
                    credits = float(col3) if col3 else 0
                    hours = int(col4) if col4 else 0
                except ValueError:
                    credits = 0
                    hours = 0
                
                # Если это модуль (есть зачетные единицы и часы)
                if credits > 0 or hours > 0:
                    current_module = {
                        "module_name": col2,
                        "credits": credits,
                        "hours": hours,
                        "disciplines": []
                    }
                    current_block["modules"].append(current_module)
        
        # Дисциплины с номером семестра в колонке 1
        elif col1 and re.match(r"^\d+$", col1) and col2 and col3 and col4:
            try:
                semester_num = int(col1)
                credits = float(col3) if col3 else 0
                hours = int(col4) if col4 else 0
                
                discipline = {
                    "semester": semester_num,
                    "name": col2,
                    "credits": credits,
                    "hours": hours
                }
                
                if current_module:
                    current_module["disciplines"].append(discipline)
                
            except ValueError:
                pass
        
        # Дисциплины без номера (подмодули)
        elif col1 == "" and col2 and not col2.startswith("Блок") and not re.match(r"^\d+$", col2) and col3 and col4:
            try:
                credits = float(col3) if col3 else 0
                hours = int(col4) if col4 else 0
                
                # Если это дисциплина (есть зачетные единицы и часы)
                if credits > 0 or hours > 0:
                    discipline = {
                        "name": col2,
                        "credits": credits,
                        "hours": hours
                    }
                    
                    if current_module:
                        current_module["disciplines"].append(discipline)
                
            except ValueError:
                pass
    
    # Добавляем последний блок
    if current_block:
        curriculum_data["blocks"].append(current_block)
    
    # Извлекаем дополнительную информацию
    curriculum_data["summary"] = extract_summary_info(curriculum_data)
    
    return curriculum_data

def extract_summary_info(curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает сводную информацию из учебного плана
    """
    summary = {
        "total_disciplines": 0,
        "semesters_count": 4,  # Стандартно для магистратуры
        "blocks_count": len(curriculum_data["blocks"]),
        "modules_count": 0,
        "practical_work": {
            "total_credits": 0,
            "total_hours": 0
        },
        "theoretical_work": {
            "total_credits": 0,
            "total_hours": 0
        },
        "semester_distribution": {
            "semester_1": {"credits": 0, "hours": 0, "disciplines": 0},
            "semester_2": {"credits": 0, "hours": 0, "disciplines": 0},
            "semester_3": {"credits": 0, "hours": 0, "disciplines": 0},
            "semester_4": {"credits": 0, "hours": 0, "disciplines": 0}
        }
    }
    
    # Подсчитываем статистику
    for block in curriculum_data["blocks"]:
        summary["modules_count"] += len(block["modules"])
        
        for module in block["modules"]:
            summary["total_disciplines"] += len(module.get("disciplines", []))
            
            # Подсчитываем практическую и теоретическую работу
            if "практика" in module["module_name"].lower() or "практик" in module["module_name"].lower():
                summary["practical_work"]["total_credits"] += module["credits"]
                summary["practical_work"]["total_hours"] += module["hours"]
            else:
                summary["theoretical_work"]["total_credits"] += module["credits"]
                summary["theoretical_work"]["total_hours"] += module["hours"]
            
            # Распределение по семестрам
            for discipline in module.get("disciplines", []):
                if "semester" in discipline:
                    semester_key = f"semester_{discipline['semester']}"
                    if semester_key in summary["semester_distribution"]:
                        summary["semester_distribution"][semester_key]["credits"] += discipline["credits"]
                        summary["semester_distribution"][semester_key]["hours"] += discipline["hours"]
                        summary["semester_distribution"][semester_key]["disciplines"] += 1
    
    return summary

def clean_module_names(curriculum_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Очищает названия модулей от лишних символов
    """
    for block in curriculum_data["blocks"]:
        for module in block["modules"]:
            # Очищаем название модуля
            module["module_name"] = module["module_name"].strip()
            
            # Очищаем названия дисциплин
            for discipline in module.get("disciplines", []):
                discipline["name"] = discipline["name"].strip()
    
    return curriculum_data

def main():
    """
    Основная функция
    """
    csv_file = "ai.csv"
    output_file = "ai_curriculum_structured.json"
    
    try:
        print("📚 Парсинг учебного плана из CSV файла...")
        
        # Парсим CSV
        curriculum_data = parse_curriculum_csv(csv_file)
        
        # Очищаем данные
        curriculum_data = clean_module_names(curriculum_data)
        
        # Сохраняем в JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(curriculum_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Учебный план успешно структурирован и сохранен в {output_file}")
        
        # Выводим статистику
        print(f"\n📊 Статистика учебного плана:")
        print(f"   Программа: {curriculum_data['program_info']['title']}")
        print(f"   Всего зачетных единиц: {curriculum_data['program_info']['total_credits']}")
        print(f"   Всего часов: {curriculum_data['program_info']['total_hours']}")
        print(f"   Блоков: {curriculum_data['summary']['blocks_count']}")
        print(f"   Модулей: {curriculum_data['summary']['modules_count']}")
        print(f"   Дисциплин: {curriculum_data['summary']['total_disciplines']}")
        
        print(f"\n📋 Структура блоков:")
        for block in curriculum_data["blocks"]:
            print(f"   Блок {block['block_number']}: {block['block_name']}")
            print(f"     Зачетных единиц: {block['total_credits']}")
            print(f"     Часов: {block['total_hours']}")
            print(f"     Модулей: {len(block['modules'])}")
            
            for module in block["modules"]:
                print(f"       - {module['module_name']} ({module['credits']} з.е., {module['hours']} ч.)")
                print(f"         Дисциплин: {len(module['disciplines'])}")
        
        print(f"\n📅 Распределение по семестрам:")
        for semester, data in curriculum_data['summary']['semester_distribution'].items():
            if data['disciplines'] > 0:
                print(f"   {semester.replace('_', ' ').title()}: {data['credits']} з.е., {data['hours']} ч., {data['disciplines']} дисциплин")
        
    except FileNotFoundError:
        print(f"❌ Файл {csv_file} не найден!")
    except Exception as e:
        print(f"❌ Ошибка при обработке: {e}")

if __name__ == "__main__":
    main() 