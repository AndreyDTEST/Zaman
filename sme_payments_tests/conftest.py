import pytest
import os
import requests
import allure


@pytest.fixture(scope="session")
def base_url():
    return os.getenv("API_BASE_URL", "https://sme-dev.zamanbank.kz").strip()


@pytest.fixture(scope="session")
def login_payload():
    return {
	"phone": "+77000000660",
	"iin": "970304450660",
	"deviceInfo": {
		"appVersion": "205",
		"deviceModel": "iPhone",
		"installationID": "818102f6-4c29-4f33-8455-efaac4c879ba",
		"systemType": "iOS",
		"systemVersion": "18.6.2"
	}
}


@pytest.fixture(scope="session")
def confirm_code():
    return "1111"


@pytest.fixture(scope="session")
def auth_tokens(base_url, login_payload, confirm_code):

    # Логин
    login_resp = requests.post(f"{base_url}/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    attempt_id = login_resp.json()["attemptID"]

    # Конфирм
    confirm_resp = requests.post(
        f"{base_url}/api/v1/auth/confirm",
        json={"attemptID": attempt_id, "code": confirm_code}
    )
    assert confirm_resp.status_code == 200, f"Confirm failed: {confirm_resp.text}"
    tokens = confirm_resp.json()["tokens"]
    user_id = confirm_resp.json()["userID"]

    return {
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "user_id": user_id
    }


# Фикстура для вытаскивания номеров счетов и валют
@pytest.fixture(scope="session")
def get_user_accounts(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}
    resp = requests.get(f"{base_url}/api/v1/user/accounts", headers=headers)
    assert resp.status_code == 200
    return [
        {
            "iban": account["iban"],
            "currency": account["currency"]
        }
        for account in resp.json()["accounts"]
    ]


# Получаем данные клиента из /client
@pytest.fixture(scope="session")
def client_info(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}
    resp = requests.get(f"{base_url}/api/v1/smepayments/client", headers=headers)
    assert resp.status_code == 200, f"Не удалось загрузить /client: {resp.text}"
    return resp.json()


@pytest.fixture(scope="session")
def api_session(auth_tokens):
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {auth_tokens['access']}"})
    return session


# Фикстура для X-Request-Id. Должна вызываться после каждого запроса
_last_responses = []
@pytest.fixture(autouse=True)
def capture_responses():
    def _capture(response):
        _last_responses.append(response)
        request_id = response.headers.get("X-Request-Id")
        if request_id:
            allure.attach(
                request_id,
                name=f"X-Request-Id ({len(_last_responses)})",
                attachment_type=allure.attachment_type.TEXT
            )
    return _capture