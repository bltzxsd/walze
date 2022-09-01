# walze
dice roller bot with some stuff


## set-up instructions

1. make an `.env` file with your bot token as 

```
DISCORD_TOKEN=<your discord token>
```
and then an `HQ` server ID for the server you want the bot to have admin commands in (`/kill` and anything else you might want to add):

```
HQ=<server id>
```

2. install python dependencies with `pip` (assuming you have python >= v3.10

```shell
pip install -r requirements.txt 
```

3. run the bot with 

```shell
python main.py
```
