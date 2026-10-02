# 데이터셋 다시 받기

이 문서는 나중에 실험을 다시 시작할 때 **공식 원 배포본을 직접 받는 방법**입니다. 2026-10-01에 배포 페이지·Zenodo API·고정 Hugging Face 파일 목록과 이용 조건을 확인했습니다. catalog의 13개 파일 URL은 HEAD 요청에서 모두 HTTP 200과 예상 크기를 반환했습니다. 대용량 오디오 전체를 이번에 다시 다운로드한 것은 아닙니다.

**현재 공개 저장소만으로 기존 v7의 학습풀과 checkpoint를 그대로 재현할 수는 없습니다.** 원본 다운로드는 가능하지만 프로젝트의 정확한 선별 목록, 원천·뷰 manifest, 가공·학습 실행기는 공개되어 있지 않습니다. 아래 명령은 다운로드와 파일 동일성 확인까지 수행합니다. 모델 가중치는 별도 [WEIGHTS](WEIGHTS.md), 실제 사용 수와 분할은 [DATASETS](DATASETS.md)를 참고합니다.

## 1. 받을 자료 선택

| 자료 | 고정 배포본 | 받을 파일 / 대략적 압축 크기¹ | 이 프로젝트에서의 역할 |
|---|---|---|---|
| [FMA](https://github.com/mdeff/fma) | 2017 release | `fma_small.zip` 7.68GB + metadata 0.36GB | v7 실제 음악; 곡별 라이선스·원천 선별 필요 |
| [MAESTRO](https://magenta.tensorflow.org/datasets/maestro) | **v3.0.0** | CSV 먼저; 전체 WAV+MIDI ZIP **108.45GB** | v7 실제 피아노; 전체 배포본 중 일부 연주 사용 |
| [FakeMusicCaps](https://zenodo.org/records/15063698) | record **15063698** | `FakeMusicCaps.zip` 12.89GB | v7 생성 음악; caption/생성기 그룹으로 분할 |
| [Echoes](https://huggingface.co/datasets/Octavian97/Echoes) | `14b0c76…` | `Echoes.zip` 8.60GB | v7 생성 음악; manifest와 오디오 연결 |
| [SONICS](https://huggingface.co/datasets/awsaf49/sonics) | `3788dca…` | **생성 part_10만** 2.70GB + metadata/CSV 0.14GB | v7 생성 노래; 다른 part·실제 노래로 대체하지 않음 |
| [GuitarSet](https://zenodo.org/records/3371780) | **v1.1.0**, record 3371780 | `audio_mono-mic.zip` 0.66GB + annotation 0.04GB | v7 보고 전용 360원천; 학습·checkpoint 선택 제외 |

¹ 1GB = 1,000,000,000 bytes. 압축본, 해제한 원본, 가공 WAV를 각각 보관할 공간이 필요합니다. v7 학습에는 초기 ML-DF/ODSS나 후속 AIME/ACE-Step를 추가하지 않습니다. 이들은 아래에 별도로 설명합니다.

다운로드 후 출처·버전·원본 해시와 이용 조건을 함께 보관합니다. 파일별 정확한 URL·바이트 수·해시·해시 출처는 [dataset_sources.json](../results/dataset_sources.json)에 있습니다. SHA-1/MD5는 배포자가 제공한 파일 동일성 확인값이며 권리 확인이나 최신 보안 보증이 아닙니다.

## 2. 새 clone에서 폴더 준비

macOS/Linux의 `git`, `curl`, Python 3를 사용합니다. 이미 clone했다면 저장소 루트에서 `mkdir`부터 실행합니다. 아래 다운로드 명령은 데이터를 `data/`에 저장하며 이 폴더는 Git에서 제외됩니다.

```bash
git clone https://github.com/jamessung644/deepvoice-dacon-2026.git
cd deepvoice-dacon-2026
mkdir -p data/raw/fma data/raw/maestro data/raw/fakemusiccaps \
  data/raw/echoes data/raw/sonics data/raw/guitarset \
  data/licenses/fma data/licenses/maestro data/licenses/fakemusiccaps \
  data/licenses/echoes data/licenses/sonics data/licenses/guitarset
```

한 자료씩 실행하고 아래 **4번 해시 검사**를 통과한 뒤 해제·가공합니다. `-C -`는 중단된 다운로드를 이어받습니다. 일부 파일이 남아도 완료로 판단하지 않습니다. 로그인·동의·접근 제한이 새로 생기면 원 배포처의 정식 절차를 따릅니다.

## 3. v7 음악 원천 다운로드

### FMA Small + metadata

[공식 README](https://github.com/mdeff/fma#data)가 안내하는 원본 URL입니다. metadata의 `tracks.csv`에서 곡·아티스트·라이선스를 먼저 확인합니다. metadata는 CC-BY-4.0이지만 **오디오는 아티스트가 정한 곡별 라이선스**입니다. 당시 프로젝트는 ND 곡을 가공·학습 전에 제외했으며, 전체 ZIP이 일괄 학습 허가를 뜻하지 않습니다.

```bash
curl -fL --retry 3 -C - -o data/raw/fma/fma_metadata.zip \
  'https://os.unil.cloud.switch.ch/fma/fma_metadata.zip'
curl -fL --retry 3 -C - -o data/raw/fma/fma_small.zip \
  'https://os.unil.cloud.switch.ch/fma/fma_small.zip'
curl -fL --retry 3 -o data/licenses/fma/README.md \
  'https://raw.githubusercontent.com/mdeff/fma/607364e7d8263f890d23c838802f29637600611f/README.md'
```

### MAESTRO v3.0.0

[공식 v3 설명](https://magenta.tensorflow.org/datasets/maestro#v300)의 CSV와 라이선스 페이지부터 받습니다. **MIDI-only ZIP에는 학습용 실제 WAV가 없습니다.** v2를 받으면 v3와 자료 및 분할이 달라집니다. 배포 조건은 CC-BY-NC-SA-4.0입니다.

```bash
curl -fL --retry 3 -o data/raw/maestro/maestro-v3.0.0.csv \
  'https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0.csv'
curl -fL --retry 3 -o data/licenses/maestro/source_page.html \
  'https://magenta.tensorflow.org/datasets/maestro'
```

다음은 **108.45GB 전체 오디오+MIDI 다운로드**입니다. 필요한 저장 공간을 확인한 뒤에만 실행합니다.

```bash
curl -fL --retry 3 -C - -o data/raw/maestro/maestro-v3.0.0.zip \
  'https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0.zip'
```

원 프로젝트는 HTTP ZIP 범위 요청으로 160개 연주(train 120 / validation 20 / test 20)의 원본 WAV·MIDI를 선택 취득했고, v7의 train/dev는 120/20개를 사용했습니다. 공개본에는 그 선택 manifest와 범위 취득 실행기가 없으므로 임의의 140개를 고르면 동일한 v7 풀이 되지 않습니다. 전체 ZIP의 공식 SHA-256과 선택 member의 CRC/개별 SHA-256 검증도 구분합니다.

### FakeMusicCaps

[원 Zenodo record](https://zenodo.org/records/15063698)의 생성 음원 ZIP만 받습니다. 배포 조건은 CC-BY-NC-4.0입니다. MusicCaps의 YouTube 실제 음원은 이 명령의 대상이 아닙니다. 같은 caption에서 나온 여러 생성 음원을 분할 간 나누지 않도록 caption 식별자가 필요합니다.

```bash
curl -fL --retry 3 -o data/licenses/fakemusiccaps/zenodo_record.json \
  'https://zenodo.org/api/records/15063698'
curl -fL --retry 3 -o data/licenses/fakemusiccaps/LICENSE \
  'https://raw.githubusercontent.com/polimi-ispl/FakeMusicCaps/cd80fa3363c761f6b129c0a7a7a57257d75f11c5/LICENSE'
curl -fL --retry 3 -C - -o data/raw/fakemusiccaps/FakeMusicCaps.zip \
  'https://zenodo.org/api/records/15063698/files/FakeMusicCaps.zip/content'
```

### Echoes

[원 배포처](https://huggingface.co/datasets/Octavian97/Echoes)의 고정 revision을 사용합니다. 배포 조건은 CC-BY-SA-4.0입니다. ZIP의 CSV manifest에서 `path_in_dataset`, `original_audio`, `generator`, `type`를 보존합니다. 같은 원본 음악에서 유래한 TTA/ATA 파일을 연결 원천으로 검사해야 합니다.

```bash
curl -fL --retry 3 -o data/licenses/echoes/README.md \
  'https://huggingface.co/datasets/Octavian97/Echoes/resolve/14b0c76c6a691c42fadfab9fb6a4eb1ee8c628a2/README.md?download=true'
curl -fL --retry 3 -C - -o data/raw/echoes/Echoes.zip \
  'https://huggingface.co/datasets/Octavian97/Echoes/resolve/14b0c76c6a691c42fadfab9fb6a4eb1ee8c628a2/Echoes.zip?download=true'
```

### SONICS · 생성 part_10만

[고정 파일 목록](https://huggingface.co/datasets/awsaf49/sonics/tree/3788dca9f9f11ad92e9097ef4b58eee247661e7f/fake_songs)에서 `part_10.zip`, `metadata.json`, `fake_songs.csv`를 받습니다. 데이터는 CC-BY-NC-4.0이며 코드의 MIT 라이선스와 다릅니다. 실제 노래 오디오는 이 프로젝트의 v7 취득 대상이 아닙니다.

```bash
curl -fL --retry 3 -o data/licenses/sonics/README.md \
  'https://huggingface.co/datasets/awsaf49/sonics/resolve/3788dca9f9f11ad92e9097ef4b58eee247661e7f/README.md?download=true'
curl -fL --retry 3 -C - -o data/raw/sonics/metadata.json \
  'https://huggingface.co/datasets/awsaf49/sonics/resolve/3788dca9f9f11ad92e9097ef4b58eee247661e7f/metadata.json?download=true'
curl -fL --retry 3 -C - -o data/raw/sonics/fake_songs.csv \
  'https://huggingface.co/datasets/awsaf49/sonics/resolve/3788dca9f9f11ad92e9097ef4b58eee247661e7f/fake_songs.csv?download=true'
curl -fL --retry 3 -C - -o data/raw/sonics/part_10.zip \
  'https://huggingface.co/datasets/awsaf49/sonics/resolve/3788dca9f9f11ad92e9097ef4b58eee247661e7f/fake_songs/part_10.zip?download=true'
```

당시 선별은 part_10 오디오와 metadata가 일치하는 행에서 `target=1`, `no_vocal=False`, `skip_time>0`를 확인했습니다. 원래 valid/test 사이에 공통 song ID가 있어 저자 split을 무검사로 복사하지 않습니다. 프로젝트의 연결 ID 분할과 추가 선별을 거친 v7 SONICS는 train 2,654 / dev 462원천이었습니다. ZIP 전체를 그대로 학습에 넣으면 이 분할을 재현할 수 없습니다.

### GuitarSet v1.1.0 · 보고 전용

[Zenodo v1.1.0](https://zenodo.org/records/3371780)에서 mono microphone 녹음과 주석을 받습니다. 배포 조건은 CC-BY-4.0입니다. 다른 pickup/multichannel 버전으로 대체하지 않습니다. 당시 360개는 개발 보고 전용으로 사용했으며 학습이나 checkpoint 선택에 넣지 않았습니다.

```bash
curl -fL --retry 3 -o data/licenses/guitarset/zenodo_record.json \
  'https://zenodo.org/api/records/3371780'
curl -fL --retry 3 -C - -o data/raw/guitarset/annotation.zip \
  'https://zenodo.org/api/records/3371780/files/annotation.zip/content'
curl -fL --retry 3 -C - -o data/raw/guitarset/audio_mono-mic.zip \
  'https://zenodo.org/api/records/3371780/files/audio_mono-mic.zip/content'
```

## 4. 받은 파일의 크기·해시 확인

저장소 루트에서 아래를 실행합니다. Python 표준 라이브러리만 사용합니다. **현재 존재하는 catalog 파일만** 검사하고 미취득 파일은 `MISSING`으로 표시합니다. 자료 일부만 받을 때도 사용할 수 있으며, `OK`인 파일을 확인한 뒤 그 자료만 해제합니다. 한 파일이라도 크기·해시가 다르면 실패합니다. 수십 GB 파일 검사는 시간이 걸립니다.

```bash
python3 - <<'PY'
import hashlib
import json
from pathlib import Path

catalog = json.loads(Path('results/dataset_sources.json').read_text())
checked = 0
for dataset in catalog['datasets']:
    for item in dataset['files']:
        path = Path(item['path'])
        if not path.is_file():
            print('MISSING', path)
            continue
        if path.stat().st_size != item['bytes']:
            raise SystemExit(f'SIZE MISMATCH: {path}')
        algorithm, expected = item['checksum'].split(':', 1)
        digest = hashlib.new(algorithm)
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                digest.update(chunk)
        if digest.hexdigest() != expected:
            raise SystemExit(f'HASH MISMATCH: {path}')
        print('OK', path)
        checked += 1
if checked == 0:
    raise SystemExit('검사할 다운로드 파일이 없습니다.')
print(f'검사한 파일 {checked}개 일치. MISSING 파일의 취득 완료를 뜻하지 않습니다.')
PY
```

해시는 [배포자 FMA README](https://github.com/mdeff/fma#usage), [MAESTRO 페이지](https://magenta.tensorflow.org/datasets/maestro), 각 Zenodo record API, 고정 HF LFS 객체에서 가져왔습니다. SONICS `metadata.json`의 SHA-256은 당시 프로젝트 기록이며 배포자 공표값으로 표시하지 않았습니다. 동일 파일인지 확인한 뒤에도 파일별 권리·라벨 확인은 별도입니다.

ZIP을 해제할 때는 목록을 먼저 확인하고 자료별 새 출력 폴더를 사용합니다. 원본 압축본을 보존한 채 가공본을 따로 저장합니다. 예를 들어 해시 확인을 마친 GuitarSet만 다음처럼 확인·해제할 수 있습니다.

```bash
unzip -l data/raw/guitarset/audio_mono-mic.zip
mkdir -p data/extracted/guitarset/audio_mono-mic
unzip -n data/raw/guitarset/audio_mono-mic.zip \
  -d data/extracted/guitarset/audio_mono-mic
```

## 5. 기존 v7 재학습에 추가로 필요한 것

다음 이름은 **보관 작업본의 구성 식별자**입니다. 현재 공개 저장소에서 실행할 수 있는 파일 링크나 명령이 아닙니다. `scripts/download_sources.py`와 download config 역시 공개본에 없으므로, 이 문서는 위의 `curl` 명령과 공개 catalog를 사용합니다.

| 단계 | 보관 작업본의 관련 파일 | 공개본에서 남은 재현 공백 |
|---|---|---|
| 원본 취득 | `download_sources.py`, `download_range_lock.py`, `fetch_real_music_v3.py`, 자료별 download JSON | MAESTRO 선택 member 목록·취득 receipt와 전체 원본 대조 |
| 원천 선별·라벨·분할 | `prepare_music_fake_sources_v4.py`, `prepare_music_fake_source_extensions_v4.py`, `materialize_music_fake_sources_v5.py`, `expand_music_fake_real_sources_v5.py` | 정확한 FMA/caption/song/original 연결 목록, 불량·권리 제외 목록, 최종 source manifest |
| 음악 분리·뷰 저장 | `prepare_music_stems_v4.py`, `prepare_music_stems_v4_sharded_v2.py`, `merge_music_fake_stem_shards_v4.py`, `materialize_music_fake_views_v5.py` | 원천과 연결된 가공 WAV·view manifest, HTDemucs/codec 버전·파라미터·해시 |
| 학습·선택 | `train_music_fake_v1.py`, `train_music_fake_v5.py`, train JSON과 실행 당시 코드 사본 | 고정 split·sampling·환경·선택 지표, optimizer/EMA/checkpoint 및 실제 사용 뷰 기록 |
| 전체 추론 | v7 보관 제출본의 실행 코드 + 외부 사전학습 자산 | 전체 5출력 런타임, 6개 가중치, 오프라인 통합검사 |

공개 `music_fake_model_v1.py` / `music_fake_model_v5.py`는 모델 정의이며 학습 실행기가 아닙니다. 모델 정의를 import하거나 회귀 테스트를 통과해도 재학습 완료가 아닙니다. 재시작할 때는 위 구성과 원본·가공 실파일이 모두 연결되는지 먼저 확인해야 합니다.

분할은 원곡·caption·song ID·동일 오디오 및 연결 원천을 묶어 만들고, 원본 파일/PCM 해시로 분할 간 중복을 검사합니다. 미확인 성분 라벨은 `null`로 남깁니다. 실제 파일에서 파생된 특정 crop의 음성·음악 존재를 원본 전체 라벨만으로 단정하지 않습니다. 대회 평가 데이터는 학습·튜닝에 넣지 않습니다.

당시 풀·seed·입력·증강·선택 epoch은 [DATASETS](DATASETS.md), 모델 결합은 [V7_ARCHITECTURE](V7_ARCHITECTURE.md), 당시 장비·환경은 [TRAINING_ENVIRONMENT](TRAINING_ENVIRONMENT.md)에 있습니다. 이 정보는 재현 준비를 돕지만 정확한 source/view manifest와 실행 코드의 대체물이 아닙니다. 동일 seed만으로 동일 checkpoint나 DACON 점수를 보장하지 않습니다.

## 6. 초기 음성 실험 · 필요할 때만

이 자료는 v7의 외부 완성 Forensics 가중치를 우리가 학습한 자료가 아닙니다.

| 자료 | 공식 배포본 / 파일 | 역할·조건 |
|---|---|---|
| [ML-DF](https://zenodo.org/records/17098081) | record 17098081 v1.0, `dataset_IT.7z` 1.49GB + `metadata.zip` | 초기 이탈리아어 음성 실험; CC-BY-4.0 |
| [ODSS](https://zenodo.org/records/8370669) | record 8370669, `odss.zip` 2.40GB | 초기 외부 평가; **학습 자료 아님**. 배포 설명에 CC-BY-SA-4.0 명시(API license 필드는 비어 있음) |

```bash
mkdir -p data/raw/mldf data/raw/odss data/licenses/mldf data/licenses/odss
curl -fL --retry 3 -o data/licenses/mldf/zenodo_record.json \
  'https://zenodo.org/api/records/17098081'
curl -fL --retry 3 -C - -o data/raw/mldf/dataset_IT.7z \
  'https://zenodo.org/api/records/17098081/files/dataset_IT.7z/content'
curl -fL --retry 3 -C - -o data/raw/mldf/metadata.zip \
  'https://zenodo.org/api/records/17098081/files/metadata.zip/content'
curl -fL --retry 3 -o data/licenses/odss/zenodo_record.json \
  'https://zenodo.org/api/records/8370669'
curl -fL --retry 3 -C - -o data/raw/odss/odss.zip \
  'https://zenodo.org/api/records/8370669/files/odss.zip/content'
```

4번 검사기는 이 파일들도 검증합니다. ML-DF의 `.7z` 해제에는 7-Zip 지원 도구가 필요합니다. 원 배포 metadata/protocol에 따라 실험 split과 연결 발화 그룹을 복원해야 하며, 보관된 프로젝트 split manifest 없이 무작위로 나누면 초기 결과의 재현이 아닙니다.

## 7. 후속 v12 · AIME와 자체 ACE-Step 생성

v12 baseline/AIME 후보는 별도 실험입니다. v7의 기존 음악 CNN 학습풀에 포함되지 않았고, 작동 검사만으로 v7보다 성능이 좋아졌다고 판단할 수 없습니다.

**AIME:** [고정 revision 파일 목록](https://huggingface.co/datasets/disco-eth/AIME/tree/b84d4be5eda830b6eb714998569dba73530f2601/data)은 Parquet 210개, 합계 62.28GB입니다. [데이터 카드](https://huggingface.co/datasets/disco-eth/AIME/blob/b84d4be5eda830b6eb714998569dba73530f2601/README.md)는 생성 음원 6,000개(CC-BY-4.0), MTG-Jamendo 실제 음원 500개(곡별 조건), `description` 태그(CC-BY-NC-SA-4.0)를 구분합니다. 이 프로젝트는 **생성기당 100개, 총 1,200개 생성 음원만** 선택했고 실제 음원과 description을 학습에 사용하지 않았습니다. 전체 저장소의 CC-BY 태그를 모든 필드에 적용하지 않습니다.

우선 카드와 고정 shard 목록만 보관합니다. 아래는 대용량 shard나 오디오를 내려받지 않습니다.

```bash
mkdir -p data/licenses/aime
curl -fL --retry 3 -o data/licenses/aime/README.md \
  'https://huggingface.co/datasets/disco-eth/AIME/resolve/b84d4be5eda830b6eb714998569dba73530f2601/README.md'
curl -fL --retry 3 -o data/licenses/aime/shard_tree.json \
  'https://huggingface.co/api/datasets/disco-eth/AIME/tree/b84d4be5eda830b6eb714998569dba73530f2601/data'
```

오디오 다운로드 URL의 형식은 `https://huggingface.co/datasets/disco-eth/AIME/resolve/b84d4be5eda830b6eb714998569dba73530f2601/data/train-00000-of-00210.parquet`처럼 shard 목록의 정확한 `path`를 붙입니다. 각 shard의 `lfs.oid`는 SHA-256입니다. `train`이라는 배포 split 이름은 이 프로젝트의 학습/검증 split을 대신하지 않습니다. 기존 1,200개를 다시 받으려면 `build_aime_selection_v1.py` / `acquire_aime_selected_v1.py`와 선택 manifest·receipt가 필요하며 이 파일들은 공개본에 없습니다. Parquet에는 오디오 외의 필드도 있으므로 `id`, `model`, `audio`만 추출하는 과정과 생성/실제 구분을 확인해야 합니다.

**ACE-Step:** [코드](https://github.com/ace-step/ACE-Step/tree/1bee4c9f5b43e30995f8d4d33b3919197ce1bd68) revision `1bee4c9f5b43e30995f8d4d33b3919197ce1bd68`, [v1-3.5B 모델](https://huggingface.co/ACE-Step/ACE-Step-v1-3.5B/tree/82cd0d7b6322bd28cd4e830fe675ddb6180ce36c) revision `82cd0d7b6322bd28cd4e830fe675ddb6180ce36c`를 사용했습니다. 고정 코드 LICENSE와 모델 카드는 Apache-2.0을 명시합니다. **모델 다운로드는 기존 256개 생성 오디오 다운로드가 아닙니다.** 당시 prompt·seed·길이·생성 코드·출력 해시와 실제 생성 WAV가 필요합니다. 모델 파일 총량은 8.28GB이며 생성에는 별도 GPU 환경이 필요합니다.

고정 원문만 확인·보관하려면 다음을 사용합니다.

```bash
mkdir -p data/licenses/acestep_v1
curl -fL --retry 3 -o data/licenses/acestep_v1/LICENSE \
  'https://raw.githubusercontent.com/ace-step/ACE-Step/1bee4c9f5b43e30995f8d4d33b3919197ce1bd68/LICENSE'
curl -fL --retry 3 -o data/licenses/acestep_v1/MODEL_CARD.md \
  'https://huggingface.co/ACE-Step/ACE-Step-v1-3.5B/resolve/82cd0d7b6322bd28cd4e830fe675ddb6180ce36c/README.md'
```

사용 목적, 가공·모델·생성 결과의 배포 범위, 원 파일별 고지 및 적용되는 대회 규정을 확인합니다. 이 안내와 과거 채점 성공은 상업 이용이나 재배포 허가를 보증하지 않습니다. 이 저장소에는 원음·가공 오디오·대회 평가 자료를 올리지 않습니다.
