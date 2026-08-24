"""The four separating traces.

Each trace is a run that satisfies every goal below level i and violates the
conjunct added at level i.  Realizing the same semantic attack against each
stack's own evidence objects is what turns the paper's non-redundancy argument
from prose into a machine-checked matrix.
"""
from dataclasses import dataclass, field


@dataclass
class Tamper:
    name: str
    rejects_at: int                      # lowest V-level whose judge must reject
    description: str = ""
    omit: frozenset = frozenset()        # identifiers removed from the manifest
    forged: frozenset = frozenset()      # authenticated with a key the device lacks
    fabricate: dict = field(default_factory=dict)   # rid -> value invented before binding
    post_alter: dict = field(default_factory=dict)  # rid -> value changed after binding
    dy: float = 0.0                      # additive change to the claimed output

    def keeps(self, rid):
        return rid not in self.omit

    def output(self, y):
        return y + self.dy


def traces(policy):
    """Instantiate the four traces against a concrete policy."""
    first = (1, 1)
    last = (policy.m, policy.k)
    mid = (2, 3) if policy.m >= 2 and policy.k >= 3 else first
    return [
        Tamper("A1", 1, "a stored record is changed after the manifest is bound",
               post_alter={mid: 400}),
        Tamper("A2", 2, "a record is invented and labelled with a device that did not sign it",
               fabricate={first: 480}, forged=frozenset({first})),
        Tamper("A3", 3, "a required record is omitted; every remaining record is authentic",
               omit=frozenset({last})),
        Tamper("A4", 4, "the manifest is complete and authentic but the reported output is wrong",
               dy=-2.0),
    ]
