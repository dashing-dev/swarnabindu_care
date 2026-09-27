from datetime import date, datetime

from nepali_datetime import date as nepali_date


BS_MONTH_NAMES_EN = [
    "Baishakh",
    "Jestha",
    "Ashar",
    "Shrawan",
    "Bhadra",
    "Ashoj",
    "Kartik",
    "Mangsir",
    "Poush",
    "Magh",
    "Falgun",
    "Chaitra",
]

BS_MONTH_NAMES_NP = [
    "बैशाख",
    "जेठ",
    "असार",
    "साउन",
    "भदौ",
    "असोज",
    "कार्तिक",
    "मंसिर",
    "पुस",
    "माघ",
    "फागुन",
    "चैत",
]


def to_bs(value):
    """
    Convert a Python/Django Gregorian date or datetime
    into a nepali_datetime.date object.
    """

    if value is None:
        return None

    if isinstance(value, datetime):
        value = value.date()

    if not isinstance(value, date):
        raise TypeError(
            f"Expected date or datetime, got {type(value).__name__}"
        )

    return nepali_date.from_datetime_date(value)


def ad_to_bs(value):
    """
    Convert Gregorian date to:
        (BS year, BS month, BS day)
    """

    bs = to_bs(value)

    if bs is None:
        return None

    return bs.year, bs.month, bs.day


def bs_to_ad(year, month, day):
    """
    Convert Nepali BS date to Python datetime.date.
    """

    bs = nepali_date(year, month, day)

    return bs.to_datetime_date()


def format_bs_date(value, format_type="full"):
    """
    Format a Gregorian date as a Nepali BS date.

    full:
        19 Ashoj 2083 BS

    short:
        2083-06-19 BS

    np:
        १९ असोज २०८३
    """

    bs = to_bs(value)

    if bs is None:
        return "N/A"

    if format_type == "short":
        return f"{bs.year:04d}-{bs.month:02d}-{bs.day:02d} BS"

    if format_type == "np":
        return f"{bs.day} {BS_MONTH_NAMES_NP[bs.month - 1]} {bs.year}"

    return f"{bs.day} {BS_MONTH_NAMES_EN[bs.month - 1]} {bs.year} BS"


def parse_bs_string(value):
    """
    Convert a BS date string such as 2083-06-19
    into a Python datetime.date.

    Returns None when the value is not a valid BS date.
    This is intentional because search boxes may contain
    arbitrary text such as patient names.
    """

    if not value:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    value = str(value).strip()

    # Only attempt BS parsing for YYYY-MM-DD
    parts = value.split("-")

    if len(parts) != 3:
        return None

    try:
        year, month, day = map(int, parts)
    except (TypeError, ValueError):
        return None

    try:
        return bs_to_ad(year, month, day)
    except (ValueError, TypeError):
        return None

def calculate_exact_age(dob, ref_date):
    """
    Calculate exact age between two Gregorian dates.

    Returns:
        years
        months
        days
        total_months
        formatted
        age_group
    """

    if isinstance(dob, datetime):
        dob = dob.date()

    if isinstance(ref_date, datetime):
        ref_date = ref_date.date()

    if not isinstance(dob, date):
        raise TypeError("dob must be a date or datetime")

    if not isinstance(ref_date, date):
        raise TypeError("ref_date must be a date or datetime")

    if ref_date < dob:
        return {
            "years": 0,
            "months": 0,
            "days": 0,
            "total_months": 0,
            "formatted": "0 years 0 months 0 days",
            "age_group": "0–6 months",
        }

    years = ref_date.year - dob.year
    months = ref_date.month - dob.month
    days = ref_date.day - dob.day

    if days < 0:
        months -= 1

        if ref_date.month == 1:
            previous_month = 12
            previous_year = ref_date.year - 1
        else:
            previous_month = ref_date.month - 1
            previous_year = ref_date.year

        if previous_month in [1, 3, 5, 7, 8, 10, 12]:
            days_in_previous_month = 31
        elif previous_month == 2:
            if (
                previous_year % 400 == 0
                or (
                    previous_year % 4 == 0
                    and previous_year % 100 != 0
                )
            ):
                days_in_previous_month = 29
            else:
                days_in_previous_month = 28
        else:
            days_in_previous_month = 30

        days += days_in_previous_month

    if months < 0:
        years -= 1
        months += 12

    total_months = years * 12 + months

    if total_months < 6:
        age_group = "0–6 months"
    elif total_months < 12:
        age_group = "6–12 months"
    elif years < 2:
        age_group = "1–2 years"
    elif years < 3:
        age_group = "2–3 years"
    elif years < 4:
        age_group = "3–4 years"
    elif years < 5:
        age_group = "4–5 years"
    else:
        age_group = "5+ years"

    if years == 0:
        formatted = f"{months} months {days} days"
    else:
        formatted = f"{years} years {months} months {days} days"

    return {
        "years": years,
        "months": months,
        "days": days,
        "total_months": total_months,
        "formatted": formatted,
        "age_group": age_group,
    }