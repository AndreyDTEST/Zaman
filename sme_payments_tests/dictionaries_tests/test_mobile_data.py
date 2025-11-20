import pytest
import requests
import json
import allure
from payment_keys import PAYMENT_KEYS

@allure.feature("Справочники")
@allure.story("Mobile-data")
def test_get_mobile_data(base_url, api_session, capture_responses):

    # Тест получения сокращенных значений
    endpoint = f"{base_url}/api/v1/smepayments/dictionaries/mobile-data"

    for short_code, payment_data in PAYMENT_KEYS.items():
        payment_code = payment_data["paymentCode"]
        params = {"key": payment_code}

        with allure.step(f"Тест: {short_code} -> {payment_code}"):
            resp = api_session.get(endpoint, params=params)

            capture_responses(resp)

            assert resp.status_code == 200, f"Ошибка API для {payment_code}: {resp.text}"
            response_json = resp.json()

            # Проверка структуры
            assert "localizedStrings" in response_json
            localized_strings = response_json["localizedStrings"]

            # Словарь для хранения данных по группам
            groups_data = {}
            for item in localized_strings:
                group_name = item["group"]
                groups_data[group_name] = {i["key"]: i["value"] for i in item["items"]}

            # Проверка уникальности ключей в группах
            for group_name, items_dict in groups_data.items():
                assert len(items_dict) == len(set(items_dict.keys())), f"Дубликаты в группе {group_name}"

            # Проверка обязательных групп
            assert "knp" in groups_data, "Нет группы knp"
            assert "purposeTemplateIP" in groups_data, "Нет группы purposeTemplateIP"

            # Проверка данных из payment_data
            pc1 = payment_data.get("purposeCode_1")
            pc2 = payment_data.get("purposeCode_2")
            v1_knp = payment_data.get("value_1")
            v2_knp = payment_data.get("value_2")
            v1_ip = payment_data.get("purposeTemplateIP_1")
            v2_ip = payment_data.get("purposeTemplateIP_2")

            # knp
            if pc1 and v1_knp:
                assert groups_data["knp"][pc1] == v1_knp, f"Несовпадение knp для {pc1}"
            if pc2 and v2_knp:
                assert groups_data["knp"][pc2] == v2_knp, f"Несовпадение knp для {pc2}"

            # purposeTemplateIP
            if pc1 and v1_ip:
                assert groups_data["purposeTemplateIP"][pc1] == v1_ip, f"Несовпадение purposeTemplateIP для {pc1}"
            if pc2 and v2_ip:
                assert groups_data["purposeTemplateIP"][pc2] == v2_ip, f"Несовпадение purposeTemplateIP для {pc2}"

            # Проверка уникальных групп
            if short_code == "IPN":
                assert "purposeTemplateEmployee" in groups_data, "Нет группы purposeTemplateEmployee для IPN"
                v1_emp = payment_data.get("purposeTemplateEmployee_1")
                v2_emp = payment_data.get("purposeTemplateEmployee_2")
                if pc1 and v1_emp:
                    assert groups_data["purposeTemplateEmployee"][pc1] == v1_emp, f"Несовпадение purposeTemplateEmployee для {pc1}"
                if pc2 and v2_emp:
                    assert groups_data["purposeTemplateEmployee"][pc2] == v2_emp, f"Несовпадение purposeTemplateEmployee для {pc2}"
