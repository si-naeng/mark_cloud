# 📦 상표 검색 API (Trademark Search API)

FastAPI를 활용한 상표 데이터 검색 API 구현 과제입니다.  
사용자는 다양한 조건으로 상표를 검색할 수 있으며, 고유 식별자를 기반으로도 상표 정보를 조회할 수 있습니다.

---

## ✅ 구현된 기능 설명

### 1. `/trademarks/search` API
조건을 조합하여 상표를 검색할 수 있는 통합 검색 API입니다.

- `product_name`: 상표명 유사도 검색 (`productName`/`productNameEng`)
- `register_status`: 등록 상태 필터  (`등록`, `실효`, `거절`, `출원` 등)
- `productMainCodeList`: 상품 분류 코드 필터
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

GET /trademarks/search?registration_number=4100136490000

GET /trademarks/search?product_name=차미&register_status=등록&productMainCodeList=30

GET /trademarks/search?application_start_date=2000-01-01&application_end_date=2005-12-31

GET /trademarks/search?publication_start_date=2008-01-01
```



## ⚙ 기술적 의사결정에 대한 설명
사용자 경험 개선을 위해 유사도 검색을 도입했습니다.
rapidfuzz 라이브러리를 선택한 이유는, 정확도뿐 아니라 속도 면에서도 뛰어나기 때문입니다.
fuzzywuzzy 대비 최대 10배 이상의 성능이며, 이를 통해 es) andy → andy warhol, andywwwhol → andy warhol 
일부 검색어 입력과 오타를 포함하고 있어도 관련 데이터를 탐색할 수 있도록 구현했습니다.

이번 과제에서는 데이터의 양이 비교적 적었기 때문에, 
JSON 파일을 메모리에 로딩한 후 단순 반복(iteration)을 통해 검색을 수행했습니다. 
이 방식은 개발과 테스트가 간단하다는 장점이 있지만, 
데이터 양이 많아지거나 구조가 복잡해질 경우에는 성능 및 관리 측면에서 한계가 있습니다.
 
실제 데이터를 분석해보니, 전체 구조가 1차 정규화가 되지 않은 상태였고, 
이 상태에서 SQL 기반 RDBMS에 저장하려면 여러 개의 테이블로 분리하고 다수의 조인을 
수행해야 했습니다. 이는 검색 성능 저하를 유발할 수 있고 유지보수 비용도 
높아질 가능성이 있다고 판단했습니다.

따라서 향후 데이터가 늘어나면 전처리를 통한 정규화는 수행하지 않고, 
문서 지향 저장 방식에 적합한 NoSQL인 MongoDB를 사용하는게 좋다고 생각 했습니다. 
이후에는 Monstache를 활용해 데이터를 Elasticsearch와 실시간 동기화하여, 
사용자 검색 경험을 최적화할 수 있는 구조로 발전시킬 계획입니다.

결론적으로, 현재는 경량화된 구조로 빠르게 개발하되, 추후 데이터 규모 증가에 대비해 확장성과 검색 성능을 동시에 고려한 구조로 설계 방향을 설정했습니다.


## 문제 해결 과정에서 고민했던 점

### 데이터 전처리
영어 발음(외래어 표기) 변환 지원
사용자 입력이 한글이든 영어든 원하는 상표를 검색할 수 있도록 하기 위해, productNameEng 값을 기반으로 한글 발음을 추정해 productName 필드를 보완하려 했습니다.
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

### 검색 정확도
검색 품질을 높이기 위해 외래어 표기를 자동으로 생성해 넣고 싶었으나, 
Hangulize나 외부 Transliterator API가 설치 오류 또는 응답 불안정 이슈가 있어, 수동 변환
밖에 답을 찾지 못했습니다.