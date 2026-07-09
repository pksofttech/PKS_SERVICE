"""Module view.py for public endpoints."""

import base64
import json
import os

# Disable mkldnn for PaddleOCR to avoid NotImplementedError on CPU
os.environ["FLAGS_use_mkldnn"] = "0"
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

import io

import httpx
import numpy as np
from dotenv import load_dotenv
from fastapi import APIRouter, File, HTTPException, UploadFile
from paddleocr import PaddleOCR
from PIL import Image
from pydantic import BaseModel, Field, ValidationError

from app.stdio import print_error, time_now

# Initialize PaddleOCR engine once globally
ocr_engine = PaddleOCR(lang="th")

router = APIRouter(prefix="/lpr", tags=["Public LPR Service"])

load_dotenv()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


class LPRResponseSchema(BaseModel):
    license_plate: str = Field(description="เลขทะเบียนรถที่อ่านได้ เช่น 1กข 1234 หรือ กข 56")
    province: str | None = Field(
        default=None, description="จังหวัดบนป้ายทะเบียน เช่น กรุงเทพมหานคร, เชียงใหม่ หากอ่านไม่ออกให้ใส่ null"
    )
    confidence_score: float = Field(ge=0.0, le=1.0, description="คะแนนความมั่นใจในการอ่านค่าของโมเดล 0.0 ถึง 1.0")


class IDCardResponseSchema(BaseModel):
    id_number: str | None = Field(
        default=None, description="เลขประจำตัวประชาชน 13 หลัก หากอ่านไม่ออกหรือไม่มีให้ใส่ null"
    )
    thai_name: str | None = Field(
        default=None, description="ชื่อและนามสกุลภาษาไทย เช่น นายสมชาย รักดี หากอ่านไม่ออกหรือไม่มีให้ใส่ null"
    )
    english_name: str | None = Field(
        default=None, description="ชื่อและนามสกุลภาษาอังกฤษ เช่น Mr. Somchai Rakdee หากอ่านไม่ออกหรือไม่มีให้ใส่ null"
    )
    license_number: str | None = Field(
        default=None, description="เลขที่ใบอนุญาตขับรถ/ขับขี่ (ถ้ามี) หากอ่านไม่ออกหรือไม่มีให้ใส่ null"
    )
    expiry_date: str | None = Field(
        default=None, description="วันสิ้นอายุหรือวันหมดอายุของบัตร หากอ่านไม่ออกหรือไม่มีให้ใส่ null"
    )


