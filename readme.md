# Nantahala Auto-Updater & Mod Manager for Railroader

The purpose of this program is to auto-update installed Railroader mods when the software is requested.

I am making this program because frankly, I am tired of manually updating everything every time.

This will hopefully be expanded to support other games in the future. As it stands, the structure of the project should allow for any game to be updated using this software. As my needs are for Railroader, I have built and tested it with that in mind.



## Nexus Mods system

Game-id (railroader) -> Mod-id (1096)

Mod-id's are per-game. This should be stored in the database as like, `railroader-1096`
Game-id's are not related to the actual name of the game

Modlist format should be `railroader-1096@1.0`, or `game-modId@version`. This is prefered over the fileId variant
If a specific file is desired, `railroader-1096#4334`, or `game-modId#fileId`. This is usually unnecessary
`railroader-1096@latest` is also a valid entry. Failure to append version information will default to the latest.