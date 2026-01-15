import os

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def icon(name, css_class="", **kwargs):
    """
    SVG 아이콘을 인라인으로 렌더링합니다.

    사용법:
        {% load icon_tags %}
        {% icon "search" %}
        {% icon "reset" css_class="w-4 h-4 text-gray-400" %}
        {% icon "email" css_class="w-5 h-5 text-blue-500" %}
    """
    # ic_ 접두사 처리
    if not name.startswith("ic_"):
        icon_name = f"ic_{name}"
    else:
        icon_name = name

    # 파일 경로
    icon_path = os.path.join(
        settings.BASE_DIR, "app", "static", "icons", f"{icon_name}.svg"
    )

    try:
        with open(icon_path) as f:
            svg_content = f.read()

        # fill을 currentColor로 변경 (Tailwind 색상 클래스 적용 가능하게)
        import re

        svg_content = re.sub(
            r'fill="[^"]*"', 'fill="currentColor"', svg_content
        )

        # CSS 클래스와 추가 속성 처리
        attrs = []
        if css_class:
            attrs.append(f'class="{css_class}"')

        for key, value in kwargs.items():
            attrs.append(f'{key}="{value}"')

        # svg 태그에 속성 추가
        if attrs:
            svg_content = svg_content.replace(
                "<svg ", f'<svg {" ".join(attrs)} ', 1
            )

        return mark_safe(svg_content)
    except FileNotFoundError:
        return mark_safe(f"<!-- Icon not found: {icon_name} -->")
