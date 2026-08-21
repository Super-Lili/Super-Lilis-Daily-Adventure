import re
import sys
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from dateutil import parser as date_parser

_TZ_MAP = [
    ("pacific time", "America/Los_Angeles"),
    ("eastern time", "America/New_York"),
    ("central time", "America/Chicago"),
    ("mountain time", "America/Denver"),
    ("pacific", "America/Los_Angeles"),
    ("eastern", "America/New_York"),
    ("central", "America/Chicago"),
    ("mountain", "America/Denver"),
    ("pt", "America/Los_Angeles"),
    ("et", "America/New_York"),
    ("ct", "America/Chicago"),
    ("mt", "America/Denver"),
    ("pdt", "America/Los_Angeles"),
    ("pst", "America/Los_Angeles"),
    ("edt", "America/New_York"),
    ("est", "America/New_York"),
    ("cdt", "America/Chicago"),
    ("cst", "America/Chicago"),
    ("mdt", "America/Denver"),
    ("mst", "America/Denver"),
    ("gmt", "UTC"),
    ("utc", "UTC"),
    ("london", "Europe/London"),
]
_TZ_LABELS = {
    "America/Los_Angeles": "Pacific Time",
    "America/New_York": "Eastern Time",
    "America/Chicago": "Central Time",
    "America/Denver": "Mountain Time",
    "UTC": "UTC",
    "Europe/London": "London Time",
}
_TZ_PHRASES = sorted([p for p, _ in _TZ_MAP], key=len, reverse=True)

_TIME_RANGE_RE = re.compile(
    r'(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)\s*(?:–|—|-|to|until)\s*(\d{1,2}(?::\d{2})?\s*(?:AM|PM)?)',
    re.I,
)


def _tz_from_text(text: str):
    if not text:
        return None
    low = text.lower()
    for phrase, tz in _TZ_MAP:
        if re.search(r'\b' + re.escape(phrase) + r'\b', low):
            return tz
    return None


def _tz_label(tz_name: str) -> str:
    return _TZ_LABELS.get(tz_name, tz_name)


def _find_time_range(text: str):
    m = _TIME_RANGE_RE.search(text)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return '', ''


def _parse_time_only(text: str):
    if not text:
        return None
    m = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)?\b', text, re.I)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    ampm = (m.group(3) or '').upper()
    if ampm == 'PM' and hour != 12:
        hour += 12
    if ampm == 'AM' and hour == 12:
        hour = 0
    return time(hour=hour, minute=minute)


def _parse_dt_text(text: str, fallback_tz: str) -> datetime:
    tz_name = _tz_from_text(text) or fallback_tz
    cleaned = text
    for phrase in _TZ_PHRASES:
        cleaned = re.sub(r'\b' + re.escape(phrase) + r'\b', '', cleaned, flags=re.I)
    try:
        dt = date_parser.parse(cleaned, fuzzy=True)
    except Exception:
        dt = datetime.now(ZoneInfo(tz_name)).replace(tzinfo=None)
    if 'noon' in text.lower():
        dt = dt.replace(hour=12, minute=0, second=0, microsecond=0)
    elif 'end of day' in text.lower() or 'end of business' in text.lower():
        dt = dt.replace(hour=17, minute=0, second=0, microsecond=0)
    if dt.tzinfo is not None:
        dt = dt.astimezone(ZoneInfo('UTC')).replace(tzinfo=None)
    return dt.replace(tzinfo=ZoneInfo(tz_name))


def _combine(day, t, tz_name: str) -> datetime:
    return datetime.combine(day, t, tzinfo=ZoneInfo(tz_name))


def _next_business_day(day):
    nd = day + timedelta(days=1)
    while nd.weekday() >= 5:
        nd += timedelta(days=1)
    return nd


def _fmt_local(dt: datetime, tz_name: str) -> str:
    hour12 = dt.hour % 12 or 12
    ampm = 'AM' if dt.hour < 12 else 'PM'
    return f"{dt.strftime('%A, %B %d, %Y')}, {hour12}:{dt.minute:02d} {ampm} {_tz_label(tz_name)}"


