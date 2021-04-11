console.log('Loaded Bindings: ' .. os.date("%X"))

---- Development
debug_logging = false
dump_logging = false

function logd(str)
    if debug_logging then
        console.log(str)
    end
end

---- Constants

SILENCE_AUDIO_PSEUDOSONG = 0x70

---- LADX Function Pointers

BeginMusicTrack_Dispatch_1B = 0x413B
PlayMusicTrack_1B_EntryPoint = 0x401E

-- TODO: clean up this "Stop Music" section
StopNoiseChannel_1B = 0x40F3
StopSquareAndWaveChannels_1B = 0x4E57
-- Falls into the StopSquareAndWaveChannels_1B function
-- Called at the end of the 0xFF music handling logic
label_01B_4E4A = 0x4E4A
-- This appears to be some sort of debug routine
-- It contains very similar but not identical code to the StopNoiseChannel_1B routine
-- After that, it falls into the label_01B_4E4A routine
STOP_MUSIC_DEBUG_ROUTINE_1B = 0x4135
-- 0x27F2 is the "Unload Audio Track" trampoline used for cutscenes, boss death, etc.
-- Since it's on bank 0, it can be called regardless of which ROM bank is loaded.
-- In short, it says:
--   Switch to Bank 1F
--   Call the silence music routine at 1F_4003
--   Restore the original bank
-- 1E and 1B banks have their own dedicated "stop music" functionality and don't use this
-- The "Current Rombank" will be the rombank of the calling code, not the rombank of this code, which is 1F
-- This is because the trampoline at UNLOAD_AUDIO_ROUTINE uses the "Current Rombank" value
-- To switch the rombank back after this function completes
-- TODO: if we can figure out how to farcall,
--   it eliminates the need to wait until we're on the 1B bank to silence the music
UNLOAD_AUDIO_TRAMPOLINE = 0x27F2
func_01F_4003 = 0x4003  -- Called by UNLOAD_AUDIO_TRAMPOLINE
func_01F_7B5C = 0x7B5C  -- Called by func_01F_4003 and others

---- LADX Data Pointers

wMusicTrackToPlay = 0xD368
MBC3SelectBank = 0x2100

-- Music timing:
-- 0 = normal,
-- 1 = double-speed,
-- 2 = half-speed
wMusicTrackTiming = 0xC10B

-- Right channel volume - low nybble only, 00-07
hVolumeRight = 0xFFA9

-- Left channel volume - high nybble only, 00-70
hVolumeLeft = 0xFFAA

-- Used to time various effect triggers in the intro Shipwreck Cutscene
wIntroTimer = 0xD001 -- Bank 01

-- Unused so far:
-- wActiveJingle = 0xD360
-- wActiveMusicIndex = 0xD369
-- wActiveWaveSfx = 0xD370
-- wActiveNoiseSfx = 0xD378
-- wActiveMusicTable = 0xD3CE

---- Script State

found_song_id = nil
suggested_song_id = nil
applied_song_id = nil
current_rombank = nil

should_silence_music = false
should_ignore_song = false

is_running_at_partial_speed = false  -- Used for Various Cutscenes

---- Helper functions

function hex(value)
    return string.format("%02X", value)
end

function isempty(s)
  return s == nil or s == ''
end

function sleep (seconds)
    local now = os.clock()
    local expiration_time = tonumber(now + seconds);
    -- TODO replace with non-busy wait
    while (os.clock() < expiration_time) do
    end
end

---- Emulator Execution Tracking

-- Note: there is an edge case in the rombank detection:
-- The "Current Bank" flag isn't always updated when farcalling.  For example,
-- when calling UNLOAD_AUDIO_ROUTINE, it points to the bank of the calling code,
-- Not the bank containing the meat of the routine (1F in this example).
-- As such, it can't always be trusted to indicate the current rom bank.
-- To get around this, we track the true rom bank ourselves every time it changes
function update_rom_bank()
    -- Same hack as on_music_track_timing_changed
    current_rombank = emu.getregister('A')
end

function on_rom_bank(rombank)
    return rombank == current_rombank
end


---- Altering Emulator State

--function gbc_push_to_stack_gambatte(value)
--    print('DEBUG: push ' .. hex(value))
--    local sp = emu.getregister('SP')
--    local new_sp = sp - 2
--    print('DEBUG: SP: ' .. hex(sp))
--    print('DEBUG: SET SP: ' .. hex(new_sp))
--    -- TODO: BizHawk's Gambatte core does not support calling setregister - use GBHawk instead
--    -- As a workaround, use GBHawk core instead
--    emu.setregister('SP', new_sp)
--    print('DEBUG: WRITE STACK: ' .. hex(value))
--    memory.write_s16_le(new_sp, value)
--end
--
--function gbc_call_function_gambatte(function_to_call)
--    print('DEBUG: call ' .. hex(function_to_call))
--    local pc = emu.getregister('PC')
--    gbc_push_to_stack(pc)
--    print('DEBUG: SET PC')
--    emu.setregister('PC', function_to_call)
--end

