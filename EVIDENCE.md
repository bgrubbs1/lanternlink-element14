# Functional evidence

## Real cross-device run

Date: 2026-08-09

Two owned computers were used. An owned macOS computer ran the sender and an
owned Windows computer ran the receiver. The receiver stayed bound to
`127.0.0.1`. A temporary SSH reverse tunnel carried the sender's loopback
request to the receiver's loopback port, so no new firewall rule or public LAN
listener was needed.

The sender issued the bounded message `READY` as node `HARBOR-1`. The receiver
accepted sequence 1 and reported:

```text
accepted sequence=1 sender=HARBOR-1 message=READY integrity=SIGNED + FRESH + UNIQUE
```

The browser interface then displayed the accepted signal and its Morse-style
pattern (`.-. . .- -.. -.--`). The screenshots in `artifacts/` were captured
from that live receiver process after the Mac-to-Windows delivery.

## Reproducibility checks

- local and remote `lanternlink.py` SHA-256 matched:
  `4cd4620b3f943eb87c7b32459bdc4e2c991269bf1b5fe9de7f24873253515e3f`;
- eight of eight automated tests passed;
- invalid signature, stale timestamp, replayed nonce, disallowed sender, and
  disallowed message cases are explicitly tested;
- the temporary receiver and SSH tunnel were stopped after evidence capture;
- no private address, account, IP, host name, key, secret, or work data is in
  the evidence files.

This is a functional educational signaling project. It is not an emergency,
life-safety, security, or guaranteed-delivery system.
