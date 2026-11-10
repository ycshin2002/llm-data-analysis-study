# 제출 답안: Chapter 09 회귀 분석

## 제출 정보
- 이름: 신윤철
- GitHub ID: ycshin2002
- 작성일: 2026-11-05
- 최종 Notebook URL: https://github.com/ycshin2002/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb

## 1. 예측 문제 정의
- Target: order_total, 같은 order_id의 quantity×unit_price 합계(원).
- 예측 단위: 주문 1건. 전체 300건을 대상으로 하며 Chapter08과 달리 completed 주문만으로 필터링하지 않는다.
- 예측 시점: 결제수단을 선택하여 주문 메타데이터와 등록 프로필은 있지만 주문 상세 수량·단가·금액은 모델에 전달되지 않은 교육용 시점.
- 알 수 있는 정보: 주문 월·요일, 등록 나이·성별·도시, 선택한 결제수단.
- 알 수 없는 정보: 상세 수량·가격·금액과 그 파생 집계, 최종 주문 상태.
### 나의 해석과 판단
Target을 직접 계산하는 재료 없이 사전 정보만으로 미래 주문 금액을 추정하는 문제로 고정했다. 실제 서비스에서 결제수단이나 프로필을 그 시점에 조회할 수 없다면 해당 Feature도 제외해야 한다. 특히 이 문제는 장바구니가 확정되어 금액이 이미 알려진 상황과는 다르다. 원본에는 프로필 변경 이력이 없어 나이·도시의 시점 일치도는 교육용 가정이며 실제 배포 전 확인해야 한다.

## 2. Feature Leakage Audit
| feature | 예측 시점 사용 가능 | Target 계산 재료 | 사후 정보/ID | 최종 사용 | 판단 이유 |
| --- | --- | --- | --- | --- | --- |
| order_month | 조건부 예 | 아니오 | 아니오 | 사용 | 현재 날짜에서 계산 |
| order_dayofweek | 조건부 예 | 아니오 | 아니오 | 사용 | 현재 날짜에서 계산 |
| age | 조건부 예 | 아니오 | 아니오 | 사용 | 예측 시점에 등록된 나이라고 가정 |
| payment_method | 조건부 예 | 아니오 | 아니오 | 사용 | 사용자가 결제수단을 선택한 후라고 가정 |
| gender | 조건부 예 | 아니오 | 아니오 | 사용 | 예측 시점에 등록된 프로필이라고 가정 |
| city | 조건부 예 | 아니오 | 아니오 | 사용 | 예측 시점의 등록 도시라고 가정 |
| order_total | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | Target 자체라 정답을 입력하는 셈 |
| line_total | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | Target을 직접 구성하는 금액 |
| quantity | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | Target 계산 재료, 상세 미제공 시점에 알 수 없음 |
| unit_price | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | Target 계산 재료, 상세 미제공 시점에 알 수 없음 |
| item_count | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | 상세가 확인된 뒤 계산하는 집계 |
| total_quantity | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | 상세 기반 Target 대리 변수 |
| avg_unit_price | 사용 불가 | 예/직간접 | 상세 확정 후 | 제외 | 상세 기반 Target 대리 변수 |
| order_status | 사용 불가 | 아니오 | 예 | 제외 | 완료·취소·환불은 사후 확정 정보 |
| order_id | 사용 불가 | 아니오 | 예 | 제외 | 주문 식별자이며 일반화 가능한 수치가 아님 |
| customer_id | 사용 불가 | 아니오 | 예 | 제외 | 고객 식별자를 외우게 할 수 있음 |
| product_id | 사용 불가 | 아니오 | 예 | 제외 | 상세에 속한 식별자이며 현재 시점의 입력이 아님 |

- 금지 Feature overlap: 0개.
- 가장 위험한 Feature: line_total 및 total_quantity 같은 Target 대리 변수. 단순한 상관 정보가 아니라 정답을 구성하거나 상세 확정 후 생성되는 정보라 제외했다.
- 스크린샷 위치: 본문 **4. Feature Audit을 확인합니다**. 파일명 `images/step02_leakage.png`.

