# Chapter 07 시각화 요약

## 분석 범위
금액 관련 그래프는 `order_status == completed` 주문만 사용했다.

## 그래프 목록
```text
   chart        scope   source_table
카테고리별 매출 completed 주문 category_sales
   월별 매출 completed 주문  monthly_sales
상품 가격 분포   전체 상품 카탈로그       products
 가격-판매수량 completed 주문  product_sales
```

## 교차 검증
- completed 주문 항목 매출 합계: 141,340,000원
- 카테고리별 매출 합계: 141,340,000원
- 월별 매출 합계: 141,340,000원
