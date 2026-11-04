# Chapter 08: 작은 데이터 분석 프로젝트

최종 제출 파일은 `chapter08.ipynb` 하나이며, 보고서에 해당하는 해석과 답안도 Notebook 안에 있다. `reports/`의 CSV·PNG·Markdown·재실행 로그는 보조 증빙이다. 아직 commit/push하지 않았다.

## 이번 과제의 핵심

질문 → 원본 확인 → 전처리 → PK/FK 및 병합 검증 → completed 범위 집계 → 카테고리/월/고객 총합 대조 → 그래프와 해석 → 별도 프로세스 재실행을 연결하는 과제다.

- 공식 `data/raw` 가상 쇼핑몰 원본을 사용했다. Chapter 05의 오염된 샘플이 아니다.
- 입력 출처·버전·SHA-256은 `source_manifest.json`에 있다.
- 고객 150명, 상품 100개, 주문 300개, 상세 764개다.
- 완료 주문은 184개, 상세 474개이며 완료 금액은 148,990,000원이다.
- 카테고리·월·고객 총합은 모두 같은 금액이다.
- 공식 Validation 8개 PASS, 독립 검증 13개 PASS, 코드 셀 18개를 모두 실행했다.
- 실제 개인정보는 아니지만 공개 고객 집계에는 이름·원본 ID를 제거했다. 입력 CSV의 가상 ID는 재현용이다.

## 남은 수동 검토와 캡처

번호는 Notebook 본문 상단의 공식 섹션 번호다. 맨 아래 제출 답안의 번호와 혼동하지 않는다.

| 저장 이름 (images 폴더) | 촬영 위치와 포함할 내용 | 현재 상태 |
| --- | --- | --- |
| step02_data_validation.png | **4. 원본을 보존하며 전처리** 바로 아래, 원본 요약표 + 전처리 전후 비교표 | 직접 캡처 |
| graph01.png | **13. 검증된 집계표에서 그래프 생성**의 카테고리 막대그래프 | 이미 그래프 PNG로 저장됨, 재촬영 불필요 |
| graph02.png | 같은 섹션의 월별 선그래프 | 이미 그래프 PNG로 저장됨, 재촬영 불필요 |
| step06_reproduce.png | **15. 전체 파이프라인 재실행** 출력 하단의 `Notebook vs separate process: all four tables MATCH`와 Validation 8개 PASS 표 | 직접 캡처 |

선택: **10. 최종 PASS/FAIL Validation**의 8개 PASS 표를 `step05_validation.png`로 추가해도 된다. 세 번째 익명 고객 그래프는 `graph03.png`로 이미 저장돼 있다.

스크린샷 저장 후 맨 아래 **캡처한 증빙 이미지 확인 (선택)** 코드 셀만 재실행하면 파일의 최신 내용을 읽는다. 이 셀의 출력까지 저장하면 캡처가 Notebook에 내장되어 상대경로 렌더링 문제도 줄일 수 있다. 미촬영 상태에서는 기존 본문 실행 출력이 증빙으로 남아 있다. 캡처를 했다고 자동 표시하지 않았다.

## 재실행

사용 중인 Jupyter Kernel과 같은 Python에서 실행한다. 현재 검증 환경은 Python 3.14다. 다른 PC에서는 Python 가상환경에 requirements.txt를 설치한다.

```cmd
cd /d C:\Users\신윤철\Documents\llm-data-analysis-study\chapter08
python scripts\run_midterm_project.py
python scripts\verify_project.py
```

Notebook은 `chapter08` 또는 저장소 루트에서 실행할 수 있다. 일부 셀이 아니라 Run All로 최종 확인한다. 전체 스크립트와 독립 검증은 네트워크 접속 없이 저장된 raw에서 재현된다. `build_submission.py`는 초안 제작 도구이고 일반 재실행에는 필요 없다(제작 당시 course 저장소를 참조함).

## 주요 산출물

- `chapter08.ipynb`: 실행 출력과 제출 답안
- `chapter08_assignment.md`: 검토용 답안 사본(별도 제출 불필요)
- `reports/ch08_midterm_report.md`: 공식 파이프라인에서 만든 보고서
- `reports/ch08_analysis_report.md`: 상세 해석 보고서
- `reports/ch08_project_validation.csv`: 공식 검증 8개
- `reports/ch08_independent_checks.csv`: 독립 검증 13개
- `reports/ch08_reproduction_log.txt`: 별도 Python 프로세스 실행 로그
- `reports/figures/`: 대표 그래프 3개

자동 실행·검증과 제출자의 수동 검토는 구분한다. 최종 답안의 해석을 읽고 필요한 표현을 수정한 뒤, 캡처·GitHub 표시 확인 및 LMS 제출 체크를 완료한다.

제출 URL: https://github.com/ycshin2002/llm-data-analysis-study/blob/main/chapter08/chapter08.ipynb
