# 학습·평가 데이터셋 정보

이 문서는 실제 학습 요약·분할 manifest·보관 v7 checkpoint 기록을 대조한 **사용 이력**이다. 원 배포본 전체 수, 다운로드 보유 수, 학습 풀, 실제 추출 수, 개발·최종 평가 수를 구분한다. 오디오 실파일이나 원문 manifest를 재배포하지 않는다.

## v7 원음 음악 CNN · sqrt/equal

두 모델은 같은 풀을 사용하고 클래스 균형 및 원천 family 추출 방식을 달리했다. 아래 수치는 프로젝트의 원천 행이며 원 배포 데이터셋 전체 크기가 아니다.

| 원천 | train | dev | 성격 / dev 역할 | 원 배포 조건의 요약 |
|---|---:|---:|---|---|
| [FMA](https://github.com/mdeff/fma) | 2,641 | 442 | 실제 음악; 메타데이터 기반 진위 proxy | 오디오는 곡별 저작자가 선택한 라이선스; metadata CC-BY-4.0과 구분 |
| [MAESTRO](https://magenta.tensorflow.org/datasets/maestro) | 120 | 20 | 실제 피아노 연주 | CC-BY-NC-SA-4.0 |
| [FakeMusicCaps](https://zenodo.org/records/15063698) | 1,800 | 800 | 생성 음악 | CC-BY-NC-4.0 |
| [Echoes](https://huggingface.co/datasets/Octavian97/Echoes) | 2,672 | 727 | 생성 음악 | CC-BY-SA-4.0 |
| [SONICS](https://huggingface.co/datasets/awsaf49/sonics) | 2,654 | 462 | 생성 노래만 사용; train에는 포함, 선택 지표에서는 제외 | 데이터 CC-BY-NC-4.0; 코드 MIT와 구분 |
| [GuitarSet](https://zenodo.org/records/3371780) | **0** | 360 | 실제 기타; 보고 전용, 선택 제외 | CC-BY-4.0 |
| **합계** | **9,887** | **2,811** | **12,698원천** | |

6개 뷰를 각 원천에서 저장해 train 59,322 / dev 16,866 / 총 76,188 WAV를 준비했다. dev loader의 선택용 14,706뷰와 보고용 GuitarSet 2,160뷰를 구분했다. SONICS는 선택용 loader 안에도 있으나 **checkpoint 선택 지표 계산에서는 제외**했다. SONICS를 학습에도 사용하지 않았다고 설명하면 틀린다.

뷰는 clean, codec_lowrate, noise_reverb, partial_presence, resample_eq, telephone_g711다. 모든 뷰가 독립 음원이 아니며, 59,322는 학습 대상 풀의 크기다. epoch draw의 복원추출과 실제 고유 사용량은 다른 값이다. 각 모델은 20 epochs × 16,384 draws = 327,680 draws를 실행했고 선택 epoch은 sqrt 18 / equal 16이었다.

원음 view manifest SHA-256: `00de2e67f2d303a9c89bc8a7f0292501f33e95116b6156947a8a1674cd0f51d1`. 정확한 최종 풀은 실제 `sources_v2` 및 `views_raw_v2` 보고서를 기준으로 했다. 이전 metadata-only 계획의 11,715원천을 최종 12,698원천과 혼동하지 않는다.

## v7 분리음 음악 CNN

| 원천 | train | dev |
|---|---:|---:|
| FMA | 1,676 | 420 |
| MAESTRO | 120 | 20 |
| FakeMusicCaps | 1,800 | 800 |
| GuitarSet · 보고 전용 | 0 | 360 |
| **합계** | **3,596** | **1,600** |

HTDemucs 비보컬 입력의 원천별 13개 뷰로 train 46,748 / dev 20,800 / 총 67,548 WAV를 보존했다. dev 중 선택용은 1,240원천/16,120뷰이고 GuitarSet은 360원천/4,680뷰의 보고 전용이다. 4개 불량 FMA가 제외된 최종 5,196원천을 사용한다.

13뷰는 clean, MP3 64/128k, AAC 64/128k, Opus 32/64k, G.711 μ-law/A-law, 잡음·잔향, gain −6/+6dB, 80ms dropout이다. 20 epochs × 8,192 draws = 163,840 draws에서 **실제로 뽑힌 고유 train 뷰 39,657개**를 확인했다. 풀 전체 46,748개가 모두 추출됐다고 주장하지 않는다. 새 초기화한 1,241,825-parameter 모델을 seed 4102026으로 학습해 epoch 20을 선택했다.

## 학습 설정과 라벨·분할 한계

음악 모델 입력은 16 kHz mono / 64,600 samples(4.0375초)다. batch 32, gradient accumulation 2, BF16, AdamW LR 3e-4 / weight decay 1e-3, label smoothing .02, gradient clipping 5를 사용했다. 원음 모델은 EMA .999, seed 5092026을 사용했다.

- FMA의 REAL은 메타데이터 기반 표적이다. 데이터셋에 있다는 이유만으로 인간 단독 제작 인증을 받은 것은 아니다.
- 생성 출처를 확인한 파일의 전체 진위와 특정 crop의 음성·음악 존재/진위는 같은 정답이 아니다. 원음 모델의 표적을 완전한 수동 성분 주석으로 소개하지 않는다.
- 원곡·동일 오디오·연결 원천을 분할 사이에서 검사하고 source/group 식별을 보존했다. 공개 사전학습 모델의 전체 학습 원천까지 배제한 독립 평가를 증명하지는 않는다.
- 원음 모델 학습에서 ElevenLabs는 train에서 제외하고 dev에 두었으며, Stable Audio는 잠금 확인 원천으로 분리했다. 이로부터 모든 과거 실험에서 해당 생성기를 한 번도 보지 않았다고 확대하지 않는다.
- 평가 뷰를 늘리거나 반복 추론을 늘려도 독립 원천 수는 늘어나지 않는다. 독립 개발/최종 평가와 재사용 개발 자료를 구분해야 한다.

## 초기 음성 실험 · v7 Forensics와 별도

[ML-DF 이탈리아어 배포](https://zenodo.org/records/17098081) 16,000개를 보유했다. 원 발화 그룹 기준 프로젝트 split은 train 11,143 / validation 2,335 / test 2,522였다. ResNet/AASIST 후속 비교에서는 train의 DDDM-VC 1,369개를 제외한 **9,774원천**을 사용했다. clean 9,774, augmented 풀 29,322, 실제 augmented 고유 사용 29,162를 구분한다. validation은 4,670뷰, test는 5,044뷰였다.

ResNet/AASIST × clean/aug 네 모델은 seed 42, 20 epochs, 모델별 163,840 draws를 실행했다. 이들은 초기 음성 경로 연구이며, **v7의 Forensics checkpoint를 ML-DF로 직접 학습한 기록이 아니다**. ML-DF는 이탈리아어와 두 타깃 화자에 제한되며 한국어·미지 생성기 일반화를 증명하지 않는다. 더 앞선 3-epoch 소형 CNN 파일럿과도 구분한다.

ODSS 1,000개(real/fake 각 500)는 당시 고정 음성 앙상블의 외부 평가 자료이지 학습 자료가 아니다. 정확한 평가 수치와 한계는 [INTERNAL_RESULTS](INTERNAL_RESULTS.md)에 정리했다. 외부 완성 Forensics의 전체 사전학습 파일 목록과 모든 중복은 미확인이다.

## v12 데이터 확대 · v7에 포함되지 않은 후속

| 후보 | 원천 | 저장 WAV | 분할 |
|---|---|---:|---|
| baseline | FMA 560 + 직접 ACE-Step-v1 생성 256 = **816** | 4,896 | train_only |
| AIME 확대 | baseline 816 + 12생성기 × 100 = **2,016** | 12,096 | train_only |

2crop × 3view(clean / telephone_mulaw / lowrate_resample_quantized)를 저장했다. 두 모델은 각각 20 epochs를 완료했으며 개발 split 없이 최종 EMA를 사용했다. 통합 작동 검사는 완료했지만 **EER·정확도·v7 개선은 미측정**이다. 새 ZIP·업로드 근거도 없다. MusicNet는 취득 중단 자료이며 두 학습에 사용하지 않았다.

[AIME 원 배포처](https://huggingface.co/datasets/disco-eth/AIME)의 revision `b84d4be5eda830b6eb714998569dba73530f2601`에서 생성 음원만 선택했다. MTG-Jamendo 실제 음악 500곡과 별도 NC-SA 설명 필드는 제외했다. 자체 생성 모델 출처는 [ACE-Step](https://github.com/ace-step/ACE-Step)이다. 이 후보들은 strict v10 기반이며 전체 v7을 그대로 학습 확장한 모델이 아니다.

## 출처 고정과 공개 정책

- Echoes HF revision `14b0c76c6a691c42fadfab9fb6a4eb1ee8c628a2`.
- SONICS HF revision `3788dca9f9f11ad92e9097ef4b58eee247661e7f`, 생성 part_10의 메타데이터 일치 자료. SONICS의 REAL 음원은 취득 대상으로 삼지 않았다.
- FakeMusicCaps Zenodo record `15063698`, 원 코드 README revision `cd80fa3363c761f6b129c0a7a7a57257d75f11c5`.

이용 조건 표는 원 배포 고지의 요약이며 최신 파일별 고지를 함께 확인해야 한다. NC/SA 원천을 쓴 이력은 사실대로 공개하되 대회 최종 규정 적합성·상업 이용·전체 재배포 허가를 주장하지 않는다. 공개하는 것은 **출처·수량·분할·가공/학습 설정**이며 원음·가공 오디오 실파일은 공개 저장소에 올리지 않는다.

## 근거 식별자

- 보관 v7 ZIP 내부 `model/music_fake/training_metrics.json`.
- `reports/remote/music_fake_v5/sources_v2.json`, `views_raw_v2.json`, 두 `training_summary.json`.
- `reports/music_mert_scale_audit_v1/scale_audit.json`.
- `data/manifests/mldf_it.jsonl`, `reports/remote/robust_data.json`, `docs/ROBUST_DATA.md`.
- `reports/v7_anchor_v12_20260910/training_verified_observation.json`, `baseline_completed_observation.json`, `posttrain_verification.json`.

원문은 경로·계정 정보 및 대용량 자료를 포함하므로 여기에는 요약과 식별자만 제공한다.
