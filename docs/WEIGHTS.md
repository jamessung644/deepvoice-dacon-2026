# v7 가중치 식별 정보

2026-10-01에 보관 v7 ZIP의 활성 가중치 6개를 스트리밍 재해시하고, 원래 패키지 기록과 내부 SHA256SUMS를 대조했다. 가중치를 공개 저장소에 업로드하거나 모델을 새로 실행·학습하지 않았다.

## 실제 사용 가중치

| ZIP 내부 파일명 | bytes | SHA-256 |
|---|---:|---|
| `model/forensics/checkpoint_epoch_5.safetensors` | 1,269,932,956 | `803d2c57e705395d007b9deaf5b1a110965950f207df223e6dff5b6d298490fb` |
| `model/panns/Cnn14_mAP=0.431.pth` | 327,428,481 | `0dc499e40e9761ef5ea061ffc77697697f277f6a960894903df3ada000e34b31` |
| `model/htdemucs/955717e8-8726e21a.th` | 84,141,911 | `8726e21a993978c7ba086d3872e7608d7d5bfca646ca4aca459ffda844faa8b4` |
| `model/music_fake/logspec_sqrt_v2.pt` | 4,996,898 | `c59d1ad550f26f338d6f461f8cc91c319854138bd76527a6c8bcc5a3ee317881` |
| `model/music_fake_provider/sqrt.pt` | 5,000,189 | `086cdc5b438a0b3bec2eef87b0b11dc3515a46be67952f1507919ab1708db04f` |
| `model/music_fake_provider/equal.pt` | 5,000,189 | `7bb0425be9c549af00edf1610c24fa6548ce1c919a4d6d42dee94f3bfb32391a` |

위 값은 파일 식별값이며 데이터나 모델의 재배포 허가를 뜻하지 않는다. ZIP 자체는 54파일/1,697,006,241 bytes, SHA-256 `16386efd80993ecafb535db3ae53dbbc79d97a2fc01433f2fa833e7456370fb9`이다. 화면 기록과 보관 ZIP의 연결 한계는 [EVIDENCE](EVIDENCE.md)에 별도로 설명했다.

## 원 배포처와 프로젝트 학습 구분

| 모델 | 출처 / 고정 식별자 | 프로젝트 학습 | 역할 |
|---|---|---|---|
| Forensics | [원 모델](https://huggingface.co/eliya/forensics_0.3B_base_deepfake_classifier), revision `49608c4162c2321217cd89b3847df3bf4caa304c` | 추가 학습 없음 | WavLM-large + AASIST-style pooling + 분류기; 원음 VOICE_FAKE |
| PANNs Cnn14 | [원 checkpoint 배포](https://zenodo.org/records/3987831), DOI `10.5281/zenodo.3987831` | 추가 학습 없음 | VOICE / MUSIC 존재 |
| HTDemucs | [원 코드](https://github.com/facebookresearch/demucs), checkpoint `955717e8-8726e21a`, runtime 4.0.1 | 추가 학습 없음 | 비보컬 성분 분리 |
| 분리음 CNN | 자체 LogSpecResNet V1; 모델 소스 SHA `afebc5094f1ec68d3787920a5b97eb7f996087c639293b6c130f1fae673a537e` | fresh initialization; seed 4102026; best epoch 20 | stem 음악 진위 |
| 원음 CNN 두 개 | 자체 LogSpecResNet V5; 모델 소스 SHA `415f2ee821adf17f54efd7f1eb60cbdeeeb6358c191e3aeba618b5fa715d527e` | fresh initialization; seed 5092026; sqrt/equal best epoch 18/16 | 원음 음악 진위 |

Forensics의 실제 forward 경로는 317,257,863개 파라미터다. 체크포인트에는 미사용 projection 205,440개와 buffer 1,030개가 추가로 있어 저장 tensor 총수와 같지 않다. 각 자체 음악 CNN은 1,241,825개 파라미터다. PANNs의 고정 전처리 tensor나 HTDemucs state tensor 요소 수를 학습 파라미터 수와 혼동하지 않기 위해 README에는 별도 수치를 넣지 않았다.

외부 모델의 사전학습은 원 저자의 작업이다. 외부 모델의 전체 학습 파일 목록, 프로젝트 자료와의 모든 중복, 원 학습 과정 재현을 이 프로젝트가 검증했다는 뜻은 아니다.

## v7에서 바뀐 것

v6의 가중치를 유지하고 MUSIC 결합을 `0.5 stem + 0.3 sqrt + 0.2 equal`로 바꿨다. v7 전환에는 새 학습이 없지만, 음악 CNN 3개는 이전 단계에서 실제 직접 학습한 모델이다. FILE 확률 결합은 별도의 학습된 head가 아니라 `max(presence × fake)`다.

## 권리와 공개 경계

보관 고지상 Forensics는 CC-BY-NC-4.0, PANNs checkpoint는 CC-BY-4.0, HTDemucs는 MIT 고지를 갖는다. Forensics의 WavLM 원래 MIT 고지와 배포 페이지의 일부 SA 링크 불일치는 해결된 것으로 취급하지 않는다. 자체 CNN도 FakeMusicCaps/SONICS의 NC, Echoes의 SA 및 원천별 이용 조건을 따로 검토해야 하며, 직접 학습했다고 무제한 재배포 권한이 생겼다고 주장하지 않는다.

원 모델 링크는 취득 위치 안내이며 이 저장소가 가중치 이용 허가를 새로 부여하는 것이 아니다. 이 저장소에는 **파일명·크기·SHA-256·출처·학습 구분만 공개**한다. 전체 공개 정책은 [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)를 참고한다.
