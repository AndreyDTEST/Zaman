import allure
import pytest
import requests


@allure.title("Авторизация и подтверждение по коду")
@allure.feature("Авторизация")
def test_login_and_confirm_flow(auth_tokens):
    with allure.step("Проверить, что токены получены"):
        assert auth_tokens["access"], "Access-токен отсутствует"
        assert auth_tokens["refresh"], "Refresh-токен отсутствует"
        assert auth_tokens["user_id"], "User ID отсутствует"

    allure.attach(
        str(auth_tokens),
        name="Полученные токены",
        attachment_type=allure.attachment_type.JSON
    )


@allure.title("Получение списка счетов пользователя")
@allure.feature("Счета")
def test_get_user_accounts(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    with allure.step("Отправить запрос на получение счетов"):
        resp = requests.get(f"{base_url}/api/v1/user/accounts", headers=headers)

        assert resp.status_code == 200, f"Ошибка получения счетов: {resp.status_code} — {resp.text}"

        accounts = resp.json()
        assert "accounts" in accounts, "Ответ не содержит поля 'accounts'"

        allure.attach(
            str(resp.status_code),
            name="HTTP Status",
            attachment_type=allure.attachment_type.TEXT
        )
        allure.attach(
            str(accounts),
            name="Ответ API",
            attachment_type=allure.attachment_type.JSON
        )


@allure.title("Проверить наличие хотя бы одного счёта в KZT")
@allure.feature("Счета")
def test_has_kzt_account(get_user_accounts):
    with allure.step("Найти счета в KZT"):
        kzt_accounts = [acc for acc in get_user_accounts if acc["currency"] == "KZT"]

        assert len(kzt_accounts) > 0, "Должен быть хотя бы один счёт в KZT"

    allure.attach(
        str(len(kzt_accounts)),
        name="Количество KZT-счетов",
        attachment_type=allure.attachment_type.TEXT
    )
    allure.attach(
        str(kzt_accounts),
        name="KZT-счета",
        attachment_type=allure.attachment_type.JSON
    )