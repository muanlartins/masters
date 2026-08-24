"""Acquisition policy, observations, manifest, and canonical serialization.

The policy P is public and known to the judge before the run.  Anything in P
-- the device roster, the eligible record identifiers, the operator and its
parameters, the epoch -- is therefore NOT charged to B_ev.  Only what the
aggregator must transmit beyond P and the claimed output y is charged.
"""
import hashlib
import json
import struct
from dataclasses import dataclass, field

# Wire format for one observation: device id, sequence number, value.
# Values are centi-degrees Celsius, which is the resolution of the loggers the
# cold-chain scenario describes.
OBS_FMT = ">HHh"
B_OBS = struct.calcsize(OBS_FMT)          # 6 bytes
EPOCH_FMT = ">Q"
POLICY_SERIALIZATION_VERSION = 1
ROSTER_VERSION = 1


@dataclass(frozen=True)
class Observation:
    device: int
    seq: int
    value: int                             # centi-degrees Celsius

    @property
    def rid(self):
        return (self.device, self.seq)

    def wire(self):
        return struct.pack(OBS_FMT, self.device, self.seq, self.value)


@dataclass
class Policy:
    """Public acquisition policy P."""
    epoch: int
    m: int                                 # devices in the roster
    k: int                                 # required readings per device
    operator: str
    params: dict = field(default_factory=dict)
    # device -> suite -> canonical public-key bytes
    pubkeys: dict = field(default_factory=dict)
    # Keys for the external anchor and modeled isolated path are policy data too.
    service_keys: dict = field(default_factory=dict)
    roster_version: int = ROSTER_VERSION

    @property
    def n(self):
        return self.m * self.k

    def required_ids(self):
        return [(d, q) for d in range(1, self.m + 1) for q in range(1, self.k + 1)]

    def credential(self, device, suite):
        """Return the exact credential enrolled by P for a named device."""
        try:
            return self.pubkeys[device][suite]
        except KeyError as exc:
            raise ValueError(f"device {device} has no enrolled {suite} credential") from exc

    def service_key(self, name):
        try:
            return self.service_keys[name]
        except KeyError as exc:
            raise ValueError(f"policy has no enrolled service key {name}") from exc

    @staticmethod
    def _field(data):
        if not isinstance(data, bytes):
            raise TypeError("canonical policy fields must be bytes")
        return struct.pack(">I", len(data)) + data

    def roster_wire(self):
        """Canonical binary serialization of the versioned credential roster."""
        out = [struct.pack(">IH", self.roster_version, len(self.pubkeys))]
        for device in sorted(self.pubkeys):
            suites = self.pubkeys[device]
            out.append(struct.pack(">HH", device, len(suites)))
            for suite in sorted(suites):
                out.append(self._field(suite.encode("ascii")))
                out.append(self._field(suites[suite]))
        out.append(struct.pack(">H", len(self.service_keys)))
        for name in sorted(self.service_keys):
            out.append(self._field(name.encode("ascii")))
            out.append(self._field(self.service_keys[name]))
        return b"".join(out)

    def wire(self):
        """Canonical serialization of every policy field that judges trust."""
        operator = self.operator.encode("utf-8")
        params = json.dumps(self.params, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=True, allow_nan=False).encode("ascii")
        return b"".join([
            b"vfusion-policy\x00",
            struct.pack(">HQHH", POLICY_SERIALIZATION_VERSION,
                        self.epoch, self.m, self.k),
            self._field(operator), self._field(params),
            self._field(self.roster_wire()),
        ])

    def roster_digest(self):
        return hashlib.sha256(self.roster_wire()).digest()

    def digest(self):
        return hashlib.sha256(self.wire()).digest()


@dataclass
class Entry:
    """One manifest row: an identifier plus a binding commitment to the value."""
    device: int
    seq: int
    commit: bytes
    sig: bytes = b""

    @property
    def rid(self):
        return (self.device, self.seq)

    def preimage(self, epoch):
        """The bytes a device signs: epoch, identifier, and value commitment."""
        return struct.pack(EPOCH_FMT, epoch) + struct.pack(">HH", self.device, self.seq) + self.commit


@dataclass
class Manifest:
    entries: list

    def ids(self):
        return [e.rid for e in self.entries]

    def __len__(self):
        return len(self.entries)


@dataclass
class Run:
    """One acquisition window: what the aggregator holds before producing evidence."""
    policy: Policy
    obs: list
    salts: dict                            # rid -> commitment salt
    run_id: bytes                          # unique identifier carried in evidence
    auditor_state: bytes                   # fresh state held independently by judge
