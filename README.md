# Leef - Stream.bot Plant Game

Leef is a simple Twitch chat minigame for Stream.bot. Viewers can water a shared plant with `!leef` and help it grow through multiple levels. When the plant levels up, a random streamer task is assigned for extra interaction.

## Features

- `!leef` waters the plant with a random amount of water (1–5)
- `!leef status` shows the current plant level, water progress, and next level target
- Level progression requires more water at each stage
- Random streamer tasks are triggered at every level-up
- Built-in command-line test mode for development without Stream.bot

## Commands

- `!leef` - water the plant and show progress
- `!leef status` - display the current plant status
- `!leef help` - show help text
- `!leef reset` - moderator-only command to reset the plant

## Setup

1. Place `leef.py` in your Stream.bot script folder or load it through your Stream.bot setup.
2. Start Stream.bot and enable the script.
3. Use chat commands in your Twitch channel to test the game.

## Command-Line Test Mode

If you do not want to run the bot in Stream.bot yet, you can still test the script locally.

1. Open a terminal or command prompt.
2. Run:
   ```bash
   python "path/to/leef.py"
   ```
   or, if you are already in the same folder:
   ```bash
   python leef.py
   ```
3. Enter commands like `!leef`, `!leef status`, `!leef help`, or `!leef reset`.

## Customization

You can modify the following settings directly in `leef.py`:

- `WaterPerLevelBase` - sets the base water amount required for level 1
- `WaterScale` - scales the required water for each next level
- `LevelNames` - define custom names for each level
- `TaskList` - add or change randomized streamer tasks

## Notes

- `data.json` stores the plant progress between runs.
- The built-in test harness is only active when running `leef.py` directly.
- When used in Stream.bot, the test harness does not affect normal bot behavior.

## Credits

Created by `NetherRain`.
