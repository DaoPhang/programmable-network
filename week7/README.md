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

## AI use

I used Claude Code (Anthropic) to walk through the lab, to explain the output of each step, and to write
`step1-commands.md` notes. It also corrected where I had pasted code in the wrong place in `inventory.py`.
I ran every command and pasted the output myself.
