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

This is all convention though. You don't have to follow this, but RMM might lose track of mods on updates.

#### Mod Decoupling

Yeah, let's just get this outta the way. If you are too vague with your RMM-ID, and mods update, RMM might lose track of some of them.

For example, the GP38 by BeeMan. Let's assume we use `railroader-143@latest`. If the Scripts file gets updated to 4.4.3, but the GP38 file is still on 4.4.2, the Scripts mod will get updated, but RMM will stock tracking the GP38 since it no longer has the highest ("latest") version number.

RMM will warn you when this happens, and uninstall the decoupled mod if it can.

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

`--export MSGPACK {NAME} --static`

#### --append

By default, RMM will create a backup of your current install as a `.mpk` modpack file before installing the new one.

If instead you want to append the modpack to your current install, use `--append`.

`--import {NAME} --append`

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

## RMM-ID Patching

### DO NOT REPORT ISSUES TO MOD MAKERS ABOUT MOD ISSUES IF YOU HAVE INSTALLED IT WITH A PATCH.

Sometimes, mods you download come with broken dependencies. Patching takes advantage of the RMM-ID system to allow patching of mods to fix issues with them. This patching gets applied during mod install.

Patches are part of the RMM-ID itself. They are a **Base64 encoded MsgPack object**. The contents contain the information for the patch, structured as followed:

```json
{
    "replaceId": {
        "beemansrollingstockscripts": "BeemansRollingStockScripts"
    },
    "removeRLConflict": ["AlinaNova21.AlinasMapMod"]
}
```

Let's use the `replaceId` example as an example. Most mods that rely on Beemans Rolling Stock Scripts expect the ID to be capitalized, when it's not currently. This, at least under FUSE, causes errors. So, you can provide a patch to fix it inside of Beeman's scripts directly, and get around the issue.

`railroader-443@latest|galyZXBsYWNlSWSBumJlZW1hbnNyb2xsaW5nc3RvY2tzY3JpcHRzukJlZW1hbnNSb2xsaW5nU3RvY2tTY3JpcHRz`

The `removeRLConflict` patch exists to remove broken conflicts. Under FUSE, mods like MICHILSON's Large Andrews Engine Facility requires Alina's Map Mod to be above version 1.3.24149.1337. This is fine under Railloader, since you are expected to have AMM installed, but here, FUSE provides it, specifically version 0.0.0.0. The Andrews Facility will refuse to load under this configuration, even though it works fine. So, we can just patch the `Definition.json` to remove the lines causing the issue.

`railroader-1334|gbByZW1vdmVSTENvbmZsaWN0kbhBbGluYU5vdmEyMS5BbGluYXNNYXBNb2Q=`

These are just examples of patches I've had to manually make for my own modded environment. This system streamlines it so you don't have to manually do it. Patches are carried over to exported modlists.

You can see what a patch does by using [this utility](https://ref45638.github.io/msgpack-converter/).


### Quirks

You may have noticed that a single modpack file can potentially install mods for multiple games at once. While this is the case, you probably shouldn't. You should also know what needs to happen for a mod to actually be installed.

For one, a `gameloc` entry for any given game needs to exist and be valid in the `config.ini` file before a modpack can even be installed. So, including a Skyrim mod in your Railroader modpack won't really do anything if the user you are sharing it with doesn't have a path for Skyrim configured. RMM will throw up warnings if something fails when it comes to these specific quirks.

## Offsite Mods

Sometimes, especially in the case of Railroader, mod makers will host mods on their own websites (like in the case of Alina's mods). This means that ***you*** are responsible for installing and updating these. RMM in it's current state cannot do it, and likely never will. This also applies to mods that only release on GitHub. This tool only knows how to pull from Nexus Mods.

If you wish to provide a list of URLs for RMM to open when the user imports a modpack, you can do it like so:

```txt
offsite-url@https://github.com/Joo200/Railloader-JooMods/releases
offsite-url@https://github.com/Reaper8f/rr-mapenhancer-fix/releases
offsite-url@https://rmh.alinanova.dev/mod/6b70312d-66d2-428a-aadc-2f6321b11081
offsite-url@https://rmh.alinanova.dev/mod/04417e51-ddc1-48cc-8d22-50526531387e
offsite-url@https://rmh.alinanova.dev/mod/9c253046-13c4-4896-a8f0-3a5c8b4560c1
offsite-url@https://rmh.alinanova.dev/mod/da44df04-5e79-4cce-92fc-909d9cbb33fd
```

RMM will open these in the browser for the user to install every time RMM is run.


## Want to support my work?

You really don't have to. In fact, I'd prefer if you don't.

I'm making this for me, but if you really really really really **really** want to support me, you can do so on my [Ko-fi](https://ko-fi.com/elenaberry).

Again, no pressure. I've put it at the bottom here for a reason. I don't wanna bother anyone.

