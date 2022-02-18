import configparser


class Config:
    _path = 'config.ini'

    def __init__(self):
        config = self.read_config()
        self.token = config.get("wordle-bot", "token", fallback=None)
        self.testtoken = config.get("wordle-bot", "testtoken", fallback=None)

    @staticmethod
    def read_config() -> configparser.ConfigParser:
        """Return the config.properties file as a dictionary. If the file does not exist, generate a new one."""
        config = configparser.ConfigParser()
        config.read(Config._path)
        if not config.has_section("wordle-bot"):
            with open(Config._path, "w") as file:
                lines = ["[wordle-bot]\n",
                         "token=enterTokenHere\n",
                         "testtoken=enterTokenHere\n"]
                file.writelines(lines)
            return Config.read_config()
        return config
