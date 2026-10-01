# 내부 실험 결과

> 아래 값은 프로젝트의 내부·외부 공개자료 실험 결과입니다. **DACON 공식 점수와 평가 대상이 다릅니다.** 서로 다른 패널의 EER을 이어 붙여 하나의 성능 상승 곡선으로 해석하지 않습니다.

EER은 낮을수록, ROC-AUC는 높을수록 좋습니다. EER 0%는 임의의 고정 임계값에서 정확도 100%라는 뜻이 아닙니다. 재사용 개발 자료의 결과와 모델 선택을 잠근 뒤의 확인 결과를 구분했습니다. 숫자의 원래 단위와 표본 정보는 [기계 판독용 결과](../results/internal_metrics.json)에 보존합니다.

## 대표 비교

| 실험 | 평가 자료 | EER ↓ — 기준 → 후보 | ROC-AUC ↑ — 기준 → 후보 | 판단 |
|---|---|---:|---:|---|
| 고정 음성 앙상블 | ODSS 1,000개 | 5.60% → **4.60%** | 0.987914 → **0.991128** | 당시 음성 경로 채택 |
| v5 파일 진위 결합 | 잠금 음악 200개 | 51.00% → **20.00%** | 0.4979 → **0.8506** | 채택 |
| Forensics 원음 전체창 | 음성·배경 96조건 | 10.42% → **4.17%** | 0.960938 → **0.978733** | 후속 v6/v7 경로에 반영 |
| 같은 소형 자료의 CNN·고정 MERT | 개발 768변형 | 기존 15.10%; CNN 30.99%, MERT 선형 26.30%, MERT MLP 25.78% | 후보 AUC 중앙값 미집계 | 세 후보 기각 |
| MERT 마지막 두 층 학습 | 같은 개발 768변형 | 15.10% → 28.91% | 후보 AUC 중앙값 미집계 | 기각 |
| v7 top-2 음악 창 집계 | 음악 내부 패널 192개 | MUSIC 38.54% → 40.63%; FILE 40.63% → 43.75% | MUSIC 0.698459 → 0.689887; FILE 0.659505 → 0.635417 | 기각 |

표의 음성 앙상블 기준은 **DF-Arena 원음 단일 구간**입니다. 같은 ODSS 표본의 이전 소형 CNN EER은 28.60%였습니다. 공식 5출력 baseline 전체를 재현한 결과는 아닙니다.

## 표본·반복·해석 범위

### 1. 고정 음성 앙상블

ODSS real/fake 각 500개를 평가했습니다. validation에서 AASIST 0.25 + DF-Arena 0.50 + ResNet 0.25를 고정했으며, 외부 결과를 보고 가중치를 다시 선택하지 않았습니다. DF-Arena 대비 EER 차이는 −1.00%p이고, 961개 원 발화 그룹의 paired bootstrap 500회에서 95% 구간은 [−2.31, −0.40]%p였습니다.

이 구간은 사후 기술 분석이며 다중 비교·모델 선택 불확실성을 반영하지 않습니다. 한국어·미지 생성기·실제 전화·음악 혼합·대회 분포로 일반화할 근거는 아닙니다. EER 개선과 별개로 외부 BCE는 DF-Arena 0.20577, 앙상블 0.35279였습니다.

근거 ID: `docs/FINAL_RESULTS.md`, `reports/remote/final_voice/external/selected_recovered/metrics.json`, `reports/final_metrics_audit.json`.

### 2. v5 파일 진위 결합

모델·혼합 비율을 고정한 뒤 실제 음악 100개와 Stable Audio Open 100개의 잠금 하위집합을 1회 평가했습니다. 200행은 199개 고유 PCM·164개 원천 그룹입니다. 1,000회 그룹 bootstrap의 후보−기준 EER 차이 95% 구간은 [−39.77, −21.57]%p였습니다. 사전 선언한 개선 gate를 통과했습니다.

전체 잠금 pilot 974행 전부의 결과가 아닙니다. FMA의 실제 라벨에는 메타데이터 근거의 한계가 있고, 사전학습 자료와의 모든 중복을 배제하지 못했습니다. 원천별 비교 행은 생성 음악을 공유하므로 서로 독립되지 않습니다.

근거 ID: `docs/IMPROVED_V5_FILE_RESULTS.md`, `reports/remote/terminal_music_v6/summary.json`, `reports/improved_v5_file_release_gate.json`.

### 3. Forensics 원음 전체창

실제/가짜 16쌍에 세 배경 조건을 적용한 96조건입니다. 네 connected groups로 연결된 반복 자료이므로 96개 독립 표본이 아닙니다. 추가 학습 없이 기존 음성 경로와 원음 Forensics의 5초창+끝창 최대값을 비교했습니다. 원음 전체창의 0.5 임계값 오류는 FP 2/48, FN 1/48이었습니다.

모델과 입력 경로가 함께 바뀌었습니다. 모델 구조 하나의 효과 또는 독립 최종평가 통과로 표현하지 않습니다. 큰 배경음 조건에서는 EER 12.5%가 남았습니다. 이 경로는 이후 v6/v7 제출 구성에 사용됐습니다.