## 3. Target 생성과 관계 검증
### 계산 기준
`line_total = quantity × unit_price`, `order_total = order_id별 line_total 합계`.
- 전체 상세 764행의 기존 line_total 불일치 0건, Target은 주문별 300행.
- orders↔target: outer merge + one_to_one + indicator로 양쪽 미매칭 0, 300→300행.
- orders→customers: many_to_one, 미매칭 0, 300→300행. 부모 PK 결측·중복도 점검했다.
- 공통 Raw의 고객/주문/상품 FK 미매칭도 모두 0이다.
### 나의 해석과 판단
중복 키는 주문 행을 늘려 표본과 금액을 중복시킬 수 있고, inner merge는 상세가 없는 주문을 조용히 없앨 수 있다. 모델을 만들기 전에 이러한 관계를 차단했다. 원본 파일의 SHA-256과 주문별 Target도 독립 재계산으로 대조했다.

## 4. Train / Final Test 분할
| split | rows | ratio_pct | start_date | end_date |
| --- | --- | --- | --- | --- |
| train | 244.00 | 81.33 | 2025-07-09 | 2026-04-13 |
| test | 56.00 | 18.67 | 2026-04-14 | 2026-07-08 |
- Train: 2025-07-09~2026-04-13, 244건.
- Final Test: 2026-04-14~2026-07-08, 56건.
- 같은 달력 날짜 중복: 없음. Train 최종 날짜 < Test 최초 날짜.
### 분할 판단
미래에 예측할 상황을 모방하려 과거로 학습하고 뒤 기간을 남겼다. 고유 날짜 기준 80:20 분할이라 행 비율은 정확한 80:20이 아닌 81.33:18.67이다. 고객 ID는 입력이 아니지만 반복 고객이 두 기간에 있을 수 있어 이 평가는 신규 고객 일반화를 별도로 증명하지 않는다.
- 스크린샷 위치: 본문 **5. 시간 순서로 Train / Final Test를 분리합니다**. `images/step04_split.png`.

## 5. Train TimeSeriesSplit 후보 비교
| model | n_splits | cv_MAE_mean | cv_MAE_std | cv_R2_mean |
| --- | --- | --- | --- | --- |
| Baseline Mean | 5.00 | 423,004.81 | 44,153.04 | -0.02 |
| Random Forest | 5.00 | 437,352.80 | 26,318.79 | -0.11 |
| Linear Regression | 5.00 | 461,386.29 | 77,792.80 | -0.31 |
### Train CV로 선택한 비베이스라인 모델
- Selected Model: Random Forest.
- 선택 기준: Linear Regression과 Random Forest 중 Train 5-fold TimeSeriesSplit의 CV MAE 평균이 작은 모델. 후보·하이퍼파라미터·seed=42는 공식값을 고정했다.
- Final Test 전에 선택했는가: 예. 본문 **8. 비베이스라인 모델 선택을 고정합니다**에서 Train CV만으로 JSON을 저장한 뒤 **9**에서 최종 평가한다. 별도 실행 스크립트도 동일 순서다.
### 나의 해석과 판단
Random Forest의 CV MAE는 437,352.80원, 표준편차는 26,318.79원이다. Linear Regression보다 낮지만 Baseline의 423,004.81원보다 나쁘므로 선택됐다는 사실이 사용 가치까지 보장하지 않는다. 표준편차는 시간 구간별 성능 변동을 보여 주며 신뢰구간이나 통계적 유의성으로 해석하지 않았다.

숫자형은 median imputation→StandardScaler, 범주형은 most-frequent imputation→OneHotEncoder(handle_unknown='ignore')를 각 Pipeline 안에서 fit했다. Test에는 transform/predict만 한다. 공통 전처리의 전체 고객 나이 중앙값 대체는 Chapter09 준비 단계에서 되돌려, 결측이 생겨도 각 Train Fold 안에서만 대체값을 학습하도록 했다. 이번 원본의 나이 결측은 0이라 해당 보완이 결과 숫자를 바꾸지 않는다. 날짜 파생·문자열 공백 정리 같은 결정적 변환은 전체 입력에 적용해도 학습 통계를 사용하지 않는다.

