import sys
import configuration
import data
import discord
import re

intents = discord.Intents.default()
intents.members = True
intents.messages = True
client = discord.Client(intents=intents)

database = data.Client()


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message: discord.Message):
    if isTest and not message.channel.name == "wordle-test":
        return

    if message.author == client.user:
        return

    if message.content.startswith("!wb") or message.content.startswith("Wordle"):
        await process_message("wb", ":book: Wordle", "Wordle [0-9]+ [1-6|X]/6", message)
    elif message.content.startswith("!wlb") or message.content.startswith("#Worldle"):
        await process_message("wlb", ":earth_americas: Worldle", "#Worldle #[0-9]+ [1-6|X]/6", message)
    elif message.content.startswith("!sb") or message.content.startswith("Subwaydle"):
        await process_message("sb", ":metro: Subwaydle", "Subwaydle [0-9]+ (\(Weekend Edition\)\s)?[1-6|X]/6", message)
    elif message.content.startswith("!tb") or message.content.startswith("Taylordle"):
        await process_message("tb", ":notes: Taylordle", "Taylordle [0-9]+ [1-6|X]/6", message)
    elif message.content.startswith("!nb") or message.content.startswith("nerdlegame"):
        await process_message("nb", "📐 Nerdle", "nerdlegame\s[0-9]+\s[1-6|X]/6", message)
    elif message.content.startswith("!lb") or message.content.startswith("Lewdle 🍆💦"):
        await process_message("lb", "🍆💦 Lewdle", "Lewdle\s🍆💦\s[0-9]+\s[1-6|X]/6", message)
    elif message.content.startswith("!hb") or message.content.startswith("#Heardle"):
        await process_message("hb", "🔊 Heardle", "#Heardle\s*#[0-9]+", message)


async def process_message(game_abbreviation, game_name, game_regex_string, message):
    if message.content == f"!{game_abbreviation} me":
        stats_string = get_stats_string(game_abbreviation, game_name, message)
        await message.channel.send(stats_string)

    elif message.content == f"!{game_abbreviation} average":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_average(message, game_abbreviation, 10)}")

    elif message.content == f"!{game_abbreviation} rate":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_win_rate(message, game_abbreviation, 10)}")

    elif message.content == f"!{game_abbreviation} games":
        await message.channel.send(f"For **{game_name}**:\n{rankings_by_games_played(message, game_abbreviation, 10)}")

    elif message.content == f"!{game_abbreviation} deletemydata":
        if database.delete_player(game_abbreviation, message.author.id):
            await message.channel.send(
                f"{message.author.nick if message.author.nick is not None else message.author.name}'s "
                f"data has been deleted.")
        else:
            await message.channel.send("I tried to delete your data, but I couldn't find any data for you!")

    elif message.content == f"!{game_abbreviation} today":
        scores = await message.channel.send(scores_for_today(game_abbreviation))

    elif message.content == f"!{game_abbreviation} help" or message.content == f"!{game_abbreviation}":
        # backticks are Discord/Markdown characters for fixed width code type display
        help_string = f"`!{game_abbreviation} help` to see this message\n" \
                      f"`!{game_abbreviation} me` to see your stats\n" \
                      f"`!{game_abbreviation} average` to see server rankings by average number of guesses\n" \
                      f"`!{game_abbreviation} rate` to see server rankings by win rate\n" \
                      f"`!{game_abbreviation} games` to see server rankings by games played\n" \
                      f"`!{game_abbreviation} deletemydata` to remove all your scores from wordle-bot (warning: this is not reversible!)\n" \
                      f"I support multiple games now! Try the above commands with `!wb` (:book: Wordle), `!wlb` (:earth_americas: Worldle), " \
                      f"`!sb` (:metro: Subwaydle), `!tb` (:notes: Taylordle), `!nb` (📐 Nerdle), `!hb` (🔊 Heardle), and `!lb` (🍆💦 Lewdle)."
        await message.channel.send(help_string)

    else:
        game_regex = re.compile(game_regex_string)
        if re.match(game_regex, message.content) is not None:
            await process_game_score(game_abbreviation, game_name, message)


