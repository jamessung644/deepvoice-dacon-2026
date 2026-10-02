# 가중치 공개조건 확인 · 2026-10-01

이 문서는 원 배포처의 공개 고지와 파일 식별값을 확인한 **공개 범위 결정**입니다. 법률 보증이나 대회 최종 규정 통과 판정이 아닙니다. NC(비상업) 표기만으로 공개 공유가 금지된다고 해석하지 않으며, 코드 라이선스를 가중치에 자동 적용하지 않습니다.

## 이번 공개 범위

| v7 가중치 | 판단 | 이유 |
|---|---|---|
| PANNs Cnn14 · 327.43 MB | **CC-BY-4.0 조건을 갖춰 Releases에 공개** | checkpoint 배포 레코드 자체가 CC-BY-4.0; 원 배포 bytes/MD5 일치, 보관 manifest SHA-256 일치 |
| HTDemucs · 84.14 MB | **공개 미러 보류** | 코드 MIT와 가중치 조건은 별도; 제작자의 scientific-purpose 고지와 재배포 허락 미확인 |
| Forensics · 1.27 GB | **공개 미러 보류** | 자체 NC는 비상업 공유 허용; 기반 WavLM MIT/SA 표기 불일치 미해결 |
| 자체 음악 CNN 3개 · 합계 15 MB | **공개 보류** | 혼합 학습원천 조건과 파일별 권리·가중치 적용 범위 미확정; 직접 학습만으로 unrestricted 허가를 주장하지 않음 |

원본 v7 ZIP, 원음·가공 오디오 및 보류 가중치는 공개하지 않습니다. 보류는 **위반 확정**이라는 뜻이 아닙니다. 원 저자에게 문의를 발송하거나 새 모델을 학습·실행하지 않았습니다.

## PANNs: checkpoint 라이선스로 확인