공식 CV는 날짜·ID로 정렬한 **행 기준** TimeSeriesSplit이다. 같은 달력 날짜가 일부 인접 CV Fold 경계에 걸릴 수 있고 불규칙한 주문 간격이라 Fold 기간 길이도 다르다. 이는 Final Test의 날짜 중복 0과 별개의 한계이며 `ch09_cv_fold_checks.csv`에 기록했다. 이번 Final Test를 본 뒤 분할이나 후보를 변경하지 않았다.

## 6. Final Test: Baseline vs Frozen Model
| model | selection_role | train_MAE | test_MAE | test_RMSE | test_R2 | MAE_improvement_vs_baseline_pct |
| --- | --- | --- | --- | --- | --- | --- |
| Baseline Mean | baseline | 416,266.19 | 443,449.65 | 522,189.70 | -0.00 | 0.00 |
| Random Forest | selected_by_train_cv | 326,438.48 | 458,819.92 | 548,190.45 | -0.10 | -3.47 |
- 스크린샷 위치: 본문 **9. 이제 Final Test에서 Baseline과 고정 모델만 평가합니다**. `images/step06_final_metrics.png`.
### 결과 관찰
Frozen Random Forest의 MAE는 458,819.92원으로 Baseline 443,449.65원보다 나쁘다. MAE 개선율 -3.47%는 약 3.47% **악화**라는 뜻이다. 다른 후보의 Final Test 성능은 계산해 모델 선택에 사용하지 않았다.
### 나의 해석과 판단
- MAE: 개별 주문 금액을 평균적으로 약 45.9만 원 틀린다. 상대 오차율이나 모든 주문의 오차 상한이 아니다.
- RMSE: 548,190.45원으로 MAE보다 커, 일부 큰 오차의 영향이 있다.
- R²: -0.1033. 이 Test의 **실제값 평균**을 항상 예측하는 기준보다 제곱오차가 크다. 학습 평균으로 예측하는 Dummy Baseline과 R²의 0 기준은 정확히 같지 않다. 음수는 코드 오류의 증명이 아니다.
- Train MAE 326,438.48원보다 Test MAE가 커 학습 기간 성능을 미래 성능으로 대체할 수 없다.
### 업무·분석적 의미
현재 정보와 모델 복잡성이 평균 예측보다 미래 오차를 줄였다는 근거가 없다. 높은 주문 금액에 대한 개별 의사결정이나 자동 운영에 쓰지 않는다. 한 Test 기간의 차이를 통계적 유의성이 입증된 결과라고 주장하지 않는다.

## 7. 대표 오차 사례
### 사례 1
- 실제값: 1,877,000원.
- 예측값: 605,528.72원.
- residual(실제−예측): 1,271,471.28원.
- absolute error: 1,271,471.28원.
- 관찰: 실제 고액 주문을 낮게 추정했다. 원본 주문 ID 대신 오차 순위로 사례를 표시했다.
- 가능한 이유 후보: 상세 수량·가격 없이 메타데이터만 사용하는 정보 제한 때문에 고액 주문을 구별하기 어려웠을 수 있다. 실제 원인으로 단정하지 않는다.
- 추가 확인: 예측 당시 기록의 정확성과 상품 구성·수량별 차이를 사후 진단으로 확인하되, 이 예측 시점의 Feature에 금지된 상세를 다시 넣지는 않는다.
- 모델 한계: 개별 고액 주문 오차가 약 100만 원 이상이므로 개인별 금액 의사결정에 위험하다.

### 사례 2
- 실제값: 1,767,000원.
- 예측값: 756,889.65원.
- residual(실제−예측): 1,010,110.35원.
- absolute error: 1,010,110.35원.
- 관찰: 실제 고액 주문을 낮게 추정했다. 원본 주문 ID 대신 오차 순위로 사례를 표시했다.
- 가능한 이유 후보: 상세 수량·가격 없이 메타데이터만 사용하는 정보 제한 때문에 고액 주문을 구별하기 어려웠을 수 있다. 실제 원인으로 단정하지 않는다.
- 추가 확인: 예측 당시 기록의 정확성과 상품 구성·수량별 차이를 사후 진단으로 확인하되, 이 예측 시점의 Feature에 금지된 상세를 다시 넣지는 않는다.
- 모델 한계: 개별 고액 주문 오차가 약 100만 원 이상이므로 개인별 금액 의사결정에 위험하다.

