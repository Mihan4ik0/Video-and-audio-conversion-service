# Развёртывание сервиса

Первоначально вам следует установить Docker и Docker Compose. Установку можно выполнить, следуя документации на официальных сайтах [docs.docker.com](https://docs.docker.com/) и [docs.docker.com/compose/](https://docs.docker.com/compose/).

## Получение образов

Вы можете загрузить гит репозиторий или скачать уже готовые образы. Если у вас нет образов, вы также можете собрать их самостоятельно с помощью следующих команд:

1. В папке `executor` выполните команду:
```docker build -t converter:latest .```

2. В папке `scheduler` выполните команду:

```docker build -t scheduler:latest .```


## Настройка переменных окружения

Далее необходимо настроить сервис путем задания соответствующих переменных окружения. Введите нужные данные в файле `env.txt`, а затем переименуйте его в `.env`.

### Обязательные настройки в `.env`:

1. Настройте свой часовой пояс `TZ`.
2. Определите переменную `KAFKA_NUM_PARTITIONS` (или `TOTAL_PARTITIONS`), устанавливающую количество желаемых обработчиков.
3. Определите переменные для доступа к базе данных:
- `POSTGRES_USER` - имя пользователя (`DB_USERNAME`)
- `POSTGRES_PASSWORD` - пароль (`DB_PASSWORD`)
- `POSTGRES_DB` - название базы данных (`DB_NAME`)
4. Введите ключи для доступа к MiniO:
- `MINIO_ACCESS_KEY` - ключ доступа (`S3_ACCESS_KEY`)
- `MINIO_SECRET_KEY` - секретный ключ (`S3_ENDPOINT_URL`)
5. Введите желаемое ыколичество часов хранения обработанного материала в переменную `DESIRED_HOURS`.

## Настройка Docker Compose

Откройте файл `docker-compose.yaml` и выполните необходимые изменения в соответствии с инструкцией:

1. Проверьте, что никакие порты не заняты в системе. Если необходимо, измените порты в разделе `ports` для сервисов, чтобы избежать конфликтов.
2. Выставление количества обработчиков:
- Скопируйте сервис `converter-worker-*` столько раз, сколько обработчиков вы желаете (замените `*` на число).
- Для каждого скопированного сервиса назначьте партицию от 0 до `TOTAL_PARTITIONS-1` (взято из `.env`).

## Запуск сервиса

Теперь вы можете запустить сервис с помощью следующей команды:

```docker-compose up -d```


Вы можете проверить состояние сервиса с помощью команды:

```docker-compose ps```

# Использование сервиса

## Первый вариант

1. Откройте `localhost:8000/docs` в вашем браузере.
2. Выберите `/convert`.
3. Выберите желаемый файл и формат.
4. В случае исключительных форматов вы получите уведомление в ответе.
5. Запомните идентификатор (`file_id`) вашей задачи.
6. Затем вы можете отправить запрос на `/files/{file_id}` и получить состояние задачи.
7. В случае ошибки конвертации вам будет предложено повторить отправку задания.

## Второй вариант

Вы также можете отправлять запросы с помощью утилит, таких как Curl.
