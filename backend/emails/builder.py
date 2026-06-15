from django.conf import settings

from .content import STANDARD_FOOTER


URDU_FONT_STACK = "'Noto Nastaliq Urdu', 'Jameel Noori Nastaleeq', 'Urdu Typesetting', serif"
LATIN_FONT_STACK = "Arial, Helvetica, sans-serif"
NAVY = '#2E4E90'
GOLD = '#C8A951'


def get_first_name(user) -> str:
    if user.full_name:
        parts = user.full_name.strip().split()
        if parts:
            return parts[0]
    if user.display_name:
        parts = user.display_name.strip().split()
        if parts:
            return parts[0]
    return user.username


def get_email_links() -> dict[str, str]:
    base_url = settings.SITE_BASE_URL.rstrip('/')
    return {
        'withdraw_link': settings.PARTICIPANT_WITHDRAW_URL or f'{base_url}/profile',
        'support_page_link': settings.PARTICIPANT_SUPPORT_URL or base_url,
    }


def build_bilingual_subject(subject_en: str, subject_ur: str) -> str:
    return f'{subject_en} / {subject_ur}'


def _render_paragraphs(paragraphs: list[str], *, greeting: str | None = None) -> str:
    blocks = []
    if greeting:
        blocks.append(f'<p style="margin: 0 0 14px; font-size: 15px; line-height: 1.6;">Dear {greeting},</p>')
    for paragraph in paragraphs:
        blocks.append(
            f'<p style="margin: 0 0 14px; font-size: 15px; line-height: 1.6; color: #3f3f46;">{paragraph}</p>'
        )
    return ''.join(blocks)


def _render_urdu_paragraphs(paragraphs: list[str], *, greeting: str | None = None) -> str:
    blocks = []
    if greeting:
        blocks.append(
            f'<p style="margin: 0 0 14px; font-size: 16px; line-height: 1.9;">محترم {greeting}،</p>'
        )
    for paragraph in paragraphs:
        blocks.append(
            f'<p style="margin: 0 0 14px; font-size: 16px; line-height: 1.9; color: #3f3f46;">{paragraph}</p>'
        )
    return ''.join(blocks)


def _build_crisis_resources_html() -> tuple[str, str]:
    from .content import CRISIS_RESOURCES

    en_blocks = []
    ur_blocks = []
    for resource in CRISIS_RESOURCES:
        en_blocks.append(
            f'<p style="margin: 0 0 12px; font-size: 14px; line-height: 1.5; color: #18181b;">'
            f'<strong>{resource["name_en"]}</strong> — {resource["phone"]}<br>'
            f'{resource["timing_en"]}<br>'
            f'{resource["desc_en"]}</p>'
        )
        ur_blocks.append(
            f'<p style="margin: 0 0 12px; font-size: 15px; line-height: 1.8; color: #18181b;">'
            f'<strong>{resource["name_ur"]}</strong> — {resource["phone"]}<br>'
            f'{resource["timing_ur"]}<br>'
            f'{resource["desc_ur"]}</p>'
        )

    en_html = (
        f'<div style="margin: 18px 0; padding: 16px; background-color: #f8fafc; '
        f'border: 1px solid #e4e4e7; border-radius: 8px;">'
        f'<p style="margin: 0 0 12px; font-size: 14px; font-weight: 600; color: {NAVY};">'
        f'Support &amp; Crisis Resources</p>{"".join(en_blocks)}</div>'
    )
    ur_html = (
        f'<div dir="rtl" style="margin: 18px 0; padding: 16px; background-color: #f8fafc; '
        f'border: 1px solid #e4e4e7; border-radius: 8px; text-align: right;">'
        f'<p style="margin: 0 0 12px; font-size: 15px; font-weight: 600; color: {NAVY};">'
        f'معاونت و بحرانی رابطے</p>{"".join(ur_blocks)}</div>'
    )
    return en_html, ur_html


def _build_crisis_resources_text() -> tuple[str, str]:
    from .content import CRISIS_RESOURCES

    en_lines = ['Support & Crisis Resources:']
    ur_lines = ['معاونت و بحرانی رابطے:']
    for resource in CRISIS_RESOURCES:
        en_lines.append(
            f'{resource["name_en"]} — {resource["phone"]} ({resource["timing_en"]}). {resource["desc_en"]}'
        )
        ur_lines.append(
            f'{resource["name_ur"]} — {resource["phone"]} ({resource["timing_ur"]}). {resource["desc_ur"]}'
        )
    return '\n'.join(en_lines), '\n'.join(ur_lines)


