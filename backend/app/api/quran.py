"""Read-only Quran endpoints backed by AlQuran.cloud.

Arabic Quran text and translations are passed through from the provider; this API
does not generate, rewrite, or correct scripture with an AI model.
"""
import logging

import httpx
from fastapi import APIRouter, HTTPException, Path, Query

router = APIRouter(prefix="/quran", tags=["Quran"])
logger = logging.getLogger(__name__)
BASE_URL = "https://api.alquran.cloud/v1"
EDITIONS = ("quran-uthmani", "ur.jalandhry", "en.sahih")


async def _provider_get(path: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0, connect=5.0)) as client:
            response = await client.get(f"{BASE_URL}{path}")
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        logger.exception("Quran content provider request failed.")
        raise HTTPException(
            status_code=502,
            detail="Quran content is temporarily unavailable. Please try again later.",
        )
    if payload.get("code") != 200 or "data" not in payload:
        raise HTTPException(status_code=502, detail="Quran content provider returned an unexpected response.")
    return payload


@router.get("/surahs")
async def list_surahs():
    """Return the provider's Surah index, including Arabic and English names."""
    payload = await _provider_get("/surah")
    return {"source": "AlQuran.cloud", "surahs": payload["data"]}


@router.get("/surah/{surah_number}")
async def read_surah(
    surah_number: int = Path(ge=1, le=114),
    translation: str = Query(default="ur.jalandhry", pattern="^(ur\\.jalandhry|en\\.sahih)$"),
):
    """Return Arabic text plus one allow-listed translation, aligned by Ayah number."""
    editions = "quran-uthmani," + translation
    payload = await _provider_get(f"/surah/{surah_number}/editions/{editions}")
    data = payload["data"]
    if not isinstance(data, list) or len(data) != 2:
        raise HTTPException(status_code=502, detail="Quran content provider returned incomplete editions.")

    arabic, translated = data[0], data[1]
    arabic_ayahs, translated_ayahs = arabic.get("ayahs", []), translated.get("ayahs", [])
    if len(arabic_ayahs) != len(translated_ayahs):
        raise HTTPException(status_code=502, detail="Quran text and translation could not be aligned safely.")

    ayahs = []
    for original, translated_ayah in zip(arabic_ayahs, translated_ayahs):
        if original.get("numberInSurah") != translated_ayah.get("numberInSurah"):
            raise HTTPException(status_code=502, detail="Quran Ayah numbering did not match.")
        ayahs.append({
            "number": original["numberInSurah"],
            "arabic": original["text"],
            "translation": translated_ayah["text"],
            "juz": original.get("juz"),
            "page": original.get("page"),
        })
    return {
        "source": "AlQuran.cloud",
        "surah": {
            "number": arabic["number"],
            "name": arabic["name"],
            "english_name": arabic["englishName"],
            "english_name_translation": arabic["englishNameTranslation"],
            "number_of_ayahs": arabic["numberOfAyahs"],
            "revelation_type": arabic["revelationType"],
        },
        "translation_edition": translation,
        "ayahs": ayahs,
    }
