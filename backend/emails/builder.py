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

    text_content_blocks = [
        email_content['subject_en'],
        '',
    ]
    if first_name:
        text_content_blocks.append(f'Dear {first_name},')
    text_content_blocks.extend(email_content['paragraphs_en'])
    text_content_blocks.append(extra_english_text)
    text_content_blocks.append(email_content['closing_en'])
    text_content_blocks.append(email_content['closing_team_en'])
    text_content_blocks.append('')
    text_content_blocks.append(email_content['subject_ur'])
    text_content_blocks.append('')
    if first_name:
        text_content_blocks.append(f'محترم {first_name}،')
    text_content_blocks.extend(email_content['paragraphs_ur'])
    text_content_blocks.append(extra_urdu_text)
    text_content_blocks.append(email_content['closing_ur'])
    text_content_blocks.append(email_content['closing_team_ur'])
    text_content_blocks.append('')
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_en'][0].format(**links))
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_en'][1].format(**links))
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_en'][2])
    text_content_blocks.append('')
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_ur'][0].format(**links))
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_ur'][1].format(**links))
    text_content_blocks.append(STANDARD_FOOTER['paragraphs_ur'][2])
    
    text_content = '\n\n'.join(text_content_blocks)

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
        "",  # Empty string so no greeting is rendered in HTML or text
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


