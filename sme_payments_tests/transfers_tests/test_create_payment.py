import allure
import pytest
import requests
import uuid
from transfers_configs import TRANSFERS_DATA


@allure.feature("Переводы по номеру счета")
@allure.story("Создание перевода по номеру счета")
@pytest.mark.parametrize("transfer_data", TRANSFERS_DATA, ids=[d["type"] for d in TRANSFERS_DATA])
def test_create_payment_by_account(
    base_url,
    auth_tokens,
    client_info,
    get_user_accounts,
    transfer_data,
    capture_responses,
    login_payload
    ):

    url = f"{base_url}/api/v1/payments/create-payment-by-account"
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    # Получаем данные клиента
    payer_bin_iin = login_payload["iin"]
    payer_name = f"{client_info['name']} {client_info['surname']}"

    # Выбираем KZT счет
    kzt_accounts = [a for a in get_user_accounts if a["currency"] == "KZT"]
    assert kzt_accounts, f"Нет KZT-счета для перевода"
    payer_account = kzt_accounts[0]["iban"]

    # Определяем тип получателя: ФЛ=0, ЮЛ=1, ИП=2
    type_map = {"FL": 0, "LE": 1, "IP": 2}
    type_prefix = transfer_data["type"].split()[0]
    beneficiary_type = type_map[type_prefix]

    # Определяем сумму и нужен ли OTP
    amount = 50.0
    otp_expected = amount > 5000

    payload = {
        "idempotencyID": str(uuid.uuid4()),
        "payerBinIIN": payer_bin_iin,
        "payerName": payer_name,
        "payerAccount": payer_account,
        "amount": amount,
        "currency": "KZT",
        "beneficiaryBinIIN": transfer_data["iin"],
        "beneficiaryName": transfer_data["name"],
        "beneficiaryType": beneficiary_type,
        "beneficiaryBank": transfer_data["bankBic"],
        "beneficiaryAccount": transfer_data["account"],
        "beneficiaryBankName": transfer_data["bankName"],
        "kbe": "19",
        "knp": "710",
        "paymentDetails": "Платежи за товары, за исключением недвижимости и товаров с кодами назначения платежей 711, 712 и 713"
    }

    with allure.step(f"Создание перевода: {transfer_data['type']}"):
        allure.attach(
            str(payload),
            name="Данные запроса",
            attachment_type=allure.attachment_type.JSON
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

        expected_fields = {"message", "otpRequired", "status", "transactionID"}
        actual_fields = set(data.keys())
        assert expected_fields == actual_fields, f"Ожидаемые поля: {expected_fields}, получены: {actual_fields}"

    with allure.step("Проверка значений ответа"):
        assert data["status"] == "IN_PROGRESS", f"Ожидался статус IN_PROGRESS, получен {data['status']}"

        if otp_expected:
            assert data["otpRequired"] is True, f"Ожидалось otpRequired=True при сумме {amount}"
        else:
            assert data["otpRequired"] is False, f"Ожидалось otpRequired=False при сумме {amount}"

    with allure.step("Перевод создан успешно"):
        allure.attach(
            f"Перевод создан создан: {data['transactionID']}, статус: {data['status']}",
            name="Результат",
            attachment_type=allure.attachment_type.TEXT
        )