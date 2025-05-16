from fastapi import FastAPI, Query
from typing import Optional
from datetime import datetime
import json
from rapidfuzz.fuzz import ratio

app = FastAPI()

with open("trademark_sample.json", encoding="utf-8") as f:
    data = json.load(f)

def normalize(text: str) -> str:
    return text.replace(" ", "").lower()

def is_similar_or_contains(product_name: str, target: str, threshold: float = 70.0) -> bool:
    if product_name in target:
        return True
    return ratio(product_name, target) >= threshold

def parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y%m%d")  # 데이터는 YYYYMMDD
    except:
        return None

@app.get("/trademarks/search")
async def search_trademarks(
    product_name: Optional[str] = Query(None, description="검색어 (한글 또는 영어)"),
    register_status: Optional[str] = Query(None, description="등록 상태 필터 (등록, 실효, 거절, 출원 등)"),
    product_main_code_list: Optional[str] = Query(None, description="상품 주 분류 코드 (예: 30, 41 등)"),
    application_number: Optional[str] = Query(None, description="출원번호"),
    registration_number: Optional[str] = Query(None, description="등록번호"),
    publication_number: Optional[str] = Query(None, description="공고번호"),
    application_start_date: Optional[str] = Query(None, description="출원 시작일 (YYYY-MM-DD)"),
    application_end_date: Optional[str] = Query(None, description="출원 종료일 (YYYY-MM-DD)"),
    publication_start_date: Optional[str] = Query(None, description="공고 시작일 (YYYY-MM-DD)"),
    publication_end_date: Optional[str] = Query(None, description="공고 종료일 (YYYY-MM-DD)")
):
    if not any([
        product_name, register_status, product_main_code_list, application_number,
        registration_number, publication_number, application_start_date,
        application_end_date, publication_start_date, publication_end_date
    ]):
        return {"message": "검색 조건을 최소 하나 이상 입력해주세요."}

    # 사용자 입력은 YYYY-MM-DD → YYYYMMDD로 정규화
    app_start = parse_date(application_start_date.replace("-", "")) if application_start_date else None
    app_end = parse_date(application_end_date.replace("-", "")) if application_end_date else None
    pub_start = parse_date(publication_start_date.replace("-", "")) if publication_start_date else None
    pub_end = parse_date(publication_end_date.replace("-", "")) if publication_end_date else None

    results = []

    for item in data:
        if application_number and item.get("applicationNumber") != application_number:
            continue
        if registration_number and registration_number not in (item.get("registrationNumber") or []):
            continue
        if publication_number and item.get("publicationNumber") != publication_number:
            continue

        # 날짜 필터 - applicationDate
        app_date = parse_date(item.get("applicationDate") or "")
        if app_start and (not app_date or app_date < app_start):
            continue
        if app_end and (not app_date or app_date > app_end):
            continue

        # 날짜 필터 - publicationDate
        pub_date = parse_date(item.get("publicationDate") or "")
        if pub_start and (not pub_date or pub_date < pub_start):
            continue
        if pub_end and (not pub_date or pub_date > pub_end):
            continue

        if product_name:
            name_norm = normalize(product_name)
            name_kor = normalize(str(item.get("productName") or ""))
            name_eng = normalize(str(item.get("productNameEng") or ""))
            kor_match = name_kor and is_similar_or_contains(name_norm, name_kor)
            eng_match = name_eng and is_similar_or_contains(name_norm, name_eng)
            if not (kor_match or eng_match):
                continue

        if register_status and item.get("registerStatus") != register_status:
            continue

        if product_main_code_list:
            code_list = item.get("asignProductMainCodeList") or []
            if product_main_code_list not in code_list:
                continue

        results.append({
            "productName": item.get("productName"),
            "productNameEng": item.get("productNameEng")
        })

        # results.append(item)

    return results[:100]