### 사례 3
- 실제값: 1,863,000원.
- 예측값: 861,784.71원.
- residual(실제−예측): 1,001,215.29원.
- absolute error: 1,001,215.29원.
- 관찰: 실제 고액 주문을 낮게 추정했다. 원본 주문 ID 대신 오차 순위로 사례를 표시했다.
- 가능한 이유 후보: 상세 수량·가격 없이 메타데이터만 사용하는 정보 제한 때문에 고액 주문을 구별하기 어려웠을 수 있다. 실제 원인으로 단정하지 않는다.
- 추가 확인: 예측 당시 기록의 정확성과 상품 구성·수량별 차이를 사후 진단으로 확인하되, 이 예측 시점의 Feature에 금지된 상세를 다시 넣지는 않는다.
- 모델 한계: 개별 고액 주문 오차가 약 100만 원 이상이므로 개인별 금액 의사결정에 위험하다.


양의 residual은 과소예측, 음의 residual은 과대예측이다. 고액 주문만 틀리는 것은 아니며 10,000원 주문을 약 897,415원으로 과대예측한 사례도 있다. 사후 오류 진단은 가능하지만 이를 바탕으로 이번 Final Test에 맞춰 모델을 다시 선택하지 않는다.

## 8. Validation Evidence
| check | value | status |
| --- | --- | --- |
| forbidden_feature_overlap | 0 | PASS |
| strict_train_before_test | True | PASS |
| selected_model_exists_in_train_cv | True | PASS |
| final_test_contains_baseline | True | PASS |
| final_test_contains_frozen_selected_model | True | PASS |
| test_rows_for_r2 | 56 | PASS |
### FAIL 항목
없음. 공식 자동 Validation 6개 모두 PASS다. 독립 검증에서 Target·분할·Baseline CV·최종 지표·개선율·공개 컬럼도 다시 확인했다. PASS는 절차를 지켰다는 뜻이지 모델 성능이 좋다는 뜻은 아니다.

## 9. Evidence와 공개 범위
### 생성된 Evidence
- [x] ch09_regression_split_summary.csv
- [x] ch09_regression_feature_audit.csv
- [x] ch09_regression_cv_summary.csv
- [x] ch09_regression_model_comparison.csv
- [x] ch09_regression_validation.csv
- [x] ch09_regression_checklist.csv
### Internal 파일
- [x] ch09_regression_model_data_internal.csv
- [x] ch09_regression_predictions_internal.csv
두 파일은 로컬에서 생성되지만 `.gitignore`의 `reports/*_internal.csv`로 Git 커밋에서 제외된다.
### 공개 결과
- [x] ch09_regression_report.md
- [x] ch09_actual_vs_predicted.png
- [x] ch09_residual_histogram.png
- [x] ch09_regression_predictions_public.csv (원본 주문 ID 제거)
### 공개 범위 판단
ID는 다른 파일과 연결해 개별 주문·고객을 추적하는 키가 될 수 있다. 모델 입력에서 제외하는 것과 공개 결과에서 제거하는 것은 별개라 둘 다 점검했다. 제공 원본은 공식 가상 데이터이지만 실제 데이터에서도 원본을 공개해도 된다는 의미는 아니다. 공개 출력은 직접 ID를 제거한 요약·진단이며 엄밀한 재식별 불가능성을 보장하지 않는다.

