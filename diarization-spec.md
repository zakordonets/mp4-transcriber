# ТЗ на добавление диаризации

## Контекст
Проект MP4 Transcriber уже поддерживает транскрибацию видео через Whisper и ffmpeg, работает в CPU-only режиме, имеет CLI-команды для одиночной и пакетной обработки и умеет экспортировать TXT, SRT, VTT и JSON.

Цель документа — добавить speaker diarization без регресса базового сценария использования и без повторного попадания в платформенно-хрупкий стек зависимостей.

## Цель
Добавить опциональную возможность определять смену спикеров и размечать сегменты транскрипта метками `SPEAKER_00`, `SPEAKER_01` и т.д., сохранив стабильность существующего CPU-only CLI на Windows.

## Критерий успеха
- Команда без диаризации работает ровно как раньше.
- Команда с диаризацией на поддерживаемом окружении добавляет метки спикеров в результат.
- При отсутствии diarization-зависимостей приложение не падает на импорте и не ломает базовую транскрибацию.

## Scope

### Что входит в первую версию
- CLI-флаг `--diarize`
- Параметр `--diarization-backend <name>`
- Список speaker segments и привязка текстовых сегментов к спикерам
- Расширение JSON/TXT/SRT/VTT speaker labels
- Проверка состояния diarization в `check`
- Отдельная optional-группа зависимостей

### Что не входит
- Обязательная интеграция именно с WhisperX
- Идентификация людей по именам
- Overlapped speech detection
- Real-time diarization
- GPU-first оптимизация

## Принципы реализации
- Diarization — это независимый слой post-processing поверх текущего ASR-пайплайна.
- Зависимости diarization должны импортироваться лениво и только по требованию.
- Базовая установка проекта не должна тянуть platform-specific зависимости ради необязательной функции.
- Архитектура не должна быть завязана на один backend.

## Функциональные требования
1. Добавить CLI-флаг `--diarize`.
2. Добавить параметр `--diarization-backend <name>`.
3. При активной diarization возвращать `speaker_segments`, `speakers` и `segments[].speaker`.
4. TXT/SRT/VTT должны уметь выводить speaker labels.
5. Batch mode должен поддерживать diarization без изменения существующей модели обработки.
6. Команда `check` должна показывать доступность backend и отсутствующие optional packages.

## Нефункциональные требования
- Текущая транскрибация без `--diarize` не должна менять поведение.
- Целевая среда первой очереди — Windows + CPU-only.
- Нельзя делать WhisperX обязательной зависимостью проекта.
- Нельзя требовать TorchCodec в базовой установке проекта, если пользователь не активировал diarization.
- При отсутствии backend приложение должно выдавать понятную диагностическую ошибку или предупреждение.
- Новые зависимости должны быть вынесены в отдельный файл `requirements-diarization.txt` либо в optional extra.

## Dependency policy
Diarization must be implemented via an optional backend with isolated dependencies. The base installation must remain Windows-friendly and CPU-safe, and diarization packages must be imported lazily only when the feature is explicitly enabled.

## Архитектурные требования
- Ввести интерфейс `BaseDiarizer`
- Ввести `DiarizationResult`
- Реализовать `assign_speakers_to_segments(...)`
- Добавить `NoOp`/`Null` backend
- Выбор backend делать через CLI/конфиг

### Рекомендуемый пайплайн
1. Extract audio через существующий ffmpeg-слой
2. Transcribe audio через текущий Whisper-пайплайн
3. Выполнить diarization только если включен `--diarize`
4. Склеить transcript segments и speaker segments
5. Сериализовать результат с учетом speaker labels

## CLI и UX

### Целевые команды
```bash
python main.py transcribe --input interview.mp4 --diarize
python main.py transcribe --input interview.mp4 --diarize --diarization-backend pyannote
python main.py batch --input ./videos --diarize
```

### Требования к сообщениям пользователю
- Если backend недоступен, сообщение должно быть прикладным и без длинного traceback.
- `check` должен показывать diarization support, active backend, missing packages.
- Batch mode не должен останавливаться из-за единичной ошибки diarization.

## Формат результата

```json
{
  "text": "Добрый день...",
  "language": "ru",
  "segments": [
    {
      "start": 0.0,
      "end": 3.2,
      "text": "Добрый день",
      "speaker": "SPEAKER_00"
    }
  ],
  "speaker_segments": [
    {
      "speaker": "SPEAKER_00",
      "start": 0.0,
      "end": 5.4
    }
  ],
  "speakers": ["SPEAKER_00", "SPEAKER_01"],
  "source_file": "./videos/interview.mp4"
}
```

## Обработка ошибок и graceful degradation
- Если `--diarize` не задан, код diarization не должен участвовать в startup path.
- Если backend не установлен, приложение должно предложить установить optional requirements или выполнить команду без diarization.
- Если diarization завершилась ошибкой в permissive-режиме, транскрибация может быть сохранена без speaker labels с предупреждением.

## Тестирование
- Unit tests на маппинг speaker segments к transcript segments
- CLI tests на сценарии с `--diarize` и без него
- Smoke test на Windows CPU-only без diarization dependencies
- Smoke test на поддерживаемом окружении с установленным backend
- Regression test для `check`, `transcribe`, `batch`, `models`

## Критерии приемки
- Команда без `--diarize` работает как до изменения.
- Команда с `--diarize` на поддерживаемом окружении завершает транскрибацию и добавляет speaker labels в JSON.
- На Windows CPU-only окружении без diarization dependencies приложение не падает на импорте.
- `check` показывает доступность или недоступность diarization backend.
- Batch processing не обрывает весь пакет из-за единичной ошибки diarization.

## Формулировка задачи для Codex
```text
Add optional speaker diarization to the existing CPU-only Windows-friendly Whisper + ffmpeg transcription CLI.
Do not make WhisperX a mandatory dependency.
Keep the current transcription flow unchanged when diarization is disabled.
Implement diarization as a separate backend interface with lazy imports.
Add --diarize and --diarization-backend flags.
Extend JSON output with speaker labels and speaker segments.
Add environment validation to the check command.
Keep compatibility with current transcribe, batch, check, and models commands.
```

## Итоговая рекомендация
Формулировать задачу как “добавить расширяемый механизм diarization без ухудшения базовой Windows/CPU установки”, а не как “добавить WhisperX”.
