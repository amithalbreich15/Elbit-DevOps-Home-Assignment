# Bonus – Multicast: Definition, Inter-Network Routing & Example

## 1. What Is Multicast?

**Multicast** is a one-to-many network communication model where a single data packet
sent from one source is efficiently delivered to a *group* of interested receivers at
the same time — without the source having to send a separate copy to each one.

| Mode | Sender → Receivers | Duplicate packets at source |
|------|-------------------|---------------------------|
| Unicast | 1 → 1 | N copies (one per receiver) |
| Broadcast | 1 → Everyone on subnet | 1 copy, floods entire layer-2 segment |
| Multicast | 1 → Subscribed group | 1 copy, replicated only at tree branch points |

IPv4 multicast addresses occupy the Class D range: **224.0.0.0 – 239.255.255.255**

### Typical Use Cases
- Live IPTV / video streaming (e.g. one feed → thousands of set-top boxes)
- Financial data feeds (stock tickers to many trading systems simultaneously)
- Online gaming state distribution
- Large-scale OS/firmware rollouts
- Routing protocols — OSPF uses 224.0.0.5, RIPv2 uses 224.0.0.9

---

## 2. Moving Multicast Between Networks

Multicast packets are not forwarded across router boundaries by default. Several
techniques make inter-network multicast possible:

### 2a. PIM-SM (Protocol Independent Multicast – Sparse Mode)
The dominant inter-domain multicast routing protocol.

**How it works:**
1. Receivers send an **IGMP Join** to their local router.
2. The router sends a **PIM Join** toward a pre-configured **Rendezvous Point (RP)**.
3. A *Shared Tree* (RPT) is built: RP ← branch routers ← receivers.
4. When traffic flows, routers may switch to a direct *Shortest Path Tree* (SPT)
   from source → receivers, cutting latency and RP load.

### 2b. GRE Tunneling (Generic Routing Encapsulation)
When transit networks don't support multicast natively, multicast packets are
**encapsulated inside unicast GRE packets**. Tunnel endpoints decapsulate and
forward as multicast on the local segment. The transit network sees only normal
unicast traffic.

### 2c. AMT (Automatic Multicast Tunneling – RFC 7450)
Allows multicast over the public internet (which has no native multicast support)
via UDP encapsulation between an **AMT Relay** (near the source) and an
**AMT Gateway** (near the receiver).

### 2d. Multicast VPN (mVPN / RFC 6513)
Service providers carry customer multicast inside an MPLS/BGP backbone that may
not itself run native multicast end-to-end. Customer traffic is encapsulated in
provider tunnels (P-tunnels) and delivered to remote PE routers.

---

## 3. Example Scenario – Corporate Video Streaming

**Topology:**
```
Network A (HQ)  10.1.0.0/24          Network B (Remote)  10.2.0.0/24
┌─────────────────────────┐          ┌──────────────────────────────┐
│  Streaming Server       │          │  Remote Employees            │
│  10.1.0.10              │          │  10.2.0.10 – 10.2.0.50       │
└──────────┬──────────────┘          └──────┬───────────────────────┘
           │                                │
      [Router A]  ──── WAN (PIM-SM) ────  [Router B]
      PIM-SM RP                            PIM-SM
```

**Multicast group:** 239.1.2.3

**Step-by-step flow:**
1. Employees open a media player → player sends **IGMP Join 239.1.2.3** to Router B.
2. Router B sends a **PIM Join** upstream toward the RP (Router A or a dedicated RP).
3. The streaming server begins sending UDP packets to **239.1.2.3**.
4. Router A receives the stream, recognises active downstream receivers, and forwards
   across the WAN toward Router B.
5. Router B replicates **one** incoming copy to all 40 interested receivers on its LAN.

**Bandwidth saving:** 40 employees receive HD video.  
- Unicast: 40 × 4 Mbps = **160 Mbps** across the WAN.  
- Multicast: 1 × 4 Mbps = **4 Mbps** across the WAN. (**97.5% saving**)

**If the WAN doesn't support multicast:**  
Router A encapsulates each multicast packet in a **GRE unicast tunnel** destined for
Router B's WAN IP.  Router B decapsulates and distributes locally.  The WAN carrier
sees only unicast traffic and routes it normally.

---

## Summary

| Problem | Solution |
|---------|----------|
| Multicast within one LAN | IGMP + Layer-2 multicast snooping |
| Multicast across routed LAN segments | PIM-SM, build distribution tree |
| WAN without native multicast | GRE tunnel or AMT |
| Public internet delivery | AMT (RFC 7450) |
| Service-provider backbone | mVPN (RFC 6513) |