function gbc_push_to_stack_gbhawk(value)
    local sph = emu.getregister('SPh')
    local spl = emu.getregister('SPl')
    local sp = bit.lshift(sph, 8) + spl

    local new_sp = sp - 2
    local new_sph = bit.rshift(new_sp, 8)
    local new_spl = bit.band(new_sp, 0xFF)

    emu.setregister('SPh', new_sph)
    emu.setregister('SPl', new_spl)
    memory.write_s16_le(new_sp, value)

    if dump_logging then
        print('DUMP: sph ' .. hex(sph))
        print('DUMP: spl ' .. hex(spl))
        print('DUMP: sp ' .. hex(sp))
        print('DUMP: new_sp ' .. hex(new_sp))
        print('DUMP: new_sph ' .. hex(new_sph))
        print('DUMP: new_spl ' .. hex(new_spl))
    end
end

function gbc_call_function_gbhawk(function_to_call)
    local pch = emu.getregister('PCh')
    local pcl = emu.getregister('PCl')
    local pc = bit.lshift(pch, 8) + pcl

    local fh = bit.rshift(function_to_call, 8)
    local fl = bit.band(function_to_call, 0xFF)

    gbc_push_to_stack_gbhawk(pc)
    emu.setregister('PCh', fh)
    emu.setregister('PCl', fl)

    if dump_logging then
        print('DUMP: pch ' .. hex(pch))
        print('DUMP: pcl ' .. hex(pcl))
        print('DUMP: pc ' .. hex(pc))
        print('DUMP: func ' .. hex(function_to_call))
        print('DUMP: fh ' .. hex(fh))
        print('DUMP: fl ' .. hex(fl))
    end
end

---- Music Handling

function check_if_music_changed_1b()
    if on_rom_bank(0x1B) then
        if should_ignore_song then
            logd('DEBUG: Ignoring song change')
            should_ignore_song = false
            return
        end

        found_song_id = emu.getregister('A')
        if found_song_id == 0xFF then
            found_song_id = SILENCE_AUDIO_PSEUDOSONG
        end
        applied_song_id = found_song_id  -- Active until overridden
        logd('\nMUSIC CHANGE: ' .. hex(found_song_id))

        local payload = 's' .. string.char(found_song_id)
        if string.len(payload) ~= 2 then
            console.log(string.format('ERROR: Song Change Payload is wrong size: expected 2 got %d', string.len(payload)))
        else
            comm.socketServerSend(payload)
            logd('SEND: Song ' .. hex(string.byte(payload, 2)))
        end

        -- Hacks to set emulator speed so cutscenes match the music
        -- TODO: move this to its own function?
        if found_song_id == 0x1A then
            -- Entering intro cutscene
            client.speedmode(90)
            is_running_at_partial_speed = true
        elseif found_song_id == 0x1E then
            -- Sleeping in Dream Shrine
            client.speedmode(75)
            is_running_at_partial_speed = true
        elseif found_song_id == 0x30 then
            -- Manbo's Mambo is slower than game's version
            client.speedmode(95)
            is_running_at_partial_speed = true
        elseif found_song_id == 0x3F then
            -- Playing the instruments after meeting the Wind Fish
            client.speedmode(75)
            is_running_at_partial_speed = true
        elseif found_song_id == 0x35 then
            -- Mamu's Song of Soul is slower than game's version
            client.speedmode(85)
            is_running_at_partial_speed = true
        elseif found_song_id == 0x4C then
            -- Waterfall Draining when Opening Angler's Tunnel
            client.speedmode(75)
            is_running_at_partial_speed = true
        elseif is_running_at_partial_speed then
            -- Leaving a cutscene (new music loaded)
            client.speedmode(100)
            is_running_at_partial_speed = false
        end
    end
end

function poll_for_new_song()
    local input = comm.socketServerResponse()
    if (not isempty(input)) then
        logd('\nRECV: length ' .. string.len(input) .. ' {' .. input .. '}')
        for i=1,string.len(input) do
            suggested_song_id = string.byte(input, i)  -- string is indexed from 1
            if suggested_song_id == nil then
                print('ERROR: New song is nil')
                return
            else
                logd('PARSE: ' .. hex(suggested_song_id))
            end
        end
        apply_song()
    end
end

function apply_song()
    if suggested_song_id == SILENCE_AUDIO_PSEUDOSONG then
        -- Need to be on the 1B bank to call the slience routine -
        -- this is the only reason to use the should_silence_music flag,
        -- otherwise we could do this immediately
        -- TODO: Might be a better way to do this than polling to see if we're on that bank
        should_silence_music = true
        logd('DEBUG: QUEUE SILENCE on GBC')
    else
        memory.writebyte(wMusicTrackToPlay, suggested_song_id)  -- Let LADX handle it
        applied_song_id = suggested_song_id
        should_ignore_song = true;
        logd('APPLY: ' .. hex(applied_song_id))
    end