[Zenodo 3987831](https://zenodo.org/records/3987831)의 [공식 API](https://zenodo.org/api/records/3987831)는 pretrained models v3에 `cc-by-4.0`을 명시합니다. 정확한 파일 `Cnn14_mAP=0.431.pth`는 327,428,481 bytes, MD5 `541141fa2ee191a88f24a3219fff024e`입니다. 보관 v7 파일과 크기·MD5가 같고, SHA-256도 [inventory](../results/model_inventory.json)와 일치했습니다.

[CC BY 4.0 법률문서](https://creativecommons.org/licenses/by/4.0/legalcode.en) 2(a)(1)은 복제·공유를 허용하고 3(a)는 저자·출처·라이선스·변경 여부·보증 부인 고지 보존을 요구합니다. [저자·출처 고지](../licenses/PANNs_NOTICE.md), [라이선스 전문](../licenses/CC-BY-4.0.txt), [SHA-256 목록](../results/WEIGHTS_SHA256SUMS.txt)을 함께 배포합니다. 원본 파일을 변경하지 않았고, 추가 NC 제한이나 프로젝트 전체 라이선스를 덧씌우지 않습니다.

## HTDemucs: 기존 MIT 설명의 한계 정정

기존 기록에는 보관된 Demucs MIT 고지가 있었습니다. 하지만 이것만으로 **가중치가 MIT라고 판단하면 안 됩니다**. 제작자 Alexandre Défossez는 [공식 issue 댓글](https://github.com/facebookresearch/demucs/issues/327#issuecomment-1134828611)에서 2022-05-23에 모델 가중치는 MIT 대상이 아니며 과학 목적용이라고 밝혔습니다. GitHub API의 작성자·날짜·본문을 확인했습니다.

이 설명은 v4 출시 전이므로 특정 HTDemucs v4 파일의 공개 재배포가 금지됐다고 확정하지 않습니다. 반대로 명확한 v4 checkpoint 재배포 허락도 확인하지 못했으므로 우리 GitHub에 미러하지 않습니다. 코드의 [v4.0.1 MIT](https://github.com/facebookresearch/demucs/blob/ef66d254cd6d558e207eeff2c4b8d053db2e77dd/LICENSE), [정확한 checkpoint 목록](https://github.com/facebookresearch/demucs/blob/ef66d254cd6d558e207eeff2c4b8d053db2e77dd/demucs/remote/files.txt)과 [원 checkpoint 다운로드](https://dl.fbaipublicfiles.com/demucs/hybrid_transformer/955717e8-8726e21a.th)를 구분합니다. 원 링크 안내도 이용 조건을 대체하지 않습니다.

## Forensics: NC 자체와 기반 모델 문제 구분

[고정 모델 카드](https://huggingface.co/eliya/forensics_0.3B_base_deepfake_classifier/blob/49608c4162c2321217cd89b3847df3bf4caa304c/README.md)는 CC-BY-NC-4.0, 기반 `microsoft/wavlm-large`, full fine-tuning을 명시합니다. [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/legalcode.en)은 조건부 비상업 복제·공유를 허용합니다. NC를 이유로 “공개 배포 불가”라고 일괄 설명하지 않습니다.

다만 [Microsoft 원본 WavLM 배포 README](https://github.com/microsoft/unilm/blob/57eb1dbf6b18ac619bef63521f867b616d0debe3/wavlm/README.md)와 [같은 revision MIT](https://github.com/microsoft/unilm/blob/57eb1dbf6b18ac619bef63521f867b616d0debe3/LICENSE)의 근거가 있는 반면, [Microsoft HF 카드](https://huggingface.co/microsoft/wavlm-large/blob/c1423ed94bb01d80a3f5ce5bc39f6026a0f4828c/README.md)는 official license를 [UniSpeech BY-SA 3.0](https://github.com/microsoft/UniSpeech/blob/6112826ac13a4327f4c9a7afa2a505e35b763514/LICENSE)으로 연결합니다. 실제 기반 파일의 권리 연결과 fine-tuning의 법적 Adaptation 여부를 확정하지 않았습니다. SA가 적용되는 Adaptation이라는 전제라면 NC 단독 표기로 충족되지 않는 문제가 있어 미러를 보류합니다.

원본은 [고정 revision](https://huggingface.co/eliya/forensics_0.3B_base_deepfake_classifier/tree/49608c4162c2321217cd89b3847df3bf4caa304c)에서 확인할 수 있습니다. 이 링크가 권리 불일치를 해결하거나 새 허가를 주는 것은 아닙니다.

## 자체 CNN: 데이터 라이선스가 가중치에 자동 전이된다고 단정하지 않음

학습원천은 [DATASETS](DATASETS.md)에 공개했습니다. 원음 모델에는 Echoes BY-SA-4.0과 MAESTRO BY-NC-SA-4.0이 함께 들어가며, FakeMusicCaps/SONICS NC 및 FMA 곡별 조건도 있습니다. 분리음 모델에도 FMA의 BY-SA와 BY-NC-SA 곡이 모두 있어 혼합 SA 문제가 원음 모델에만 한정되지 않습니다. 곡별 조건과 MAESTRO NC-SA를 별도로 확인해야 합니다.

[CC의 AI 관련 공식 FAQ](https://creativecommons.org/faq/#artificial-intelligence-and-cc-licenses)는 저작권상 허락이 필요한 기술 이용에는 기존 라이선스 조건을 적용하고, 새 기술이라는 이유만으로 특별 허가가 항상 필요한 것은 아니라고 설명합니다. **학습했다는 사실만으로 가중치가 원음의 Adaptation이라고 단정하지 않습니다.** 다만 실제 Adaptation이라는 전제하에 BY-SA와 BY-NC-SA의 [허용 adapter license](https://creativecommons.org/compatible-licenses/)는 다르므로 임의로 한 라이선스를 붙여 해결했다고 주장할 수 없습니다.

따라서 현재는 자체 가중치 공개 허락을 확정하지 않고 파일별 원천·라이선스/귀속 정보와 적용 범위 확인을 남깁니다. 크기 때문이 아니라 권리 확인 범위 때문입니다. 비공개 원본은 보존하고, 공개가 필요하면 해당 파일별 권리 검토·필요한 저작권자 확인 후 별도 릴리스합니다.
