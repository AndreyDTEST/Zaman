from payment_configs import PAYMENT_TYPES
import uuid
import datetime

def get_last_month_context():
    today = datetime.date.today()
    prev = (today.replace(day=1) - datetime.timedelta(days=1))
    period = prev.strftime("%m%Y")
    month_ru = [
        "январь", "февраль", "март", "апрель", "май", "июнь",
        "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
    ][prev.month - 1]
    return period, month_ru, prev.year

def build_budget_payment_payload(
    payment_type_key: str,
    payer_account: str,
    client_info: dict,
    period: str,
    month_ru: str,
    year: int,
    total_amount: str = "100.00"
):
    config = PAYMENT_TYPES[payment_type_key]
    purpose_details = config["description_template"].format(month_ru, year)
    signatory_a = f"{client_info['surname']} {client_info['name']} {client_info['patronymic']}"

    # Общий базовый блок
    payment_data = {
        "paymentPeriod": period,
        "purposeCode": config["purposeCode"],
        "purposeDetails": purpose_details,
        "amount": total_amount,
        "payerAccount": payer_account,
        "signatoryA": signatory_a
    }

    if config["type"] == "employee_based":
        # Стандартный платёж (ОПВ, ОПВР, СО и т.д.)
        employee = {
            "name": client_info["name"],
            "middleName": client_info["patronymic"],
            "lastName": client_info["surname"],
            "iin": client_info["iin"],
            "birthday": client_info["birthdate"],
            "country": "KZ",
            "amount": total_amount,
            "valuePeriod": period
        }
        payment_data["employees"] = [employee]

    elif config["type"] == "tax_ipn":
        # ИПН с beneficiary
        payment_data.update({
            "beneficiaryBINIIN": config["beneficiaryBINIIN"],
            "beneficiaryName": config["beneficiaryName"],
            "kbk": config["kbk"]
        })

    else:
        raise ValueError(f"Неизвестный тип платежа: {config['type']}")

    return {
        "paymentCode": config["paymentCode"],
        "idempotencyKey": str(uuid.uuid4()),
        "paymentData": payment_data
    }