## 10. 최종 사용 판단
- [ ] 현재 수준에서 참고용 사용 가능
- [ ] 추가 검증 후 사용 가능
- [x] 현재 데이터로는 사용 보류
### 판단 근거
1. Train CV에서 두 비베이스라인 후보가 모두 Baseline보다 MAE가 나빴다. Random Forest가 후보 중 선택된 것일 뿐 Baseline을 이기지 못했다.
2. Final Test에서도 MAE 약 45.9만 원, RMSE 약 54.8만 원, R² 약 -0.1033이고 Baseline 대비 3.47% 악화됐다.
3. Feature 누수·최종 시간 분할 검증은 PASS지만, 고액·저액 주문을 모두 크게 틀리는 사례가 있어 실사용 위험이 크다.
### 업무적 위험
고객별 예상 금액으로 예산·혜택·위험도를 자동 결정하면 큰 오차와 프로필 기반 편향을 전파할 수 있다. 성별·나이 같은 변수의 필요성·공정성도 별도로 검토해야 한다.
### 현재 데이터의 한계
가상 데이터 300건, 최종 테스트 56건으로 작다. 월·요일·프로필·결제수단만으로 상세 금액을 설명하기 어려우며 실제 서비스 대표성·시점별 프로필·분포 변화는 확인되지 않았다. 여러 CV Fold에서 같은 날의 주문이 양쪽에 걸릴 수 있는 한계도 남는다.
### 다음 개선 우선순위
1. 예측 시점에 실제로 존재하는 Feature와 프로필 이력을 확인하고 표본을 늘린다. 상세 재료를 몰래 추가하지 않는다.
2. 날짜 단위 CV와 추가 미래 기간·신규 고객 평가를 **새로운 보호 평가 구간**에서 설계한다.
3. 안전한 사전 정보가 확보되면 Train 내부에서만 후보를 검토하고 이번 Final Test는 재사용하지 않는다.

## 11. 전체 재실행 확인
`python scripts/prepare_ch09_data.py` → `python scripts/run_regression_analysis.py` → `python scripts/verify_ch09.py`를 본문 **13**에서 동일 Python의 별도 프로세스로 실행한다.
- 실행 성공 여부: 모두 종료 코드 0.
- Train CV Selected Model: Random Forest.
- Final Validation: 6개 모두 PASS.
- Notebook과 스크립트의 CV·최종 지표·시간 분할·공개 예측값: 허용 오차 내 일치.
- 같은 고정 설정을 재현한 것이며 반복 결과를 보고 모델·Feature를 바꾸지 않았다.

## 12. LLM 활용 및 검증
- 사용 목적: 코드·경로 구성, 누수 점검, 지표·오차 해석 초안 작성.
- Prompt 요약: 공식 Chapter09 순서를 유지해 실행 노트북과 증빙을 작성하고 결과를 실제 데이터로 검증하도록 요청했다.
- 제안/반영: Pipeline 내 결측 대체, Train CV만의 선택, 선택 JSON 사전 저장, 공개 ID 제거, 별도 프로세스 재현을 반영했다.
- 수정/보류: Target 대리 Feature, Test를 보고 다른 모델로 교체, 약한 성능을 성공으로 표현하는 해석은 제외했다.
- 검증 근거: 실제 CV·최종 Test CSV, 공식 Validation, 독립 지표 재계산, 재실행 로그. 자동 검증은 AI가 수행했고 제출자의 수동 검토는 아직 별도로 필요하다.
- Safe Context: 코드·스키마·집계·ID 제거 진단만 사용했다. 원본 고객 행·개인 식별정보를 Prompt로 제공하지 않았다.

## 최종 체크
- [x] Target과 예측 시점을 정의하고 Leakage Audit을 수행했다.
- [x] Target·관계·시간 분할·Pipeline 내부 전처리를 확인했다.
- [x] Train CV에서 선택을 고정한 뒤 Final Test를 평가했다.
- [x] Baseline과 비교하고 낮은 성능·음수 R²를 숨기지 않았다.
- [x] 대표 오차·한계·사용 보류 판단을 작성했다.
- [x] Validation 6개 PASS, 공개/내부 결과 구분, 별도 재실행을 확인했다.
- [ ] 제출자 수동 검토와 필요한 캡처를 완료했다.
- [ ] GitHub 최종 표시 확인 후 Notebook URL을 LMS에 제출했다.
