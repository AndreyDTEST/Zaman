import allure
import pytest
import requests


@allure.feature("Справочники")
@allure.story("УГД")
def test_get_tax_authorities_list(base_url, api_session, capture_responses):

    #Тест получения списка УГД
    endpoint = f"{base_url}/api/v1/smepayments/dictionaries/tax-authorities"

    with allure.step("Отправляем запрос на получение УГД"):
        resp = api_session.get(endpoint)

    with allure.step("Проверяем статус ответа"):
        assert resp.status_code == 200, f"Ожидался статус 200, получен: {resp.status_code}"

    with (allure.step("Проверяем структуру ответа")):
        json_data = resp.json()
        assert "ugds" in json_data, "В ответе отсутствует поле 'ugds'"
        assert isinstance(json_data["ugds"], list), "Поле 'ugds' должно быть списком"

        for item in json_data["ugds"]:
            assert "ugd" in item, "Каждый элемент списка должен содержать поле 'ugd'"
            ugd_obj = item["ugd"]
            assert "bin" in ugd_obj, "Поле 'ugd' должно содержать 'bin'"
            assert "code" in ugd_obj, "Поле 'ugd' должно содержать 'code'"
            assert "name" in ugd_obj, "Поле 'ugd' должно содержать 'name'"
            assert "regionCode" in ugd_obj, "Поле 'ugd' должно содержать 'regionCode'"
            assert "regionName" in ugd_obj, "Поле 'ugd' должно содержать 'regionName'"
            assert isinstance(ugd_obj["bin"], str), "Поле 'bin' должно быть строкой"
            assert isinstance(ugd_obj["code"], str), "Поле 'code' должно быть строкой"
            assert isinstance(ugd_obj["name"], str), "Поле 'name' должно быть строкой"
            assert isinstance(ugd_obj["regionCode"], str), "Поле 'regionCode' должно быть строкой"
            assert isinstance(ugd_obj["regionName"], str), "Поле 'regionName' должно быть строкой"

            # Проверка: BIN должен быть длиной 12 символов
            assert len(ugd_obj["bin"]) == 12, (f"Поле 'bin' должно быть длиной 12 символов, получено: "
                                               f"{len(ugd_obj['bin'])} ('{ugd_obj['bin']}')")

    capture_responses(resp)

    with allure.step("Пример полученных данных"):
        allure.attach(
            str(json_data["ugds"][:1]),
            name="Пример УГД",
            attachment_type=allure.attachment_type.JSON
        )
