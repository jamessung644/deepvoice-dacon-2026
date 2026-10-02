# v7 PANNs checkpoint · 부분 가중치 릴리스

v7의 외부 사전학습 **음성·음악 존재 탐지 모델 PANNs Cnn14 1개만** 공개했습니다.
전체 v7 모델 릴리스, 직접 학습 음악 CNN 공개, 대회 제출 ZIP 또는 재학습 완료판이 아닙니다.

## 포함 파일

- `Cnn14_mAP_0.431.pth` · 327,428,481 bytes · 원본 바이트 그대로이며 추가 학습은 하지 않았습니다. 원 배포 파일명의 `=`만 릴리스에서는 `_`로 표기했습니다.
- `PANNs_NOTICE.md` · 저자·출처·변경 여부·보증 부인.
- `CC-BY-4.0.txt` · 원 라이선스 전문.
- `WEIGHTS_SHA256SUMS.txt` · 원본 식별 SHA-256.

Authors: Qiuqiang Kong, Yin Cao, Turab Iqbal, Yuxuan Wang, Wenwu Wang, Mark Plumbley.
Source: [PANNs pretrained models v3, Zenodo 3987831](https://zenodo.org/records/3987831),
[DOI 10.5281/zenodo.3987831](https://doi.org/10.5281/zenodo.3987831).
Licensed **CC BY 4.0**. Supplied as-is without warranties; no endorsement by the original authors is implied.
The project's licensing policy does not add restrictions to this externally licensed asset.

SHA-256: `0dc499e40e9761ef5ea061ffc77697697f277f6a960894903df3ada000e34b31`.
Bytes and MD5 also matched the publisher's official record before mirroring.

Clone한 저장소에서 다음을 실행하면 다운로드 후 크기와 SHA-256을 검사합니다.

```bash
python3 tools/download_weights.py panns
```

[데이터셋 다운로드 가이드](https://github.com/jamessung644/deepvoice-dacon-2026/blob/main/docs/DOWNLOAD_DATASETS.md),
[공개조건 확인](https://github.com/jamessung644/deepvoice-dacon-2026/blob/main/docs/WEIGHT_LICENSE_REVIEW.md),
[가중치 목록](https://github.com/jamessung644/deepvoice-dacon-2026/blob/main/docs/WEIGHTS.md)을 함께 확인해 주세요.
**PANNs 하나만으로 전체 v7 추론을 실행할 수 없습니다.**

Forensics, HTDemucs 및 자체 음악 CNN 3개는 이번 릴리스에서 제외했습니다.
원음·가공 데이터와 DACON 스크린샷도 포함하지 않았습니다.