근거 ID: `docs/FORENSICS_VOICE_MODEL_2026-09-06.md`, `reports/remote/forensics_voice_probe_v1/forensics_voice_probe_v1/run_v1/receipt.json`의 `score_table.overall`.

### 4. 같은 소형 자료의 CNN·고정 MERT

train 1,024원천/3,072변형, dev 256원천/768변형/222그룹으로 세 구성×세 seed, 총 9개 학습을 완료했습니다. 표에는 최고 seed 대신 세 seed EER의 중앙값을 사용했습니다. CNN 범위는 29.69–32.68%, MERT 선형 25.52–26.56%, MERT MLP 25.00–26.82%입니다. 세 후보 모두 사전 선언한 탐색 기준을 통과하지 못했습니다.

평가 표적은 약한 **출처 진위**이며 crop의 MUSIC/VOICE 성분 정답은 null입니다. 재사용 개발 자료이고, 기존 v7 원음 CNN은 더 큰 자료로 학습됐습니다. MERT 구조 자체의 열등함을 입증한 비교가 아닙니다.

근거 ID: `docs/MUSIC_REPR_COMPARISON_V2_2026-09-07.md`, `reports/music_repr_comparison_v2_r1/comparison.json`.

### 5. MERT 마지막 두 층 학습

같은 소형 자료에서 마지막 두 transformer 층과 분류기 14,375,681개 파라미터를 세 seed×8 epochs 학습했습니다. 실제 가중치 갱신도 확인했습니다. 세 seed EER은 28.65%, 28.91%, 29.17%였고 모두 채택 기준을 통과하지 못했습니다.

중앙값 EER 증가분은 +13.80%p이며, 222그룹을 1,000회 재추출한 95% 구간은 [+8.85, +18.88]%p입니다. 고정된 세 학습과 재사용 개발 자료를 조건으로 한 값입니다. 약한 출처 표적 및 자료 규모 차이의 한계는 앞 실험과 같습니다.

근거 ID: `docs/MUSIC_MERT_TAIL_V3_RESULTS_2026-09-07.md`, `reports/music_mert_tail_v3_r1/comparison.json`, `reports/music_mert_tail_v3_r1/parameter_update_audit.json`.

### 6. v7 top-2 음악 창 집계

기존 mean pooling과 상위 두 창의 평균을 비교했습니다. real 96행은 GuitarSet 24부모·6연주자 그룹의 가공 뷰이며, fake 96행은 AIME 12생성기×8개입니다. baseline/candidate 각각 2회, 총 4회 추론을 완료했고 반복 출력이 일치했습니다. 반복 추론은 평가 원천 수를 늘리지 않습니다.

MUSIC/FILE EER과 실제 음악 오탐이 악화했습니다. FPR@0.5는 MUSIC 26/96→44/96, FILE 20/96→38/96이었습니다. MUSIC 개선·FILE 비악화·핵심 slice·오탐 gate가 실패해 후보를 기각했습니다.

추론·분석은 완료됐지만 이후 runner의 입력 계약 불일치로 전체 파이프라인은 `failed` 종료했습니다. 저장 분석을 재검증했으며 실패를 완료로 덮어쓰지 않았습니다. 재사용 출처 진위 proxy이며 독립 봉인 평가·부분 위조·DACON 성능을 검증하지 않았습니다.

근거 ID: `reports/v7_top2_selection_20260913_r4_gpu1/POSTMORTEM.md`, `reports/v7_top2_selection_20260913_r4_gpu1/remote_snapshot/analysis/analysis.json`.

## 후속 상태

| 후속 | 확인된 작업 | 아직 확인되지 않은 것 |
|---|---|---|
| v12 데이터 확대 | 기준 816원천과 AIME 추가 2,016원천 모델 각각 20 epochs 완료; 모델 단독·5출력 통합 기능검사 통과 | 정확도/EER/v7 개선, 공식 L4 전체 실행, 새 제출 ZIP·업로드 |
| HeartMuLa | qualification 및 새 패널·v12 overlay 계획/구현 기록 | 현재 정리 자료에서 완료 생성·패널 성능·ZIP 완료 영수증 미확인 |

v12는 strict v10 기반 후보입니다. 원본 v7 전체를 그대로 유지한 후보로 설명하지 않습니다. 기능검사에서 10×60초 파일은 7.98초/8.24초, 최대 RSS 약 1.594GB였지만 이는 공식 L4 1,200개 실행 시간이 아닙니다.

후속 근거 ID: `reports/v7_anchor_v12_20260910/INTEGRATION_RESULTS.md`, `reports/v7_anchor_v12_20260910/PROGRESS.md`, `docs/superpowers/plans/2026-09-13-v7-heartmula-qualification-probe.md`, `docs/superpowers/plans/2026-09-13-v7-heartmula-panel-overlay-zip.md`.

이 문서의 근거 ID는 원래 연구 기록의 식별자이며 공개 저장소에 해당 원문이 모두 포함된다는 뜻은 아닙니다. 데이터·가중치 재배포 허가 또는 대회 규칙 준수를 확정하는 문서도 아닙니다.
