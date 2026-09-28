# Consul Connect Service Mesh Performance Impact

## 1. Overview

This document evaluates the performance impact of introducing **Consul Connect** service mesh communication between two microservices.

The test compares:

* Direct service-to-service communication
* Service-to-service communication through Consul Connect and Envoy sidecars

The comparison focuses on:

* Throughput
* Request latency
* Error rate
* CPU utilization
* Memory utilization

The tests were performed in a local Docker environment using ApacheBench.

---

## 2. Objective

The objective of this test is to determine the performance overhead introduced when microservice communication is routed through the Consul Connect service mesh.

The test specifically measures the difference between:

```text
Direct:
Client → Service A → Service B
```

and:

```text
Consul Connect:
Client → Service A → Envoy A → Envoy B → Service B
```

---

## 3. Test Environment

### Host Environment

* Operating System: Windows 11 Pro
* Linux environment: WSL2 / Ubuntu
* Container runtime: Docker
* Consul: HashiCorp Consul 1.21
* Envoy: v1.36
* Python: 3.12
* Benchmarking tool: ApacheBench 2.3

### Services

Two lightweight Python HTTP services were used:

* `service-a`
* `service-b`

Service A acts as the client-facing service and makes requests to Service B.

Service B returns a small JSON response.

### Consul Components

The service mesh configuration consists of:

* One Consul server
* Envoy sidecar for Service A
* Envoy sidecar for Service B

The Service A Envoy proxy provides an upstream listener on:

```text
127.0.0.1:9000
```

Requests sent to this listener are routed through the Consul Connect service mesh to Service B.

---

## 4. Communication Paths

### Direct Communication

The direct test uses the normal Docker service-to-service connection:

```text
ApacheBench
    │
    ▼
Service A
    │
    │ Docker network
    ▼
Service B
```

Service A connects directly to:

```text
http://service-b:8000
```

### Consul Connect Communication

The Connect test uses the Envoy sidecars:

```text
ApacheBench
    │
    ▼
Service A
    │
    ▼
Envoy A
    │
    │ Consul Connect / mTLS
    ▼
Envoy B
    │
    ▼
Service B
```

Service A connects to the local Envoy upstream listener:

```text
http://127.0.0.1:9000
```

Envoy then discovers Service B through Consul and forwards the request to the Service B sidecar.

---

## 5. Functional Validation

Before running the performance tests, the Consul Connect path was validated independently.

A request through the Service A Envoy listener:

```bash
curl http://127.0.0.1:9000/
```

successfully returned:

```json
{
  "service": "service-b",
  "message": "Hello from Service B"
}
```

The application-level Connect endpoint was also tested:

```bash
curl http://localhost:8001/connect
```

The request successfully returned the Service B response.

This confirmed that the service mesh communication path was operational before benchmarking.

---

## 6. Benchmark Methodology

ApacheBench was used to generate HTTP requests.

The primary comparison used:

```text
Total requests: 10,000
Concurrency:    10
```

Direct communication:

```bash
ab -n 10000 -c 10 -l http://localhost:8001/
```

Consul Connect:

```bash
ab -n 10000 -c 10 -l http://localhost:8001/connect
```

The same Service A and Service B containers were used for both tests.

No containers were restarted between the final direct and Connect benchmark.

The `-l` option was used because the JSON response contains a timestamp and therefore has a variable response length.

---

## 7. Performance Results

### 7.1 Direct Communication

| Metric          |         Result |
| --------------- | -------------: |
| Requests        |         10,000 |
| Concurrency     |             10 |
| Failed requests |              0 |
| Test duration   | 36.520 seconds |
| Throughput      |   273.82 req/s |
| Mean latency    |       36.52 ms |
| p50 latency     |          20 ms |
| p90 latency     |          24 ms |
| p95 latency     |          26 ms |
| p99 latency     |          31 ms |
| Maximum latency |      19,494 ms |

### 7.2 Consul Connect

| Metric          |         Result |
| --------------- | -------------: |
| Requests        |         10,000 |
| Concurrency     |             10 |
| Failed requests |              0 |
| Test duration   | 69.605 seconds |
| Throughput      |   143.67 req/s |
| Mean latency    |       69.61 ms |
| p50 latency     |          33 ms |
| p90 latency     |          38 ms |
| p95 latency     |          40 ms |
| p99 latency     |          44 ms |
| Maximum latency |      69,595 ms |

---

## 8. Performance Impact

Using the 10,000-request tests:

### Throughput

Direct communication:

```text
273.82 req/s
```

Consul Connect:

```text
143.67 req/s
```

The observed throughput reduction was approximately:

```text
47.5%
```

### Mean Latency

Direct:

```text
36.52 ms
```

Consul Connect:

```text
69.61 ms
```

The observed increase in mean latency was approximately:

```text
90.6%
```

### Median Latency

Direct:

```text
20 ms
```

Consul Connect:

```text
33 ms
```

Observed increase:

```text
65.0%
```

### P95 Latency

Direct:

```text
26 ms
```

Consul Connect:

```text
40 ms
```

Observed increase:

```text
53.8%
```

### P99 Latency

Direct:

```text
31 ms
```

