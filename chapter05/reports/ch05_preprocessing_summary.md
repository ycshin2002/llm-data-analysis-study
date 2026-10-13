# Chapter 5 데이터 전처리 요약

## 전처리 결과 파일

- customers_clean.csv
- products_clean.csv
- orders_clean.csv
- order_items_clean.csv

## 전처리 전후 데이터 크기

```text
    dataset  rows_raw  columns_raw  rows_processed  columns_processed
  customers       152            6             150                  6
   products       102            4              96                  4
     orders       302            5             300                  7
order_items       765            5             752                  6
```

## 파일 간 관계 점검 결과

```text
                                               check  invalid_count
  orders.customer_id exists in customers.customer_id              2
      order_items.order_id exists in orders.order_id              2
order_items.product_id exists in products.product_id             26
```

## 주요 처리 내용

- 원본 데이터를 직접 수정하지 않고 복사본을 사용함
- 문자열 컬럼 앞뒤 공백 제거
- 고객 나이 결측치는 중앙값으로 대체
- 고객 도시 결측치는 Unknown으로 처리
- 주문 상태값 표기 통일
- 날짜 컬럼 변환 및 주문 월/요일 파생 컬럼 생성
- 가격, 수량, 단가를 숫자형으로 변환
- 0 이하 가격, 수량, 단가 확인 및 처리
- line_total 파생 컬럼 생성
- 파일 간 키 관계 재확인

## 주의 사항

이 전처리 기준은 실습용 예시입니다. 실제 업무에서는 결측치와 이상값을 삭제하거나 대체하기 전에 원본 시스템, 수집 과정, 업무 담당자 확인이 필요합니다.
