"""Module view.py for public endpoints."""

# import os
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core import config

# from sqlalchemy.orm import Session
from app.stdio import print_debug, print_error, time_now

DIR_PATH = config.DIR_PATH
templates = Jinja2Templates(directory="templates")
router = APIRouter(tags=["Public"])


@router.get("/page_404")
async def page_404(url: str = ""):
    """Function page_404."""
    _now = time_now()
    print_error(f"page_404 : {url}")
    return templates.TemplateResponse(
        "404.html",
        {"request": {}, "now": _now, "app_title": config.APP_TITLE, "url": url},
    )


@router.get("/")
async def ep_main():
    """main path"""
    _now = time_now()
    return RedirectResponse(url="/docs")


@router.get("/ping")
async def ep_ping(request: Request):
    """end point tool-ping"""
    _now = time_now()
    _header = request.headers
    # for k, v in _header.items():
    #     print(k, v)
    # return f"Time process : {time_now() - _now}"
    return {"date": f"{_now}"}


# """ggIEMuJEVBsggZVFWGJnuaUhCy6HQwsn4b2pzddEiBB""" qr-payment-ingo
def send_line_notify(message, token):
    print_debug("send_line_notify")
    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {token}",
    }
    data = {
        "message": message,
    }
    print_debug(headers)
    response = httpx.post(url, headers=headers, data=data)
    print_debug(f"send_line_notify : {response.text}")
    return response.status_code, response.text


# from time import sleep

""" {'amount': 10, 'type': 'promptpay', 'billing_details[email]': 'pksofttecg@gmail.com'}"""
"""  {'id': 'pi_3PbcaKAXQrTOcid51dnG3GB6'}"""


class StripData(BaseModel):
    api_key: str
    data: dict = {
        "amount": 10,
        "type": "promptpay",
        "billing_details[email]": "pksofttecg@gmail.com",
        "id": "000",
    }
    # qr_sn: Optional[str] = None  # แนะนำให้ใส่ = None สำหรับ Optional
    # line_token: Optional[str] = None


async def qr_strip_payment(api: str, strip_data: StripData):
    error_msg = ""
    api_key = strip_data.api_key
    payment_data = strip_data.data
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    stripe_url = "https://api.stripe.com/v1"
    success = False
    if api == "payment_promptpay":
        amount = payment_data.get("amount")
        # print_debug(payment_data)
        if amount:
            with httpx.Client() as client:
                url_payment_methods = f"{stripe_url}/payment_methods"
                url_payment_intents = f"{stripe_url}/payment_intents"
                client.headers = headers
                data = {
                    "type": payment_data.get("type"),
                    "billing_details[email]": payment_data.get("billing_details[email]"),
                }
                r = client.post(url_payment_methods, data=data)
                payment_methods = r.json()
                # print(payment_methods)
                # print("*" * 50)

                if payment_methods.get("error") or not payment_methods.get("id"):
                    return {"success": False, "error": payment_methods.get("error")}

                pm_id = payment_methods.get("id")
                data = {
                    "amount": int(amount * 100),
                    "currency": "thb",
                    "payment_method": pm_id,
                    "payment_method_types[0]": payment_data.get("type"),
                }

                r = client.post(url_payment_intents, data=data)
                payment_intent = r.json()
                # print(payment_intent)
                # print("*" * 50)

                if payment_intent.get("error") or not payment_intent.get("id"):
                    return {"success": False, "error": payment_intent.get("error")}

                r = client.post(
                    f"{url_payment_intents}/{payment_intent.get('id')}/confirm",
                )
                payment_intent = r.json()
                # print(payment_intent)
                # print("*" * 50)
                data = payment_intent.get("next_action")
                ref = None
                if data:
                    data = data["promptpay_display_qr_code"]["data"]
                    ref = payment_intent.get("id")
                    print(data)

                return {"success": True, "data": data, "ref": ref}
        else:
            error_msg = "amount not value"
    elif api == "payment_promptpay_status":
        with httpx.Client() as client:
            url_payment_intents = f"{stripe_url}/payment_intents"
            client.headers = headers
            r = client.get(
                f"{url_payment_intents}/{payment_data.get('id')}",
            )
            payment_intent = r.json()
            # print(payment_intent)
            # print("*" * 50)
            status = payment_intent.get("status")
            if status == "succeeded":
                print_debug("Payment was successful!")
                # print(payment_intent)
                success = True
                # qr_sn = strip_data.qr_sn
                # if not qr_sn:
                #     qr_sn = "ไม่ระบุชื่อ"
                # line_token = strip_data.line_token
                # if line_token:
                #     id = payment_intent.get("id")
                #     amount = int(payment_intent.get("amount")) * 0.01
                #     print_debug("line_token :" + line_token)
                #     await run_in_threadpool(
                #         send_line_notify,
                #         f"{qr_sn}\nGET-AMOUNT:{amount:0.2f}\n{id}",
                #         line_token,
                #     )
            else:
                print_debug(f"Payment status: {status}")
            return {"success": success, "data": status}

    return {"success": success, "data": None, "error": error_msg}


