from fastapi import FastAPI, Query
from typing import Optional, Dict, Any
from datetime import datetime
import json
from rapidfuzz.fuzz import ratio

app = FastAPI()

with open("trademark_sample.json", encoding="utf-8") as f:
    data = json.load(f)

# 공백 제거 및 소문자 변환
def normalize(text: str) -> str:
    return text.replace(" ", "").lower()

# 유사도 검사
def is_similar_or_contains(product_name: str, target: str, threshold: float = 70.0) -> bool:
    if product_name in target:
        return True
    return ratio(product_name, target) >= threshold

# 날짜 파싱 (YYYYMMDD)
def parse_date(date_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return None

# 날짜 범위 비교
def in_date_range(date_str: str, start: Optional[str], end: Optional[str]) -> bool:
    if not date_str:
        return True  # 날짜가 없으면 통과시키도록 설정
    date = parse_date(date_str)
    if not date:
        return False
    if start:
        start_date = parse_date(start.replace("-", ""))
        if date < start_date:
            return False
    if end:
        end_date = parse_date(end.replace("-", ""))
        if date > end_date:
            return False
    return True

# 키워드 필터
def match_name(item: Dict[str, Any], product_name: str) -> bool:
    name_norm = normalize(product_name)
    name_kor = normalize(str(item.get("productName") or ""))
    name_eng = normalize(str(item.get("productNameEng") or ""))
    return (
        name_kor and is_similar_or_contains(name_norm, name_kor)
    ) or (
        name_eng and is_similar_or_contains(name_norm, name_eng)
    )


# 전체 조건 필터
def passes_all_conditions(item: Dict[str, Any], filters: Dict[str, Optional[str]]) -> bool:
    if filters.get("application_number") and (item.get("applicationNumber") != filters["application_number"]):
        return False
    if filters.get("registration_number") and (filters["registration_number"] not in (item.get("registrationNumber")) or []):
        return False
    if filters.get("publication_number") and (item.get("publicationNumber") != filters["publication_number"]):
        return False
    if filters.get("product_name") and not (match_name(item, filters["product_name"])):
        return False
    if filters.get("register_status") and (item.get("registerStatus") != filters["register_status"]):
        return False
    if filters.get("product_main_code_list"):
        code_list = item.get("asignProductMainCodeList") or []
        if filters["product_main_code_list"] not in code_list:
            return False
    if not in_date_range(item.get("applicationDate", ""), filters.get("application_start_date"), filters.get("application_end_date")):
        return False
    if not in_date_range(item.get("publicationDate", ""), filters.get("publication_start_date"), filters.get("publication_end_date")):
        return False
    return True

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

    filters = {
        "product_name": product_name,
        "register_status": register_status,
        "product_main_code_list": product_main_code_list,
        "application_number": application_number,
        "registration_number": registration_number,
        "publication_number": publication_number,
        "application_start_date": application_start_date,
        "application_end_date": application_end_date,
        "publication_start_date": publication_start_date,
        "publication_end_date": publication_end_date,
    }

    results = []
    for item in data:
        if passes_all_conditions(item, filters):
            result_item = {
                "productName": item.get("productName"),
                "productNameEng": item.get("productNameEng")
            }
            results.append(result_item)

    return results[:100]
