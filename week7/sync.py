#!/usr/bin/env python3
"""Make the lab API hold exactly what intent.yaml says.

    python3 sync.py intent.yaml --dry-run     # print the plan, change nothing
    python3 sync.py intent.yaml               # plan, apply, then check

Environment: LAB_API_URL (default http://api:8000), LAB_USERNAME, LAB_PASSWORD.
No token or password is written in this file.
"""
import argparse
import os
import random
import sys
import time
import uuid

import requests
import yaml

API = os.environ.get("LAB_API_URL", "http://api:8000")
DEFAULT_VLAN = 1  # the API owns VLAN 1; it is never created, changed or deleted


class Client:
    """A logged-in session. Every request is retried only when that is safe."""

    def __init__(self):
        self.token = None
        self.requests = 0  # HTTP requests sent, retries included

    def login(self):
        try:
            user, password = os.environ["LAB_USERNAME"], os.environ["LAB_PASSWORD"]
        except KeyError:
            sys.exit("Set LAB_USERNAME and LAB_PASSWORD in the environment first.")
        r = requests.post(f"{API}/api/v1/auth/token", json={"username": user, "password": password}, timeout=5)
        r.raise_for_status()
        self.token = r.json()["token"]
        print(f"logged in as {user}")

    def request(self, method, path, accept=(), **kw):
        """Send one request and return the response once it is a success.

        path: a path such as /api/v1/vlans, or a full URL (the API's "next" links).
        accept: extra status codes to treat as success (for example 404 on a DELETE).
        Safe to retry because every request here is GET, PUT, DELETE, or a POST with a key.
        """
        if self.token is None:
            self.login()
        url = path if path.startswith("http") else API + path
        headers = kw.pop("headers", {})
        failures, delay = 0, 1
        while True:
            self.requests += 1
            try:
                r = requests.request(method, url, timeout=5, **kw,
                                     headers={**headers, "Authorization": f"Bearer {self.token}"})
            except (requests.ConnectionError, requests.Timeout):
                r = None
            if r is not None:
                if r.ok or r.status_code in accept:
                    return r
                if r.status_code == 401:
                    self.login()
                    continue
                if r.status_code == 429:
                    time.sleep(float(r.headers.get("Retry-After", 1)))
                    continue
                if r.status_code != 503:
                    r.raise_for_status()
            failures += 1
            if failures >= 6:
                sys.exit(f"giving up on {method} {path} after 6 failed tries")
            time.sleep(delay + random.random())
            delay *= 2

    def get_all(self, path):
        """Read a list endpoint to the end, following the "next" links."""
        items = []
        while path:
            body = self.request("GET", path).json()
            items.extend(body["items"])
            path = body.get("next")
        return items


def acl_key(entry):
    """The identity of an ACL entry: every field, with the API's defaults filled in.

    The API has no way to edit an ACL entry, so two entries are the same only if
    all of these match. A changed entry is a delete plus an add.
    """
    return (
        entry["action"],
        entry["src"],
        entry["dst"],
        entry.get("protocol", "any"),
        entry.get("port"),
        entry.get("description", ""),
    )


def load_intent(path):
    """Read intent.yaml and reject anything the API would refuse anyway."""
    with open(path) as f:
        intent = yaml.safe_load(f)
    vlans = {}
    for v in intent.get("vlans", []):
        vid = v["id"]
        if vid == DEFAULT_VLAN:
            sys.exit("intent.yaml lists VLAN 1, which belongs to the API: remove it.")
        if vid in vlans:
            sys.exit(f"intent.yaml lists VLAN {vid} twice.")
        vlans[vid] = v["name"]
    acl = []
    for e in intent.get("acl", []):
        if e.get("port") is not None and e.get("protocol", "any") not in ("tcp", "udp"):
            sys.exit(f"ACL entry '{e.get('description', '')}': a port needs protocol tcp or udp.")
        if acl_key(e) in [acl_key(x) for x in acl]:
            sys.exit(f"ACL entry '{e.get('description', '')}' is listed twice.")
        acl.append(e)
    return vlans, acl


def read_state(client):
    """Read what the API holds now: {vlan id: name} and the list of ACL entries."""
    vlans = {v["id"]: v["name"] for v in client.get_all("/api/v1/vlans")}
    acl = client.get_all("/api/v1/acl/entries")
    return vlans, acl


