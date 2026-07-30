import codecs
import json
import os
import random

# Leef: a simple plant watering game for Stream.bot
# Users can water the plant with !leef, view the current status with !leef status,
# and trigger a random streamer task when the plant levels up.
# This version also supports a local command-line test harness for development.

# Stream.bot metadata
ScriptName = "Leef"
Website = "https://github.com/NetherRain/LeefCommandTTV"
Description = "A fun plant watering minigame for Stream.bot with growable plant levels, randomized streamer tasks, and a built-in command-line test mode."
Creator = "NetherRain"
Version = "1.1.0"

SettingsFile = "settings.json"
DataFile = "data.json"
OverlayStateFile = "overlay_state.json"
BarWidth = 20
Parent = None

# Chat emojis for nicer output
WaterEmoji = "💧"
SeedEmoji = "🌱"
PlantEmoji = "🌿"
FlowerEmoji = "🌸"
TreeEmoji = "🌳"
SparkleEmoji = "✨"
StarEmoji = "🌟"

LevelIcons = [
    SeedEmoji,
    SeedEmoji,
    PlantEmoji,
    FlowerEmoji,
    TreeEmoji,
    TreeEmoji,
    StarEmoji,
]


class BotBridge:
    def __init__(self, parent=None):
        self.parent = parent

    def send_message(self, message):
        if self.parent is None:
            print("[BOT]", message)
            return
        if hasattr(self.parent, "send_message"):
            self.parent.send_message(message)
        elif hasattr(self.parent, "SendStreamMessage"):
            self.parent.SendStreamMessage(message)
        elif callable(self.parent):
            self.parent(message)
        else:
            print("[BOT]", message)

    def is_moderator(self, user):
        if self.parent is None:
            return False
        if hasattr(self.parent, "is_moderator"):
            return self.parent.is_moderator(user)
        if hasattr(self.parent, "IsModerator"):
            return self.parent.IsModerator(user)
        return False

    def has_permission(self, user, permission):
        if self.parent is None:
            return False
        if hasattr(self.parent, "has_permission"):
            return self.parent.has_permission(user, permission)
        if hasattr(self.parent, "HasPermission"):
            return self.parent.HasPermission(user, permission)
        if permission == "Moderator" and self.is_moderator(user):
            return True
        return False


class GenericChatData:
    def __init__(self, source):
        self.source = source
        self.UserName = self._extract_user_name(source)
        self._params = self._extract_params(source)

    def IsChatMessage(self):
        return True

    def GetParam(self, index):
        if index < len(self._params):
            return self._params[index]
        return None

    def _extract_user_name(self, source):
        if isinstance(source, dict):
            return source.get("user_name") or source.get("user") or source.get("username") or ""
        return getattr(source, "UserName", None) or getattr(source, "user_name", None) or getattr(source, "user", None) or ""

    def _extract_params(self, source):
        if isinstance(source, dict):
            message = source.get("message") or source.get("text") or source.get("content") or ""
            if isinstance(message, str):
                return message.split()
            params = source.get("params")
            if isinstance(params, (list, tuple)):
                return list(params)
            return []

        if hasattr(source, "message"):
            message = getattr(source, "message")
            if isinstance(message, str):
                return message.split()
        if hasattr(source, "text"):
            message = getattr(source, "text")
            if isinstance(message, str):
                return message.split()
        if hasattr(source, "content"):
            message = getattr(source, "content")
            if isinstance(message, str):
                return message.split()
        if hasattr(source, "params"):
            params = getattr(source, "params")
            if isinstance(params, (list, tuple)):
                return list(params)
        return []


def NormalizeChatData(data):
    if data is None:
        return None
    if hasattr(data, "IsChatMessage") and callable(data.IsChatMessage):
        return data
    if isinstance(data, dict) or hasattr(data, "message") or hasattr(data, "text") or hasattr(data, "content"):
        return GenericChatData(data)
    return data


def ResolveParent(parent=None):
    if isinstance(parent, BotBridge):
        return parent
    if parent is not None:
        return BotBridge(parent)
    if Parent is not None:
        return BotBridge(Parent)
    return BotBridge(None)


def SendBotMessage(message, parent=None):
    ResolveParent(parent).send_message(message)


