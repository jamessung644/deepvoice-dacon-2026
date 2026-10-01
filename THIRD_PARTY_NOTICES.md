# 출처 · 권리 · 공개 범위

이 저장소는 결과 설명과 선별한 연구 코드의 공개 기록이다. **PANNs checkpoint 1개만 원본 CC-BY-4.0을 유지해 별도 Releases에 배포**한다. 나머지 모델 가중치·원본 학습 오디오·가공 오디오·제출 ZIP·제3자 모델 구현은 배포하지 않는다. 아래 원 배포처 링크는 이용조건을 대신하지 않는다.

가중치 출처·revision·식별 해시는 [WEIGHTS](docs/WEIGHTS.md), [공개조건 검토](docs/WEIGHT_LICENSE_REVIEW.md), 실제 데이터 구성은 [DATASETS](docs/DATASETS.md), 취득 절차는 [DOWNLOAD_DATASETS](docs/DOWNLOAD_DATASETS.md), 학습 환경은 [TRAINING_ENVIRONMENT](docs/TRAINING_ENVIRONMENT.md)에 정리했다. 정보 공개와 파일 본체 재배포를 구분한다.

| 사용 또는 비교한 구성 | 원 출처 | 이 저장소에 포함한 것 |
|---|---|---|
| PANNs Cnn14 | https://zenodo.org/records/3987831 | 구조 설명 + 변경 없는 checkpoint 별도 Releases; CC-BY-4.0 |
| HTDemucs | https://github.com/facebookresearch/demucs | 구조 설명만; 코드 MIT와 가중치 고지를 구분, 미러 보류 |
| WavLM | https://github.com/microsoft/unilm/tree/master/wavlm | 구조 설명만 |
| Forensics classifier | https://huggingface.co/eliya/forensics_0.3B_base_deepfake_classifier | 구조 설명만; 보관 자산에는 CC-BY-NC-4.0 고지 |
| MERT | https://github.com/yizhilll/MERT | 내부 비교 결과만 |
| DACON 대회 | https://www.dacon.io/competitions/official/236749/overview/description | 보관 제출 화면과 대조해 정리한 수치; 화면 자체는 미공개 |

사용자의 최신 요청에 따라 DACON 스크린샷 자체는 공개하지 않는다. 기존 보관 화면은 점수 검증 근거로만 사용했다. 개인 프로필·연락처·인증정보는 포함하지 않는다. 점수 그래프는 전사 수치로 재작성한 시각화이며 원 화면 캡처가 아니다.

모델·데이터의 이용 조건은 원 배포처의 해당 revision, 파일별 고지, 당시 대회 규정과 함께 확인해야 한다. 이 저장소는 v7의 최종 규정 적합성, 상업적 사용 가능성 또는 모든 과거 자료의 재배포 권한을 주장하지 않는다.

프로젝트 자체 코드에 별도의 포괄적 오픈소스 라이선스를 부여하지 않았다. 저장소 공개는 열람을 위한 것이며, 제3자 자산까지 일괄 MIT 또는 다른 라이선스로 재라이선스하지 않는다. 재사용·재배포를 원하면 저작권자와 원 배포 조건을 확인해야 한다.

위 프로젝트 코드 설명은 PANNs에 별도 제한을 부과하지 않는다. PANNs checkpoint의 저자·출처·원본 그대로임·보증 부인 고지는 [PANNs_NOTICE](licenses/PANNs_NOTICE.md), 원 라이선스 전문은 [CC-BY-4.0](licenses/CC-BY-4.0.txt)에 보존한다. 해당 checkpoint에는 원본 CC-BY-4.0이 적용된다.
