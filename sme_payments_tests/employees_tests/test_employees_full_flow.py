import allure
import pytest
import requests
import random
from datetime import date, timedelta
import json
import os
import tempfile

EMPLOYEE_IDS_FILE = os.path.join(tempfile.gettempdir(), "temp_employee_ids_for_steps.json")

# Сохраняет список ID сотрудников во временный файл
def save_employee_ids_to_file(ids_list):
    with open(EMPLOYEE_IDS_FILE, 'w') as f:
        json.dump(ids_list, f)


# Загружает список ID сотрудников из временного файла
def load_employee_ids_from_file():
    if os.path.exists(EMPLOYEE_IDS_FILE):
        try:
            with open(EMPLOYEE_IDS_FILE, 'r') as f:
                ids = json.load(f)
            return ids
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    else:
        return []

# Удаляет временный файл с ID сотрудников
def clear_employee_ids_file():
    if os.path.exists(EMPLOYEE_IDS_FILE):
        os.remove(EMPLOYEE_IDS_FILE)


def _random_birthday():
    start = date(1900, 1, 1)
    end = date.today()
    days_between = (end - start).days
    random_date = start + timedelta(days=random.randint(0, days_between))
    return random_date.strftime("%Y-%m-%d")


# 12-значный ИИН: YYMMDDXXXXXZ
def _generate_valid_test_iin():
    prefix = "740312"  # YYMMDD
    middle = str(random.randint(10000, 99999))
    suffix = str(random.randint(1, 9))
    return prefix + middle + suffix


# Фикстура для очистки файла после всех тестов
@pytest.fixture(scope="module", autouse=True)
def cleanup_employee_ids_file():
    yield
    clear_employee_ids_file()


# Создание сотрудников
@allure.title("Создание 3 сотрудников")
@allure.feature("Сотрудники")
def test_employee_creation_step(
    base_url,
    auth_tokens,
    get_user_accounts,
    client_info
):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}
    created_employees = []

    employees_data = [
        {
            "name": "Тест",
            "lastName": "Сотрудников",
            "middleName": "Иванович",
            "iin": _generate_valid_test_iin(),
            "birthday": _random_birthday()
        },
        {
            "name": "Анна",
            "lastName": "Петрова",
            "middleName": None,
            "iin": _generate_valid_test_iin(),
            "birthday": _random_birthday()
        },
        {
            "name": "Олег",
            "lastName": "Сидоров",
            "middleName": "Викторович",
            "iin": _generate_valid_test_iin(),
            "birthday": _random_birthday()
        }
    ]

    with allure.step("Создать 3 сотрудников"):
        for emp_data in employees_data:
            payload = {
                "name": emp_data["name"],
                "lastName": emp_data["lastName"],
                "iin": emp_data["iin"],
                "birthday": emp_data["birthday"],
                "country": "KZ",
                "employerIinBin": client_info["iin"],
                "displayOrder": 0
            }

            if emp_data["middleName"] is not None:
                payload["middleName"] = emp_data["middleName"]

            resp = requests.post(
                f"{base_url}/api/v1/smepayments/employee-list/new",
                json=payload,
                headers=headers
            )
            assert resp.status_code == 200, f"Ошибка создания: {resp.text}"

            emp_response = resp.json()
            created_employees.append({
                "id": emp_response["id"],
                "name": emp_response["name"],
                "lastName": emp_response["lastName"],
                "iin": emp_response["iin"],
                "birthday": emp_response["birthday"],
                "middleName": emp_response.get("middleName")
            })

    # Сохраняем ID созданных сотрудников во временный файл
    created_ids = [emp["id"] for emp in created_employees]
    save_employee_ids_to_file(created_ids)

    allure.attach(
        str(created_ids),
        name="Созданные ID сотрудников",
        attachment_type=allure.attachment_type.TEXT
    )