end

function try_silencing_music()
    if should_silence_music and on_rom_bank(0x1B) then
        logd('DEBUG: APPLY SILENCE on GBC')
        gbc_call_function_gbhawk(STOP_MUSIC_DEBUG_ROUTINE_1B)
        applied_song_id = SILENCE_AUDIO_PSEUDOSONG
        should_silence_music = false
    end
end

function on_gbc_silence_music()
    if on_rom_bank(0x1F) then
        local payload = 's' .. string.char(SILENCE_AUDIO_PSEUDOSONG)
        comm.socketServerSend(payload)
        logd('SEND: SILENCE AUDIO')
    end
end

function on_volume_left_channel_changed()
    -- Same hack as on_music_track_timing_changed
    local raw_volume = emu.getregister('A')
    local shift_volume = bit.rshift(raw_volume, 4)  -- left channel uses high nybble only
    local volume = bit.band(shift_volume, 0xF)
    local payload = 'l' .. string.char(volume)
    comm.socketServerSend(payload)
    logd('SEND: VOLUME LEFT to ' .. hex(volume))
end

function on_volume_right_channel_changed()
    -- Same hack as on_music_track_timing_changed
    local raw_volume = emu.getregister('A')
    local volume = bit.band(raw_volume, 0xF)  -- left channel uses low nybble only
    local payload = 'r' .. string.char(volume)
    comm.socketServerSend(payload)
    logd('SEND: VOLUME RIGHT to ' .. hex(volume))
end

---- Intro Cutscene

function delay_during_intro_fade_to_white()
    if on_rom_bank(0x01) then
        local intro_timer = memory.readbyte(wIntroTimer)
        if intro_timer == 0xA1 then  -- During whiteout, after music ends
            -- TODO: print something clever to the screen maybe?
            sleep(7)  -- Should really be 6.8?
            client.speedmode(75)
        end
    end
end

function on_music_track_timing_changed()
    -- Hack: For some reason, reading wMusicTrackTiming when this callback executes
    -- always gets the previous value from BizHawk rather then the new one
    -- that was (presumably) just written.  Fortunately, judging from the LADX code,
    -- wMusicTrackTiming is only ever written with the value from Register A.
    -- As such, we read register A here and use that value as the value we expect should be in wMusicTrackTiming.
    local reg_a = emu.getregister('A')
    local payload = 't' .. string.char(reg_a)
    comm.socketServerSend(payload)

    if debug_logging then
        local pch = emu.getregister('PCh')
        local pcl = emu.getregister('PCl')
        local pc = bit.lshift(pch, 8) + pcl
        console.log('SEND: MUSIC TIMING to ' .. hex(reg_a) .. ' at ' .. hex(current_rombank) .. '_' .. hex(pc))
    end
end

---- Handler Registration

-- Track current rombank to determine when routines are actually invoked
event.onmemorywrite(update_rom_bank, MBC3SelectBank)
-- Intro Cutscene Pause
event.onmemorywrite(delay_during_intro_fade_to_white, wIntroTimer)
-- Music Change
event.onmemoryexecute(check_if_music_changed_1b, BeginMusicTrack_Dispatch_1B)
-- Apply a queued music silencing request
--   TODO: this isn't terribly efficient since it happens basically every frame
--   But we need some way to tell when we're on the 1B bank before calling the silencing routine
event.onmemoryexecute(try_silencing_music, PlayMusicTrack_1B_EntryPoint)
-- Music Speed Change
event.onmemorywrite(on_music_track_timing_changed, wMusicTrackTiming)
-- Music Volume Change
event.onmemorywrite(on_volume_left_channel_changed, hVolumeLeft)
event.onmemorywrite(on_volume_right_channel_changed, hVolumeRight)
-- Game tries to silence its own audio
event.onmemoryexecute(on_gbc_silence_music, func_01F_7B5C)

---- Main Loop

while true do
    poll_for_new_song()
    if debug_logging then
        local found = (found_song_id == nil) and "XX" or hex(found_song_id)
        local suggested = (suggested_song_id == nil) and "XX" or hex(suggested_song_id)
        local applied = (applied_song_id == nil) and "XX" or hex(applied_song_id)
        local rombank = (current_rombank == nil) and "XX" or hex(current_rombank)
        gui.text(0, 45, 'Song Found: ' .. found)
        gui.text(0, 60, 'Song Suggested: ' .. suggested)
        gui.text(0, 75, 'Song Applied: ' .. applied)
        gui.text(0, 90, 'Rom Bank: ' .. rombank)
    end
    emu.frameadvance()
end
