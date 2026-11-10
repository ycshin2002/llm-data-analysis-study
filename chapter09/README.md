# Chapter 09 회귀 분석 제출 안내

최종 제출 파일은 `chapter09.ipynb`다. 실행 결과, 해석, 답안, Validation을 같은 Notebook에 담았다. Markdown 사본과 reports 폴더는 보조 자료이며 별도 제출하지 않아도 된다. 아직 Git commit/push하지 않았다.

## 무엇을 하는 과제인가?

주문 1건의 금액을 예측하되, 그 시점에 모르는 상세 수량·단가·금액과 사후 주문 상태를 입력에서 제외한다. 과거 주문으로 학습하고 Train 내부 시간순 CV에서 후보를 선택한 뒤, 남겨둔 미래 주문에서 평균 예측 Baseline보다 나은지 확인한다.

- 전체 300건: Train 244건(2025-07-09~2026-04-13), Final Test 56건(2026-04-14~2026-07-08).
- 공식 공통 가상 데이터이며 Chapter05 오류 탐지용 데이터가 아니다. Chapter08과 달리 completed 주문만으로 필터링하지 않는다.
- 선택: Random Forest. 후보/하이퍼파라미터/seed=42는 공식 기준을 유지했다.
- Baseline MAE 약 443,450원, 선택 모델 MAE 약 458,820원으로 3.47% 악화.
- 선택 모델 RMSE 약 548,190원, R² 약 -0.1033. 따라서 현재 데이터로는 모델 사용 보류로 판단했다.
- 공식 Validation 6개 PASS와 성능 개선 여부는 별개다. 낮은 성능도 그대로 보고했다.

## 촬영할 곳

아래 번호는 **Notebook 본문** 번호다. 맨 아래 제출 답안의 번호와 다르다.

| 파일명 (chapter09/images 안에 저장) | 촬영 위치와 내용 |
| --- | --- |
| step02_leakage.png | **4. Feature Audit을 확인합니다**의 allowed/forbidden Feature 표. 길면 VS Code 확대를 줄여 전체가 보이게 찍는다. |
| step04_split.png | **5. 시간 순서로 Train / Final Test를 분리합니다**의 날짜·행 수 표와 `Chronological split gate: PASS`. |
| step06_final_metrics.png | **9. 이제 Final Test에서 Baseline과 고정 모델만 평가합니다**의 두 모델 지표 표. 열이 잘리지 않게 촬영한다. |

선택 추가: **11. 자동 Validation Evidence를 만듭니다**의 6개 PASS 표, 또는 **13. 전체 공통 함수를 새 실행으로 다시 확인합니다** 끝의 `all four tables MATCH`와 PASS 표를 찍어도 된다.

`graph01.png`(실제값-예측값 산점도), `graph02.png`(잔차 히스토그램)는 이미 저장했다. 재촬영할 필요 없다. Notebook 본문에도 그림 출력이 남아 있다.

세 캡처를 저장한 뒤 맨 아래 **캡처 이미지 최신본 확인 (선택)** 코드 셀만 실행하고 Ctrl+S를 누르면 최신 파일을 직접 읽어 Notebook 출력에 내장한다. 캐시 때문에 동기화 스크립트를 따로 돌릴 필요 없다.

## 필요한 검토

노트북 맨 아래 제출 답안을 읽고 본인의 해석으로 검토한다. 사람의 검수가 이미 끝났다고 자동 표시하지 않았다. 공식 `ch09_regression_checklist.csv`의 빈 박스는 사람 검토용이며 자동 Validation PASS 표와 구분한다.

**중요한 한계:** 공식 TimeSeriesSplit은 날짜 정렬 후 행 기준이다. 마지막 CV Fold는 같은 2026-02-24의 주문이 학습과 검증에 각각 들어간다. Final Test 날짜 경계는 엄격히 분리돼 있다. 이 차이와 프로필 시점의 교육용 가정을 답안에 명시했고, Test를 본 뒤 분할이나 모델을 바꾸지는 않았다.

## 재실행

현재 검증 환경은 `source_manifest.json`에 기록했다. Python의 실행 파일이 Notebook 커널과 다르지 않은지 확인한다. 다른 PC에서는 가상환경에 requirements.txt를 설치하면 된다.

```cmd
cd /d C:\Users\신윤철\Documents\llm-data-analysis-study\chapter09
python scripts\prepare_ch09_data.py
python scripts\run_regression_analysis.py
python scripts\verify_ch09.py
```

Notebook은 chapter09 폴더 또는 저장소 루트에서 Run All할 수 있다. 공식 파일의 큰 흐름을 유지하고 경로·증빙·공개 범위·추가 감사·해석을 보완했다. 일반 재실행에는 `build_submission.py`가 필요 없다. 제작 도구인 그 파일은 원본 course 저장소를 참조한다.

## 개인정보와 Git 전체 폴더 업로드

원본은 가상 실습 데이터다. 공개 Notebook·보고서·재현 로그에는 주문 ID를 출력하지 않는다. 두 `reports/*_internal.csv` 파일은 로컬에 남고 .gitignore가 있으므로 `git add chapter09`로 폴더를 통째로 추가해도 커밋에서 빠진다. 파일명을 internal로 붙이는 것만으로 보호했다고 판단하지 않았다. 다른 위치에 복사한 진단 파일이나 스크린샷에 식별자가 들어가지 않도록 검토해야 한다.

최종 제출 URL:
https://github.com/ycshin2002/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