class Settings(object):
    def __init__(self, settingsFile=None):
        # Default command and gameplay settings
        self.Command = "!leef"
        self.WaterMin = 1
        self.WaterMax = 5
        self.WaterPerLevelBase = 100
        self.WaterScale = 1.25
        self.LevelNames = [
            "Samen",
            "Setzling",
            "Jungpflanze",
            "Blühende Pflanze",
            "Reife Pflanze",
            "Großer Baum",
            "LAZ Baum"
        ]
        self.TaskList = [
            "Du musst 2 Minuten lang Englisch sprechen",
            "Trinke einen Schluck Wasser",
            "Lass den Chat eine Taste wählen, die du 60 Sekunden nicht benutzen darfst",
            "Klatsche nach jedem Kill oder Tod einmal in die Hände",
            "Dreh deine Kopfhörer verkehrt herum bis zum nächsten Match",
            "Lobe den Enemy Spieler, der dich als letztes getötet hat, bis zum Ende des Spiels",
            "Dehnen! Dehne dich, egal in welcher Situation du dich gerade befindest",
            "Wechsle nach dem nächsten Tod den Helden und spiele ihn bis zum Ende des Spiels",
            "Sage nach jedem Tod 'Das war geplant'" ,
            "Sportlich bleiben! Mache 10 Liegestütze"
        ]
        self.EnableStreamMessage = True
        self.Defaults = {
            "Command": self.Command,
            "WaterMin": self.WaterMin,
            "WaterMax": self.WaterMax,
            "WaterPerLevelBase": self.WaterPerLevelBase,
            "WaterScale": self.WaterScale,
            "LevelNames": self.LevelNames,
            "TaskList": self.TaskList,
            "EnableStreamMessage": self.EnableStreamMessage,
        }

        # Load settings from file if a path was provided
        if settingsFile is not None:
            self.SettingsFile = settingsFile
            self.Reload(self.Load())

    def Load(self):
        # Read settings from disk or create default file if missing
        path = os.path.join(os.path.dirname(__file__), SettingsFile)
        if not os.path.exists(path):
            self.Save(self.Defaults)
        with codecs.open(path, encoding="utf-8", mode="r") as f:
            try:
                return json.load(f)
            except:
                return self.Defaults

    def Save(self, data):
        # Save the current settings dictionary to disk
        path = os.path.join(os.path.dirname(__file__), SettingsFile)
        with codecs.open(path, encoding="utf-8", mode="w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def Reload(self, data):
        # Apply loaded settings and normalize typed values
        self.Command = data.get("Command", self.Command)
        self.WaterMin = int(data.get("WaterMin", self.WaterMin))
        self.WaterMax = int(data.get("WaterMax", self.WaterMax))
        self.WaterPerLevelBase = int(data.get("WaterPerLevelBase", self.WaterPerLevelBase))
        self.WaterScale = float(data.get("WaterScale", self.WaterScale))
        self.LevelNames = data.get("LevelNames", self.LevelNames)
        self.TaskList = data.get("TaskList", self.TaskList)
        self.EnableStreamMessage = bool(data.get("EnableStreamMessage", self.EnableStreamMessage))

        # Allow JSON arrays to be stored as strings in settings
        if isinstance(self.LevelNames, str):
            try:
                self.LevelNames = json.loads(self.LevelNames)
            except:
                self.LevelNames = self.Defaults["LevelNames"]
        if isinstance(self.TaskList, str):
            try:
                self.TaskList = json.loads(self.TaskList)
            except:
                self.TaskList = self.Defaults["TaskList"]

        # Write normalized values back to file for consistency
        self.Save({
            "Command": self.Command,
            "WaterMin": self.WaterMin,
            "WaterMax": self.WaterMax,
            "WaterPerLevelBase": self.WaterPerLevelBase,
            "WaterScale": self.WaterScale,
            "LevelNames": self.LevelNames,
            "TaskList": self.TaskList,
            "EnableStreamMessage": self.EnableStreamMessage,
        })


def Init(parent=None):
    global settings, plantData, scriptPath, Parent
    scriptPath = os.path.dirname(__file__)
    settings = Settings(os.path.join(scriptPath, SettingsFile))
    plantData = LoadData()
    if parent is not None:
        Parent = parent
    WriteOverlayState()


def Execute(data, parent=None):
    bridge = ResolveParent(parent)
    data = NormalizeChatData(data)
    if data is None:
        return

    # Only react to chat commands and correct command trigger
    first_param = data.GetParam(0)
    if not data.IsChatMessage() or first_param is None or first_param.lower() != settings.Command.lower():
        return

    user = data.UserName or ""
    second_param = data.GetParam(1)
    param = second_param.lower() if second_param is not None else ""

    if param == "status":
        response = GetStatusMessage()
        bridge.send_message(response)
        return

    if param == "reset" and (bridge.is_moderator(data.UserName) or bridge.has_permission(data.UserName, "Moderator")):
        ResetPlant(user, parent=bridge)
        return

    if param == "help":
        bridge.send_message("!leef gießt die Pflanze zufällig mit 1-5 Wasser. !leef status zeigt den aktuellen Stand.")
        return

    amount = random.randint(settings.WaterMin, settings.WaterMax)
    WaterPlant(user, amount, parent=bridge)


def Tick():
    # Called periodically by Stream.bot; no periodic actions needed here
    return


def ReloadSettings(jsonData):
    settings.Reload(json.loads(jsonData))


def GetDataPath():
    return os.path.join(scriptPath, DataFile)


def LoadData():
    # Load stored plant progress, or initialize defaults if missing/corrupted
    path = GetDataPath()
    if not os.path.exists(path):
        data = {
            "total_water": 0,
            "level": 0,
            "last_task": "",
            "last_user": "",
            "last_action": "",
            "last_amount": 0,
        }
        SaveData(data)
        return data

    with codecs.open(path, encoding="utf-8", mode="r") as f:
        try:
            data = json.load(f)
            data["total_water"] = int(data.get("total_water", 0))
            data["level"] = int(data.get("level", 0))
            data["last_task"] = data.get("last_task", "")
            data["last_user"] = data.get("last_user", "")
            data["last_action"] = data.get("last_action", "")
            data["last_amount"] = int(data.get("last_amount", 0))
            return data
        except:
            return {
                "total_water": 0,
                "level": 0,
                "last_task": "",
                "last_user": "",
                "last_action": "",
                "last_amount": 0,
            }


def SaveData(data=None):
    # Persist plant progress to disk
    path = GetDataPath()
    if data is None:
        data = plantData
    with codecs.open(path, encoding="utf-8", mode="w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    WriteOverlayState()


def WriteOverlayState():
    currentLevel = plantData.get("level", 0)
    totalWater = plantData.get("total_water", 0)
    levelName = GetLevelName(currentLevel)
    waterThisLevel = GetWaterInCurrentLevel(totalWater, currentLevel)
    needed = GetWaterNeededForLevel(currentLevel)
    progress = 100 if needed <= 0 else int(min(100, max(0, round((waterThisLevel / needed) * 100))))
    nextLevelWater = 0 if currentLevel >= len(settings.LevelNames) - 1 else max(0, needed - waterThisLevel)

    state = {
        "level": currentLevel,
        "levelName": levelName,
        "icon": GetLevelIcon(currentLevel),
        "totalWater": totalWater,
        "waterThisLevel": waterThisLevel,
        "needed": needed,
        "progress": progress,
        "nextLevelWater": nextLevelWater,
        "lastTask": plantData.get("last_task", ""),
        "lastUser": plantData.get("last_user", ""),
        "lastAction": plantData.get("last_action", ""),
        "lastAmount": plantData.get("last_amount", 0),
        "maxLevel": len(settings.LevelNames) - 1,
        "isComplete": currentLevel >= len(settings.LevelNames) - 1,
    }

    path = os.path.join(scriptPath, OverlayStateFile)
    with codecs.open(path, encoding="utf-8", mode="w") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)


def GetLevelIcon(level):
    # Choose an emoji icon depending on the current stage
    if level < 0:
        return SeedEmoji
    if level >= len(LevelIcons):
        return LevelIcons[-1]
    return LevelIcons[level]


def GetLevelName(level):
    # Retrieve the display name for the current plant level
    if level < 0:
        return settings.LevelNames[0]
    if level >= len(settings.LevelNames):
        return settings.LevelNames[-1]
    return settings.LevelNames[level]


def GetWaterNeededForLevel(level):
    # Each level requires more water than the previous one
    return int(round(settings.WaterPerLevelBase * (settings.WaterScale ** level)))


def GetLevelFromTotalWater(totalWater):
    # Determine the current level from total water with growing thresholds
    level = 0
    while level < len(settings.LevelNames) - 1:
        threshold = sum(GetWaterNeededForLevel(i) for i in range(level + 1))
        if totalWater < threshold:
            return level
        level += 1
    return len(settings.LevelNames) - 1


def GetWaterInCurrentLevel(totalWater, level):
    # Calculate how much water has been filled in the current level
    previous_needed = sum(GetWaterNeededForLevel(i) for i in range(level))
    return totalWater - previous_needed


def GetProgressBar(current, total, width=BarWidth):
    # Build a simple text bar for progress display
    if total <= 0:
        return "[" + " " * width + "]"

    progress = float(current) / float(total)
    filled = int(round(progress * width))
    empty = width - filled
    return "[{}{}] {}%".format("#" * filled, "-" * empty, int(progress * 100))


def GetStatusMessage():
    maxLevel = len(settings.LevelNames) - 1
    currentLevel = plantData["level"]
    totalWater = plantData["total_water"]
    levelName = GetLevelName(currentLevel)

    currentIcon = GetLevelIcon(currentLevel)
    if currentLevel >= maxLevel:
        return "{icon} Leef Status » Die Pflanze ist voll ausgewachsen als '{name}' mit insgesamt {water} Wasser! {tree}".format(
            icon=currentIcon,
            name=levelName,
            water=totalWater,
            tree=TreeEmoji,
        )

    waterThisLevel = GetWaterInCurrentLevel(totalWater, currentLevel)
    needed = GetWaterNeededForLevel(currentLevel)
    nextLevelWater = needed - waterThisLevel
    progressBar = GetProgressBar(waterThisLevel, needed)
    nextIcon = GetLevelIcon(currentLevel + 1)

    return "{icon} Leef Status » Level {level} '{name}' | {waterEmoji} {water}/{needed} {bar} | Noch {remaining} bis Level {next} {nextIcon}".format(
        icon=currentIcon,
        level=currentLevel,
        name=levelName,
        waterEmoji=WaterEmoji,
        water=waterThisLevel,
        needed=needed,
        bar=progressBar,
        remaining=nextLevelWater,
        next=currentLevel + 1,
        nextIcon=nextIcon,
    )


def GetRequiredWaterForNextLevel(level):
    # Provide a readable value for the next level threshold
    return GetWaterNeededForLevel(level)


def WaterPlant(user, amount, parent=None):
    # Add water and determine whether the plant leveled up
    bridge = ResolveParent(parent)
    maxLevel = len(settings.LevelNames) - 1
    oldLevel = plantData["level"]
    plantData["last_user"] = user
    plantData["last_action"] = "watering"
    plantData["last_amount"] = amount
    plantData["total_water"] += amount
    newLevel = GetLevelFromTotalWater(plantData["total_water"])

    if newLevel > oldLevel:
        plantData["level"] = newLevel
        plantData["last_action"] = "levelup"
        task = random.choice(settings.TaskList)
        plantData["last_task"] = task
        SaveData()
        currentWater = GetWaterInCurrentLevel(plantData["total_water"], newLevel)
        needed = GetWaterNeededForLevel(newLevel)
        progressBar = GetProgressBar(currentWater, needed)
        levelIcon = GetLevelIcon(newLevel)
        message = (
            "{sparkle} {user} gießt die Pflanze mit {amount} Wasser! {water} "
            "Level-Up: {oldLevel} → {newLevel} {levelIcon} '{levelName}' {sparkle} "
            "| {bar} | Aufgabe: {task}"
        ).format(
            user=user,
            amount=amount,
            oldLevel=oldLevel,
            newLevel=newLevel,
            levelIcon=levelIcon,
            levelName=GetLevelName(newLevel),
            task=task,
            water=WaterEmoji,
            sparkle=SparkleEmoji,
            bar=progressBar,
        )
    else:
        SaveData()
        currentWater = GetWaterInCurrentLevel(plantData["total_water"], oldLevel)
        needed = GetWaterNeededForLevel(oldLevel)
        progressBar = GetProgressBar(currentWater, needed)
        levelIcon = GetLevelIcon(oldLevel)
        message = (
            "{plant} {user} gießt die Pflanze mit {amount} Wasser. {water} "
            "Level {level} '{levelName}' | {current}/{needed} | {bar}"
        ).format(
            plant=levelIcon,
            user=user,
            amount=amount,
            water=WaterEmoji,
            level=oldLevel,
            levelName=GetLevelName(oldLevel),
            current=currentWater,
            needed=needed,
            bar=progressBar,
        )

    bridge.send_message(message)


def ResetPlant(user, parent=None):
    # Reset plant progress and inform chat
    bridge = ResolveParent(parent)
    plantData["total_water"] = 0
    plantData["level"] = 0
    plantData["last_task"] = ""
    plantData["last_user"] = user
    plantData["last_action"] = "reset"
    plantData["last_amount"] = 0
    SaveData()
    bridge.send_message("{} hat die Pflanze zurückgesetzt. Sie beginnt wieder bei Level 0 (Samen).".format(user))


class CLITestHarness:
    class DummyParent:
        def send_message(self, message):
            print("[BOT]", message)

        def is_moderator(self, user):
            return True

        def has_permission(self, user, permission):
            return permission == "Moderator"

    class DummyData:
        def __init__(self, user_name, params):
            self.UserName = user_name
            self.params = params

        def IsChatMessage(self):
            return True

        def GetParam(self, index):
            if index < len(self.params):
                return self.params[index]
            return None

    def run(self):
        global Parent
        Parent = CLITestHarness.DummyParent()
        Init()
        print("Leef CMD test mode: enter '!leef', '!leef status', '!leef help', '!leef reset' or 'quit'.")
        while True:
            try:
                line = input('> ').strip()
            except EOFError:
                break
            if not line:
                continue
            if line.lower() in ('quit', 'exit', 'q'):
                break
            tokens = line.split()
            if tokens[0].lower() not in (settings.Command.lower(), '!leef'):
                tokens.insert(0, settings.Command)
            data = CLITestHarness.DummyData('Tester', tokens)
            Execute(data)


if __name__ == "__main__":
    CLITestHarness().run()
