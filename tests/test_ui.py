from playwright.sync_api import Page, expect


def test_example(page: Page):
    page.goto("http://localhost:8000/admin/login/")
    expect(page.get_by_text("로그인")).to_be_visible()
