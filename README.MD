# The Second Awakening

## Huh?

In 2014-2015, Jeremiah Sun (a.k.a The Second Narrator) created [a full orchestration
of the soundtrack for Link's Awakening DX (1998)](https://www.youtube.com/playlist?list=PLQ58HYTDzLvL92US1q6csKkVmQN-4SeT-)
for the Game Boy Color.

(Note: I have no affiliation with Jeremiah Sun.  Go listen to his music though; it's really good.)

He also produced (warning: spoilers!) [a Let's Play of the entire game](https://www.youtube.com/watch?v=mdiXsPTZ3QM)
to showcase his music, with each of his tracks edited into the video at the appropriate points in the game.

Now you can too, no video-editing skills required.


# No really, what is it?

Link's Awakening DX (hereafter, LADX),
with a fully orchestrated soundtrack,
playable in an emulator.

You get:
- Every in-game song replaced with the orchestration, if available
- Music as close as possible to the original game
  - Song introductions
  - Seamless music loops
- Hand-timed cutscenes with synced audio
- A single easter egg (not even counting the original game's easter eggs)

# Seems pretty cool I guess; how do I use it?

Development and testing took place on BizHawk 2.6.1 for Windows using the LADX English 1.1 Release,
though other versions will likely work as well.

## Gathering Dependencies

You'll need a computer running Windows, with the following installed:
- [Python](https://www.python.org/) (with `virtualenv`)
- [BizHawk Emulator](http://tasvideos.org/BizHawk.html)
- A ROM dump of LADX for the Game Boy Color (you'll need to find this yourself)
- A dump of the Game Boy Color Boot ROM (ditto)

**Linux support is in the works** - see FAQ for details

## Installing Prerequsites (one time only)
1. Install Python, `virtualenv`, and BizHawk according to their directions.
   * Bizhawk's Windows version has a prerequisite installer,
  but I had no issues running BizHawk without it.  YMMV.
2. Set up BizHawk:
    1. Run `EmuHawk.exe` from the BizHawk directory (`EmuHawkMono.sh` for Linux).
    2. In the main Bizhawk window, select **Config >> Firmwares...**
       1. scroll down to **Game Boy Color**, right click
          **Game Boy Color Boot ROM >> Set Customization...**,
          and select the location of your Game Boy Color Boot ROM File.
    3. In the main Bizhawk window, select **Config >> Cores >> GB >> GBHawk**.
    4. Close EmuHawk

## Running the Project
1. Download or clone this repo.
2. (Optional) If on a laptop, set your power settings to "Maximum Performance"
   and/or plug in the computer
   to give yourself the best chance of emulating at full speed.
3. Run the `run_server.bat` script.
   * If asked you where you installed EmuHawk (first time only):
      * For Windows, paste the path to `EmuHawk.exe`
      * For Linux, paste the path to `EmuHawkMono.sh`
   * Note - on first run, this will:
     1. create a virtual environment called `venv` if it doesn't already exist
     2. install the necessary packages from `requirements.txt`
     3. download [the Second Narrator's LADX orchestrated soundtrack](https://soundcloud.com/jeremiah-sun/sets/link-awakening-orchestral-arrangement) from SoundCloud to `res/tracks`
     4. populate `res/clips` with audio files
   * When the server is ready, it'll print "Socket now listening".
4. Run the `run_emulator.bat` script.
    - in the `Lua Console` window, you should see "1 script (1 active, 0 paused)",
      and the first line of the output window will show "Loaded Bindings" and the current time.
    - If the script isn't active, activate it with the "Toggle Script" button
      (the green checkmark in the toolbar of the `Lua Console` window).
   - You can ignore the warnings from NullHawk, if there are any.
5. Open your Link's Awakening DX ROM from the main BizHawk window under **File >> Open ROM**.
6. Play Link's Awakening in BizHawk with awesome music.

The music will stop if you close BizHawk.
You can restart BizHawk without restarting the music server, but not vice-versa.

## Upgrading the Project
1. `git pull` any updates.
2. Delete `res/clips` so they'll be re-created in case any of the timings have changed.

# Important Notes about Saving

## Saving In-Game

To save, LADX requires you to push four buttons at once.
If your keyboard doesn't support this, here's an easy workaround:

1. Go to **Config >> Controllers...**
2. Deselect `Auto Tab` at the bottom of the window
3. Choose a key to use to trigger the save function
3. Add that same key to the mappings for the Start, Select, A, and B buttons

## Saving Outside-of-Game

**BizHawk doesn't automatically write your saves to disk.**
After performing the in-game save, **you must select *File >> Save Ram >> Flush Save RAM*
or push Ctrl-S before closing BizHawk or your save file will be lost.**

For more information, see the `In-game saves` section
of the [BizHawk Readme](https://github.com/TASVideos/BizHawk).

# FAQ

## Is this a ROM Hack?

No; it uses the stock ROM as shipped on the original cartridges.

## How does this work?

By inspecting the state of the emulated GBC at runtime,
then modifying it on the fly.

## I can't get BizHawk to talk to the music server

That's not a question ;)

The music server and `bizhawk_bindings.lua` communicate over port 19938.
Make sure port 19938 is available for connections from the local machine.

Running the emulator and music server on two separate machines is possible,
but not terribly useful
as sound effects will still play locally through the emulator.

## Why isn't the emulator saving my game?

See the section titled "Important Notes about Saving"

## Why is the emulator running slowly?

**This is intentional**; some of The Second Narrator's tracks have different lengths than their in-game counterparts.
In some cases they've been truncated, where in others the game's speed has been altered for cinematic effect.
This will happen in a few areas of the game, most notably the intro cutscene.

If, however, the cutscene is out of sync or the emulator hasn't returned to normal speed (60 fps)
by the time you hit the title screen, one of three things is probably happening:
- You're on a laptop and your power settings are throttling the processor.
  - Try plugging in or switching to "Best Performance" (on Windows).
- Debug printouts have been enabled on the BizHawk side and are causing lag.
  - Try setting the `debug_logging` flag to `false` in `bizhawk_bindings.lua`
- Your computer isn't fast enough to handle the gloriously unoptimized code in this project.
  - Try using a faster computer - I can usually get between 70-90 fps consistently
    even with debug printouts turned on

## Why BizHawk instead of [insert emulator here]?
BizHawk was the first emulator I found with support for both IPC
and programatic breakpoints, both of which are necessary for this project to work.
Would be open to porting to other emulators as well.

# Linux Support

LUA support in Linux is an ongoing project in BizHawk.
At this project's inception, there was no support, but it's fast approaching.

As of writing, the most recent BizHawk dev build has LUA support (what will become 2.9).
The stable version (2.8) does not.

What works:
- `run_server` and `run_emulator` scripts have versions for `bash`
- Music server works on Linux using SoLoud library for Linux

What doesn't work yet:
- BizHawk LUA mostly works, except for an issue with the client-server communication:
   - BizHawk blocks endlessly in LUA waiting for data on the network socket
   - There is no way to specify a timeout or continue until the client sends more data

Not sure if this is a behavior change since version 2.6.1 or if it's a Linux bug, but the code will need changing to support this behavior.

# What's Next?

See `TODO.txt` for potential future work.

In addition, there are comments in `bizhawk_bindings.lua`
noting potential points of optimization if a way to make them can be found.
  
# Acknowledgements

The following dependencies are bundled with the project:
- [SoLoud](https://sol.gfxile.net/soloud/index.html) by Jari Komppa (for playing audio)

The following dependencies are specified in requirements.txt:
- [Pandas](https://pandas.pydata.org/) (for reading the config file)
- [PyGame](https://www.pygame.org/) (for creating audio clips - can also be used to play audio if SoLoud isn't working, though some features are unavailable)
- [PyDub](https://github.com/jiaaro/pydub) (for creating silent audio clips)

Thanks to the following projects as well for helping to make this possible:
- [BGB](https://bgb.bircd.org/), for the amazing emulator and debugger
- The [Link's Awakening DX Disassembly Project](https://github.com/zladx/LADX-Disassembly),
  for saving a considerable amount of time in the BGB debugger
- The developers of [PyBoy](https://github.com/Baekalfen/PyBoy) and [mGBA](https://mgba.io/),
  for patiently explaining to me why their emulators are not suited to this project,
  though they are both awesome and worth checking out
  
...and, of course...
- [The Second Narrator](https://www.youtube.com/channel/UChcmd07Qpsl9AG58GeLnldQ), Jeremiah Sun,
  for an amazing soundtrack to an amazing game.
