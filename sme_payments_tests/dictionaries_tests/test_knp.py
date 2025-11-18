import allure
import pytest
import requests


@allure.feature("Справочники")
@allure.story("КНП")
def test_get_knp_list(base_url, api_session):
    # Тест получения списка КНП
    endpoint = f"{base_url}/api/v1/smepayments/dictionaries/knp"

    with allure.step("Отправляем запрос на получение КНП"):
        resp = api_session.get(endpoint)

    with allure.step("Проверяем статус ответа"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен: {resp.status_code}"

    with allure.step("Проверяем структуру ответа"):
        json_data = resp.json()
        assert "codes" in json_data, "В ответе отсутствует поле 'codes'"
        assert isinstance(json_data["codes"], list), "Поле 'codes' должно быть списком"

        for item in json_data["codes"]:
            assert "code" in item, "Каждый элемент списка должен содержать поле 'code'"
            code_obj = item["code"]
            assert "name" in code_obj, "Поле 'code' должно содержать 'name'"
            assert "value" in code_obj, "Поле 'code' должно содержать 'value'"
            assert isinstance(code_obj["name"], str), "Поле 'name' должно быть строкой"
            assert isinstance(code_obj["value"], str), "Поле 'value' должно быть строкой"

    with allure.step("Пример полученных данных"):
        allure.attach(
            str(json_data["codes"][:1]),
            name="Пример КНП",
            attachment_type=allure.attachment_type.JSON
        )
