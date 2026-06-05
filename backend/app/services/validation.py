"""Validation service: СЃСЂР°РІРЅРµРЅРёРµ SQL-СЂРµР·СѓР»СЊС‚Р°С‚РѕРІ.

РЎС‚СЂР°С‚РµРіРёРё РїСЂРѕРІРµСЂРєРё:
- exact_match: СЃСЂР°РІРЅРёС‚СЊ РєРѕР»РѕРЅРєРё, СЃС‚СЂРѕРєРё, Р·РЅР°С‡РµРЅРёСЏ
- not_empty: РїСЂРѕРІРµСЂРёС‚СЊ, С‡С‚Рѕ Р·Р°РїСЂРѕСЃ РІРµСЂРЅСѓР» СЃС‚СЂРѕРєРё
"""

from app.services.sandbox import execute_sql_for_validation


async def validate_submission(
    student_sql: str,
    expected_sql: str,
    strategy: str = "exact_match",
) -> dict:
    """РЎСЂР°РІРЅРёС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚ СЃС‚СѓРґРµРЅС‚Р° СЃ СЌС‚Р°Р»РѕРЅРѕРј РёР»Рё РїСЂРѕРІРµСЂРёС‚СЊ, С‡С‚Рѕ РЅРµ РїСѓСЃС‚Рѕ.

    Args:
        student_sql: SQL-Р·Р°РїСЂРѕСЃ СЃС‚СѓРґРµРЅС‚Р°.
        expected_sql: СЌС‚Р°Р»РѕРЅРЅС‹Р№ SQL (РґР»СЏ exact_match).
        strategy: СЃС‚СЂР°С‚РµРіРёСЏ РїСЂРѕРІРµСЂРєРё ("exact_match" РёР»Рё "not_empty").

    Returns:
        {"is_correct": bool, "match_type": str, "differences": list[str]}
    """
    if strategy == "not_empty":
        return await _validate_not_empty(student_sql)
    if strategy == "sql_result":
        return await _validate_exact_match(student_sql, expected_sql)
    return await _validate_exact_match(student_sql, expected_sql)


async def _validate_not_empty(student_sql: str) -> dict:
    """РџСЂРѕРІРµСЂРёС‚СЊ, С‡С‚Рѕ Р·Р°РїСЂРѕСЃ РІРµСЂРЅСѓР» С…РѕС‚СЏ Р±С‹ РѕРґРЅСѓ СЃС‚СЂРѕРєСѓ."""
    student_result = await execute_sql_for_validation(student_sql)

    if student_result["row_count"] > 0:
        return {
            "is_correct": True,
            "match_type": "not_empty",
            "differences": [],
        }

    return {
        "is_correct": False,
        "match_type": "empty",
        "differences": ["Р—Р°РїСЂРѕСЃ РЅРµ РІРµСЂРЅСѓР» РЅРё РѕРґРЅРѕР№ СЃС‚СЂРѕРєРё. РџСЂРѕРІРµСЂСЊ РёРјСЏ С‚Р°Р±Р»РёС†С‹."],
    }