def _fmt_time(t: time) -> str:
    if t is None:
        return 'not provided'
    hour12 = t.hour % 12 or 12
    ampm = 'AM' if t.hour < 12 else 'PM'
    return f"{hour12}:{t.minute:02d} {ampm}"


def _fmt_duration(td: timedelta) -> str:
    total_min = int(td.total_seconds() // 60)
    h, m = divmod(total_min, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def _extract_essay_title(text: str) -> str:
    m = re.search(r'essay\s+is\s+["“]([^"”]+)["”]', text, re.I)
    return m.group(1).strip() if m else ''


def _extract_publication(text: str) -> str:
    m = re.search(r'\bfor\s+([A-Z][A-Za-z0-9& ,]+?)(?:\.|Editor:|$)', text, re.I)
    return m.group(1).strip() if m else ''


def _extract_editor(text: str):
    name, email = '', ''
    m = re.search(r'Editor\s*:\s*([^()]+)', text, re.I)
    if m:
        name = re.sub(r'\s+', ' ', m.group(1).strip()).rstrip('.').strip()
    em = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    if em:
        email = em.group(0)
    return name, email


def process(text: str) -> str:
    """Convert a deadline through shift/sleep windows and return a ready-to-send brief."""
    if not text.strip():
        return "Please paste your deadline, shift, sleep, and as-of details."

    flat = re.sub(r'\s+', ' ', text.replace('\n', ' ')).strip()
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', flat) if s.strip()]

    def find(*keys: str) -> str:
        for s in sentences:
            if any(k.lower() in s.lower() for k in keys):
                return s
        return ''

    deadline_line = find('deadline')
    shift_line = find('shift')
    sleep_line = find('sleep')
    asof_line = find('right now', 'as of', 'as-of', 'current')
    essay_line = find('essay')
    editor_line = find('editor')

    essay_title = _extract_essay_title(essay_line)
    publication = _extract_publication(essay_line)
    editor_name, editor_email = _extract_editor(editor_line)

    user_tz = _tz_from_text(asof_line) or _tz_from_text(shift_line) or _tz_from_text(sleep_line) or 'UTC'
    editorial_tz = _tz_from_text(deadline_line) or user_tz

    deadline_utc = _parse_dt_text(deadline_line, editorial_tz).astimezone(ZoneInfo('UTC'))
    asof_utc = _parse_dt_text(asof_line, user_tz).astimezone(ZoneInfo('UTC'))
    deadline_local = deadline_utc.astimezone(ZoneInfo(user_tz))
    deadline_editorial = deadline_utc.astimezone(ZoneInfo(editorial_tz))
    base_date = deadline_local.date()

    shift_start_t = shift_end_t = None
    if shift_line:
        st, et = _find_time_range(shift_line)
        shift_start_t = _parse_time_only(st)
        shift_end_t = _parse_time_only(et)

    sleep_start_t = sleep_end_t = None
    if sleep_line:
        st, et = _find_time_range(sleep_line)
        sleep_start_t = _parse_time_only(st)
        sleep_end_t = _parse_time_only(et)

    inferred_sleep = False
    sleep_start_dt = sleep_end_dt = None

    if sleep_start_t is None and shift_end_t is not None:
        inferred_sleep = True
        shift_end_dt = _combine(base_date, shift_end_t, user_tz)
        if shift_start_t is not None and shift_end_t <= shift_start_t:
            shift_end_dt += timedelta(days=1)
        sleep_start_dt = shift_end_dt + timedelta(minutes=30)
        sleep_end_dt = sleep_start_dt + timedelta(hours=8)
    else:
        if sleep_start_t is not None and sleep_end_t is not None:
            sleep_start_dt = _combine(base_date, sleep_start_t, user_tz)
            sleep_end_dt = _combine(base_date, sleep_end_t, user_tz)
            if sleep_end_dt <= sleep_start_dt:
                sleep_end_dt += timedelta(days=1)

    if sleep_start_dt is None or sleep_end_dt is None:
        inferred_sleep = True
        sleep_start_dt = _combine(base_date, time(23, 0), user_tz)
        sleep_end_dt = sleep_start_dt + timedelta(hours=8)

    missed = asof_utc > deadline_utc
    in_sleep = sleep_start_dt <= deadline_local < sleep_end_dt

    if missed:
        status = 'MISSED'
    elif in_sleep:
        status = 'BLOCKED'
    else:
        status = 'ACCESSIBLE'

    safe_submit_at = sleep_start_dt - timedelta(minutes=60)
    missed_duration = None
    if missed:
        missed_duration = asof_utc - deadline_utc

    proposed_new_deadline = deadline_editorial
    proposed_tz = editorial_tz
    if missed:
        ed_today = asof_utc.astimezone(ZoneInfo(editorial_tz)).date()
        nd = _next_business_day(ed_today)
        proposed_new_deadline = _combine(nd, time(12, 0), editorial_tz)

    note_type = 'extension' if status in ('MISSED', 'BLOCKED') else 'early-submission'
    greeting_name = editor_name or 'Editor'
    to_line = editor_email or editor_name or 'Editor'
    if editor_email and editor_name:
        to_line = f"{editor_name} <{editor_email}>"

    if note_type == 'extension':
        subject = f"Extension Request: \"{essay_title or 'my essay'}\""
        if publication:
            subject += f" for {publication}"
    else:
        subject = f"Early Submission: \"{essay_title or 'my essay'}\""
        if publication:
            subject += f" for {publication}"

    body_lines = [f"Dear {greeting_name},", ""]
    if note_type == 'extension':
        first = f"I am writing to request an extension for my essay \"{essay_title or 'my essay'}\""
        if publication:
            first += f" for {publication}"
        first += f". The original deadline was {_fmt_local(deadline_editorial, editorial_tz)}"
        first += f" ({_fmt_local(deadline_local, user_tz)} in my local timezone)."
        body_lines.append(first)
        if shift_start_t and shift_end_t:
            body_lines.append(f"My shift is {_fmt_time(shift_start_t)}–{_fmt_time(shift_end_t)} {_tz_label(user_tz)}.")
        if sleep_start_dt and sleep_end_dt:
            body_lines.append(f"I sleep from {_fmt_time(sleep_start_dt.time())} to {_fmt_time(sleep_end_dt.time())} {_tz_label(user_tz)}.")
        body_lines.append("")
        if status == 'MISSED':
            body_lines.append("As of now, the deadline has already passed.")
            body_lines.append(f"Missed duration: {_fmt_duration(missed_duration)}.")
        else:
            body_lines.append("The deadline falls inside my sleep window, so I cannot safely submit without missing sleep.")
        body_lines.append("")
        body_lines.append(f"Proposed new deadline: {_fmt_local(proposed_new_deadline, proposed_tz)}.")
        body_lines.append("")
        body_lines.append("I appreciate your understanding and will deliver the essay by the proposed deadline.")
    else:
        first = f"I am submitting my essay \"{essay_title or 'my essay'}\""
        if publication:
            first += f" for {publication}"
        first += f" ahead of the deadline. The deadline is {_fmt_local(deadline_editorial, editorial_tz)}"
        first += f" ({_fmt_local(deadline_local, user_tz)} in my local timezone)."
        body_lines.append(first)
        if shift_start_t and shift_end_t:
            body_lines.append(f"My shift is {_fmt_time(shift_start_t)}–{_fmt_time(shift_end_t)} {_tz_label(user_tz)}.")
        if sleep_start_dt and sleep_end_dt:
            body_lines.append(f"I sleep from {_fmt_time(sleep_start_dt.time())} to {_fmt_time(sleep_end_dt.time())} {_tz_label(user_tz)}.")
        body_lines.append("")
        body_lines.append(f"Safe submit-by time: {_fmt_local(safe_submit_at, user_tz)}.")

    body_lines += ["", "Thank you,", "", "Sincerely,", "Writer"]
    email = f"To: {to_line}\nSubject: {subject}\n\n" + "\n".join(body_lines)
    header = f"SHIFT-ADJUSTED DEADLINE: {_fmt_local(deadline_local, user_tz)}"
    return header + "\n\n" + email


if __name__ == '__main__':
    _browser_input = globals().get('USER_INPUT', None)
    if _browser_input is None:
        _browser_input = sys.stdin.read()
    print(process(_browser_input))
