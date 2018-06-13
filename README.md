# TelegramNewsticker
A Telegram bot impementing a newsticker based on Google Calendar events.

# Exemplary interaction with the bot

![Screenshot of adding an event with the bot](/img/user_interface_screenshot.png)

# Usage

1. Copy `example_config.ini` to `config.ini`
2. Set config parameters in `config.ini` accordingly
3. Run `bot.py`. You should now be able to chat with the bot, and add it to Telegram groups

# Configuration parameters

## TelegramAccessToken

The access token you get from BotFather after creating the bot.

## AllowedChatIds

The [chat ids](https://core.telegram.org/bots/api#chat) that are allowed to communicate with the bot. This parameter accepts the empty list `[]`, which disables access control (i.e., everyone can communicate with the bot). To get the chat id of a group or a user, set this parameter to an invalid chat id so that access control is enabled, and send a message to the bot. The chat id will be shown on the console output.

## CalendarClientSecretFile

The path to `client_id.json` (or similar). You can download this file from the [Google API Console](https://console.developers.google.com/).

## CalendarID

The calendar ID for the calendar to be used for data storage. E.g. `foobarquxbaz@group.calendar.google.com`.
