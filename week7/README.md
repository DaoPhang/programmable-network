# Lab 7: REST APIs, Retries and Idempotency

Student ID suffix: 6042  
Date: 21 November 2026

[Course lab instructions](https://firdaussahran.github.io/wic2005/weeks/week-07/#tab-lab)

## Setup

The lab API (`labapi.py --id 6042`) ran in a detached `python:3.12` container named `api`. A second
`python:3.12` container named `client` ran the `curl` commands and the Python scripts. Both were on the
user-defined Docker network `apilab` and mounted the `week7` folder at `/lab`. The API is reachable only
inside that network, at `http://api:8000`. It serves 242 devices (200 + NN, with NN = 42) on `10.42.0.0/16`.
Tokens last 600 s and the rate limit is 5 requests per second per token, until Step 6 changed both.

## Practical results

| Step | Actual result | Evidence |
|---|---|---|
| 1: First request | `GET /api/v1/` answered with `Content-Type: application/json`. | |
| 2: Status codes | Provoked 404, 405 (with `Allow: GET, PUT, PATCH, DELETE`), 400, 422, 409 and 403 (viewer token). A loop of GETs on one token got five 200s, then 429s. | [status.txt](lab7/status.txt) |
| 3: Idempotency | `PUT /vlans/30` gave 201 then 200. `DELETE /vlans/99` gave 204 then 404. `POST /acl/entries` twice gave 201 and 201 and two entries (1 and 2). A keyed POST sent twice gave 201 then 201 with `Idempotent-Replayed: true`, and the audit showed 5 writes, not 6. | [audit-step3.txt](lab7/audit-step3.txt) |
| 4: Lost responses | With `lose_responses` 0.5, `retry_naive.py` made 8 runs and 11 writes. `retry_safe.py` made 6 runs and 6 writes, although 3 of those runs lost a response and retried. | [audit-step4.txt](lab7/audit-step4.txt) |
| 5: Read everything | `inventory.py` with `errors_503` 0.2 read 242 devices (the API said 242) in 31 requests. Sites: johor 60, kl-hq 61, penang 60, pj-dc 61. | [inventory.txt](lab7/inventory.txt) |
| 6: Token expiry | With `--token-ttl 5 --rate 2`, `inventory.py` logged in 3 times (the first login and 2 re-logins after a 401), read all 242 devices and needed 39 requests. | [expiry.txt](lab7/expiry.txt) |
| 7: OpenAPI | Read from `/openapi.json`: largest `limit` 50, `/acl/entries/{id}` allows GET and DELETE, `?site=` filters devices. | |

## Wrap-up answers

### 1. What `docker network inspect apilab` shows, and how it is built from Week 6

It shows a `bridge` network with subnet `172.22.0.0/16` and gateway `172.22.0.1`, and the two attached
containers with their addresses: `api` at `172.22.0.2/16` and `client` at `172.22.0.3/16`, each with a MAC
address. The API's own log shows the requests arriving from `172.22.0.3`, which is the client. Docker builds
this from the Week 6 building blocks: each container is a process in its own network namespace (Week 6 Part
1), each gets one end of a veth pair, and the other end is attached to a Linux bridge for the network (Week 6
Part 2). The gateway address belongs to that bridge. A user-defined network also gives name resolution, which
is why `api` resolves to `172.22.0.2` inside the network and the name does not resolve from the Windows host.
`docker network inspect` lists the network and its members, but not the veth pairs or the bridge, so that
part is how Docker works, not something this output shows.

### 2. What a client should do next for each status code in Step 2

| Code | Server message in my run | What the client should do next |
|---|---|---|
| 404 | `VLAN 77 not found` | Do not retry. The resource isn't there. Check the URL or create it. |
| 405 | `POST is not allowed on a single VLAN` | Do not retry. Use a method from the `Allow` header (GET, PUT, PATCH, DELETE). |
| 400 | `the request body is not valid JSON` | Do not retry. Fix the body first. |
| 422 | `id must be a VLAN number from 1 to 4094` | Do not retry. Fix the value first. |
| 409 | `VLAN 10 already exists: use PUT to replace it` | Do not retry the same request. Use PUT, or treat it as already done if that is the intended end state. |
| 403 | `viewer has a read-only token` | Do not retry. Use an account with write access. |
| 429 | (loop of GETs, after five 200s) | Retry after the number of seconds in `Retry-After`. |

The ones to never retry as they stand are 404, 405, 400, 422, 409 and 403, because the same request fails
again. The ones worth retrying are 429 (after waiting `Retry-After`), 503 and no response at all (with
backoff, and with an `Idempotency-Key` on a POST). A 401 means the token expired: log in again, then send the
same request again (Step 6).

### 3. Why `retry_naive.py` created duplicates, and how the fix prevents them

When a response is lost, the client cannot tell whether the server never got the request or did it and the reply
was lost. `retry_naive.py` resends, and a POST is not idempotent, so a request the server had already carried
out is carried out again. In my run 8 runs made 11 writes: run 3 lost one response (entries 6 and 7), and run 5
lost two (entries 9, 10 and 11). The fix in `retry_safe.py` creates `KEY = str(uuid.uuid4())` once before the
loop and sends it as the `Idempotency-Key` header on every attempt. The server stores the first result under
that key, and a retry with the same key and the same body gets that result back (with `Idempotent-Replayed:
true`) and adds nothing. With the fix, 6 runs made 6 writes (entries 15 to 20, no duplicates), although 3 runs
retried. The key must be chosen once, before the first attempt, because the server can only recognise a retry
as the same change if it carries the same key. A new key on each attempt would look like a new change, and the
server would add the entry again, which is what the naive script did.

### 4. How many requests `inventory.py` sent, and why more than the number of pages

With `limit=10`, 242 devices take 25 pages (24 pages of 10 and one of 2). In Step 5, with `errors_503` 0.2, it
sent 31 requests, so 6 were retries. In Step 6, with 5-second tokens and 2 requests per second, it sent 39
requests, so 14 were retries, plus 3 login requests that the counter does not include. A page can cost more
than one request when the server answers 503 or 429, when the response is lost, or when a 401 makes the client
log in again and send the page again. The output does not split the retries by status code.

### 5. What I found in the OpenAPI document that I would never have guessed

The devices endpoint takes `?site=` (`kl-hq`, `pj-dc`, `penang` or `johor`), which the lecture never mentioned.
Its `limit` goes up to 50 (default 20), so the same inventory could be read in 5 pages instead of 25.
`/api/v1/acl/entries/{id}` allows only GET and DELETE, so an ACL entry can be removed but not edited. The
`Idempotency-Key` description says the same key with a different body is rejected with 422. I read that from
the document and did not test it.

## Assignment: `sync.py` makes the API match `intent.yaml`

`intent.yaml` lists 6 VLANs (10 users, 20 servers, 30 guests, 40 voice, 50 iot, 99 mgmt) and 5 ACL entries on
`10.42.0.0/16`: permits (one with tcp/443, one with udp/161, one with udp/5060) and denies (two, protocol any).
`python3 sync.py intent.yaml --dry-run` prints the plan and sends only reads. Without `--dry-run` it applies the
plan, reads the state back and prints `Check: MATCH` or `Check: MISMATCH` (exit code 1).
It reads `LAB_API_URL` (default `http://api:8000`), `LAB_USERNAME` and `LAB_PASSWORD` from the environment.

| Evidence | What it shows |
|---|---|
| [dry-run.txt](evidence/dry-run.txt) | Fresh API: plan of 4 VLAN PUTs and 5 ACL POSTs, 2 requests (reads), audit `writes: 0`. |
| [apply.txt](evidence/apply.txt) | Chaos `lose_responses` 0.3 and `errors_503` 0.2: 28 requests, `Check: MATCH`, audit `writes: 9` (4 PUTs, 5 POSTs, each once), VLANs 1, 10, 20, 30, 40, 50, 99 and ACL entries 1 to 5, no duplicates. |
| [second-run.txt](evidence/second-run.txt) | Same API, chaos still on, audit cleared first: empty plan, `Check: MATCH`, 4 requests (2 reads for the plan, 2 for the check), audit `writes: 0`. |
| [expiry.txt](evidence/expiry.txt) | API with `--token-ttl 3 --rate 2`: logged in 3 times (first login and 2 re-logins after a 401), `Check: MATCH`, audit `writes: 9`, 21 requests. |
| [delete-path.txt](evidence/delete-path.txt) | Extra check: I added a stray VLAN 77 and a stray ACL entry 6 by hand. `sync.py` planned exactly `DELETE ACL entry 6` and `DELETE VLAN 77`, ended with `Check: MATCH`, and the audit shows 2 writes (both 204). |

### 1. How `sync.py` decides what to change

It reads both collections (`GET /vlans`, `GET /acl/entries`, following `next`) and compares them with the intent
without sending anything. VLANs are matched by id. In my apply run, VLAN 30 `guests` was missing, so the plan was
`PUT VLAN 30 guests: create`. VLAN 99 existed as `old-guest`, so the plan was `PUT VLAN 99 mgmt: rename from
old-guest`. A VLAN on the API that is not in the intent is deleted, except VLAN 1, which the API owns and never
lets go (a delete gives 409). ACL entries have no usable id in the intent, so an entry is identified by all its
fields: action, src, dst, protocol, port and description. The API fills in `protocol: any` and `port: null`, and
`sync.py` fills in the same defaults before comparing. An entry in the intent that has no match is a POST, for
example `permit 10.42.10.0/24 -> 10.42.20.0/24 tcp/443 (users-reach-web)`. An entry on the API that matches nothing
in the intent is a `DELETE` by id. The API has no PUT or PATCH for ACL entries, so a changed entry is a delete plus
a new add. After applying, it reads the state again and runs the same comparison. The check passes only if that
plan is empty.

### 2. Which requests are safe to retry, and why

| Request | Retried? | Why |
|---|---|---|
| `GET` (reads and the check) | Yes | Reading changes nothing. |
| `PUT /vlans/{id}` | Yes | It sets the VLAN to the given name, so sending it twice gives the same end state (201 then 200 in Step 3). |
| `DELETE` | Yes | A second delete gives 404, which `sync.py` treats as done, because a retry follows a lost reply that may have deleted it already. |
| `POST /acl/entries` | Yes, only with an `Idempotency-Key` | Without the key a retry after a lost reply adds the entry again (the duplicates in `retry_naive.py`). With the key the server replays the first result. |

A 401 means the token expired, so it logs in again and sends the same request. A 429 waits for `Retry-After`. A 503
or no reply at all waits 1, 2, 4... seconds plus a random part and tries again, up to 6 failed tries, then it stops with an
error. Other 4xx codes (such as 400, 404, 409 and 422) are not retried, because the same request would fail again.
The only exception is the 404 on a `DELETE`, which is accepted as done.

### 3. PUT for VLANs, POST for ACL entries, and how the key is chosen

A VLAN has an id that I choose, and `PUT /vlans/{id}` states the whole result, so it can be repeated safely and
needs no key. An ACL entry has an id that the server assigns, and the only way to add one is `POST`, which adds a new
entry each time. Because of that, every planned POST gets a new key (`str(uuid.uuid4())`), made once before the first
attempt of that POST and reused only by the retries of that same POST. If a new key were made for each attempt, the
server would see each retry as a new change, and a lost reply would add the entry again, which is the duplicates I
got with `retry_naive.py`. If one key were used for every entry or every run, the server would answer later POSTs
with the stored first result and add nothing: a second entry sent with the same key and a different body should be
rejected with 422 (from the OpenAPI document, which I did not test), and a later run that needed the same entry
again, after it was deleted, would just get the old reply back and the entry would stay missing. So the key
identifies one attempt-and-its-retries of one change, never more.

### 4. Two people running different intents at the same time

Each `sync.py` makes the API equal to its own intent, so each one deletes what the other one added. They would keep
undoing each other, and the last run wins. There is also a gap between reading the state and applying the plan: a
plan made from a state that has since changed can delete or add the wrong thing. The OpenAPI document I read shows no
version number, ETag or lock, so the API cannot detect this today. It would need a version for the collection (an
ETag, with `If-Match` on every write and a 412 answer when the version is old, after which the client reads again
and plans again), or a lock with a timeout that one client holds while it applies, or a single shared intent file in
git so that only one intent exists.

### 5. Where the credentials are, and why none are in the repository

The username and password are only read from the environment variables `LAB_USERNAME` and `LAB_PASSWORD`, which I
set in the client container shell for the session. `sync.py` and `inventory.py` contain no password or token. The
token is kept only in memory and renewed when the API answers 401. The evidence files print `logged in as netops`
and never the token, and the audit log does not contain tokens. I checked the repository and its history for token
and password strings before the final commit (see the commit step of this assignment).

## AI use

I used Claude Code (Anthropic), at Level 3 (Open), for both the lab and the assignment. For the lab it walked me
through the steps, explained the output of each step, wrote `step1-commands.md` notes, and corrected where I had
pasted code in the wrong place in `inventory.py`. For the assignment it proposed the content of `intent.yaml`,
wrote the first version of `sync.py`, gave me the commands for each evidence run, checked the pasted output against
what I expected, and drafted the answers above from my evidence. I ran every command myself, in my own containers,
and pasted the output; the evidence files are what those runs produced. I read `sync.py` and the answers before
committing them.
