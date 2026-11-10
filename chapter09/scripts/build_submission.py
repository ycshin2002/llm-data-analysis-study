"""Fill the official Chapter09 notebook and execute a fresh, explicit Python kernel."""
from pathlib import Path
import hashlib
import importlib.metadata
import inspect
import json
import numbers
import shutil
import sys
import tempfile

import nbformat
import pandas as pd
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
COURSE = ROOT.parent.parent / "llm-data-analysis-course"


def code(s):
    return nbformat.v4.new_code_cell(inspect.cleandoc(s))


def md(s):
    return nbformat.v4.new_markdown_cell(inspect.cleandoc(s))


def table(df):
    def value(v):
        if isinstance(v, numbers.Real) and not isinstance(v, bool):
            return f"{v:,.2f}"
        return str(v).replace("|", "\\|")
    header = "| " + " | ".join(map(str, df.columns)) + " |"
    divider = "| " + " | ".join("---" for _ in df.columns) + " |"
    rows = ["| " + " | ".join(value(v) for v in row) + " |" for row in df.itertuples(index=False, name=None)]
    return "\n".join([header, divider, *rows])


def main():
    report = ROOT / "reports"
    metrics = pd.read_csv(report / "ch09_regression_model_comparison.csv")
    cv = pd.read_csv(report / "ch09_regression_cv_summary.csv")
    split = pd.read_csv(report / "ch09_regression_split_summary.csv")
    validation = pd.read_csv(report / "ch09_regression_validation.csv")
    errors = pd.read_csv(report / "ch09_regression_predictions_internal.csv").head(3)
    base = metrics[metrics.selection_role.eq("baseline")].iloc[0]
    selected = metrics[metrics.selection_role.eq("selected_by_train_cv")].iloc[0]
    # These fixed official candidates are not tuned after inspecting Final Test.
    manifest = {
        "source": "https://github.com/GilbertMoon/llm-data-analysis-course",
        "commit": "6105f42bd8294cb364dde6dcc2fee71c32e14794",
        "prepared_date": "2026-11-05", "input": "official synthetic common shopping-mall data, not Chapter05 dirty data",
        "raw_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "data/raw").glob("*.csv"))},
        "python": sys.version, "packages": {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "scikit-learn", "matplotlib", "nbclient", "nbformat"]},
    }
    (ROOT / "source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    allowed_rows = [
        ("order_month", "현재 날짜에서 계산"), ("order_dayofweek", "현재 날짜에서 계산"),
        ("age", "예측 시점에 등록된 나이라고 가정"), ("payment_method", "사용자가 결제수단을 선택한 후라고 가정"),
        ("gender", "예측 시점에 등록된 프로필이라고 가정"), ("city", "예측 시점의 등록 도시라고 가정"),
    ]
    forbidden_rows = [
        ("order_total", "Target 자체라 정답을 입력하는 셈"),
        ("line_total", "Target을 직접 구성하는 금액"),
        ("quantity", "Target 계산 재료, 상세 미제공 시점에 알 수 없음"),
        ("unit_price", "Target 계산 재료, 상세 미제공 시점에 알 수 없음"),
        ("item_count", "상세가 확인된 뒤 계산하는 집계"),
        ("total_quantity", "상세 기반 Target 대리 변수"),
        ("avg_unit_price", "상세 기반 Target 대리 변수"),
        ("order_status", "완료·취소·환불은 사후 확정 정보"),
        ("order_id", "주문 식별자이며 일반화 가능한 수치가 아님"),
        ("customer_id", "고객 식별자를 외우게 할 수 있음"),
        ("product_id", "상세에 속한 식별자이며 현재 시점의 입력이 아님"),
    ]
    audit = "| feature | 예측 시점 사용 가능 | Target 계산 재료 | 사후 정보/ID | 최종 사용 | 판단 이유 |\n| --- | --- | --- | --- | --- | --- |\n"
    for name, reason in allowed_rows:
        audit += f"| {name} | 조건부 예 | 아니오 | 아니오 | 사용 | {reason} |\n"
    for name, reason in forbidden_rows:
        audit += f"| {name} | 사용 불가 | {'예/직간접' if name in ['order_total','line_total','quantity','unit_price','item_count','total_quantity','avg_unit_price'] else '아니오'} | {'예' if name.endswith('_id') or name=='order_status' else '상세 확정 후'} | 제외 | {reason} |\n"

    error_text = ""
    for rank, (_, row) in enumerate(errors.iterrows(), 1):
        error_text += f'''### 사례 {rank}
- 실제값: {row.actual_order_total:,.0f}원.
- 예측값: {row.predicted_order_total:,.2f}원.
- residual(실제−예측): {row.residual:,.2f}원.
- absolute error: {row.abs_error:,.2f}원.
- 관찰: 실제 고액 주문을 낮게 추정했다. 원본 주문 ID 대신 오차 순위로 사례를 표시했다.
- 가능한 이유 후보: 상세 수량·가격 없이 메타데이터만 사용하는 정보 제한 때문에 고액 주문을 구별하기 어려웠을 수 있다. 실제 원인으로 단정하지 않는다.
- 추가 확인: 예측 당시 기록의 정확성과 상품 구성·수량별 차이를 사후 진단으로 확인하되, 이 예측 시점의 Feature에 금지된 상세를 다시 넣지는 않는다.
- 모델 한계: 개별 고액 주문 오차가 약 100만 원 이상이므로 개인별 금액 의사결정에 위험하다.

'''
    answer = f'''# 제출 답안: Chapter 09 회귀 분석

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
{audit}
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
{table(split)}
- Train: 2025-07-09~2026-04-13, 244건.
- Final Test: 2026-04-14~2026-07-08, 56건.
- 같은 달력 날짜 중복: 없음. Train 최종 날짜 < Test 최초 날짜.
### 분할 판단
미래에 예측할 상황을 모방하려 과거로 학습하고 뒤 기간을 남겼다. 고유 날짜 기준 80:20 분할이라 행 비율은 정확한 80:20이 아닌 81.33:18.67이다. 고객 ID는 입력이 아니지만 반복 고객이 두 기간에 있을 수 있어 이 평가는 신규 고객 일반화를 별도로 증명하지 않는다.
- 스크린샷 위치: 본문 **5. 시간 순서로 Train / Final Test를 분리합니다**. `images/step04_split.png`.

## 5. Train TimeSeriesSplit 후보 비교
{table(cv)}
### Train CV로 선택한 비베이스라인 모델
- Selected Model: {selected.model}.
- 선택 기준: Linear Regression과 Random Forest 중 Train 5-fold TimeSeriesSplit의 CV MAE 평균이 작은 모델. 후보·하이퍼파라미터·seed=42는 공식값을 고정했다.
- Final Test 전에 선택했는가: 예. 본문 **8. 비베이스라인 모델 선택을 고정합니다**에서 Train CV만으로 JSON을 저장한 뒤 **9**에서 최종 평가한다. 별도 실행 스크립트도 동일 순서다.
### 나의 해석과 판단
Random Forest의 CV MAE는 437,352.80원, 표준편차는 26,318.79원이다. Linear Regression보다 낮지만 Baseline의 423,004.81원보다 나쁘므로 선택됐다는 사실이 사용 가치까지 보장하지 않는다. 표준편차는 시간 구간별 성능 변동을 보여 주며 신뢰구간이나 통계적 유의성으로 해석하지 않았다.

숫자형은 median imputation→StandardScaler, 범주형은 most-frequent imputation→OneHotEncoder(handle_unknown='ignore')를 각 Pipeline 안에서 fit했다. Test에는 transform/predict만 한다. 공통 전처리의 전체 고객 나이 중앙값 대체는 Chapter09 준비 단계에서 되돌려, 결측이 생겨도 각 Train Fold 안에서만 대체값을 학습하도록 했다. 이번 원본의 나이 결측은 0이라 해당 보완이 결과 숫자를 바꾸지 않는다. 날짜 파생·문자열 공백 정리 같은 결정적 변환은 전체 입력에 적용해도 학습 통계를 사용하지 않는다.

공식 CV는 날짜·ID로 정렬한 **행 기준** TimeSeriesSplit이다. 같은 달력 날짜가 일부 인접 CV Fold 경계에 걸릴 수 있고 불규칙한 주문 간격이라 Fold 기간 길이도 다르다. 이는 Final Test의 날짜 중복 0과 별개의 한계이며 `ch09_cv_fold_checks.csv`에 기록했다. 이번 Final Test를 본 뒤 분할이나 후보를 변경하지 않았다.

## 6. Final Test: Baseline vs Frozen Model
{table(metrics)}
- 스크린샷 위치: 본문 **9. 이제 Final Test에서 Baseline과 고정 모델만 평가합니다**. `images/step06_final_metrics.png`.
### 결과 관찰
Frozen Random Forest의 MAE는 {selected.test_MAE:,.2f}원으로 Baseline {base.test_MAE:,.2f}원보다 나쁘다. MAE 개선율 {selected.MAE_improvement_vs_baseline_pct:.2f}%는 약 3.47% **악화**라는 뜻이다. 다른 후보의 Final Test 성능은 계산해 모델 선택에 사용하지 않았다.
### 나의 해석과 판단
- MAE: 개별 주문 금액을 평균적으로 약 45.9만 원 틀린다. 상대 오차율이나 모든 주문의 오차 상한이 아니다.
- RMSE: {selected.test_RMSE:,.2f}원으로 MAE보다 커, 일부 큰 오차의 영향이 있다.
- R²: {selected.test_R2:.4f}. 이 Test의 **실제값 평균**을 항상 예측하는 기준보다 제곱오차가 크다. 학습 평균으로 예측하는 Dummy Baseline과 R²의 0 기준은 정확히 같지 않다. 음수는 코드 오류의 증명이 아니다.
- Train MAE {selected.train_MAE:,.2f}원보다 Test MAE가 커 학습 기간 성능을 미래 성능으로 대체할 수 없다.
### 업무·분석적 의미
현재 정보와 모델 복잡성이 평균 예측보다 미래 오차를 줄였다는 근거가 없다. 높은 주문 금액에 대한 개별 의사결정이나 자동 운영에 쓰지 않는다. 한 Test 기간의 차이를 통계적 유의성이 입증된 결과라고 주장하지 않는다.

## 7. 대표 오차 사례
{error_text}
양의 residual은 과소예측, 음의 residual은 과대예측이다. 고액 주문만 틀리는 것은 아니며 10,000원 주문을 약 897,415원으로 과대예측한 사례도 있다. 사후 오류 진단은 가능하지만 이를 바탕으로 이번 Final Test에 맞춰 모델을 다시 선택하지 않는다.

## 8. Validation Evidence
{table(validation)}
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
'''
    (ROOT / "chapter09_assignment.md").write_text(answer, encoding="utf-8")
    nb = nbformat.read(COURSE / "notebooks/ch09_regression_analysis.ipynb", as_version=4)
    nb.cells[2] = code('''from pathlib import Path
    import sys
    import json
    import pandas as pd
    import numpy as np

    def find_chapter_root(start):
        for candidate in [start, start / "chapter09", *start.parents]:
            if (candidate / "source_manifest.json").exists() and (candidate / "src/regression.py").exists():
                return candidate.resolve()
        raise FileNotFoundError("chapter09 폴더에서 Notebook을 열어 실행하세요.")

    PROJECT_ROOT = find_chapter_root(Path.cwd())
    PROCESSED_DIR = PROJECT_ROOT / "data/processed"
    REPORT_DIR = PROJECT_ROOT / "reports"
    sys.path.insert(0, str(PROJECT_ROOT))
    from scripts.prepare_ch09_data import prepare_ch09_data
    prepared = prepare_ch09_data()
    print("Input preparation: PASS")
    display(prepared["relationship_checks"])
    from src.regression import (
        FEATURE_COLUMNS, FORBIDDEN_FEATURES, TARGET_COLUMN, build_feature_audit,
        build_leakage_checklist, build_regression_dataset, build_regression_validation,
        build_split_summary, create_prediction_result, cross_validate_regression_models,
        load_regression_source_data, make_regression_models, run_regression_analysis,
        save_regression_outputs, select_diagnostic_model, split_model_data_by_time,
        train_and_evaluate_models, validate_feature_columns, public_prediction_result,
    )
    print("Python:", sys.executable)
    print("PROJECT_ROOT:", PROJECT_ROOT)''')
    nb.cells[8] = code('''model_data = build_regression_dataset(data['customers'], data['orders'], data['order_items'])
    items = data['order_items']
    target = (items['quantity'] * items['unit_price']).groupby(items['order_id']).sum()
    assert np.allclose(model_data['order_total'], model_data['order_id'].map(target))
    relation_checks = pd.DataFrame([
        {"check": "line_total == quantity * unit_price", "rows": len(items), "unmatched_or_mismatch": int((~np.isclose(items['line_total'], items['quantity'] * items['unit_price'])).sum()), "status": "PASS"},
        {"check": "orders <-> target (one_to_one)", "rows": len(model_data), "unmatched_or_mismatch": len(set(data['orders'].order_id) ^ set(target.index)), "status": "PASS"},
        {"check": "orders -> customers (many_to_one)", "rows": len(model_data), "unmatched_or_mismatch": int((~data['orders'].customer_id.isin(data['customers'].customer_id)).sum()), "status": "PASS"},
    ])
    assert relation_checks['unmatched_or_mismatch'].eq(0).all()
    display(relation_checks)
    display(model_data[['order_date', *FEATURE_COLUMNS, TARGET_COLUMN]].head())
    print('Model rows:', len(model_data), '(원본 ID는 표시하지 않음)')''')
    nb.cells[19] = code('''selected_model_name = select_diagnostic_model(cv_summary)
    frozen_selection = {
        'selected_model': selected_model_name,
        'selection_basis': 'lowest train TimeSeriesSplit MAE among non-baseline candidates',
        'final_test_used_for_selection': False, 'random_state': 42,
        'features': FEATURE_COLUMNS, 'cv_summary': cv_summary.to_dict(orient='records'),
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / 'ch09_model_selection_frozen.json').write_text(json.dumps(frozen_selection, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Frozen selected model:', selected_model_name)
    print('선택 파일 저장 완료. 이 다음 셀에서 처음 Final Test 성능을 계산한다.')''')
    nb.cells[24] = code('''prediction_result = create_prediction_result(test_data, y_test, predictions[selected_model_name], selected_model_name)
    public_errors = public_prediction_result(prediction_result)
    display(public_errors.head(10))
    print('residual = 실제 - 예측; 원본 order_id는 공개 출력에서 제외')''')
    nb.cells[30] = code('''import os
    import subprocess
    snapshot = {
        'ch09_regression_cv_summary.csv': cv_summary.copy(deep=True),
        'ch09_regression_model_comparison.csv': model_comparison.copy(deep=True),
        'ch09_regression_split_summary.csv': split_summary.copy(deep=True),
        'ch09_regression_predictions_public.csv': public_prediction_result(prediction_result).copy(deep=True),
    }
    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'MPLBACKEND': 'Agg'}
    logs = []
    for filename in ['prepare_ch09_data.py', 'run_regression_analysis.py', 'verify_ch09.py']:
        completed = subprocess.run([sys.executable, str(PROJECT_ROOT / 'scripts' / filename)], cwd=PROJECT_ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
        logs.append(f'[{filename}] exit code = {completed.returncode}\\n{completed.stdout}\\n{completed.stderr}')
        print(logs[-1])
        assert completed.returncode == 0, filename
    for filename, frame in snapshot.items():
        saved = pd.read_csv(REPORT_DIR / filename)
        expected = frame.copy()
        for column in expected.select_dtypes(include=['datetime']).columns:
            expected[column] = expected[column].dt.strftime('%Y-%m-%d')
        pd.testing.assert_frame_equal(expected.reset_index(drop=True), saved.reset_index(drop=True), check_dtype=False, check_exact=False, rtol=1e-8, atol=1e-6)
    print('Notebook vs separate process: all four tables MATCH')
    display(pd.read_csv(REPORT_DIR / 'ch09_regression_validation.csv'))
    (REPORT_DIR / 'ch09_reproduction_log.txt').write_text('\\n'.join(logs) + '\\nNotebook vs separate process: all four tables MATCH', encoding='utf-8')''')
    nb.cells[32].source = nb.cells[32].source.replace('- [ ]', '- [x]')

    notes = {
        8: "### Target 검증 해석\n764개 상세로 주문 300건의 Target을 만들었고 행 증식·연결 누락이 없다. 여기서 사용한 수량·단가는 정답 생성용이지 모델 입력용이 아니다. 이번 회귀는 모든 주문을 포함하며 Chapter08의 completed 금액 분석과 다르다.",
        12: "### 시간 분할 판단\n244개 과거 주문과 56개 이후 주문으로 나뉘며 최종 날짜 2026-04-13 < 최초 Test 날짜 2026-04-14다. 같은 날짜는 Final Test 경계를 넘지 않는다. Test는 선택이 고정될 때까지 평가하지 않는다.",
        17: "### CV 해석\nRandom Forest가 비베이스라인 후보 중 CV MAE가 더 작지만, Baseline Mean의 CV MAE가 세 모델 중 가장 작다. 평균뿐 아니라 시간 Fold별 변동도 고려해야 하며 선택 모델이라는 이유만으로 실제 사용을 승인하지 않는다.",
        21: f"### Final Test 관찰·판단·의미·한계\nRandom Forest MAE {selected.test_MAE:,.2f}원, RMSE {selected.test_RMSE:,.2f}원, R² {selected.test_R2:.4f}다. Baseline MAE {base.test_MAE:,.2f}원보다 3.47% 악화됐다. RMSE가 더 큰 것은 일부 큰 오차의 영향이며, 음수 R²는 Test 실제값 평균을 기준으로 제곱오차가 더 크다는 뜻이다. 고정 모델은 교체하지 않고 현재 사용을 보류한다. 작은 가상 Test 56건으로 실제 운영의 일반화나 통계적 유의성을 주장하지 않는다.",
        24: "### 대표 오차 해석\n상위 3건은 실제 약 177만~188만 원 주문을 약 61만~86만 원으로 과소예측했다. 메타데이터만으로 개별 금액을 구별하기 어려웠을 가능성이 있지만 상세가 원인임을 입증하지는 않는다. 상세 자료는 사후 진단에만 활용하고 현재 시점 Feature에 넣지 않는다. 저액 주문의 큰 과대예측도 있어 고액 주문만의 문제가 아니다.",
    }
    cells = []
    for i, cell in enumerate(nb.cells):
        if cell.cell_type == 'code':
            cell.outputs, cell.execution_count = [], None
        cells.append(cell)
        if i == 0:
            cells.append(md('## 실행 전 예측 문제·선택 규칙 고정\n' + answer.split('## 1. 예측 문제 정의\n')[1].split('## 2.')[0] + '\n후보는 공식 Baseline Mean / Linear Regression / Random Forest, seed=42, Train TimeSeriesSplit 5-fold다. 비베이스라인 CV MAE 최소 모델을 선택하고 Test 결과로 바꾸지 않는다.'))
        if i in notes:
            cells.append(md(notes[i]))
        if i == 21:
            cells.append(code('''# Pipeline 전처리 통계가 실제 Train에서만 학습됐는지 재검증
            from src.regression import NUMERIC_FEATURES, CATEGORICAL_FEATURES
            preprocessor = models[selected_model_name].named_steps['preprocessor']
            numeric = preprocessor.named_transformers_['numeric']
            categorical = preprocessor.named_transformers_['categorical']
            expected_median = np.nanmedian(X_train[NUMERIC_FEATURES].to_numpy(dtype=float), axis=0)
            transformed_train = numeric.named_steps['imputer'].transform(X_train[NUMERIC_FEATURES])
            categories_fit = categorical.named_steps['encoder'].categories_
            categories_expected = [sorted(X_train[column].dropna().unique().tolist()) for column in CATEGORICAL_FEATURES]
            preprocessing_checks = pd.DataFrame([
                {'check': 'numeric_median_from_train', 'passed': bool(np.allclose(numeric.named_steps['imputer'].statistics_, expected_median))},
                {'check': 'scaler_mean_from_train', 'passed': bool(np.allclose(numeric.named_steps['scaler'].mean_, transformed_train.mean(axis=0)))},
                {'check': 'encoder_categories_from_train', 'passed': all(sorted(actual.tolist()) == expected for actual, expected in zip(categories_fit, categories_expected))},
                {'check': 'dummy_constant_is_train_target_mean', 'passed': bool(np.isclose(models['Baseline Mean'].named_steps['model'].constant_.ravel()[0], y_train.mean()))},
            ])
            preprocessing_checks['status'] = preprocessing_checks['passed'].map({True:'PASS', False:'FAIL'})
            assert preprocessing_checks['passed'].all()
            preprocessing_checks.to_csv(REPORT_DIR / 'ch09_preprocessing_checks.csv', index=False, encoding='utf-8-sig')
            display(preprocessing_checks[['check','status']])'''))
        if i == 28:
            cells.append(md('### 진단 그래프\n산점도 대각선은 예측=실제 기준선이다. 잔차 양수는 과소예측, 음수는 과대예측이다. 그래프는 고정 모델의 동일한 Final Test 예측만 사용한다.'))
            cells.append(code('''from IPython.display import Image, display
            import shutil
            (PROJECT_ROOT / 'images').mkdir(exist_ok=True)
            for source, target in [('ch09_actual_vs_predicted.png','graph01.png'), ('ch09_residual_histogram.png','graph02.png')]:
                path = REPORT_DIR / 'figures' / source
                shutil.copy2(path, PROJECT_ROOT / 'images' / target)
                display(Image(data=path.read_bytes(), width=850))'''))
    cells.append(md(answer))
    cells.append(md('## 캡처 이미지 최신본 확인 (선택)\n아래 파일을 images에 저장한 뒤 이 셀만 재실행하고 Ctrl+S로 저장하면 최신 캡처가 Notebook 출력에 내장된다. 캡처가 없어도 위의 실제 실행 출력은 남아 있다.'))
    cells.append(code('''from IPython.display import Image, display
    for filename in ['step02_leakage.png','step04_split.png','step06_final_metrics.png']:
        path = PROJECT_ROOT / 'images' / filename
        if path.exists():
            print(filename)
            display(Image(data=path.read_bytes(), width=1000))
        else:
            print('선택 캡처 대기:', filename)'''))
    nb.cells = cells
    nb.metadata.kernelspec = {'display_name':'Python 3','language':'python','name':'python3'}
    client = NotebookClient(nb, timeout=240, resources={'metadata':{'path':str(ROOT)}})
    with tempfile.TemporaryDirectory(prefix='chapter09-kernel-') as tmp:
        kd = Path(tmp) / 'chapter09'
        kd.mkdir()
        (kd / 'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Chapter09 Python','language':'python'}),encoding='utf-8')
        client.kernel_name = 'chapter09'
        client.km = client.create_kernel_manager()
        client.km.kernel_spec_manager = KernelSpecManager(kernel_dirs=[tmp])
        client.execute()
    nbformat.write(nb, ROOT / 'chapter09.ipynb')
    (report / 'ch09_analysis_report.md').write_text(answer,encoding='utf-8')
    print('Saved executed chapter09.ipynb, completed Markdown answers, figures and evidence.')


if __name__ == '__main__':
    main()
