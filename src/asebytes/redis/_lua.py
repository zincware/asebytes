"""Lua scripts for atomic single-row Redis operations.

Each script resolves a (possibly negative) positional index to a sort key
and performs the operation in a single round trip.

KEYS[1] = sort-key list key  (e.g. ``prefix:sort_keys``)
ARGV[1] = row-key prefix     (e.g. ``prefix:row:``)
ARGV[2] = positional index   (may be negative)
Additional ARGV vary per script.
"""

# -- GET (full row) --------------------------------------------------------
# Returns flat key-value list from HGETALL.
# Returns {false} for None rows (hash does not exist).
# Raises redis.error('IndexError') for out-of-bounds.
LUA_GET = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
if redis.call('EXISTS', rk) == 0 then return false end
return redis.call('HGETALL', rk)
"""

# -- GET_WITH_KEYS (filtered row) -----------------------------------------
# ARGV[3..] = requested field names.
# Returns flat key-value list of found fields.
# Returns {false} for None rows.
LUA_GET_WITH_KEYS = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
if redis.call('EXISTS', rk) == 0 then return false end
local result = {}
for i = 3, #ARGV do
    local v = redis.call('HGET', rk, ARGV[i])
    if v then
        result[#result + 1] = ARGV[i]
        result[#result + 1] = v
    end
end
return result
"""

# -- KEYS (field names) ----------------------------------------------------
# Returns list of field names (HKEYS).
# Returns empty table for None rows.
LUA_KEYS = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
if redis.call('EXISTS', rk) == 0 then return {} end
return redis.call('HKEYS', rk)
"""

# -- SET (replace row) -----------------------------------------------------
# ARGV[3..] = flat key-value pairs for new row (empty = set to None).
# Deletes existing hash first, then writes pairs in a loop.
LUA_SET = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
redis.call('DEL', rk)
for i = 3, #ARGV, 2 do
    redis.call('HSET', rk, ARGV[i], ARGV[i + 1])
end
return true
"""

# -- DELETE (remove row + list entry) --------------------------------------
LUA_DELETE = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
redis.call('DEL', rk)
redis.call('LREM', KEYS[1], 1, sk)
return true
"""

# -- UPDATE (merge fields) -------------------------------------------------
# ARGV[3..] = flat key-value pairs to merge.
LUA_UPDATE = """
local n = redis.call('LLEN', KEYS[1])
local idx = tonumber(ARGV[2])
if idx < 0 then idx = n + idx end
if idx < 0 or idx >= n then return redis.error_reply('IndexError') end
local sk = redis.call('LINDEX', KEYS[1], idx)
local rk = ARGV[1] .. sk
for i = 3, #ARGV, 2 do
    redis.call('HSET', rk, ARGV[i], ARGV[i + 1])
end
return true
"""