def build_standard_footer_html(links: dict[str, str]) -> str:
    en_paragraphs = [
        paragraph.format(**links) for paragraph in STANDARD_FOOTER['paragraphs_en']
    ]
    ur_paragraphs = [
        paragraph.format(**links) for paragraph in STANDARD_FOOTER['paragraphs_ur']
    ]

    en_html = ''.join(
        f'<p style="margin: 0 0 10px; font-size: 12px; line-height: 1.5; color: #71717a;">{paragraph}</p>'
        for paragraph in en_paragraphs
    )
    ur_html = ''.join(
        f'<p style="margin: 0 0 10px; font-size: 13px; line-height: 1.8; color: #71717a;">{paragraph}</p>'
        for paragraph in ur_paragraphs
    )

    return f"""
    <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">
    <div style="font-family: {LATIN_FONT_STACK};">
        {en_html}
    </div>
    <div dir="rtl" style="font-family: {URDU_FONT_STACK}; text-align: right; margin-top: 16px;">
        {ur_html}
    </div>
    """


def build_welcome_email(first_name: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import WELCOME_EMAIL

    links = links or get_email_links()
    subject = build_bilingual_subject(WELCOME_EMAIL['subject_en'], WELCOME_EMAIL['subject_ur'])

    english_body = _render_paragraphs(WELCOME_EMAIL['paragraphs_en'], greeting=first_name)
    english_body += (
        f'<p style="margin: 18px 0 4px; font-size: 15px; line-height: 1.6;">{WELCOME_EMAIL["closing_en"]}</p>'
        f'<p style="margin: 0; font-size: 15px; line-height: 1.6; font-weight: 600;">'
        f'{WELCOME_EMAIL["closing_team_en"]}</p>'
    )

    urdu_body = _render_urdu_paragraphs(WELCOME_EMAIL['paragraphs_ur'], greeting=first_name)
    urdu_body += (
        f'<p style="margin: 18px 0 4px; font-size: 16px; line-height: 1.9;">{WELCOME_EMAIL["closing_ur"]}</p>'
        f'<p style="margin: 0; font-size: 16px; line-height: 1.9; font-weight: 600;">'
        f'{WELCOME_EMAIL["closing_team_ur"]}</p>'
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px 16px;">
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 24px;">
                <h1 style="margin: 0 0 18px; font-family: {LATIN_FONT_STACK}; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                    {WELCOME_EMAIL['title_en']}
                </h1>
                <div style="font-family: {LATIN_FONT_STACK}; color: #18181b;">
                    {english_body}
                </div>
                <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">
                <div dir="rtl" style="font-family: {URDU_FONT_STACK}; text-align: right; color: #18181b;">
                    <h2 style="margin: 0 0 18px; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                        {WELCOME_EMAIL['title_ur']}
                    </h2>
                    {urdu_body}
                </div>
                {build_standard_footer_html(links)}
            </div>
        </div>
    </body>
    </html>
    """

    text_content = '\n\n'.join([
        WELCOME_EMAIL['subject_en'],
        '',
        f'Dear {first_name},',
        *WELCOME_EMAIL['paragraphs_en'],
        WELCOME_EMAIL['closing_en'],
        WELCOME_EMAIL['closing_team_en'],
        '',
        WELCOME_EMAIL['subject_ur'],
        '',
        f'محترم {first_name}،',
        *WELCOME_EMAIL['paragraphs_ur'],
        WELCOME_EMAIL['closing_ur'],
        WELCOME_EMAIL['closing_team_ur'],
        '',
        STANDARD_FOOTER['paragraphs_en'][0].format(**links),
        STANDARD_FOOTER['paragraphs_en'][1].format(**links),
        STANDARD_FOOTER['paragraphs_en'][2],
        '',
        STANDARD_FOOTER['paragraphs_ur'][0].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][1].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][2],
    ])

    return {
        'subject': subject,
        'text_content': text_content,
        'html_content': html_content,
    }


def _build_simple_bilingual_email(
    first_name: str,
    email_content: dict,
    *,
    links: dict[str, str] | None = None,
    extra_english_html: str = '',
    extra_urdu_html: str = '',
    extra_english_text: str = '',
    extra_urdu_text: str = '',
) -> dict[str, str]:
    links = links or get_email_links()
    subject = build_bilingual_subject(email_content['subject_en'], email_content['subject_ur'])

    english_body = _render_paragraphs(email_content['paragraphs_en'], greeting=first_name)
    english_body += extra_english_html
    english_body += (
        f'<p style="margin: 18px 0 4px; font-size: 15px; line-height: 1.6;">{email_content["closing_en"]}</p>'
        f'<p style="margin: 0; font-size: 15px; line-height: 1.6; font-weight: 600;">'
        f'{email_content["closing_team_en"]}</p>'
    )

    urdu_body = _render_urdu_paragraphs(email_content['paragraphs_ur'], greeting=first_name)
    urdu_body += extra_urdu_html
    urdu_body += (
        f'<p style="margin: 18px 0 4px; font-size: 16px; line-height: 1.9;">{email_content["closing_ur"]}</p>'
        f'<p style="margin: 0; font-size: 16px; line-height: 1.9; font-weight: 600;">'
        f'{email_content["closing_team_ur"]}</p>'
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px 16px;">
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 24px;">
                <h1 style="margin: 0 0 18px; font-family: {LATIN_FONT_STACK}; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                    {email_content['title_en']}
                </h1>
                <div style="font-family: {LATIN_FONT_STACK}; color: #18181b;">
                    {english_body}
                </div>
                <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">
                <div dir="rtl" style="font-family: {URDU_FONT_STACK}; text-align: right; color: #18181b;">
                    <h2 style="margin: 0 0 18px; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                        {email_content['title_ur']}
                    </h2>
                    {urdu_body}
                </div>
                {build_standard_footer_html(links)}
            </div>
        </div>
    </body>
    </html>
    """

    text_content = '\n\n'.join([
        email_content['subject_en'],
        '',
        f'Dear {first_name},',
        *email_content['paragraphs_en'],
        extra_english_text,
        email_content['closing_en'],
        email_content['closing_team_en'],
        '',
        email_content['subject_ur'],
        '',
        f'محترم {first_name}،',
        *email_content['paragraphs_ur'],
        extra_urdu_text,
        email_content['closing_ur'],
        email_content['closing_team_ur'],
        '',
        STANDARD_FOOTER['paragraphs_en'][0].format(**links),
        STANDARD_FOOTER['paragraphs_en'][1].format(**links),
        STANDARD_FOOTER['paragraphs_en'][2],
        '',
        STANDARD_FOOTER['paragraphs_ur'][0].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][1].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][2],
    ])

    return {
        'subject': subject,
        'text_content': text_content,
        'html_content': html_content,
    }


