import pytest
from fastapi.testclient import TestClient

from app.api import quran
from app.main import app


@pytest.mark.parametrize("number", [0, 115])
def test_surah_number_must_be_valid(number):
    with TestClient(app) as client:
        response = client.get(f"/api/v1/quran/surah/{number}")
    assert response.status_code == 422


def test_translation_edition_is_allow_list_only():
    with TestClient(app) as client:
        response = client.get("/api/v1/quran/surah/1?translation=unknown-edition")
    assert response.status_code == 422


@pytest.mark.anyio
async def test_surah_reader_aligns_arabic_and_translation(monkeypatch):
    async def fake_provider(path):
        return {
            "code": 200,
            "data": [
                {
                    "number": 1, "name": "سُورَةُ ٱلْفَاتِحَةِ",
                    "englishName": "Al-Faatiha",
                    "englishNameTranslation": "The Opening",
                    "numberOfAyahs": 1, "revelationType": "Meccan",
                    "ayahs": [{"numberInSurah": 1, "text": "بِسْمِ اللَّهِ", "juz": 1, "page": 1}],
                },
                {
                    "ayahs": [{"numberInSurah": 1, "text": "اللہ کے نام سے"}],
                },
            ],
        }

    monkeypatch.setattr(quran, "_provider_get", fake_provider)
    with TestClient(app) as client:
        response = client.get("/api/v1/quran/surah/1")
    assert response.status_code == 200
    assert response.json()["ayahs"][0]["arabic"] == "بِسْمِ اللَّهِ"
    assert response.json()["ayahs"][0]["translation"] == "اللہ کے نام سے"


@pytest.mark.anyio
async def test_surah_reader_rejects_misaligned_ayahs(monkeypatch):
    async def fake_provider(path):
        return {
            "code": 200,
            "data": [
                {"number": 1, "name": "Arabic", "englishName": "One", "englishNameTranslation": "One",
                 "numberOfAyahs": 1, "revelationType": "Meccan",
                 "ayahs": [{"numberInSurah": 1, "text": "آية"}]},
                {"ayahs": [{"numberInSurah": 2, "text": "Translation"}]},
            ],
        }

    monkeypatch.setattr(quran, "_provider_get", fake_provider)
    with TestClient(app) as client:
        response = client.get("/api/v1/quran/surah/1")
    assert response.status_code == 502
