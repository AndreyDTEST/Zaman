import allure
import pytest
import requests
from transfers_configs import TRANSFERS_DATA


@allure.feature("Проверка счета по ИИН")
@allure.story("Проверка структуры ответа для разных счетов")
@pytest.mark.parametrize("transfer_data", TRANSFERS_DATA, ids=[d["type"] for d in TRANSFERS_DATA])
def test_check_account_iin(
    base_url,
    auth_tokens,
    transfer_data,
    capture_responses
    ):

    url = f"{base_url}/api/v1/payments/check-account-iin"

    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    payload = {
        "clientIinBin": transfer_data["iin"],
        "account": transfer_data["account"]
    }

    with allure.step(f"Тест: {transfer_data['type']}"):
        allure.attach(
            f"ИИН: {transfer_data['iin']}\nСчет: {transfer_data['account']}",
            name="Данные запроса",
            attachment_type=allure.attachment_type.TEXT
        )

        resp = requests.post(url, json=payload, headers=headers)

        capture_responses(resp)

        allure.attach(
            resp.text,
            name="Ответ API",
            attachment_type=allure.attachment_type.JSON
        )

        assert resp.status_code == 200, f"Ожидался статус 200, получен {resp.status_code}"

    with allure.step("Проверка структуры ответа"):
        data = resp.json()

        # Обязательные поля (без additionalIndividualType)
        expected_fields = {"name", "bankName", "bankBic", "taxPayerType"}
        actual_fields = set(data.keys())

        # Проверяем, что обязательные поля есть
        missing_fields = expected_fields - actual_fields
        assert not missing_fields, f"Отсутствуют обязательные поля: {missing_fields}"

        # Проверяем типы обязательных полей
        assert isinstance(data["name"], str), "name должен быть строкой"
        assert isinstance(data["bankName"], str), "bankName должен быть строкой"
        assert isinstance(data["bankBic"], str), "bankBic должен быть строкой"
        assert isinstance(data["taxPayerType"], str), "taxPayerType должен быть строкой"

        # Проверяем additionalIndividualType, если он есть
        if "additionalIndividualType" in data:
            additional = data["additionalIndividualType"]
            assert isinstance(additional, dict), "additionalIndividualType должен быть объектом"
            assert set(additional.keys()) == {"name", "type"}, f"Поля в additionalIndividualType: {set(additional.keys())}"
            assert isinstance(additional["name"], str), "additionalIndividualType.name должен быть строкой"
            assert isinstance(additional["type"], int), "additionalIndividualType.type должен быть числом"