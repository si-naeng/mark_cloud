# 📦 상표 검색 API (Trademark Search API)

FastAPI를 활용한 상표 데이터 검색 API 구현 과제입니다.  
사용자는 다양한 조건으로 상표를 검색할 수 있으며, 고유 식별자를 기반으로도 상표 정보를 조회할 수 있습니다.

---

## ✅ 구현된 기능 설명
이 프로젝트는 FastAPI 기반의 상표 검색 API로, 다양한 조건에 따라 JSON 형태의 상표 데이터를 필터링하고 결과를 반환하는 구조입니다.

먼저 전체 데이터를 메모리에 로딩한 뒤, 사용자로부터 전달된 검색 조건들을 기준으로 데이터를 필터링합니다. 
조건을 하나라도 만족하지 않으면 필터링에서 제외되며, 모든 조건을 만족한 상표만 결과로 포함됩니다.

특히 키워드 검색 품질 향상을 위해 정확히 일치하지 않더라도 유사한 결과를 찾을 수 있도록 
Rapidfuzz의 ratio()를 사용해 문자열 유사도 비교를 적용했습니다. 
이로 인해 예를 들어 "andy"만 입력해도 "Andy Warhol"과 같은 관련 상표를 찾을 수 있어, 검색 정확도와 사용자 편의성을 높였습니다.

### 1. `/trademarks/search` API
조건을 조합하여 상표를 검색할 수 있는 통합 검색 API입니다.

- `product_name`: 상표명 유사도 검색 (`productName`/`productNameEng`)
- `register_status`: 등록 상태 필터  (`등록`, `실효`, `거절`, `출원` 등)
- `product_main_code_list`: 상품 분류 코드 필터
- `application_number`: 출원번호 기반 검색
- `registration_number`: 등록번호 기반 검색
- `publication_number`: 공고번호 기반 검색
- `application_start_date`, `application_end_date`: 출원일자 범위 검색 (YYYY-MM-DD)
- `publication_start_date`, `publication_end_date`: 공고일자 범위 검색 (YYYY-MM-DD)

## 🔎 API 사용법 및 실행 방법

### 1. 환경 세팅
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. 서버실행
```bash
uvicorn main:app --reload
```

### 3.API 문서 확인
```
Swagger: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
```

### 4. API 사용 예시
```
GET /trademarks/search?조건1&조건2& ...

GET /trademarks/search?product_name=andywarhol 

GET /trademarks/search?product_name=andywwwhol

GET /trademarks/search?application_number=4019990001829

GET /trademarks/search?registration_number=4101049820000

GET /trademarks/search?product_name=차미&register_status=등록&productMainCodeList=30

GET /trademarks/search?application_start_date=2000-01-01&application_end_date=2005-12-31

GET /trademarks/search?publication_start_date=2008-01-01
```




## ⚙ 기술적 의사결정에 대한 설명

이번 과제에서는 FastAPI를 사용하여 JSON 파일 기반의 검색 API를 구현했습니다. 데이터 양이 작기 때문에 별도의 DB 없이 JSON을 메모리에 로딩하고 반복문을 통해 필터링하는 방식으로 처리했습니다.

### 유사도 검색 도입
- 사용자 편의를 위해 검색어 오타나 불완전 입력에도 대응하도록, `rapidfuzz` 라이브러리의 `ratio()` 함수를 활용해 유사도 기반 검색을 구현했습니다.


- 실제 구현에서는 `normalize()`를 통해 공백 제거 및 소문자 통일 후, `productName`과 `productNameEng`에 대해 **유사도 ≥ 70** 조건을 만족하면 검색 결과에 포함되도록 설계했습니다.

### 날짜 포맷 처리
- 데이터 내 `applicationDate`, `publicationDate`는 `YYYYMMDD` 형식으로 되어 있어, 사용자는 `YYYY-MM-DD`로 입력하고 내부적으로 변환하여 비교했습니다.

### 조건 기반 필터링 구조화
- 반복문 내에서 각 조건을 순차적으로 검증하며 통과한 데이터만 결과에 포함시키는 구조입니다.


