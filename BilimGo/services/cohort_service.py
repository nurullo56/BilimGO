from __future__ import annotations

import datetime
from typing import Optional


def calculate_course_cohort(
    course_created_at: Optional[str],
    enrollment_time: Optional[str] = None,
    students_in_month_count: int = 1,
    max_per_cohort: int = 20,
) -> str:
    """
    Patok (oqim) raqamini avtomatik hisoblash:
    - Har oy asosiy patok 1 ga oshadi: 1-oy = 1.x, 2-oy = 2.x, 3-oy = 3.x
    - Har bir oydagi 20 ta o'quvchi uchun alohida patok guruhi ochiladi:
        * 1 - 20 o'quvchi: .0 (masalan 1.0)
        * 21 - 40 o'quvchi: .1 (masalan 1.1)
        * 41 - 60 o'quvchi: .2 (masalan 1.2)
        * 61 - 80 o'quvchi: .3 (masalan 1.3)
    """
    now = datetime.datetime.now()
    ref_time = now
    if enrollment_time:
        try:
            ref_time = datetime.datetime.fromisoformat(enrollment_time.replace("Z", "+00:00"))
        except Exception:
            pass

    start_date = ref_time
    if course_created_at:
        try:
            start_date = datetime.datetime.fromisoformat(course_created_at.replace("Z", "+00:00"))
        except Exception:
            pass

    # Oy farqini hisoblash (kurs ochilgan oydan hisoblab)
    month_diff = (ref_time.year - start_date.year) * 12 + (ref_time.month - start_date.month)
    major_cohort = max(1, month_diff + 1)

    # Oydagi o'quvchilar sig'imi (20 kishilik limit)
    student_idx = max(1, students_in_month_count)
    sub_cohort = (student_idx - 1) // max_per_cohort

    return f"{major_cohort}.{sub_cohort}"


def format_course_title_with_cohort(course_title: str, cohort: Optional[str]) -> str:
    """
    Kurs nomi yoniga patok raqamini to'g'ridan-to'g'ri qo'shish ('Potok' so'zisiz).
    Masalan: 'ChinaSeller PRO' + '1.0' -> 'ChinaSeller PRO 1.0'
    """
    if not cohort:
        return course_title
    clean_title = course_title.strip()
    # Agar allaqachon raqam oxirida mavjud bo'lsa, qayta qo'shmaslik
    if clean_title.endswith(f" {cohort}"):
        return clean_title
    return f"{clean_title} {cohort}"