# Проверка списка
@allure.title("Проверка списка сотрудников")
@allure.feature("Сотрудники")
def test_employee_list_check_step(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    # Загружаем ID из временного файла
    ids_to_check = load_employee_ids_from_file()
    if not ids_to_check:
        pytest.fail("Нет ID сотрудников для проверки. Проверьте шаг 1.")

    with allure.step("Проверить, что все созданные сотрудники есть в списке"):
        resp = requests.get(
            f"{base_url}/api/v1/smepayments/employee-list",
            headers=headers
        )
        assert resp.status_code == 200, f"Ошибка получения списка: {resp.text}"
        employees_list = resp.json()["employees"]


        for emp_id in ids_to_check:
            found = next((e for e in employees_list if e["id"] == emp_id), None)
            assert found is not None, f"Сотрудник с ID {emp_id} не найден в списке"
            allure.attach(
                str(found),
                name=f"Данные сотрудника {emp_id}",
                attachment_type=allure.attachment_type.JSON
            )



# Редактирование
@allure.title("Редактирование первого сотрудника")
@allure.feature("Сотрудники")
def test_employee_update_step(base_url, auth_tokens, client_info):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    # Загружаем ID из временного файла
    ids_to_check = load_employee_ids_from_file()
    if not ids_to_check:
        pytest.fail("Нет ID сотрудников для редактирования. Проверьте шаг 1.")

    employee_id = ids_to_check[0]

    updated_payload = {
        "name": "Обновлённое Имя",
        "lastName": "Обновлён",
        "middleName": "Обновлёнович",
        "iin": _generate_valid_test_iin(), # Новый уникальный ИИН
        "birthday": _random_birthday(),    # Новый день рождения
        "country": "KZ",
        "employerIinBin": client_info["iin"],
        "displayOrder": 0
    }

    with allure.step(f"Редактировать сотрудника с ID: {employee_id}"):
        resp = requests.put(
            f"{base_url}/api/v1/smepayments/employee-list/{employee_id}/edit",
            json=updated_payload,
            headers=headers
        )
        assert resp.status_code == 200, f"Ошибка редактирования: {resp.text}"

        updated_employee = resp.json()
        assert updated_employee["name"] == "Обновлённое Имя"
        assert updated_employee["lastName"] == "Обновлён"
        assert updated_employee["middleName"] == "Обновлёнович"
        assert updated_employee["iin"] == updated_payload["iin"]
        assert updated_employee["birthday"] == updated_payload["birthday"]

        allure.attach(
            str(updated_payload),
            name="Запрос на редактирование",
            attachment_type=allure.attachment_type.JSON
        )
        allure.attach(
            str(updated_employee),
            name="Ответ после редактирования",
            attachment_type=allure.attachment_type.JSON
        )


# Повторная проверка
@allure.title("Повторная проверка списка после редактирования")
@allure.feature("Сотрудники")
def test_employee_list_check_after_update_step(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    # Загружаем ID из временного файла
    ids_to_check = load_employee_ids_from_file()
    if not ids_to_check:
        pytest.fail("Нет ID сотрудников для проверки. Проверьте шаг 1.")

    with allure.step("Проверить список снова (все 3, но первый обновлён)"):
        resp = requests.get(
            f"{base_url}/api/v1/smepayments/employee-list",
            headers=headers
        )
        assert resp.status_code == 200, f"Ошибка получения списка: {resp.text}"
        employees_list = resp.json()["employees"]

        first_id = ids_to_check[0]
        other_ids = ids_to_check[1:]

        # Проверяем обновленного сотрудника
        updated_emp = next((e for e in employees_list if e["id"] == first_id), None)
        assert updated_emp is not None, f"Обновленный сотрудник с ID {first_id} не найден"
        assert updated_emp["name"] == "Обновлённое Имя"
        assert updated_emp["lastName"] == "Обновлён"
        assert updated_emp["middleName"] == "Обновлёнович"

        # Проверяем остальных сотрудников
        for emp_id in other_ids:
            found = next((e for e in employees_list if e["id"] == emp_id), None)
            assert found is not None, f"Сотрудник с ID {emp_id} не найден в списке"


# Удаление всех
@allure.title("Удаление всех созданных сотрудников")
@allure.feature("Сотрудники")
def test_employee_deletion_step(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    # Загружаем ID из временного файла
    ids_to_delete = load_employee_ids_from_file()
    if not ids_to_delete:
        return

    with allure.step("Удалить всех созданных сотрудников"):
        for emp_id in ids_to_delete:
            with allure.step(f"Удалить сотрудника с ID: {emp_id}"):
                resp = requests.delete(
                    f"{base_url}/api/v1/smepayments/employee-list/{emp_id}/delete",
                    headers=headers
                )
                assert resp.status_code == 200, f"Ошибка удаления сотрудника {emp_id}: {resp.text}"


# Проверка пустого списка
@allure.title("Проверка ошибки при пустом списке")
@allure.feature("Сотрудники")
def test_employee_list_empty_error_step(base_url, auth_tokens):
    headers = {"Authorization": f"Bearer {auth_tokens['access']}"}

    with allure.step("Проверить, что список сотрудников пуст (ожидаем 400 с ошибкой 32.10)"):
        resp = requests.get(
            f"{base_url}/api/v1/smepayments/employee-list",
            headers=headers
        )

        # Проверка удаления всех сотрудников
        assert resp.status_code == 400, f"Ожидался статус 400 при пустом списке, получен: {resp.status_code}"

        error_response = resp.json()
        assert "error" in error_response, "Ответ не содержит поля 'error'"
        assert error_response["error"] == "32.10", f"Ожидалась ошибка 32.10, получена: {error_response['error']}"

        allure.attach(
            f"Получена ошибка 400: {error_response['error']}",
            name="Ответ API при пустом списке",
            attachment_type=allure.attachment_type.JSON
        )