async def process_game_score(game_abbreviation, game_name, message):
    # extract the Wordle number from message
    lines = message.content.splitlines()

    game_number = -1
    score = "X"

    if game_abbreviation == "wlb":
        game_number = lines[0].split(" ")[1]
        score = lines[0].split(" ")[-2][0]
    elif game_abbreviation == "hb":
        game_number_token = lines[0].split(" ")[1]
        # substring to skip the first char (the # character)
        game_number = game_number_token[1:]

        # [0] is the top line and [1] is the blank second line, [2] is the score line
        scoreLine = lines[2]
        score = scoreLine.count("🟩") + scoreLine.count("⬛️")
    elif game_abbreviation == "lb":
        game_number = lines[0].split(" ")[2]
        score = lines[0].split(" ")[-1][0]
    else:
        game_number = lines[0].split(" ")[1]
        score = lines[0].split(" ")[-1][0]

    if score == "X":
        score = "7"
    score = int(score)

    result = database.add_score(
        game_abbreviation, message.author.id, game_number, score)

    if not result:
        await message.channel.send(f"You've already submitted a score for this {game_name}.")
    elif score == 1:
        await message.channel.send("Uh... you should probably go buy a lottery ticket...")
    elif score == 2:
        await message.channel.send("Wow! That's impressive!")
    elif score == 3:
        await message.channel.send("Very nice!")
    elif score == 4:
        await message.channel.send("Not bad!")
    elif score == 5:
        await message.channel.send("Unlucky...")
    elif score == 6:
        await message.channel.send("Cutting it a little close there...")
    else:
        await message.channel.send("I will pretend like I didn't see that one...")

    await message.channel.send(get_stats_string(game_abbreviation, game_name, message))


def get_stats_string(game_abbreviation, game_name, message):
    stats = database.get_player_stats(game_abbreviation, message.author.id)
    player = message.author.nick if message.author.nick is not None else message.author.name
    stats_string = f"{game_name}: **{player}**: **{stats[2]}** wins out of **{stats[1]}** games played " \
        f" (**{round(stats[3] * 100, 4)}%**), averaging **{round(stats[0], 4)}** guesses."

    return stats_string


def scores_for_today(game_abbreviation: str) -> str:
    """Return string formatted leaderboard ordered by number of guesses for specified game for today only"""
    scores = database.get_game_stats_for_today(game_abbreviation)

    scores.sort(key=lambda x: x[1][0])

    scoreboard = "Scores for today:"
    i = 0

    for score in scores:
        i += 1
        scoreboard += f"\n{i} **{score[0]}** **{score[1]}"

    return scoreboard


def rankings_by_average(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by average guesses where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][0])

    scoreboard = "Rankings by average number of guesses:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({round(scores[i][1][0], 4)})"
        i += 1

    return scoreboard


def rankings_by_win_rate(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by win rate where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][3], reverse=True)

    scoreboard = "Rankings by win rate:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({round(scores[i][1][3] * 100, 4)}%)"
        i += 1

    return scoreboard


def rankings_by_games_played(message, game_abbreviation: str, n: int) -> str:
    """Return string formatted leaderboard ordered by number of games played where message is the message data from the
    triggering Discord message and n is the max number of rankings to return.
    """
    members = [(member.nick if member.nick is not None else member.name, member.id)
               for member in message.guild.members]
    scores = []
    for member in members:
        score = database.get_player_stats(game_abbreviation, member[1])
        if score[0] == 0:
            continue
        scores.append((member[0], score))
    scores.sort(key=lambda x: x[1][1], reverse=True)

    scoreboard = "Rankings by games played:"
    i = 0
    while i < n and i != len(scores):
        scoreboard += f"\n{i + 1}. **{scores[i][0]}** ({scores[i][1][1]})"
        i += 1

    return scoreboard


if __name__ == "__main__":
    global isTest

    config = configuration.Config()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        isTest = True
        if config.testtoken == None:
            print("Set \"testtoken\" value in config.ini to the token value from Discord developer site at https://discord.com/developers/applications/<application id>/bot")
        else:
            client.run(config.testtoken)

    else:
        isTest = False
        if config.token == None:
            print("Set \"token\" value in config.ini to the token value from Discord developer site at https://discord.com/developers/applications/<application id>/bot")
        else:
            client.run(config.token)
