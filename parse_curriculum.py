#!/usr/bin/env python3
"""
Extract all tables from a PDF into a single CSV using pdfplumber (no Java).

Examples
--------
# все страницы
python parse_curriculum_pdfplumber.py -i ai.pdf -o ai.csv

# только 1‑3 и 5‑я страницы
python parse_curriculum_pdfplumber.py -i ai.pdf -o ai.csv -p 1-3,5
"""

from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

import pandas as pd
import pdfplumber

# ────────────────────────── CLI ──────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extract tables from PDF into CSV via pdfplumber."
    )
    p.add_argument("-i", "--input", required=True, help="Input PDF file")
    p.add_argument("-o", "--output", required=True, help="Output CSV file")
    p.add_argument(
        "-p",
        "--pages",
        default="all",
        help='Pages to scan, e.g. "all" (default) or "1‑3,5"',
    )
    return p.parse_args()


# ──────────────────── helpers & extraction ────────────────────


def parse_page_spec(spec: str, num_pages: int) -> list[int]:
    """
    Convert a pages spec like "1-3,5" into zero‑based indices.
    """
    if spec.strip().lower() == "all":
        return list(range(num_pages))

    indices: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        m = re.match(r"(\d+)-(\d+)$", part)
        if m:
            start, end = map(int, m.groups())  # inclusive
            indices.extend(range(start - 1, end))
        else:
            idx = int(part) - 1
            indices.append(idx)

    # фильтрация выхода за диапазон
    return [i for i in indices if 0 <= i < num_pages]


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Простая очистка: убираем пустые столбцы, тримим пробелы.
    """
    df = df.dropna(how="all", axis=1)
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df = df.replace({"": None})
    return df


def extract_tables(pdf_path: Path, pages_spec: str) -> pd.DataFrame:
    """
    Возвращает один объединённый DataFrame с таблицами со всех указанных страниц.
    """
    rows: list[list[str | None]] = []
    header: list[str] | None = None

    with pdfplumber.open(pdf_path) as pdf:
        pages_to_process = parse_page_spec(pages_spec, len(pdf.pages))

        for page_idx in pages_to_process:
            page = pdf.pages[page_idx]

            # extract_tables() → list[list[list[str]]]
            for table in page.extract_tables():
                if not table:
                    continue

                # первая строка ‒ заголовок (предположительно)
                if header is None:
                    header = table[0]
                    data_rows = table[1:]
                else:
                    # если на этой странице заголовок повторяется, пропускаем его
                    data_rows = table[1:] if table[0] == header else table

                rows.extend(data_rows)

    if header is None:
        raise RuntimeError("Таблицы не найдены. Проверьте pages/area или PDF‑файл.")

    df = pd.DataFrame(rows, columns=header)
    return clean_dataframe(df)


# ──────────────────────────── main ────────────────────────────


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.input)
    csv_path = Path(args.output)

    if not pdf_path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    df = extract_tables(pdf_path, args.pages)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print(f"✅  Saved {len(df):,} rows → {csv_path}")


if __name__ == "__main__":
    main()
