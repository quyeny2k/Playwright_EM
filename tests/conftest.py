import pytest
from playwright.sync_api import sync_playwright, expect, Page

#from tespopup import EMHOST

LOGINRETRIES = 4
EMHOST = "https://169.254.0.1"

def pytest_addoption(parser):
    parser.addoption(
        "--em-url",
        action="store",
        default="https://169.254.0.1",
        help="URL of the test EM",
    )

@pytest.fixture(scope="session")
def em_url(request):
    return request.config.getoption("--em-url")

@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--ignore-certificate-errors'])
        yield browser
        browser.close()

@pytest.fixture(scope="session")
def context(browser):
    context = browser.new_context()
    yield context
    context.close()

@pytest.fixture(scope="session")
def page(context):
    page = context.new_page()
    page.set_default_timeout(5000)
    yield page
    page.close()

@pytest.fixture(scope="session")
def login(page, em_url) -> Page:
    global EMHOST
    EMHOST = em_url
    page.goto(EMHOST)
    page.locator("#userNameTextBox").fill("admin")
    page.locator("#passwordTextBox").fill("Pass@123")
    page.get_by_role("button", name="Sign in").click()
    expect(page).to_have_url(f"{EMHOST}/ems/licenseSupport/management.ems")
    expect(page.locator("#welcome")).to_contain_text("WELCOME admin")
    yield page

@pytest.fixture(scope="session")
def emfacilitiespage(login) -> Page:
    page = login
    page.goto(f"{EMHOST}/ems/facilities/home.ems?")

    page.wait_for_load_state("networkidle")
    page.get_by_role("tab", name="Facilities").get_by_role("link").click()
    page.locator("#campus_1").get_by_role("insertion").first.click()
    page.get_by_role("insertion").nth(2).click()
    if page.locator('#building_1').evaluate('el => el.classList.contains("jstree-closed")'):
        page.locator("#building_1").get_by_role("insertion").first.click()

    page.get_by_role("link", name="Main").click()

    #time.sleep(5)  # Wait for the load(s) javascript to load the iframe completely
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("link", name="Energy Consumption")).to_be_visible()
    yield page

def transformpos2canvas(pos: dict, scale: float):
    return {"x": 148 + pos['x'] // scale, "y": 416 - pos['y'] // scale }

def transformpos2canvasincommissiondialog(pos: dict, scale: float):
    return {"x": 17.65 + pos['x'] // scale, "y": 718 - pos['y'] // scale }

def handle_dialog(dialog):
    print(f"Dialog type: {dialog.type}")  # Get the dialog type (alert, confirm, or prompt)
    if dialog.type == 'alert':
        print(f"Alert message: {dialog.message}")
        dialog.accept()  # Close the alert by accepting it
    elif dialog.type == 'confirm':
        print(f"Confirm message: {dialog.message}")
        dialog.dismiss()  # Close the confirm dialog by dismissing it
    elif dialog.type == 'prompt':
        print(f"Prompt message: {dialog.message}")
        dialog.accept('Test Response')  # Accept the prompt with a response

