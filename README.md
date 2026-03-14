# The Construct

Queueing, drafting, and ranking all in one place.

## Getting Started

Setting up the bot to work with your server is very simple. The following instructions assume you have the `Manage Server` permission.
All of the bot's commands have descriptive text in the Discord client, or you can use `/help` to get command usage information.

### Invite

Use this [invite link](https://discord.com/oauth2/authorize?client_id=1470118099150704913) to invite the bot. It already has necessary
permissions pre-selected.

### Season Management

In order to start matches, the server must have an active season (used to isolate seasonal stats and player rankings).
To do so, enter the command `/season start` and follow the prompts.

| Command         | Description                     | Notes                               |
|-----------------|---------------------------------|-------------------------------------|
| `/season start` | Starts a new season             | Requires `Manage Server` permission |
| `/season stop`  | Stops the current active season | Requires `Manage Server` permission |

### Queue Management

Queues may be created at any time, even without an active season. Up to 20 queues can be created at a time per server.

| Command                       | Description                                                  | Notes                                                                                                  |
|-------------------------------|--------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| `/queue create [type] [name]` | Create a queue of the specified type with the specified name | Any user is able to create a queue                                                                     |
| `/queue delete [name]`        | Delete a queue with the specified name                       | Only the queue owner may perform this operation                                                        |
| `/queue join [name]`          | Join a queue with the specified name                         | This operation may only be done while the queue is unlocked and no match is in progress for said queue |
| `/queue leave [name]`         | Leave a queue you have previously joined                     | This operation may only be done while the queue is unlocked and no match is in progress for said queue |
| `/queue lock [name]`          | Lock a queue with the specified name                         | Only the queue owner may perform this operation                                                        |
| `/queue unlock [name]`        | Unlock a queue with the specified name                       | Only the queue owner may perform this operation                                                        |
| `/queue list`                 | Lists all active queues in the server                        |                                                                                                        |

### Match Management

A match can be started once a queue has two or more players in it.

| Command        | Description                                  | Notes                                                                      |
|----------------|----------------------------------------------|----------------------------------------------------------------------------|
| `/match start` | Start a match using the prematch setup modal | Anyone can start a match so long as they are the owner of startable queues |

### Player Stats Management

Server administrators can directly manipulate player statistics in order to perform
corrections or adjustments whenever necessary.

| Command                | Description                                             | Notes                               |
|------------------------|---------------------------------------------------------|-------------------------------------|
| `player reset [name]`  | Resets stats for a player in the current active season  | Requires `Manage Server` permission |
| `player delete [name]` | Deletes stats for a player in the current active season | Requires `Manage Server` permission |
| `player edit [name]`   | Edits stats for a player in the current active season   | Requires `Manage Server` permission |

### Leaderboard

Access leaderboards for current or previous seasons.

| Command               | Description                                              | Notes                                                                           |
|-----------------------|----------------------------------------------------------|---------------------------------------------------------------------------------|
| `/leaderboard (name)` | View an interactive leaderboard for the specified season | If the season name is unspecified, it will default to the current active season |

### Feedback

Give feedback directly to the developers.

| Command     | Description                            | Notes                                             |
|-------------|----------------------------------------|---------------------------------------------------|
| `/feedback` | Submit feedback via the feedback modal | There is a per-user cooldown of 300s between uses |