def make_plan(want_vlans, want_acl, have_vlans, have_acl):
    """Compare intent with state. Returns the creates, changes and deletes, and sends nothing."""
    plan = {"vlan_put": [], "vlan_delete": [], "acl_delete": [], "acl_add": []}
    for vid, name in sorted(want_vlans.items()):
        if vid not in have_vlans:
            plan["vlan_put"].append((vid, name, "create"))
        elif have_vlans[vid] != name:
            plan["vlan_put"].append((vid, name, f"rename from {have_vlans[vid]}"))
    for vid, name in sorted(have_vlans.items()):
        if vid != DEFAULT_VLAN and vid not in want_vlans:
            plan["vlan_delete"].append((vid, name))

    # Match each wanted entry with one entry already on the API; the rest are extra.
    spare = {}
    for e in have_acl:
        spare.setdefault(acl_key(e), []).append(e["id"])
    for e in want_acl:
        ids = spare.get(acl_key(e))
        if ids:
            ids.pop()
        else:
            plan["acl_add"].append(e)
    for key, ids in spare.items():
        for entry_id in ids:
            plan["acl_delete"].append((entry_id, key))
    return plan


def plan_is_empty(plan):
    return not any(plan.values())


def describe(key):
    action, src, dst, protocol, port, description = key
    where = f"{protocol}/{port}" if port is not None else protocol
    return f"{action} {src} -> {dst} {where} ({description})"


def show_plan(plan):
    print("Plan:")
    if plan_is_empty(plan):
        print("  (empty: the API already matches the intent)")
        return
    for vid, name, why in plan["vlan_put"]:
        print(f"  PUT    VLAN {vid} {name}: {why}")
    for entry_id, key in plan["acl_delete"]:
        print(f"  DELETE ACL entry {entry_id}: {describe(key)}")
    for e in plan["acl_add"]:
        print(f"  POST   ACL entry: {describe(acl_key(e))}")
    for vid, name in plan["vlan_delete"]:
        print(f"  DELETE VLAN {vid} {name}")
    print(f"  {len(plan['vlan_put'])} VLAN put, {len(plan['vlan_delete'])} VLAN delete, "
          f"{len(plan['acl_add'])} ACL add, {len(plan['acl_delete'])} ACL delete")


def apply_plan(client, plan):
    """Carry out the plan. Each call is safe to repeat, so the client may retry it."""
    for vid, name, _ in plan["vlan_put"]:
        client.request("PUT", f"/api/v1/vlans/{vid}", json={"name": name})
    for entry_id, _ in plan["acl_delete"]:
        # 404 means someone (or an earlier try whose reply was lost) already removed it
        client.request("DELETE", f"/api/v1/acl/entries/{entry_id}", accept=(404,))
    for e in plan["acl_add"]:
        body = {k: e[k] for k in ("action", "src", "dst") }
        body["protocol"] = e.get("protocol", "any")
        body["description"] = e.get("description", "")
        if e.get("port") is not None:
            body["port"] = e["port"]
        # One new key for this planned entry, reused by every retry of this one POST.
        # A key is never shared between entries or between runs.
        client.request("POST", "/api/v1/acl/entries", json=body,
                       headers={"Idempotency-Key": str(uuid.uuid4())})
    for vid, _ in plan["vlan_delete"]:
        client.request("DELETE", f"/api/v1/vlans/{vid}", accept=(404,))


def verify(client, want_vlans, want_acl):
    """Read the state back and say whether it equals the intent."""
    have_vlans, have_acl = read_state(client)
    plan = make_plan(want_vlans, want_acl, have_vlans, have_acl)
    if plan_is_empty(plan):
        print(f"Check: MATCH. The API holds exactly the intent "
              f"({len(want_vlans)} VLANs besides VLAN 1, {len(want_acl)} ACL entries).")
        return True
    print("Check: MISMATCH. What is still different:")
    show_plan(plan)
    return False


def main():
    ap = argparse.ArgumentParser(description="Make the lab API hold exactly what intent.yaml says.")
    ap.add_argument("intent", help="the intent file, for example intent.yaml")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and change nothing")
    args = ap.parse_args()

    want_vlans, want_acl = load_intent(args.intent)
    client = Client()
    have_vlans, have_acl = read_state(client)
    plan = make_plan(want_vlans, want_acl, have_vlans, have_acl)
    show_plan(plan)

    if args.dry_run:
        print(f"Dry run: nothing was changed ({client.requests} requests, all reads).")
        return
    if not plan_is_empty(plan):
        apply_plan(client, plan)
    ok = verify(client, want_vlans, want_acl)
    print(f"{client.requests} requests sent.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
