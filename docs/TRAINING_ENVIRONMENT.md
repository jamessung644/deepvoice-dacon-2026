# 실제 학습 환경 · 보관 기록 기준

2026-08-31의 초기 학습 보고서, 2026-09-04의 GPU/RAM preflight, 후속 환경 및 실험 protocol을 대조했다. 2026-10-01 현재 SSH 서버 사양을 새로 조회한 문서는 아니다. 학습 장비와 DACON 평가 장비, 확인되지 않은 별도 서버를 섞지 않는다.

## 하드웨어

| 항목 | 확인값 | 범위 |
|---|---|---|
| GPU | NVIDIA RTX 2000 Ada Generation × 2 | 2026-09-04 장착 inventory |
| GPU VRAM | 명목 16GB/장; nvidia-smi 16,380MiB/장 | 합산 32GB 단일 주소공간이 아님 |
| RAM | OS MemTotal 15,968,407,552 bytes ≈ 14.87GiB | 물리 모듈 설치 용량을 별도 추정하지 않음 |
| Swap | 0 bytes | 같은 preflight |
| CPU 모델 / 코어 수 | 미확인 | 실행기의 worker/thread 수를 CPU 사양으로 쓰지 않음 |
| OS | Linux x86_64, kernel 6.8.0-134-generic, glibc 2.39 | Ubuntu 배포판 버전은 미확인 |

Torch의 사용가능 VRAM 값과 nvidia-smi의 전체 VRAM 값은 측정 범위가 달라 동일 값이라고 주장하지 않는다. 개별 실행에서 관측한 peak 메모리는 모델 파라미터 파일 크기와도 다르다.

## 소프트웨어 환경 구분

| 환경 기록 | Python | PyTorch | CUDA runtime | 기타 |
|---|---|---|---|---|
| 초기 CNN / 음성 실험 | 3.11.15 | 2.13.0+cu130 | 13.0 | NumPy 1.26.4, SciPy 1.15.3, scikit-learn 1.8.0, SoundFile 0.13.1 |
| 별도 후속 호환 runtime | 3.11.15 | 2.7.1+cu128 | 12.8 | Torchaudio 2.7.1+cu128 |

후속 환경 기록에 NVIDIA driver 595.71.05가 있다. 해당 JSON 자체에 시각이 없으므로 모든 과거 학습에서 같은 driver를 사용했다고 확정하지 않는다. PyTorch에 표시된 CUDA는 runtime 버전이며 시스템 toolkit/driver 버전과 하나로 합치지 않는다. 두 환경은 같은 장비에서 별도로 사용한 기록이다.

## 실제 GPU 사용 사례

- GPU 0: AASIST clean, 분리음 CNN exact→sqrt 순차 비교, 작은 자료 CNN 비교.
- GPU 1: AASIST augmented, MERT head 비교, MERT 마지막 두 층 학습.
- 실험별 단일 GPU 학습이며, 독립 실험을 GPU별로 병행한 기록이 있다. 두 장을 사용하는 분산학습으로 소개하지 않는다.

Mac은 수집·검사·문서/결과 보관에 사용했다. 기록된 모델 학습은 원격 GPU 장비에서 수행했다.

## 근거 식별자

- `reports/remote/cnn_pilot/metrics.json`: platform, versions, started_at_utc.
- `reports/remote/remote_environment.json`: 초기 Python/PyTorch/CUDA 및 라이브러리 기록.
- `reports/remote/music_fake_task5/launch_task6_ab_v2_run2/launch_context.json`: resources_before_launch.gpu_records / memory_bytes / execution.
- `reports/remote/voice_background_training_v1/completed_v1/environment.json`: 후속 runtime / gpu_driver.
- `reports/remote/robust_experiments/aasist_clean_s42_queue.log`, `aasist_aug_s42_queue.log`: 개별 학습 GPU 지정.
- `reports/music_repr_comparison_v2_r1/cnn_same_data/protocol.json`, `mert_heads/protocol.json`, `reports/music_mert_tail_v3_r1/protocol.json`: CNN/MERT 사용 GPU.

근거 식별자는 기존 비공개 연구 기록의 파일명이며 원문 전체가 공개 저장소에 포함된다는 뜻은 아니다. 호스트 이름·계정·IP·SSH 포트·GPU UUID·절대 저장 경로는 공개 요약에서 제외했다.
