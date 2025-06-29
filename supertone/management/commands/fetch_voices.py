# supertone/management/commands/fetch_voices.py

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from supertone.models import Voice


class Command(BaseCommand):
    help = "GET /v1/voices API 로부터 전체 보이스 목록을 가져와 DB에 저장합니다."
    headers = {
        "Content-Type": "application/json",
        "x-sup-api-key": settings.SUPERTONE_API_KEY,
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            default="https://supertoneapi.com/v1/voices",
            help="목록을 가져올 API 엔드포인트",
        )

    def handle(self, *args, **options):
        endpoint = options["url"]
        self.stdout.write(f"▶ API 호출 (language=ko, page_size=100): {endpoint}")

        # 100개씩, language=ko 필터 적용하여 전체 아이템 순환
        params = {"language": "ko", "page_size": 100}
        all_voices = []
        page_token = None

        while True:
            if page_token:
                params["next_page_token"] = page_token

            resp = requests.get(
                endpoint, headers=self.headers, params=params, timeout=10
            )
            resp.raise_for_status()
            data = resp.json()

            items = data.get("items", [])
            all_voices.extend(items)
            self.stdout.write(
                f"DEBUG: fetched {len(items)} items, next_page_token={data.get('next_page_token')!r}"
            )

            page_token = data.get("next_page_token")
            if not page_token:
                break

        voices = all_voices
        created = updated = 0

        for item in voices:
            # If API returned just a list of voice IDs, fetch full details
            if isinstance(item, str):
                detail_url = f"{endpoint}/{item}"
                detail_resp = requests.get(detail_url, headers=self.headers, timeout=10)
                detail_resp.raise_for_status()
                item = detail_resp.json()

            vid = item.get("voice_id")
            name = item.get("name")
            styles = item.get("styles", [])
            gender = item.get("gender")
            user_case = item.get("use_case")  # API 의 use_case → 모델의 user_case
            samples = item.get("samples", [])
            models_ = item.get("models", [])

            obj, is_created = Voice.objects.update_or_create(
                voice_id=vid,
                defaults={
                    "name": name,
                    "styles": styles,
                    "gender": gender,
                    "user_case": user_case,
                    "samples": samples,
                    "models": models_,
                },
            )
            if is_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"완료: {created}건 생성, {updated}건 업데이트")
        )
