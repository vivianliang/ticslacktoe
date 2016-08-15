# Tic slack toe

A tic slack toe slash command for Slack

## Usage

The app is hosted at `https://tickslacktoe.herokuapp.com/`. (Note spelling tic**k**).
Since the Heroku free dyno goes to sleep, please visit that URL in the browser before
accessing via Slack.

In the Slack team where the app is installed, use:
`/ticslacktoe help` to see usage commands.

1. To connect your username `/ticslacktoe connect`
2. To show current board `/ticslacktoe show`
3. To start a game with another user `/ticslacktoe start [username]` where username is a user
   that has connected (1) at some time.
4. To play a move on your turn `/ticslacktoe play [x] [y]` where x and y are coordinates 0-2
   on the board:

```
|0 2|1 2|2 2|
|0 1|1 1|2 1|
|0 0|1 0|2 0|
```
