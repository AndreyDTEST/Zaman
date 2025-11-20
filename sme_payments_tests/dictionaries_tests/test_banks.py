import allure
import pytest
import requests


@allure.feature("Справочники")
@allure.story("БВУ")
def test_get_banks_list(base_url, api_session, capture_responses):

    # Тест получения списка БВУ
    endpoint = f"{base_url}/api/v1/smepayments/dictionaries/banks"

    with allure.step("Отправляем запрос на получение БВУ"):
        resp = api_session.get(endpoint)

    with allure.step("Проверяем статус ответа"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен: {resp.status_code}"

    with allure.step("Проверяем структуру ответа"):
        json_data = resp.json()
        assert "banks" in json_data, "В ответе отсутствует поле 'banks'"
        assert isinstance(json_data["banks"], list), "Поле 'banks' должно быть списком"

        for item in json_data["banks"]:
            assert "bank" in item, "Каждый элемент списка должен содержать поле 'bank'"
            bank_obj = item["bank"]
            assert "name" in bank_obj, "Поле 'bank' должно содержать 'name'"
            assert "code" in bank_obj, "Поле 'bank' должно содержать 'code'"
            assert "bic" in bank_obj, "Поле 'bank' должно содержать 'bic'"
            assert isinstance(bank_obj["name"], str), "Поле 'name' должно быть строкой"
            assert isinstance(bank_obj["code"], str), "Поле 'code' должно быть строкой"
            assert isinstance(bank_obj["bic"], str), "Поле 'bic' должно быть строкой"

    capture_responses(resp)

    with allure.step("Пример полученных данных"):
        allure.attach(
            str(json_data["banks"][:1]),
            name="Пример БВУ",
            attachment_type=allure.attachment_type.JSON
        )
