from typing import Tuple, List
from pymongo.mongo_client import MongoClient


class Client:
    """Data access interface for MongoDB database for use with wordle-bot.

    The database has collections this collection:

    players:
        - _id
        - scores (Dictionary with Wordle number keys and score values)
        - count (number of scores)
        - win_count (number of scores that are not 7, for average computation)
        - average
    """

    def __init__(self):
        """Initialize a new Client connected to the local MongoDB instance."""
        self.mongo = MongoClient()
        self.wordle_db = self.mongo.wordle
        self.worldle_db = self.mongo.worldle
        self.subwaydle_db = self.mongo.subwaydle
        self.taylordle_db = self.mongo.taylordle
        self.nerdle_db = self.mongo.nerdle
        self.lewdle_db = self.mongo.lewdle

    def get_db_by_game_abbreviation(self, game_abbreviation):
        if game_abbreviation == "wb":
            return self.wordle_db
        elif game_abbreviation == "wlb":
            return self.worldle_db
        elif game_abbreviation == "sb":
            return self.subwaydle_db
        elif game_abbreviation == "tb":
            return self.taylordle_db
        elif game_abbreviation == "nb":
            return self.nerdle_db
        elif game_abbreviation == "lb":
            return self.lewdle_db

    def add_score(self, game_abbreviation: str, pid: int, game_number: str, score: int) -> bool:
        db = self.get_db_by_game_abbreviation(game_abbreviation)

        """Adds a score to the relevant player in the database. If a score already exists, return False."""
        player = db.players.find_one({'_id': pid})
        if player is not None and game_number in player["scores"]:
            return False

        if player is None:
            # make a new one!
            player = {
                "_id": pid,
                "scores": {},
                "count": 0,
                "win_count": 0,
                "average": 0,
                "win_rate": 0
            }

        player["scores"][game_number] = score
        player["count"] += 1
        player["win_count"] = player["win_count"] if score == 7 else player["win_count"] + 1
        player["average"] = player["average"] + \
            (score - player["average"]) / (player["count"])
        player["win_rate"] = player["win_count"] / player["count"]

        db.players.replace_one({"_id": pid}, player, True)

        return True

    def get_player_stats(self, game_abbreviation: str, pid: int) -> Tuple[float, int, int, float]:
        """Return the stats of the player with provided id, given as a tuple in the form
        (average, count, win_count, win_rate).
        """
        db = self.get_db_by_game_abbreviation(game_abbreviation)

        player = db.players.find_one({'_id': pid})

        if player is None:
            return 0.0, 0, 0, 0

        return player["average"], player["count"], player["win_count"], player["win_rate"]

    def delete_player(self, game_abbreviation: str, pid: int) -> bool:
        """Return True iff the player with pid was successfully deleted."""
        db = self.get_db_by_game_abbreviation(game_abbreviation)
        result = db.players.delete_one({"_id": pid})
        if result.deleted_count != 0:
            return True
        return False

    def get_game_stats_for_today(self, game_abbreviation: str) -> List:
        db = self.get_db_by_game_abbreviation(game_abbreviation)

        # get most recent game number
        most_recent_game = 0
        for player in db.players:
            if player.scores[-1].key > most_recent_game:
                most_recent_game = player.scores[-1].key

        # compile scores
        scores = []

        for player in db.players:
            if player.scores[most_recent_game] is not None:
                scores.append((player._id, player.scores[most_recent_game]))

        return scores
