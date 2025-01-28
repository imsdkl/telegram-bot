# Telegram forwarder auth client


# How to setup
```
pip install -r requirements.txt
```

# Run

```
python main_bot.py
```

# ENV

Check .env.example


# Build docker
```
docker build -t tg-bot-auth .
```

# Run docker with envs

```
docker stop auth-bot
docker rm auth-bot
docker run -d --env-file .env --name auth-bot tg-bot-auth
```
