# 점수 근거와 검증 범위

2026-10-01에 기존 프로젝트의 결과 JSON·Markdown 전사·실제 보관 PNG를 대조했다. 새로운 인증된 DACON 화면 조회는 하지 않았다. 사용자의 최신 요청에 따라 **스크린샷은 저장소에 올리지 않는다**.

## 근거 등급

| 기록 | 제출 ID | 근거 |
|---|---|---|
| v1 | 78917 | 보관 화면과 결과 JSON 대조 |
| v2 | 79465 | 보관 화면과 결과 JSON 대조 |
| v3 / v4 / v5 | 82491 / 82793 / 82822 | v5 보관 화면의 세 행과 결과 JSON 대조 |
| v6 / v7 | 83485 / 83804 | v7 보관 화면의 두 행과 결과 JSON 대조 |
| v8 | 84048 | 보관 화면과 결과 JSON 대조 |
| v9_debugged / v9 오류 | 85981 / 85924 | 동일 보관 화면에서 채점 행과 오류 행 확인 |
| v10 | 86849 | 보관 화면과 결과 JSON 대조 |
| v11 | 86972 | 사용자 제공 결과의 Markdown 전사만 보존; 전용 화면 없음 |

`results/official_scores.json`의 `evidence_level`은 이 차이를 보존한다. 점수는 표시 자리수를 기준으로 정리했고, 총점 산식 및 v7 대비 차이를 재계산했다. v9 오류는 0점으로 채우지 않고 null로 둔다.

## 보관 화면 식별 해시

아래 SHA-256은 프로젝트에 남아 있는 원본 PNG를 식별하기 위한 값이다. 공개 저장소에는 이미지 바이트가 없으므로 제3자가 이 해시만으로 화면 내용을 검증할 수는 없다.

| 근거 ID | 연결 버전 | SHA-256 |
|---|---|---|
| submission_78917_user_screenshot.png | v1 | `4d43076aaa8439d1a659712cdeeae5aaa2f5d8ea5bc430ec1c7f092f0dd76146` |
| submission_79465_score_user_screenshot.png | v2 | `5f18432b5036a30e5c91136f212e882f10abff1586d65bc143e479daf54a050f` |
| submission_82822_score_user_screenshot.png | v3–v5 | `761aabdd5478556cb31e14af3fe9f401fd0250f0111bc1d13c0ae194f24a2685` |
| submission_83804_score_user_screenshot.png | v6/v7 | `c6c80093a6737828d4d972e6c5dcd668914c7ab3c2a325d19eaa1350195d786c` |
| submission_84048_score_user_screenshot.png | v8 | `c0c6c90446069e9fc7094ffbe621e688581358118bee5e28c38908b246758085` |
| dacon_85981_result_screenshot.png | v9_debugged/오류 | `250abc93a64f26c4b3d17e3f8ed344d6b54d67aac320448239e4eed1475c1b5f` |
| dacon_score_86849.png | v10 | `9ef7f1b1b2e1ebadedba4c43c8e20f68a5a1d7ddd390126199517673bd1ca9f5` |

## 무엇을 입증하지 않는가

- 인증된 현재 계정의 전체 제출 목록, 최종 순위·수상·최종 규정 적합성.
- 각 공식 FILE/VOICE/MUSIC EER 및 성분 존재 AUC의 개별 값.
- 실제 업로드 ZIP과 보관 ZIP의 모든 바이트 동일성.
- 내부 실험에서 확인한 개선이 대회 평가 분포에도 그대로 적용된다는 주장.
- 코드 테스트 통과가 탐지 성능 개선을 의미한다는 주장.

## 그래프 재생성

```bash
pip install -r requirements-charts.txt
python tools/render_score_chart.py
```

그래프는 [정리 수치](../results/official_scores.json)만 사용한다. 모델 가중치와 오디오를 로드하지 않는다. y축은 0–1 전체 범위이며 v11은 낮은 근거 등급을 구분하는 빈 마커로 표시한다.
