# LanternLink

LanternLink is a small, cloud-free signaling system for two computers or
single-board computers on the same local network. A sender transmits one of
four deliberately bounded messages. The receiver verifies an HMAC signature,
timestamp, and one-time nonce, then displays the message as both text and a
timed Morse-style signal lantern in a browser.

The project is being built for Element14 Project14 **Make a Connection**. It
is intended to make a network connection visible and understandable rather
than hiding it inside a notification service.

- Functional video: https://youtu.be/4I7CQW-IZXQ
- Public source: https://github.com/bgrubbs1/lanternlink-element14

## Messages

- `CHECK_IN` - request a status check;
- `READY` - sender is ready;
- `ASSIST` - sender requests attention;
- `ALL_CLEAR` - condition has cleared.

Free-form text is intentionally rejected. This avoids accidental publication
of addresses, names, machine details, or private message content.

## Quick local demonstration

Use Python 3.9 or newer and choose a private secret of at least 16 characters.
Do not commit the secret.

```text
set LANTERNLINK_SECRET=replace-with-a-private-random-value
python lanternlink.py serve
```

In another terminal:

```text
set LANTERNLINK_SECRET=replace-with-a-private-random-value
python lanternlink.py send --sender WORKSHOP-1 --message READY
```

Open `http://127.0.0.1:8782/`. The receiver binds to loopback by default.

For the documented two-device test, the receiver remained on loopback and an
SSH reverse tunnel exposed receiver port 8782 as sender-loopback port 8783:

```text
ssh -N -R 127.0.0.1:8783:127.0.0.1:8782 sender-account@owned-sender
python lanternlink.py send --server http://127.0.0.1:8783 --sender HARBOR-1 --message READY
```

This keeps LanternLink off the rest of the LAN while still making a real
machine-to-machine connection. A direct private-LAN bind is also possible by
explicitly passing `--host 0.0.0.0`, but it was not used for the public test.

## Security and privacy design

- no cloud account or third-party service;
- no database and no request/client-IP logging;
- only the most recent valid signal is held in memory;
- an HMAC-SHA256 signature authenticates each signal;
- timestamps older than 90 seconds are rejected;
- one-time nonces are cached briefly to reject replays;
- message and sender labels use strict allowlists;
- the receiver listens only on loopback unless the operator opts into a LAN
  bind;
- the shared secret is supplied only through an environment variable.

This is an educational local signaling project, not an emergency, life-safety,
security, or guaranteed-delivery system.

## Tests

```text
python -m unittest discover -s tests -v
```

The test suite covers Morse encoding, valid delivery, bad signatures, stale
timestamps, nonce replay, bounded sender/message fields, receiver UI markers,
and public-package privacy rules.

## Verified evidence

On 2026-08-09, an owned macOS sender delivered `READY` to the receiver on a
separate owned Windows computer through a temporary local SSH reverse tunnel.
The receiver accepted sequence 1 as `SIGNED + FRESH + UNIQUE`. The source file
used on both devices had the same SHA-256 hash, and all eight automated tests
passed. See `EVIDENCE.md`, the sanitized JSON record, and the live receiver
screenshots in `artifacts/`.

The 60-second public video was visually reviewed across all six scenes. It is
1920x1080 H.264 at 30 fps, is caption-driven, and has a digitally silent audio
track. YouTube's upload check reported no copyright issues.

The package does not include a home address, phone/email, private IP,
credential, network inventory, employer/customer material, neighborhood RF
data, or screenshots from private systems.