async def _validate_exact_match(
    student_sql: str,
    expected_sql: str,
) -> dict:
    """РЎСЂР°РІРЅРёС‚СЊ СЂРµР·СѓР»СЊС‚Р°С‚ СЃС‚СѓРґРµРЅС‚Р° СЃ СЌС‚Р°Р»РѕРЅРѕРј.

    Р’С‹РїРѕР»РЅСЏРµС‚ РѕР±Р° Р·Р°РїСЂРѕСЃР° РІ training_db Рё СЃСЂР°РІРЅРёРІР°РµС‚:
    - РёРјРµРЅР° Рё РїРѕСЂСЏРґРѕРє РєРѕР»РѕРЅРѕРє
    - РєРѕР»РёС‡РµСЃС‚РІРѕ СЃС‚СЂРѕРє
    - Р·РЅР°С‡РµРЅРёСЏ РІ РєР°Р¶РґРѕР№ СЏС‡РµР№РєРµ

    Returns:
        {"is_correct": bool, "match_type": str, "differences": list[str]}
    """
    student_result = await execute_sql_for_validation(student_sql)
    expected_result = await execute_sql_for_validation(expected_sql)

    differences: list[str] = []

    # 1. РЎСЂР°РІРЅРµРЅРёРµ РєРѕР»РѕРЅРѕРє
    s_cols = student_result["columns"]
    e_cols = expected_result["columns"]

    if s_cols != e_cols:
        # Р§РµР»РѕРІРµС‡РµСЃРєРѕРµ РѕР±СЉСЏСЃРЅРµРЅРёРµ РґР»СЏ SELECT *
        if len(s_cols) > len(e_cols):
            extra = set(s_cols) - set(e_cols)
            diff_text = ", ".join(sorted(extra))
            if "*" in student_sql.split("FROM")[0]:
                differences.append(
                    f"Р—Р°РїСЂРѕСЃ РЅР°С€С‘Р» РїСЂР°РІРёР»СЊРЅС‹Рµ СЃС‚СЂРѕРєРё, РЅРѕ SELECT * РІС‹РІРѕРґРёС‚ РІСЃРµ РєРѕР»РѕРЅРєРё "
                    f"С‚Р°Р±Р»РёС†С‹. Р’ Р·Р°РґР°РЅРёРё РЅСѓР¶РЅРѕ РІС‹РІРµСЃС‚Рё С‚РѕР»СЊРєРѕ РѕРїСЂРµРґРµР»С‘РЅРЅС‹Рµ РєРѕР»РѕРЅРєРё: "
                    f"{', '.join(e_cols)}."
                )
            else:
                differences.append(
                    f"Р—Р°РїСЂРѕСЃ РІРµСЂРЅСѓР» Р»РёС€РЅРёРµ РєРѕР»РѕРЅРєРё: {diff_text}. "
                    f"РќСѓР¶РЅС‹Рµ РєРѕР»РѕРЅРєРё: {', '.join(e_cols)}."
                )
        else:
            missing = set(e_cols) - set(s_cols)
            diff_text = ", ".join(sorted(missing))
            differences.append(
                f"Р’ Р·Р°РїСЂРѕСЃРµ РЅРµ С…РІР°С‚Р°РµС‚ РєРѕР»РѕРЅРѕРє: {diff_text}. "
                f"РќСѓР¶РЅС‹Рµ РєРѕР»РѕРЅРєРё: {', '.join(e_cols)}."
            )
        return {
            "is_correct": False,
            "match_type": "different",
            "differences": differences if differences else ["Р РµР·СѓР»СЊС‚Р°С‚С‹ РЅРµ СЃРѕРІРїР°РґР°СЋС‚"],
        }

    # 2. РЎСЂР°РІРЅРµРЅРёРµ РєРѕР»РёС‡РµСЃС‚РІР° СЃС‚СЂРѕРє
    s_count = student_result["row_count"]
    e_count = expected_result["row_count"]

    if s_count != e_count:
        differences.append(
            f"РћР¶РёРґР°Р»РѕСЃСЊ {e_count} СЃС‚СЂРѕРє, РїРѕР»СѓС‡РµРЅРѕ {s_count}. "
            f"РџСЂРѕРІРµСЂСЊ СѓСЃР»РѕРІРёРµ WHERE."
        )

    # 3. РЎСЂР°РІРЅРµРЅРёРµ Р·РЅР°С‡РµРЅРёР№ (С‚РѕР»СЊРєРѕ РµСЃР»Рё РєРѕР»РѕРЅРєРё СЃРѕРІРїР°Р»Рё)
    s_rows = student_result["rows"]
    e_rows = expected_result["rows"]

    max_rows = min(len(s_rows), len(e_rows))
    for i in range(max_rows):
        s_row = s_rows[i]
        e_row = e_rows[i]
        if s_row != e_row:
            for j in range(min(len(s_row), len(e_row))):
                s_val = s_row[j]
                e_val = e_row[j]
                if s_val != e_val:
                    col_name = e_cols[j] if j < len(e_cols) else f"col{j}"
                    differences.append(
                        f"РЎС‚СЂРѕРєР° {i + 1}, РєРѕР»РѕРЅРєР° '{col_name}': "
                        f"РѕР¶РёРґР°Р»РѕСЃСЊ {e_val!r}, РїРѕР»СѓС‡РµРЅРѕ {s_val!r}"
                    )

    if not differences:
        return {
            "is_correct": True,
            "match_type": "exact",
            "differences": [],
        }

    return {
        "is_correct": False,
        "match_type": "different",
        "differences": differences,
    }