def build_evening_reminder_email(
    first_name: str,
    *,
    phase: int,
    day_in_phase: int,
    exercise_link: str | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .booster_content import EVENING_REMINDER_EMAIL

    links = links or get_email_links()
    exercise_link = exercise_link or get_exercise_button_link()
    subject_en = EVENING_REMINDER_EMAIL['subject_en'].format(phase=phase, day_in_phase=day_in_phase)
    subject_ur = EVENING_REMINDER_EMAIL['subject_ur'].format(phase=phase, day_in_phase=day_in_phase)

    lead_en = EVENING_REMINDER_EMAIL['lead_en'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    lead_ur = EVENING_REMINDER_EMAIL['lead_ur'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    cta_en, cta_ur, cta_en_text, cta_ur_text = _build_cta_button_html(
        exercise_link,
        EVENING_REMINDER_EMAIL['button_en'],
        EVENING_REMINDER_EMAIL['button_ur'],
    )

    email_shell = {
        'subject_en': subject_en,
        'subject_ur': subject_ur,
        'title_en': EVENING_REMINDER_EMAIL['title_en'],
        'title_ur': EVENING_REMINDER_EMAIL['title_ur'],
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


def build_consecutive_misses_email(
    first_name: str,
    *,
    phase: int,
    day_in_phase: int,
    exercise_link: str | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .booster_content import CONSECUTIVE_MISSES_EMAIL

    links = links or get_email_links()
    exercise_link = exercise_link or get_exercise_button_link()
    subject_en = CONSECUTIVE_MISSES_EMAIL['subject_en'].format(phase=phase)
    subject_ur = CONSECUTIVE_MISSES_EMAIL['subject_ur'].format(phase=phase)

    lead_en = CONSECUTIVE_MISSES_EMAIL['lead_en'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    lead_ur = CONSECUTIVE_MISSES_EMAIL['lead_ur'].format(
        first_name=first_name, phase=phase, day_in_phase=day_in_phase,
    )
    cta_en, cta_ur, cta_en_text, cta_ur_text = _build_cta_button_html(
        exercise_link,
        CONSECUTIVE_MISSES_EMAIL['button_en'],
        CONSECUTIVE_MISSES_EMAIL['button_ur'],
    )

    email_shell = {
        'subject_en': subject_en,
        'subject_ur': subject_ur,
        'title_en': CONSECUTIVE_MISSES_EMAIL['title_en'],
        'title_ur': CONSECUTIVE_MISSES_EMAIL['title_ur'],
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


def build_assessment_due_email(message_en: str, links: dict[str, str] | None = None) -> dict[str, str]:
    from .content import ASSESSMENT_DUE_EMAIL, ASSESSMENT_OVERDUE_EMAIL

    # Normalize message for matching
    msg_norm = message_en.strip()

    # Determine if overdue or due
    is_overdue = 'overdue' in msg_norm.lower()
    email_content = ASSESSMENT_OVERDUE_EMAIL if is_overdue else ASSESSMENT_DUE_EMAIL

    # Paragraph mapping
    # Maps exact English message to Urdu message
    mapping = {
        # Standard Due
        "Hello! Your 7-day post-test assessment is now due. Please complete it today!":
            "السلام علیکم! آپ کا 7 روزہ پوسٹ ٹیسٹ اسیسمنٹ اب دستیاب ہے۔ براہِ کرم اسے آج ہی مکمل کریں۔",
        "Hello! Your 1-month follow-up assessment is now due. Please complete it today!":
            "السلام علیکم! آپ کا 1 ماہ کا فالو اپ اسیسمنٹ اب دستیاب ہے۔ براہِ کرم اسے آج ہی مکمل کریں۔",
        "Hello! Your 3-month follow-up assessment is now due. Please complete it today!":
            "السلام علیکم! آپ کا 3 ماہ کا فالو اپ اسیسمنٹ اب دستیاب ہے۔ براہِ کرم اسے آج ہی مکمل کریں۔",
        "Hello! Your 6-month follow-up assessment is now due. Please complete it today!":
            "السلام علیکم! آپ کا 6 ماہ کا فالو اپ اسیسمنٹ اب دستیاب ہے۔ براہِ کرم اسے آج ہی مکمل کریں۔",
        "Hello! Your 1-year follow-up assessment is now due. Please complete it today!":
            "السلام علیکم! آپ کا 1 سال کا فالو اپ اسیسمنٹ اب دستیاب ہے۔ براہِ کرم اسے آج ہی مکمل کریں۔",

        # Final Re-engagement
        "PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the 7-day post-test assessment. Please complete it to stay active in the study.":
            "پی آئی ایم ایس فائنل دوبارہ شمولیت: ہم نے دیکھا کہ آپ پچھلے فالو اپس مکمل نہیں کر پائے۔ یہ آپ کو 7 روزہ پوسٹ ٹیسٹ اسیسمنٹ کے لیے شامل کرنے کی ہماری آخری کوشش ہے۔ مطالعہ میں فعال رہنے کے لیے براہِ کرم اسے مکمل کریں۔",
        "PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the 1-month follow-up assessment. Please complete it to stay active in the study.":
            "پی آئی ایم ایس فائنل دوبارہ شمولیت: ہم نے دیکھا کہ آپ پچھلے فالو اپس مکمل نہیں کر پائے۔ یہ آپ کو 1 ماہ کے فالو اپ اسیسمنٹ کے لیے شامل کرنے کی ہماری آخری کوشش ہے۔ مطالعہ میں فعال رہنے کے لیے براہِ کرم اسے مکمل کریں۔",
        "PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the 3-month follow-up assessment. Please complete it to stay active in the study.":
            "پی آئی ایم ایس فائنل دوبارہ شمولیت: ہم نے دیکھا کہ آپ پچھلے فالو اپس مکمل نہیں کر پائے۔ یہ آپ کو 3 ماہ کے فالو اپ اسیسمنٹ کے لیے شامل کرنے کی ہماری آخری کوشش ہے۔ مطالعہ میں فعال رہنے کے لیے براہِ کرم اسے مکمل کریں۔",
        "PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the 6-month follow-up assessment. Please complete it to stay active in the study.":
            "پی آئی ایم ایس فائنل دوبارہ شمولیت: ہم نے دیکھا کہ آپ پچھلے فالو اپس مکمل نہیں کر پائے۔ یہ آپ کو 6 ماہ کے فالو اپ اسیسمنٹ کے لیے شامل کرنے کی ہماری آخری کوشش ہے۔ مطالعہ میں فعال رہنے کے لیے براہِ کرم اسے مکمل کریں۔",
        "PIMS Final Re-engagement: We noticed you missed your previous follow-ups. This is our final attempt to re-engage you for the 1-year follow-up assessment. Please complete it to stay active in the study.":
            "پی آئی ایم ایس فائنل دوبارہ شمولیت: ہم نے دیکھا کہ آپ پچھلے فالو اپس مکمل نہیں کر پائے۔ یہ آپ کو 1 سال کے فالو اپ اسیسمنٹ کے لیے شامل کرنے کی ہماری آخری کوشش ہے۔ مطالعہ میں فعال رہنے کے لیے براہِ کرم اسے مکمل کریں۔",

        # Overdue (1 Day Overdue)
        "Reminder: Your 7-day post-test assessment is overdue. Please complete it at your earliest convenience.":
            "یاد دہانی: آپ کا 7 روزہ پوسٹ ٹیسٹ اسیسمنٹ اب واجب الادہ ہے۔ براہِ کرم اسے اپنی اولین فرصت میں مکمل کریں۔",
        "Reminder: Your 1-month follow-up assessment is overdue. Please complete it at your earliest convenience.":
            "یاد دہانی: آپ کا 1 ماہ کا فالو اپ اسیسمنٹ اب واجب الادہ ہے۔ براہِ کرم اسے اپنی اولین فرصت میں مکمل کریں۔",
        "Reminder: Your 3-month follow-up assessment is overdue. Please complete it at your earliest convenience.":
            "یاد دہانی: آپ کا 3 ماہ کا فالو اپ اسیسمنٹ اب واجب الادہ ہے۔ براہِ کرم اسے اپنی اولین فرصت میں مکمل کریں۔",
        "Reminder: Your 6-month follow-up assessment is overdue. Please complete it at your earliest convenience.":
            "یاد دہانی: آپ کا 6 ماہ کا فالو اپ اسیسمنٹ اب واجب الادہ ہے۔ براہِ کرم اسے اپنی اولین فرصت میں مکمل کریں۔",
        "Reminder: Your 1-year follow-up assessment is overdue. Please complete it at your earliest convenience.":
            "یاد دہانی: آپ کا 1 سال کا فالو اپ اسیسمنٹ اب واجب الادہ ہے۔ براہِ کرم اسے اپنی اولین فرصت میں مکمل کریں۔",
    }

    message_ur = mapping.get(msg_norm, "براہِ کرم اپنی اسیسمنٹ مکمل کرنے کے لیے اپنے ڈیش بورڈ پر جائیں۔")

    # Build the CTA button
    dashboard_link = get_exercise_button_link()
    cta_en_button, cta_ur_button, cta_en_text, cta_ur_text = _build_cta_button_html(
        dashboard_link,
        "Go to Dashboard",
        "ڈیش بورڈ پر جائیں"
    )

    email_shell = {
        'subject_en': email_content['subject_en'],
        'subject_ur': email_content['subject_ur'],
        'title_en': email_content['title_en'],
        'title_ur': email_content['title_ur'],
        'paragraphs_en': [message_en],
        'paragraphs_ur': [message_ur],
        'closing_en': email_content['closing_en'],
        'closing_team_en': email_content['closing_team_en'],
        'closing_ur': email_content['closing_ur'],
        'closing_team_ur': email_content['closing_team_ur'],
    }

    # Use empty first name to prevent personal greeting in header ("Dear Name" / "Hi Name")
    result = _build_simple_bilingual_email(
        first_name="",
        email_content=email_shell,
        links=links,
        extra_english_html=cta_en_button,
        extra_urdu_html=cta_ur_button,
        extra_english_text=cta_en_text,
        extra_urdu_text=cta_ur_text,
    )
    return result


def build_ticket_created_participant_email(
    first_name: str,
    ticket_number: str,
    subject: str,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .content import TICKET_CREATED_PARTICIPANT_EMAIL

    formatted_content = {
        'subject_en': TICKET_CREATED_PARTICIPANT_EMAIL['subject_en'].format(ticket_number=ticket_number),
        'subject_ur': TICKET_CREATED_PARTICIPANT_EMAIL['subject_ur'].format(ticket_number=ticket_number),
        'title_en': TICKET_CREATED_PARTICIPANT_EMAIL['title_en'],
        'title_ur': TICKET_CREATED_PARTICIPANT_EMAIL['title_ur'],
        'paragraphs_en': [p.format(ticket_number=ticket_number, subject=subject) for p in TICKET_CREATED_PARTICIPANT_EMAIL['paragraphs_en']],
        'paragraphs_ur': [p.format(ticket_number=ticket_number, subject=subject) for p in TICKET_CREATED_PARTICIPANT_EMAIL['paragraphs_ur']],
        'closing_en': TICKET_CREATED_PARTICIPANT_EMAIL['closing_en'],
        'closing_team_en': TICKET_CREATED_PARTICIPANT_EMAIL['closing_team_en'],
        'closing_ur': TICKET_CREATED_PARTICIPANT_EMAIL['closing_ur'],
        'closing_team_ur': TICKET_CREATED_PARTICIPANT_EMAIL['closing_team_ur'],
    }

    return _build_simple_bilingual_email(first_name, formatted_content, links=links)


def build_ticket_updated_participant_email(
    first_name: str,
    ticket_number: str,
    status: str,
    admin_reply: str | None = None,
    links: dict[str, str] | None = None,
) -> dict[str, str]:
    from .content import TICKET_UPDATED_PARTICIPANT_EMAIL

    status_map_ur = {
        'Open': 'اوپن',
        'In Progress': 'کام جاری ہے',
        'Resolved': 'حل شدہ',
    }
    status_ur = status_map_ur.get(status, status)

    formatted_content = {
        'subject_en': TICKET_UPDATED_PARTICIPANT_EMAIL['subject_en'].format(ticket_number=ticket_number),
        'subject_ur': TICKET_UPDATED_PARTICIPANT_EMAIL['subject_ur'].format(ticket_number=ticket_number),
        'title_en': TICKET_UPDATED_PARTICIPANT_EMAIL['title_en'],
        'title_ur': TICKET_UPDATED_PARTICIPANT_EMAIL['title_ur'],
        'paragraphs_en': [p.format(ticket_number=ticket_number, status=status) for p in TICKET_UPDATED_PARTICIPANT_EMAIL['paragraphs_en']],
        'paragraphs_ur': [p.format(ticket_number=ticket_number, status_ur=status_ur) for p in TICKET_UPDATED_PARTICIPANT_EMAIL['paragraphs_ur']],
        'closing_en': TICKET_UPDATED_PARTICIPANT_EMAIL['closing_en'],
        'closing_team_en': TICKET_UPDATED_PARTICIPANT_EMAIL['closing_team_en'],
        'closing_ur': TICKET_UPDATED_PARTICIPANT_EMAIL['closing_ur'],
        'closing_team_ur': TICKET_UPDATED_PARTICIPANT_EMAIL['closing_team_ur'],
    }

    # Admin reply block
    reply_en_html = ""
    reply_ur_html = ""
    reply_en_text = ""
    reply_ur_text = ""
    if admin_reply:
        reply_en_html = (
            f'<div style="margin: 18px 0; padding: 16px; background-color: #f0fdf4; '
            f'border: 1px solid #bbf7d0; border-radius: 8px;">'
            f'<p style="margin: 0 0 8px; font-size: 14px; font-weight: 600; color: #166534;">'
            f'Message from Support Team:</p>'
            f'<p style="margin: 0; font-size: 14px; color: #1f2937; white-space: pre-wrap;">{admin_reply}</p></div>'
        )
        reply_ur_html = (
            f'<div dir="rtl" style="margin: 18px 0; padding: 16px; background-color: #f0fdf4; '
            f'border: 1px solid #bbf7d0; border-radius: 8px; text-align: right;">'
            f'<p style="margin: 0 0 8px; font-size: 15px; font-weight: 600; color: #166534;">'
            f'سپورٹ ٹیم کا پیغام:</p>'
            f'<p style="margin: 0; font-size: 15px; color: #1f2937; white-space: pre-wrap;">{admin_reply}</p></div>'
        )
        reply_en_text = f"\nMessage from Support Team:\n{admin_reply}\n"
        reply_ur_text = f"\nسپورٹ ٹیم کا پیغام:\n{admin_reply}\n"

    # CTA Button
    base_url = settings.SITE_BASE_URL.rstrip('/')
    support_link = f"{base_url}/dashboard?support=true"
    cta_en, cta_ur, cta_en_text, cta_ur_text = _build_cta_button_html(
        support_link,
        "View Support Tickets",
        "سپورٹ ٹکٹ دیکھیں"
    )

    return _build_simple_bilingual_email(
        first_name,
        formatted_content,
        links=links,
        extra_english_html=reply_en_html + cta_en,
        extra_urdu_html=reply_ur_html + cta_ur,
        extra_english_text=reply_en_text + "\n" + cta_en_text,
        extra_urdu_text=reply_ur_text + "\n" + cta_ur_text,
    )


def build_ticket_created_admin_email(
    ticket_number: str,
    user_name: str,
    user_email: str,
    subject: str,
    message: str,
) -> dict[str, str]:
    admin_link = f"{settings.SITE_BASE_URL.rstrip('/')}/admin/support-queries"
    subject_line = f"New Support Ticket Raised: {ticket_number}"

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f4f5; font-family: Arial, sans-serif;">
        <div style="max-width: 600px; margin: 0 auto; padding: 24px 16px;">
            <div style="background-color: #ffffff; border: 1px solid #e4e4e7; border-radius: 8px; padding: 24px;">
                <h1 style="margin: 0 0 18px; font-size: 20px; color: #2E4E90; border-bottom: 2px solid #C8A951; padding-bottom: 10px;">
                    New Support Ticket Raised
                </h1>
                <p style="font-size: 15px; color: #18181b;">A participant has raised a new support ticket.</p>
                
                <div style="margin: 20px 0; padding: 15px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;">
                    <p style="margin: 0 0 8px; font-size: 14px;"><strong>Ticket Number:</strong> {ticket_number}</p>
                    <p style="margin: 0 0 8px; font-size: 14px;"><strong>Submitted By:</strong> {user_name} ({user_email})</p>
                    <p style="margin: 0 0 8px; font-size: 14px;"><strong>Subject:</strong> {subject}</p>
                    <p style="margin: 0; font-size: 14px;"><strong>Message:</strong><br><span style="white-space: pre-wrap; display: block; margin-top: 5px; color: #3f3f46;">{message}</span></p>
                </div>
                
                <div style="margin: 24px 0; text-align: center;">
                    <a href="{admin_link}" style="background-color: #2E4E90; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                        View in Admin Dashboard
                    </a>
                </div>
                <hr style="border: 0; border-top: 1px solid #e4e4e7; margin: 24px 0;">
                <p style="font-size: 12px; color: #71717a; margin: 0;">This is an automated notification. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    text_content = f"""New Support Ticket Raised: {ticket_number}

Submitted By: {user_name} ({user_email})
Subject: {subject}

Message:
{message}

View and manage this ticket at: {admin_link}
"""
    return {
        'subject': subject_line,
        'html_content': html_content,
        'text_content': text_content,
    }




