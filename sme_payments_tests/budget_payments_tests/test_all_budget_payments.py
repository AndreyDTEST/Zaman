import allure
import pytest
import requests
from utils import build_budget_payment_payload, get_last_month_context
from payment_configs import PAYMENT_TYPES


# Список всех платежей
PAYMENT_TYPES_LIST = [
    "OPV",
    "OPV_PENYA",
    "OPVR",
    "OPVR_PENYA",
    "CO",
    "CO_PENYA",
    "VOCMC",
    "VOCMC_PENYA",
    "OOCMC",
    "OOCMC_PENYA",
    "IPN",
    "IPN_PENYA"
]


def _attach_json(name: str, data: dict):
    import json
    allure.attach(
        json.dumps(data, ensure_ascii=False, indent=2),
        name=name,
        attachment_type=allure.attachment_type.JSON
    )

def _attach_response(response: requests.Response):
    allure.attach(str(response.status_code), name="HTTP Status", attachment_type=allure.attachment_type.TEXT)
    if response.text:
        try:
            import json
            parsed = response.json()
            allure.attach(
                json.dumps(parsed, ensure_ascii=False, indent=2),
                name="Ответ API",
                attachment_type=allure.attachment_type.JSON
            )
        except ValueError:
            allure.attach(response.text, name="Ответ (raw)", attachment_type=allure.attachment_type.TEXT)


@allure.story("Платежи в бюджет NEW")
@pytest.mark.parametrize("payment_type", PAYMENT_TYPES_LIST)
def test_budget_payment(
    payment_type,
    base_url,
    auth_tokens,
    get_user_accounts,
    client_info,
    capture_responses
    ):

    config = PAYMENT_TYPES[payment_type]
    display_name = config["display_name"]
    allure.dynamic.title(f"Платеж {display_name}")

    # Выбираем KZT счет
    kzt_accounts = [a for a in get_user_accounts if a["currency"] == "KZT"]
    assert kzt_accounts, f"Нет KZT-счета для платежа {display_name}"
    payer_account = kzt_accounts[0]["iban"]

    period, month_ru, year = get_last_month_context()

    # Создание платежа
    with allure.step(f"1. Создать платеж: {display_name}"):
        payload = build_budget_payment_payload(
            payment_type_key=payment_type,
            payer_account=payer_account,
            client_info=client_info,
            period=period,
            month_ru=month_ru,
            year=year
        )
        _attach_json("Запрос", payload)

        headers = {"Authorization": f"Bearer {auth_tokens['access']}"}
        resp = requests.post(f"{base_url}/api/v1/smepayments/transactions", json=payload, headers=headers)
        _attach_response(resp)

        assert resp.status_code == 200, f"Не создан платеж {display_name}"
        tx_data = resp.json()
        assert tx_data.get("otpNeeded") is True
        transaction_id = tx_data["transactionID"]

        capture_responses(resp)

    # Запрос OTP
    with allure.step("2. Запрашиваем OTP"):
        otp_payload = {
            "phone": "+77000000660",
	        "deviceInfo": {}
        }
        _attach_json("OTP Запрос", otp_payload)

        resp = requests.post(f"{base_url}/api/v1/smepayments/otp", json=otp_payload, headers=headers)
        _attach_response(resp)
        assert resp.status_code == 200
        attempt_id = resp.json()["attemptId"]

        capture_responses(resp)

    # Подтверждение OTP
    with allure.step("3. Подтверждаем OTP"):
        validate_payload = {"code": "1111", "transactionID": transaction_id}
        _attach_json("OTP Подтверждение", validate_payload)

        url = f"{base_url}/api/v1/smepayments/otp/{attempt_id}/validate"
        resp = requests.post(url, json=validate_payload, headers=headers)
        _attach_response(resp)
        assert resp.status_code == 200

        capture_responses(resp)

    # Финальное подтверждение
    with allure.step("4. Подтверждение транзакции"):
        url = f"{base_url}/api/v1/smepayments/transactions/{transaction_id}/confirm"
        resp = requests.post(url, headers=headers)
        _attach_response(resp)

        assert resp.status_code == 200, "Подтверждение не выполнено"
        result = resp.json()
        assert result.get("otpNeeded") is False
        assert result.get("status") == "IN_PROGRESS", f"Статус: {result.get('status')}"

        capture_responses(resp)

    allure.attach(
        f"Платеж {display_name} в статусе IN_PROGRESS",
        name="Результат",
        attachment_type=allure.attachment_type.TEXT
    )

    # Платежное поручение
    with allure.step("5. Платежное поручение"):
        url = f"{base_url}/api/v1/smepayments/transactions/{transaction_id}/payment-order"
        resp = requests.get(url, headers=headers)
        _attach_response(resp)

        assert resp.status_code == 200, "Платежное поручение не сгенерировано"
        result = resp.json()

        # Определяем ожидаемое название в зависимости от типа платежа
        if payment_type in ["IPN", "IPN_PENYA"]:
            expected_title = "Платёжное поручение"
        else:
            expected_title = "Массовое платежное поручение"

        actual_title = result.get("title")
        assert actual_title == expected_title, f"Название: {actual_title}, ожидаемо: {expected_title}"

        capture_responses(resp)