@router.post("/lpr_read_plate")
async def ep_lpr_read_plate(file: UploadFile = File(...)):
    """Read LPR plate using Gemini 1.5 Flash via Direct HTTP REST API."""

    _now = time_now()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured in .env")

    try:
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")

        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Image file is too large. Maximum size is 5 MB.")

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{os.getenv('GEMINI_MODEL')}:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": file.content_type,
                                "data": base64_image,
                            }
                        },
                        {
                            "text": (
                                "Extract the Thai license plate number and province from this image. "
                                "If the license plate or province is unclear, do not guess. "
                                "Return null for province if unreadable. "
                                "Return confidence_score between 0.0 and 1.0."
                            )
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "license_plate": {
                            "type": "STRING",
                            "description": "เลขทะเบียนรถที่อ่านได้ เช่น 1กข 1234 หรือ กข 56 หากอ่านไม่ออกให้ใส่ค่าว่าง",
                        },
                        "province": {
                            "type": "STRING",
                            "nullable": True,
                            "description": "จังหวัดบนป้ายทะเบียน เช่น กรุงเทพมหานคร, เชียงใหม่ หากอ่านไม่ออกให้ใส่ null",
                        },
                        "confidence_score": {
                            "type": "NUMBER",
                            "description": "คะแนนความมั่นใจในการอ่านค่าของโมเดล 0.0 ถึง 1.0",
                        },
                    },
                    "required": [
                        "license_plate",
                        "province",
                        "confidence_score",
                    ],
                },
                "temperature": 0.0,
            },
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are a precise License Plate Recognition system specialized in Thai license plates. "
                            "Analyze the image carefully. "
                            "Do not guess unreadable characters. "
                            "Output only valid JSON according to the schema. "
                            "Do not include markdown or explanation."
                        )
                    }
                ]
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            res = await httpx_client.post(url, json=payload)

        if res.status_code != 200:
            print_error(f"Gemini API Error Response: {res.text}")
            raise HTTPException(status_code=502, detail="Gemini remote API error")

        response_json = res.json()

        try:
            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            print_error(f"Unexpected Gemini Response: {response_json}")
            raise HTTPException(status_code=502, detail="Unexpected Gemini response format")

        try:
            result_data = json.loads(text_response)
        except json.JSONDecodeError:
            print_error(f"Invalid JSON from Gemini: {text_response}")
            raise HTTPException(status_code=502, detail="Gemini returned invalid JSON")

        try:
            parsed = LPRResponseSchema(**result_data)
        except ValidationError as e:
            print_error(f"Gemini response validation error: {e}")
            raise HTTPException(status_code=502, detail="Gemini response schema validation failed")

        return {
            "status": "success",
            "timestamp": _now.isoformat(),
            "data": parsed.model_dump(),
        }

    except HTTPException:
        raise

    except httpx.TimeoutException:
        print_error("Gemini API timeout")
        raise HTTPException(status_code=504, detail="Gemini API timeout")

    except httpx.RequestError as e:
        print_error(f"Gemini request error: {str(e)}")
        raise HTTPException(status_code=502, detail="Cannot connect to Gemini API")

    except Exception as e:
        print_error(f"LPR Direct HTTP Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"LPR Processing Error: {str(e)}")


def extract_id_card_info(texts: list[str]) -> dict:
    """Helper to extract structured info from Thai ID card and Driver's License texts."""
    import re

    info = {
        "id_number": None,
        "thai_name": None,
        "english_name": None,
        "license_number": None,
        "expiry_date": None,
    }

    # 1. Look for ID number (13 digits)
    for text in texts:
        cleaned = re.sub(r"\D", "", text)
        if len(cleaned) == 13:
            info["id_number"] = cleaned
            break

    if not info["id_number"]:
        all_digits = re.sub(r"\D", "", "".join(texts))
        match = re.search(r"\d{13}", all_digits)
        if match:
            info["id_number"] = match.group(0)

    # 2. Look for Thai names (prefixed by title like นาย/นาง/นางสาว)
    thai_title_pattern = re.compile(r"(นาย|นาง|นางสาว|ด\.ช\.|ด\.ญ\.)\s*([ก-๙]+)\s+([ก-๙]+)")
    for text in texts:
        m = thai_title_pattern.search(text)
        if m:
            info["thai_name"] = m.group(0).strip()
            break

    # 3. Look for English names
    mr_pattern = re.compile(r"(Mr\.|Mrs\.|Miss|Ms\.)\s*([a-zA-Z\s]+)")
    for text in texts:
        m = mr_pattern.search(text)
        if m:
            info["english_name"] = m.group(0).strip()
            break

    if not info["english_name"]:
        for text in texts:
            if "Name" in text:
                name_part = text.split("Name")[-1].strip()
                if name_part:
                    info["english_name"] = name_part
                    break

    # 4. Look for Driver's License Number
    license_pattern = re.compile(r"(เลขที่ใบอนุญาต|ใบอนุญาตขับขี่เลขที่|No\.)\s*([0-9\-/]+)", re.IGNORECASE)
    for text in texts:
        m = license_pattern.search(text)
        if m:
            info["license_number"] = m.group(2).strip()
            break

    # 5. Look for Expiry Date
    expiry_pattern = re.compile(r"(วันสิ้นอายุ|วันหมดอายุ|Expiry\s+Date|Exp\.)\s*([\w\s\-/]+)", re.IGNORECASE)
    for text in texts:
        m = expiry_pattern.search(text)
        if m:
            info["expiry_date"] = m.group(2).strip()
            break

    return info


@router.post("/ocr_id_card_paddle")
async def ep_ocr_id_card_paddle(file: UploadFile = File(...), use_crop: bool = True, fallback: bool = True):
    """Perform OCR on ID card using PaddleOCR.
    If use_crop is True, crops the ID number and Name regions for a 2x+ speedup.
    If fallback is True, falls back to full-image OCR if cropped regions do not yield a citizen ID.
    """
    _now = time_now()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")

        image = Image.open(io.BytesIO(image_bytes))
        W, H = image.size

        rec_texts = []
        rec_scores = []
        extracted = {
            "id_number": None,
            "thai_name": None,
            "english_name": None,
        }

        from fastapi.concurrency import run_in_threadpool

        if use_crop:
            # Crop 1: Citizen ID Number (เลขประจำตัวประชาชน)
            # Typically at top-right: X (35% to 88%), Y (8% to 22%)
            id_crop = image.crop((int(W * 0.35), int(H * 0.08), int(W * 0.88), int(H * 0.22)))

            # Crop 2: Thai Name / English Name
            # Typically at middle-left/center: X (15% to 70%), Y (20% to 40%)
            name_crop = image.crop((int(W * 0.15), int(H * 0.20), int(W * 0.70), int(H * 0.40)))

            # Run prediction on crops in parallel/batch
            crops_np = [np.array(id_crop), np.array(name_crop)]
            results = await run_in_threadpool(ocr_engine.predict, crops_np)

            id_texts = results[0].get("rec_texts", []) if len(results) > 0 else []
            id_scores = results[0].get("rec_scores", []) if len(results) > 0 else []

            name_texts = results[1].get("rec_texts", []) if len(results) > 1 else []
            name_scores = results[1].get("rec_scores", []) if len(results) > 1 else []

            rec_texts = id_texts + name_texts
            rec_scores = [float(s) for s in (id_scores + name_scores)]
            extracted = extract_id_card_info(rec_texts)

            # Fallback to full-image OCR if enabled and we couldn't find a valid 13-digit ID number
            if fallback and not extracted["id_number"]:
                full_results = await run_in_threadpool(ocr_engine.predict, np.array(image))
                if full_results:
                    first_page = full_results[0]
                    rec_texts = first_page.get("rec_texts", [])
                    rec_scores = [float(s) for s in first_page.get("rec_scores", [])]
                    extracted = extract_id_card_info(rec_texts)
        else:
            # Full image OCR
            result = await run_in_threadpool(ocr_engine.predict, np.array(image))
            if result:
                first_page = result[0]
                rec_texts = first_page.get("rec_texts", [])
                rec_scores = [float(score) for score in first_page.get("rec_scores", [])]
                extracted = extract_id_card_info(rec_texts)

        return {
            "status": "success",
            "timestamp": _now.isoformat(),
            "data": {"raw_texts": rec_texts, "raw_scores": rec_scores, "extracted_info": extracted},
        }

    except Exception as e:
        print_error(f"OCR ID Card Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR ID Card Processing Error: {str(e)}")


@router.post("/ocr_id_card")
async def ep_ocr_id_card(file: UploadFile = File(...), use_crop: bool = True, fallback: bool = True):
    """Perform OCR on ID card or Driver's License using Gemini 1.5 Flash via Direct HTTP REST API."""

    _now = time_now()

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image.")

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured in .env")

    try:
        image_bytes = await file.read()

        if not image_bytes:
            raise HTTPException(status_code=400, detail="Uploaded image is empty.")

        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="Image file is too large. Maximum size is 5 MB.")

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        model_name = os.getenv("GEMINI_MODEL") or "gemini-1.5-flash"
        url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/{model_name}:generateContent?key={api_key}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": file.content_type,
                                "data": base64_image,
                            }
                        },
                        {
                            "text": (
                                "Extract information from this Thai ID card or Driver's license. "
                                "Return null for fields that are unreadable or missing. "
                                "Do not guess names or digits if they are not clear."
                            )
                        },
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "id_number": {
                            "type": "STRING",
                            "description": "เลขประจำตัวประชาชน 13 หลัก หากอ่านไม่ออกหรือไม่มีให้ใส่ null",
                            "nullable": True,
                        },
                        "thai_name": {
                            "type": "STRING",
                            "description": "ชื่อและนามสกุลภาษาไทย เช่น นายสมชาย รักดี หากอ่านไม่ออกหรือไม่มีให้ใส่ null",
                            "nullable": True,
                        },
                        "english_name": {
                            "type": "STRING",
                            "description": "ชื่อและนามสกุลภาษาอังกฤษ เช่น Mr. Somchai Rakdee หากอ่านไม่ออกหรือไม่มีให้ใส่ null",
                            "nullable": True,
                        },
                        "license_number": {
                            "type": "STRING",
                            "description": "เลขที่ใบอนุญาตขับรถ/ขับขี่ (ถ้ามี) หากอ่านไม่ออกหรือไม่มีให้ใส่ null",
                            "nullable": True,
                        },
                        "expiry_date": {
                            "type": "STRING",
                            "description": "วันสิ้นอายุหรือวันหมดอายุของบัตร หากอ่านไม่ออกหรือไม่มีให้ใส่ null",
                            "nullable": True,
                        },
                    },
                    "required": [
                        "id_number",
                        "thai_name",
                        "english_name",
                        "license_number",
                        "expiry_date",
                    ],
                },
                "temperature": 0.0,
            },
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are a precise Thai ID card and Driver's license OCR system. "
                            "Analyze the image carefully. "
                            "Do not guess unreadable characters. "
                            "Output only valid JSON according to the schema. "
                            "Do not include markdown or explanation."
                        )
                    }
                ]
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as httpx_client:
            res = await httpx_client.post(url, json=payload)

        if res.status_code != 200:
            print_error(f"Gemini API Error Response: {res.text}")
            raise HTTPException(status_code=502, detail="Gemini remote API error")

        response_json = res.json()

        try:
            text_response = response_json["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            print_error(f"Unexpected Gemini Response: {response_json}")
            raise HTTPException(status_code=502, detail="Unexpected Gemini response format")

        try:
            result_data = json.loads(text_response)
        except json.JSONDecodeError:
            print_error(f"Invalid JSON from Gemini: {text_response}")
            raise HTTPException(status_code=502, detail="Gemini returned invalid JSON")

        try:
            parsed = IDCardResponseSchema(**result_data)
        except ValidationError as e:
            print_error(f"Gemini response validation error: {e}")
            raise HTTPException(status_code=502, detail="Gemini response schema validation failed")

        return {
            "status": "success",
            "timestamp": _now.isoformat(),
            "data": {
                "raw_texts": [],
                "raw_scores": [],
                "extracted_info": parsed.model_dump(),
            },
        }

    except HTTPException:
        raise

    except httpx.TimeoutException:
        print_error("Gemini API timeout")
        raise HTTPException(status_code=504, detail="Gemini API timeout")

    except httpx.RequestError as e:
        print_error(f"Gemini request error: {str(e)}")
        raise HTTPException(status_code=502, detail="Cannot connect to Gemini API")

    except Exception as e:
        print_error(f"OCR ID Card Direct HTTP Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OCR ID Card Processing Error: {str(e)}")
