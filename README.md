# walze

dice roller bot with some stuff

## It is recommended to back up `stats.json` frequently

## Set-up instructions

1. Make an `Config.toml` file in the project source directory with your Discord bot token and any other configuration variables

    Example config file:

    ```toml
    # All the numbers in this example are randomly generated.
    # Angled brackets should be removed when values are replaced by real data.

    [owner]
    # Bot owner's ID
    id = 722379980443142249
    # Servers denoted by their IDs where administrator commands should be shown. (Eg. /kill, or /unstable commands)
    servers = [305487992852808329, 817597115771594450]

    [tokens]
    # Your discord bot token.
    # TIP: A valid token starts with M, N or O and has 2 dots.
    discord = "<a valid discord bot token>"

    [log]
    # File where walze should store logs.
    file = "bot.log" # deleting this line will print all logs to the terminal instead

    [barred]
    # Any users (denoted by their IDs) you may want to bar from using the bot.
    users = [859371497610690861, 240239511032785293]

    ```

1. Install python dependencies with `pip` (assuming you have python >= v3.10

    ```shell
    pip install -r requirements.txt 
    ```

1. Run the bot with

    ```shell
    python main.py
    ```
