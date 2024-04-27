# Language-bot

Telegram bot providing basic translation functionality + keeping tack of user's personal
vocabulary with the recognition rating for each word. Additional features includes preparing
personalized tests based on the knowledge of user's word-recognition profile.

Was initially developed for personal use to improve and extend my own vocabulary.
Note, that this is very draft version of the application.
You're using it on your own risk and responsibility. Any meaningful changes and improvements are welcomed.


1. Building docker images  
```bash
./scripts/build_images.sh
```
2. Edit config.json - place your bot token to **TG_API_KEY**


3. Run environment
```bash
BRANCH_NAME=master docker-compose -f ./deploy/docker-compose.yml up languagebot
```
**NOTE**: It might take sometime for libretranslate service to start first time because it should
load language models first. Once being loaded, these models are persisted in docker volumes so
next restarts will take less time

**NOTE2**: PostgreSQL data is not persisted the same way so all the information from DB will be lost
if environment restarted.

 