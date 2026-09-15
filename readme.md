# NOT ALL FEATURES ARE IMPLEMENTED YET

# Railroader Mod Manager (RMM)

The purpose of this program is to auto-update installed Railroader mods when requested.

I am making this program because frankly, I am tired of manually updating everything every time.

This could potentially be expanded to support other games in the future. As it stands, the structure of the project should allow for any game to be updated using this software. As my needs are for Railroader, I have built and tested it with that in mind. Feel free to fork the project for your specific needs (or make some PRs!)

You will need a [Nexus Mods API Key](https://next.nexusmods.com/settings/api-keys) to use this software.

#### Scope

This manager will only manage the mods that you have added to the game via the manager. If you manually add a mod, it will not handle that, and it'll be up to you to maintain and update it.

## RMM-ID Format

Game-id (railroader) -> Mod-id (143)

Mod-id's are per-game. This should be stored in the database as such: `railroader-143`

Valid modlist formats
- `railroader-143` (will download the single newest file)
- `railroader-143@latest` (download all files matching the highest version number)
- `railroader-143@4.4.2` (version query, will download all files matching version 4.4.2)
- `railroader-1096#4334` (fileID query, will only download this specific fileID)
- `railroader-1378$fuse;install` (deliminated search query, get single newest file labelled with FUSE and INSTALL)
- `railroader-1378@2.0.4$fuse;install` (version query + deliminated search query, get all files of specific version labelled with FUSE and INSTALL)
- `railroader-239!yardhar;comp`  (deliminated exclude query. If these terms exist in a label, we skip over the file)
- `railroader-1084$fuse!rl;rf` (deliminated search query + deliminated exclude query + single newest file)

For most use cases, you will want to use a deliminated search query.

### 1 RMM-ID, 2 files.

Some filters, for example `railroader-143@4.4.2`, will download *multiple* files. While RMM supports this, you should really use 2 separate strict entries where you can. For example:
- `railroader-143@4.4.2$scripts` 
- `railroader-143@4.4.2$gp38!scripts`

For some mods though, you'll want to take advantage of the multi-file capability. For example, the trucks required for the GP38: `railroader-143@3.05.11$trucks`

This is all convention though. You don't have to follow this, but you might lose mods on updates.

#### Losing Mods On Updates

Yeah, let's just get this outta the way. If you are too vague with your RMM-ID, and mods update, you might lose some of them.

For example, the GP38 by BeeMan. Let's assume we use `railroader-143@latest`. If the Scripts file gets updated to 4.4.3, but the GP38 file is still on 4.4.2, the GP38 file will get uninstalled since it no longer has the highest ("latest") version number.

RMM will warn you when this happens. The only way to avoid this is by using 

### Order of Operations

The filters have an order of operations. They are the following:
- Specific File Query
- Deliminated Search Query
- Deliminated Exclude Query
- Version Query
- Newest File Query


#### Single Newest File

The default, and not always the one you want. This will download the single newest file uploaded to the mod page. If a mod page has multiple primary files, you may need to define some extra parameters to filter for the one you want.

#### Version Query

As we know, mod versioning schemes are not all the same. I've done my best here to support many different versioning formats, but it may not be enough. If the version cannot be determined, it will fallback to Newest File

#### Specific File Query

This requests the specific file based on it's Nexus Mods File ID. Good for building very strict modpacks, not much else.

#### Deliminated Search Query

Deliminated queries search for any match of any term and are case insensitive. If the file is `INSTALL FUSE`, and your query is `$fuse;install`, it will still match and fetch the file.

#### Deliminated Exclude Query

This is the opposite of the search query. If there's a match, we skip the file.

### RMM-ID In Other Games

The RMM-ID format works for anything hosted on Nexus Mods. This includes other games, although right now, I cannot guarantee that it will work.

## RMM Modpacks

Modpacks can be saved and shared via a few different file formats. Simply launch RMM with the --export or --import arguments and include the path to the file after.

- `--export MSGPACK {NAME}`
- `--import {PATH}`

The available export options are
- MSGPACK
- JSON
- PLAINTEXT

#### --static

Want to share your modpack with friends but specifically wanna share a version of it that wont update? Add `--static` after `--export` to generate a modpack that will only ever use the specific mod versions you already have installed. The resulting RMM-IDs will be generated with Specific File Query.

So, `--export MSGPACK {NAME} --static`

### Supported Formats

Below are the available import and export formats that RMM supports. Examples for these files can be found in /examples

#### MsgPack

MsgPack Modpacks are intented to be shared via a `.mpk` MsgPack file.

The data contained in this specific type is formatted slightly differently from the RMM-ID format. Instead of every single entry containing the game identifier, the gameID is stripped and stored as a key, with the mods for that game as the value.

So, `railroader-143@latest` and `railroader-239` would be stored as `{"railroader": ["143@latest", 239]}` in the MsgPack object.

#### JSON

While MsgPack is the preferred storage medium for modpacks, JSON can also be used. JSON pack data is structured in the exact same way as MsgPack.

#### Plaintext

Newline/Return delimited RMM-IDs can be read by RMM and installed. Ideally, you really shouldn't use this unless you are building a modpack to then export as a `.mpk`. 


### Quirks

You may have noticed that a single modpack file can potentially install mods for multiple games at once. While this is the case, you probably shouldn't. You should also know what needs to happen for a mod to actually be installed.

For one, a `gameloc` entry for any given game needs to exist and be valid in the `config.ini` file before a modpack can even be installed. So, including a Skyrim mod in your Railroader modpack won't really do anything if the user you are sharing it with doesn't have a path for Skyrim configured. RMM will throw up warnings if something fails when it comes to these specific quirks.

