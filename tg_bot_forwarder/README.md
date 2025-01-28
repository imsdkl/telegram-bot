# Telegram forwarder


# How to setup
```
pip install -r requirements.txt
```

# Build docker
```
docker build -t tg-bot-forwarder-y .
```

# Run docker with envs

```
docker run -d --restart=on-failure:2 --env-file env.list -e PHONE_NUMBER=995571111111 --name bot_995571111111 tg-bot-forwarder
docker run -d --restart=on-failure:2 --env-file .env -e PHONE_NUMBER=998959800566 --name bot_998959800566 forwarder-bot
```

# ENV

check .env.example

HUMO Card has ID 856254490

CardXabar has ID 915326936
