# discord bot meant for pinging users not in voice chat

## possible commands

### !set \<time> \<List of users>- 
at the specified time, will look at every voice channel in a server, and ping users who are not in any, the command requires display names of users
#### examples: <br>
 !set 20:00  user2DisplayName <br>
 !set 20:42 user1DisplayName user2DisplayName

### !create_timetable \<list of arguments to multiply with weekday>- 
creates a list of specified arguments with every weekday, every element has random emote. The bot reacts with the emote itself, so users should react themselves to show they are available for set hours & day
#### examples: <br>

!create_timetable 20 21 <br>

##### output
```
Emojis Randomized!@Little Guns, @Guns
mon 20 - 🧛
mon 21 - 👠
tue 20 - ⛴
tue 21 - 👩
wed 20 - 🚣
wed 21 - 🤹
thu 20 - 👰
thu 21 - 🏃
fri 20 - 💂
fri 21 - 🛑
sat 20 - ℹ
sat 21 - ☀
sun 20 - 🇱
sun 21 - 🪸
```

### !add_message <message>- 
allows users to add their own message to the bot's list, THE MESSAGE NEEDS TO CONTAIN EXACTLY ONE \<user> to be accepted
#### examples: <br>

!add_message "Be ashamed <user>!"


## the bot requires a config file to use, current config
```json
{
    "TOKEN": "", // discord app token
    "BOT_OWNER" : "", // who to ping in case of emergencies
    "CHANNEL_IDS": [ // channels where you want the bot to work
    ],
    "MAX_NO_EVENTS": , // how many pings can the bot at one could happen
    "MESSAGES": [ // a list of possible messages to post, a message needs a <user>
    ]
}
```

the config needs to be in the same directory as run.py file