- 조건 검사 로직은 passes_all_conditions() 함수 하나로 통합하고, 제품명, 날짜, 상태 코드 등은 각각 별도 함수(match_name, in_date_range)로 분리하여 가독성과 재사용성을 고려했습니다.


- 또한, 조건이 주어졌을 때만 해당 로직이 동작하도록 설계하여 불필요한 연산을 줄이고 실행 효율성도 확보했습니다.
### 향후 확장성 고려
- 현재는 경량 JSON 데이터를 대상으로 하지만, 데이터가 커지거나 검색 성능이 중요해지면 **MongoDB + Elasticsearch + Monstache** 구조로 확장하는 것을 고려하고 있습니다.


- MongoDB 같은 문서형 데이터베이스와 Elasticsearch 기반의 검색 엔진 도입을 통해 고속 검색, 유사도 검색, 자동완성 등 다양한 기능을 추가하는 구조로의 확장을 고려하고 있습니다.
### MongoDB를 사용하려는 이유

해당 JSON 데이터는 다수의 중첩 필드(예: `asignProductMainCodeList`, `viennaCodeList`, `priorityClaimNumList`)를 포함하고 있어 1차 정규화된 구조가 아닙니다.

만약 이를 관계형 DB(RDBMS)에 저장하려면 다음과 같은 문제들이 발생합니다:

- 여러 개의 테이블로 분리해야 하며,
- 각 행마다 출원번호 등 외래 키를 기준으로 JOIN이 필요하고,
- 중첩 리스트가 많기 때문에 JOIN 수가 늘어날수록 쿼리 성능 저하 및 복잡한 SQL 작성 부담이 생깁니다.

따라서 이러한 구조는 NoSQL MongoDB가 더 적합하다고 생각합니다. 

또한 Mongodb를 사용하면 중첩된 JSON 구조 그대로 저장 가능하여 설계가 단순하고, ES와 연동이 간편해집니다.



## 문제 해결 과정에서 고민했던 점

### 데이터 전처리

검색 품질을 높이기 위해 사용자 입력이 한글이든 영어든 원하는 상표를 검색할 수 있도록, productNameEng 값을 기반으로 한글 발음을 추정해 productName 필드를 보완하려 했습니다.

그런데 Hangulize나 외부 Transliterator API가 설치 오류 또는 응답 불안정 이슈가 있어, 수동 변환
밖에 답을 찾지 못했습니다.

이 과정에서 productName과 productNameEng가 모두 비어 있는 경우가 존재했는데, 해당 항목들은 단순히 결측치로 간주하고 제거하기에는 상품 분류 코드, 출원번호 등 다른 메타 정보가 여전히 유효한 데이터들이었기 때문에,
데이터 정합성을 해치지 않기 위해 전처리 및 삭제는 보류했습니다.

### 어떤 키워드를 검색에 사용할지에 대한 판단
검색 API를 설계할 때 가장 먼저 고민한 부분은 어떤 필드를 사용자 검색 키워드로 활용할 것인가였습니다.
이를 위해 먼저 전체 500건의 데이터를 대상으로 결측치 분포와 유니크한 값의 존재 여부를 분석했습니다.

검색 키워드로 제외한 필드
아래 컬럼들은 대부분의 데이터가 비어 있어, 검색 필드로 활용하기에 부적절하다고 판단했습니다.

| 컬럼명                   | 결측치 개수  |
|-------------------------|---------|
`registrationPubNumber`   | 500     |
`registrationPubDate`     | 500     |
`internationalRegDate`    | 500     |
`internationalRegNumbers` | 500     |
`priorityClaimNumList`    | 493     |
`priorityClaimDateList`   | 493     |

검색 키워드로 선택한 필드
다음은 유니크하며, 실제 사용자 검색 의도와 밀접한 항목들입니다

| 컬럼명                   | 결측치 개수  |
|-------------------------|---------|
`applicationNumber`       |    0   |
`productName`             |    287 |
`productNameEng`          |    154 |
`publicationNumber`       |    214 |
`registrationNumber`      |    106 |
`asignProductMainCodeList`|    1   |