Consul Connect:

```text
44 ms
```

Observed increase:

```text
41.9%
```

---

## 9. Resource Utilization

An idle resource snapshot was captured before the load test.

### Idle

| Container |   CPU |    Memory |
| --------- | ----: | --------: |
| Service A | 0.03% | 13.78 MiB |
| Envoy A   | 1.20% | 18.83 MiB |
| Service B | 0.02% | 23.42 MiB |
| Envoy B   | 1.35% | 17.31 MiB |

The two Envoy sidecars consumed approximately:

```text
36.14 MiB
```

of memory while idle.

### During Connect Load

Several Docker statistics snapshots were captured while the Connect benchmark was running.

Observed values were approximately:

| Container | CPU observed | Memory observed |
| --------- | -----------: | --------------: |
| Service A |   36.2–36.6% |       ~13.8 MiB |
| Envoy A   |   42.3–43.0% |  ~19.5–20.3 MiB |
| Service B |   16.8–17.9% |       ~23.4 MiB |
| Envoy B   |   37.9–38.5% |  ~17.4–17.9 MiB |

The Envoy sidecars therefore introduced additional memory consumption and significant CPU activity during the Connect load test.

These CPU values are instantaneous Docker statistics snapshots rather than long-duration CPU averages and should therefore be interpreted as observations rather than exact average utilization.

---

## 10. Observations

The benchmark demonstrated measurable overhead when service-to-service communication was routed through Consul Connect.

The primary observations were:

1. Direct communication achieved higher throughput than the Connect configuration.

2. Consul Connect increased average request latency.

3. Consul Connect increased p95 and p99 latency.

4. The Envoy sidecars consumed additional memory.

5. The Envoy sidecars showed significantly higher CPU activity under load than when idle.

6. Both communication methods completed the final 10,000-request benchmark with zero failed requests.

7. Consul Connect adds additional network hops and proxy processing:

```text
Service A → Envoy A → Envoy B → Service B
```

instead of:

```text
Service A → Service B
```

---

## 11. Important Considerations

The measured performance impact should not be interpreted as a universal performance penalty for Consul Connect.

This test was performed using:

* A local Docker environment
* WSL2
* A lightweight Python `HTTPServer`
* A single Consul server
* Two Envoy sidecars
* Low concurrency
* Small HTTP responses
* Local container networking

Production environments can produce different results depending on:

* CPU and memory resources
* Network latency
* Number of services
* Request payload size
* Request concurrency
* Envoy configuration
* Consul cluster configuration
* TLS/mTLS requirements
* Service discovery traffic
* Retry and timeout configuration
* Application architecture

The Python `HTTPServer` used in this test is also intentionally simple and is not representative of a production-grade application server.

---

## 12. Limitations

The following limitations apply to this benchmark:

### Local Environment

The benchmark was performed on a local development environment rather than production infrastructure.

### Single Consul Server

The test used a single Consul server and therefore did not evaluate Consul cluster scaling or failure scenarios.

### Simple Application

The microservices perform minimal processing and return a small JSON response.

### CPU Measurement

Docker CPU measurements were point-in-time snapshots rather than averages collected over the entire benchmark.

### Small Concurrency

The primary comparison used concurrency of 10. Higher concurrency produced connection resets/timeouts with the simple Python server, so those tests were not used as the primary performance comparison.

### Outliers

The maximum latency values were significantly higher than the p99 values. These outliers were therefore not used as the primary indicator of typical request performance.

---

## 13. Reproduction

Start the application and Consul components according to the project configuration.

Verify the Connect path:

```bash
curl http://localhost:8001/connect
```

Run the direct benchmark:

```bash
ab -n 10000 -c 10 -l http://localhost:8001/ | tee direct-load.txt
```

Run the Connect benchmark:

```bash
ab -n 10000 -c 10 -l http://localhost:8001/connect | tee connect-load.txt
```

Check resource usage:

```bash
docker stats --no-stream \
  --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' \
  consul-perf-service-a \
  consul-perf-service-a-proxy \
  consul-perf-service-b \
  consul-perf-service-b-proxy
```

Check Envoy request counters:

```bash
docker exec consul-perf-service-a python3 -c \
"import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:19000/clusters').read().decode())" \
| grep 'service-b.*rq_'
```

---

## 14. Conclusion

The benchmark successfully demonstrated the performance characteristics of direct microservice communication compared with Consul Connect service mesh communication.

In this local test environment, Consul Connect introduced measurable overhead in throughput, latency, CPU utilization, and memory consumption due primarily to the additional Envoy proxy layer and service-mesh communication path.

The final 10,000-request comparison showed:

```text
Direct throughput:        273.82 req/s
Consul Connect throughput: 143.67 req/s

Direct p95:               26 ms
Consul Connect p95:       40 ms

Direct p99:               31 ms
Consul Connect p99:       44 ms
```

Both tests completed with zero failed requests.

The results demonstrate the trade-off between the additional processing overhead of a service mesh and the capabilities it provides, such as service discovery, traffic management, observability, and secure service-to-service communication.

The measurements should be treated as baseline results for this specific Docker-based test environment rather than generalized production performance figures.
o
