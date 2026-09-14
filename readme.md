# Railroader Mod Manager (RMM)

The purpose of this program is to auto-update installed Railroader mods when requested.

I am making this program because frankly, I am tired of manually updating everything every time.

This could potentially be expanded to support other games in the future. As it stands, the structure of the project should allow for any game to be updated using this software. As my needs are for Railroader, I have built and tested it with that in mind. Feel free to fork the project for your specific needs (or make some PRs!)

You will need a [Nexus Mods API Key](https://next.nexusmods.com/settings/api-keys) to use this software.

#### Scope

This manager will only manage the mods that you have added to the game via the manager. If you manually add a mod, it will not handle that, and it'll be up to you to maintain and update it.

## RMM Format

Game-id (railroader) -> Mod-id (143)

Mod-id's are per-game. This should be stored in the database as like, `railroader-143`
Game-id's are not related to the actual name of the game.

Valid modlist formats
- `railroader-143` (will download the latest file no matter what)
- `railroader-143@latest` (download all files matching the highest version number)
- `railroader-143@4.4.2` (version query, will download all files matching version 4.4.2)
- `railroader-1096#4334` (fileID query, will only download this specific fileID)
- `railroader-1378$fuse;install` (deliminated search query, get newest file labelled with FUSE and INSTALL)
- `railroader-1378@2.0.4$fuse;install` (version query + deliminated search query, get all files of specific version labelled with FUSE and INSTALL)
- `railroader-239!yardhar;comp`  (deliminated exclude query. If these terms exist in a label, we skip over file)
- `railroader-1084$fuse!rl;rf` (deliminated search query + deliminated exclude query)

For most use cases, you will want to use a deliminated search query.

## Order of Operations

The filters have an order of operations. They are the following:
- Specific File Query
- Deliminated Search Query
- Deliminated Exclude Query
- Version Query
- Newest File Query


### Newest File

The default, and not always the one you want. This will download the newest file uploaded to the mod page. If a mod page has multiple primary files, you may need to define some extra parameters to filter for the one you want.

### Version Query

As we know, mod versioning schemes are not all the same. I've done my best here to support many different versioning formats, but it may not be enough. If the version cannot be determined, it will fallback to Newest File

### Specific File Query

This requests the specific file based on it's Nexus Mods File ID. Good for building very strict modpacks, not much else.

### Deliminated Search Query

Deliminated queries search for any match of any term and are case insensitive. If the file is `INSTALL FUSE`, and your query is `$fuse;install`, it will still match and fetch the file.

### Deliminated Exclude Query

This is the opposite of the search query. If there's a match, we skip the file.


## Technical Docs (temporary)

Modlist format should be `railroader-1096@1.0`, or `game-modId@version`. This is prefered over the fileId variant
If a specific file is desired, `railroader-1096#4334`, or `game-modId#fileId`. This is usually unnecessary.

`railroader-1096@latest` is also a valid entry, and will fetch all files matching the highest version number