def build_support_email(first_name: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import SUPPORT_EMAIL

    crisis_en_html, crisis_ur_html = _build_crisis_resources_html()
    crisis_en_text, crisis_ur_text = _build_crisis_resources_text()
    return _build_simple_bilingual_email(
        first_name,
        SUPPORT_EMAIL,
        links=links,
        extra_english_html=crisis_en_html,
        extra_urdu_html=crisis_ur_html,
        extra_english_text=crisis_en_text,
        extra_urdu_text=crisis_ur_text,
    )


def build_socio_disqualification_email(first_name: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import SOCIO_DISQUALIFICATION_EMAIL

    return _build_simple_bilingual_email(first_name, SOCIO_DISQUALIFICATION_EMAIL, links=links)


def build_screen_out_email(first_name: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import SCREEN_OUT_EMAIL

    links = links or get_email_links()
    subject = build_bilingual_subject(SCREEN_OUT_EMAIL['subject_en'], SCREEN_OUT_EMAIL['subject_ur'])
    crisis_en_html, crisis_ur_html = _build_crisis_resources_html()
    crisis_en_text, crisis_ur_text = _build_crisis_resources_text()

    lead_en = SCREEN_OUT_EMAIL['paragraphs_en'][:4]
    tail_en = SCREEN_OUT_EMAIL['paragraphs_en'][4:]
    lead_ur = SCREEN_OUT_EMAIL['paragraphs_ur'][:4]
    tail_ur = SCREEN_OUT_EMAIL['paragraphs_ur'][4:]

    english_body = _render_paragraphs(lead_en, greeting=first_name)
    english_body += crisis_en_html
    english_body += _render_paragraphs(tail_en)
    english_body += (
        f'<p style="margin: 18px 0 4px; font-size: 15px; line-height: 1.6;">{SCREEN_OUT_EMAIL["closing_en"]}</p>'
        f'<p style="margin: 0; font-size: 15px; line-height: 1.6; font-weight: 600;">'
        f'{SCREEN_OUT_EMAIL["closing_team_en"]}</p>'
    )

    urdu_body = _render_urdu_paragraphs(lead_ur, greeting=first_name)
    urdu_body += crisis_ur_html
    urdu_body += _render_urdu_paragraphs(tail_ur)
    urdu_body += (
        f'<p style="margin: 18px 0 4px; font-size: 16px; line-height: 1.9;">{SCREEN_OUT_EMAIL["closing_ur"]}</p>'
        f'<p style="margin: 0; font-size: 16px; line-height: 1.9; font-weight: 600;">'
        f'{SCREEN_OUT_EMAIL["closing_team_ur"]}</p>'
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Noto+Nastaliq+Urdu&display=swap" rel="stylesheet">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px 16px;">
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 24px;">
                <h1 style="margin: 0 0 18px; font-family: {LATIN_FONT_STACK}; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                    {SCREEN_OUT_EMAIL['title_en']}
                </h1>
                <div style="font-family: {LATIN_FONT_STACK}; color: #18181b;">
                    {english_body}
                </div>
                <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">
                <div dir="rtl" style="font-family: {URDU_FONT_STACK}; text-align: right; color: #18181b;">
                    <h2 style="margin: 0 0 18px; font-size: 22px; color: {NAVY}; border-bottom: 2px solid {GOLD}; padding-bottom: 10px;">
                        {SCREEN_OUT_EMAIL['title_ur']}
                    </h2>
                    {urdu_body}
                </div>
                {build_standard_footer_html(links)}
            </div>
        </div>
    </body>
    </html>
    """

    text_content = '\n\n'.join([
        SCREEN_OUT_EMAIL['subject_en'],
        '',
        f'Dear {first_name},',
        *lead_en,
        crisis_en_text,
        *tail_en,
        SCREEN_OUT_EMAIL['closing_en'],
        SCREEN_OUT_EMAIL['closing_team_en'],
        '',
        SCREEN_OUT_EMAIL['subject_ur'],
        '',
        f'محترم {first_name}،',
        *lead_ur,
        crisis_ur_text,
        *tail_ur,
        SCREEN_OUT_EMAIL['closing_ur'],
        SCREEN_OUT_EMAIL['closing_team_ur'],
        '',
        STANDARD_FOOTER['paragraphs_en'][0].format(**links),
        STANDARD_FOOTER['paragraphs_en'][1].format(**links),
        STANDARD_FOOTER['paragraphs_en'][2],
        '',
        STANDARD_FOOTER['paragraphs_ur'][0].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][1].format(**links),
        STANDARD_FOOTER['paragraphs_ur'][2],
    ])

    return {
        'subject': subject,
        'text_content': text_content,
        'html_content': html_content,
    }


def get_exercise_button_link() -> str:
    base_url = settings.SITE_BASE_URL.rstrip('/')
    return f'{base_url}/dashboard'


def _build_cta_button_html(link: str, label_en: str, label_ur: str) -> tuple[str, str, str, str]:
    en_html = (
        f'<div style="margin: 24px 0; text-align: center;">'
        f'<a href="{link}" style="background-color: {NAVY}; color: #ffffff; padding: 14px 28px; '
        f'text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">'
        f'{label_en}</a></div>'
    )
    ur_html = (
        f'<div style="margin: 24px 0; text-align: center;">'
        f'<a href="{link}" style="background-color: {NAVY}; color: #ffffff; padding: 14px 28px; '
        f'text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">'
        f'{label_ur}</a></div>'
    )
    return en_html, ur_html, f'{label_en}: {link}', f'{label_ur}: {link}'


def build_daily_nudge_email(
    first_name: str,
    *,
    phase: int,
    day_in_phase: int,
    exercise_link: str | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .booster_content import DAILY_NUDGE_EMAIL

    links = links or get_email_links()
    exercise_link = exercise_link or get_exercise_button_link()
    subject_en = DAILY_NUDGE_EMAIL['subject_en'].format(phase=phase, day_in_phase=day_in_phase)
    subject_ur = DAILY_NUDGE_EMAIL['subject_ur'].format(phase=phase, day_in_phase=day_in_phase)

    lead_en = DAILY_NUDGE_EMAIL['lead_en'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    lead_ur = DAILY_NUDGE_EMAIL['lead_ur'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    cta_en, cta_ur, cta_en_text, cta_ur_text = _build_cta_button_html(
        exercise_link,
        DAILY_NUDGE_EMAIL['button_en'],
        DAILY_NUDGE_EMAIL['button_ur'],
    )

    email_shell = {
        'subject_en': subject_en,
        'subject_ur': subject_ur,
        'title_en': DAILY_NUDGE_EMAIL['title_en'],
        'title_ur': DAILY_NUDGE_EMAIL['title_ur'],
        'paragraphs_en': [lead_en.replace(f'Dear {first_name}, ', '')],
        'paragraphs_ur': [lead_ur.replace(f'محترم {first_name}، ', '')],
        'closing_en': '',
        'closing_team_en': 'Psycheversity Research Team',
        'closing_ur': '',
        'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
    }
    result = _build_simple_bilingual_email(
        first_name,
        email_shell,
        links=links,
        extra_english_html=cta_en,
        extra_urdu_html=cta_ur,
        extra_english_text=cta_en_text,
        extra_urdu_text=cta_ur_text,
    )
    result['subject'] = build_bilingual_subject(subject_en, subject_ur)
    return result


def build_phase_invite_email(
    first_name: str,
    invite_key: str,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .booster_content import PHASE_INVITE_TEMPLATES

    template = PHASE_INVITE_TEMPLATES[invite_key]
    shell = {
        **template,
        'closing_en': 'Warm regards,',
        'closing_team_en': 'Psycheversity Research Team',
        'closing_ur': 'نیک تمناؤں کے ساتھ،',
        'closing_team_ur': 'سائیکیورسٹی ریسرچ ٹیم',
    }
    return _build_simple_bilingual_email(first_name, shell, links=links)


def build_phase_complete_email(
    first_name: str,
    template_key: str,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .booster_content import (
        PHASE_1_COMPLETE_EMAIL,
        PHASE_2_COMPLETE_EMAIL,
        PHASE_REPORT_COMPLETE_EMAIL,
    )

    templates = {
        'phase_1_complete': PHASE_1_COMPLETE_EMAIL,
        'phase_2_complete': PHASE_2_COMPLETE_EMAIL,
        **PHASE_REPORT_COMPLETE_EMAIL,
    }
    return _build_simple_bilingual_email(first_name, templates[template_key], links=links)


def build_otp_email(otp: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import OTP_EMAIL

    otp_html = (
        f'<div style="margin: 24px 0; text-align: center;">'
        f'<span style="background-color: #f8fafc; color: {NAVY}; font-size: 32px; '
        f'font-weight: bold; letter-spacing: 4px; padding: 12px 30px; '
        f'border: 2px solid #e2e8f0; border-radius: 8px; display: inline-block;'
        f'font-family: Arial, sans-serif;">{otp}</span>'
        f'</div>'
    )
    otp_text = f'\nVerification Code: {otp}\n'

    return _build_simple_bilingual_email(
        first_name="",
        email_content=OTP_EMAIL,
        links=links,
        extra_english_html=otp_html,
        extra_urdu_html=otp_html,
        extra_english_text=otp_text,
        extra_urdu_text=otp_text,
    )


def build_password_reset_email(first_name: str, otp: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import PASSWORD_RESET_EMAIL

    otp_html = (
        f'<div style="margin: 24px 0; text-align: center;">'
        f'<span style="background-color: #f8fafc; color: {NAVY}; font-size: 32px; '
        f'font-weight: bold; letter-spacing: 4px; padding: 12px 30px; '
        f'border: 2px solid #e2e8f0; border-radius: 8px; display: inline-block;'
        f'font-family: Arial, sans-serif;">{otp}</span>'
        f'</div>'
    )
    otp_text = f'\nVerification Code: {otp}\n'

    return _build_simple_bilingual_email(
        first_name=first_name,
        email_content=PASSWORD_RESET_EMAIL,
        links=links,
        extra_english_html=otp_html,
        extra_urdu_html=otp_html,
        extra_english_text=otp_text,
        extra_urdu_text=otp_text,
    )