async def qr_beam_payment(api: str, strip_data: StripData):
    """api_beam"""
    api_key = strip_data.api_key
    payment_data = strip_data.data
    success = False
    beam_user, beam_api_key = api_key.split("@")
    is_beam_x_header = True
    if beam_user.startswith("&"):
        beam_user = beam_user[1:]
        is_beam_x_header = False

    headers = {
        "Content-Type": "application/json",
    }
    if is_beam_x_header:
        headers["X-Beam-Partner-ID"] = "pnr_2uIiuWQajUeO06RujjxYiILcAsL"
    if api == "payment_promptpay":
        amount = payment_data.get("amount")
        _now_z = datetime.now() + timedelta(minutes=10)
        expiresAt = _now_z.strftime("%Y-%m-%dT%H:%M:%S")
        expiresAt = expiresAt.split(".")[0] + "Z"
        amount = amount * 100
        payload = {
            "amount": amount,
            "currency": "THB",
            "paymentMethod": {
                "paymentMethodType": "QR_PROMPT_PAY",
                "qrPromptPay": {"expiresAt": expiresAt},
            },
            "referenceId": str(_now_z.timestamp()),
            # "returnUrl": pay_success_url,
        }
        print_debug(payload)
        try:
            # """https://playground-partner-api.beamdata.co/api/v1/charges"""
            url_beam_server_api = "https://api.beamcheckout.com/api/v1/charges"

            auth = httpx.BasicAuth(beam_user, beam_api_key)
            with httpx.Client(auth=auth) as client:
                client.headers = headers
                r = client.post(
                    url_beam_server_api,
                    json=payload,
                )
                rep_data = r.json()
                print_debug(rep_data)
                error_code = rep_data.get("code")
                if error_code:
                    return {
                        "success": False,
                        "error_code": error_code,
                        "msg": rep_data.get("message"),
                    }
                chargeId = rep_data.get("chargeId")
                if chargeId:
                    ref = None
                    data = rep_data.get("encodedImage").get("rawData")
                    ref = chargeId
                    print(data)
                    return {"success": True, "data": data, "ref": ref}
                error_msg = "not chargeId"

        except Exception as err:
            print_error(str(err))
            error_msg = str(err)

    elif api == "payment_promptpay_status":
        # return {"success": success, "error": error_msg}
        purchaseId = payment_data.get("id")
        if purchaseId:
            auth = httpx.BasicAuth(beam_user, beam_api_key)
            # https://api.beamcheckout.com/api/v1/charges/id--xxxx
            url_beam_server_api = f"https://api.beamcheckout.com/api/v1/charges/{purchaseId}"
            print_debug(url_beam_server_api)
            if url_beam_server_api:
                try:
                    with httpx.Client(auth=auth) as client:
                        client.headers = headers
                        r = client.get(
                            url_beam_server_api,
                        )
                        rep_data = r.json()
                        print_debug(rep_data)
                        status = rep_data.get("status")
                        if status == "SUCCEEDED":
                            success = True
                            status = "succeeded"
                            return {"success": success, "data": status}

                        return {"success": False, "data": status}

                except Exception as err:
                    error_msg = str(err)
            else:
                success = False
                error_msg = "not url_beam_server_api"

    else:
        error_msg = "not api"
    return {"success": success, "error": error_msg}


@router.post("/strip/{api}")
async def ep_proxy(
    request: Request,
    # strip_data: StripData,
    api: str,
):
    """ep_post_payment"""
    _now = time_now()
    payload = await request.json()
    print_debug(payload)
    strip_data = StripData(api_key=payload.get("api_key"), data=payload.get("data"))
    print_debug(strip_data)
    api_key = strip_data.api_key
    if api_key.find("@") > 0:
        return await qr_beam_payment(api, strip_data)

    return await qr_strip_payment(api, strip_data)
