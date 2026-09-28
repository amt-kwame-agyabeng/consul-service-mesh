# Consul Connect Service Mesh Performance Test

## Overview

This project demonstrates and evaluates **Consul Connect service mesh communication** between two containerized microservices.

The project consists of two Python-based microservices:

* **Service A** — acts as the calling/client microservice.
* **Service B** — acts as the downstream microservice.

The project implements two communication paths:

### Direct Communication

```text
Service A → Service B
```

### Consul Connect Communication

```text
Service A → Envoy A → Envoy B → Service B
```

The two approaches are then benchmarked to measure the performance impact introduced by the Consul Connect service mesh.

---

## Project Objectives

The main objectives are to:

* Deploy two containerized microservices.
* Configure Consul as the service discovery and service mesh control plane.
* Enable Consul Connect.
* Register Service A and Service B with Consul.
* Deploy Envoy sidecars for both services.
* Configure Service A's Envoy proxy to discover Service B through Consul.
* Route Service A's Connect traffic through the Envoy sidecars.
* Validate service-to-service communication through the mesh.
* Compare direct communication with Consul Connect communication.
* Measure latency, throughput, CPU usage, memory usage, and request failures.
* Document the observed performance impact.

---

## Architecture

### Direct Communication

In the direct communication mode, Service A communicates with Service B through the Docker application network.

```text
                    Docker Network

┌──────────────┐        HTTP        ┌──────────────┐
│              │ ─────────────────► │              │
│  Service A   │                    │  Service B   │
│  :8000       │                    │  :8000       │
│              │                    │              │
└──────────────┘                    └──────────────┘
```

Service A uses:

```text
http://service-b:8000
```

for direct communication.

---

## Consul Connect Architecture

When using Consul Connect, Service A sends its request to its local Envoy sidecar.

```text
                              Consul
                         ┌─────────────┐
                         │   Server    │
                         │   :8500     │
                         │   :8502     │
                         └──────┬──────┘
                                │
                       Service Discovery
                                │
                                ▼

┌────────────┐       ┌────────────┐       ┌────────────┐       ┌────────────┐
│            │       │            │       │            │       │            │
│ Service A  │──────►│  Envoy A   │──────►│  Envoy B   │──────►│ Service B  │
│ :8000      │       │ :9000      │       │ :21000     │       │ :8000      │
│            │       │            │       │            │       │            │
└────────────┘       └────────────┘       └────────────┘       └────────────┘
```

Consul acts as the control plane for service discovery and Envoy configuration.

The Envoy proxies handle the service-to-service data-plane traffic.

---

## Components

### Service A

Service A is a lightweight Python HTTP service.

It exposes:

```text
Port: 8000
```

The Docker host maps this to:

```text
localhost:8001
```

Service A supports two request paths:

```text
/
```

and:

```text
/connect
```

The root endpoint uses direct communication with Service B.

The `/connect` endpoint uses the local Envoy listener.

### Service B

Service B is a lightweight Python HTTP service that returns a JSON response.

It exposes:

```text
Port: 8000
```

The Docker host maps this to:

```text
localhost:8002
```

Example response:

```json
{
  "service": "service-b",
  "message": "Hello from Service B",
  "timestamp": 1234567890
}
```

---

## Consul

The project uses:

```text
HashiCorp Consul 1.21
```

Consul is configured as a single-server development/test environment.

Consul provides:

* Service registration
* Service discovery
* Connect control plane
* Envoy configuration through xDS
* Service health information

The Consul HTTP API is exposed on:

```text
localhost:8500
```

The Consul gRPC port used for Envoy configuration is:

```text
8502
```

The Consul UI can be accessed through:

```text
http://localhost:8500
```

---

## Envoy

Envoy is used as the Consul Connect data-plane proxy.

The project uses:

```text
envoyproxy/envoy:v1.36-latest
```

Each application service has its own Envoy sidecar.

### Service A Envoy

Service A's Envoy provides the local upstream listener:

```text
127.0.0.1:9000
```

Requests sent to this port are routed to Service B through the Connect mesh.

It also exposes the Service A Connect listener:

```text
172.21.0.4:21001
```

### Service B Envoy

Service B's Envoy provides the Connect listener:

```text
172.21.0.3:21000
```

This listener receives traffic destined for Service B through the service mesh.

### Envoy Admin Interface

The Envoy admin interface is available internally at:

```text
127.0.0.1:19000
```

It can be used to inspect:

* Listeners
* Clusters
* Request counters
* Connection status
* Health information

---

## Directory Structure

```text
consul-connect-performance/
│
├── README.md
├── PERFORMANCE.md
│
├── docker-compose.yml
│
├── baseline.txt
├── baseline-direct.txt
├── baseline-direct-c10.txt
├── connect.txt
├── connect-c10.txt
├── direct-load.txt
└── connect-load.txt
│
├── service-a/
│   ├── Dockerfile
│   └── app.py
│
├── service-b/
│   ├── Dockerfile
│   └── app.py
│
└── consul/
    ├── config.json
    ├── docker-compose.consul.yml
    │
    └── services/
        ├── service-a.json
        ├── service-a-bootstrap.json
        ├── service-b.json
        └── service-b-bootstrap.json
```

---

## Docker Network

The application containers communicate over a shared Docker network:

```text
consul-connect-performance_default
```

The network allows:

* Service A to reach Service B
* Consul to reach the application containers
* Envoy sidecars to communicate with Consul
* Envoy proxies to communicate with each other

---

## Service Registration

### Service B

Service B is registered with Consul as:

```text
Name:    service-b
Address: 172.21.0.3
Port:    8000
```

Its registration includes a Connect sidecar configuration.

The Service B sidecar is therefore registered with Consul as a Connect proxy.

### Service A

Service A is registered as:

```text
Name:    service-a
Address: 172.21.0.4
Port:    8000
```

Its Connect configuration defines an upstream dependency on:

```text
service-b
```

The upstream is exposed locally to Service A at:

```text
127.0.0.1:9000
```

This means Service A does not need to directly connect to Service B when using the Connect path.

Instead:

```text
Service A
    │
    ▼
127.0.0.1:9000
    │
    ▼
Envoy A
    │
    ▼
Consul Connect
    │
    ▼
Envoy B
    │
    ▼
Service B
```

---

## Bootstrap Configuration

The Envoy bootstrap files were generated using the Consul CLI:

```bash
consul connect envoy
```

The generated configurations were adapted for the Docker environment.

The Envoy configuration uses Consul's gRPC interface:

```text
consul-server:8502
```

The local Consul agent cluster was configured to use DNS discovery so that the Envoy sidecars could resolve:

```text
consul-server
```

---

## Starting the Project

### 1. Start the application services

From the project directory:

```bash
docker compose up -d --build
```

Verify:

```bash
docker ps
```

You should see:

```text
consul-perf-service-a
consul-perf-service-b
```

### 2. Start Consul

Start the Consul server:

```bash
cd consul
docker compose -f docker-compose.consul.yml up -d
```

Verify:

```bash
docker ps
```

Consul should be running as:

```text
consul-server
```

### 3. Verify Consul

Check the leader:

```bash
curl http://localhost:8500/v1/status/leader
```

A valid leader address should be returned.

Check registered services:

```bash
curl http://localhost:8500/v1/catalog/services
```

---

## Validating Service B

Test Service B directly:

```bash
curl http://localhost:8002/
```

Expected response:

```json
{
  "service": "service-b",
  "message": "Hello from Service B"
}
```

---

## Validating Direct Service Communication

Test Service A's direct endpoint:

```bash
curl http://localhost:8001/
```

The request follows:

```text
Service A → Service B
```

Service A should return the response received from Service B.

---

## Validating Consul Connect

Test Service A's Connect endpoint:

```bash
curl http://localhost:8001/connect
```

The request follows:

```text
Service A
    ↓
Envoy A
    ↓
Envoy B
    ↓
Service B
```

A successful response from Service B confirms that the Connect path is operational.

---

## Checking Envoy

Check the Service A Envoy listeners:

```bash
docker exec consul-perf-service-a \
  python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:19000/listeners').read().decode())"
```

The Connect upstream listener should include:

```text
127.0.0.1:9000
```

Check the Service B cluster from Service A's Envoy:

```bash
docker exec consul-perf-service-a \
  python3 -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:19000/clusters').read().decode())" \
  | grep service-b
```

This allows the Service A proxy to be verified as having discovered Service B.

---

## Checking Container Resources

Docker resource usage can be inspected with:

```bash
docker stats
```

Or for the project containers:

```bash
docker stats --no-stream \
  --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}' \
  consul-perf-service-a \
  consul-perf-service-a-proxy \
  consul-perf-service-b \
  consul-perf-service-b-proxy
```

---

## Performance Testing

ApacheBench is used for performance testing.

Install it on Ubuntu if required:

```bash
sudo apt update
sudo apt install -y apache2-utils
```

### Direct Test

```bash
ab -n 10000 -c 10 -l http://localhost:8001/
```

### Consul Connect Test

```bash
ab -n 10000 -c 10 -l http://localhost:8001/connect
```

The detailed benchmark results are documented separately in:

```text
PERFORMANCE.md
```

---

## Why Use Consul Connect?

Consul Connect introduces an additional proxy layer between services, but it provides service-mesh capabilities that direct communication does not provide by itself.

These include:

* Service discovery
* Service identity
* Secure service-to-service communication
* Traffic control
* Service health information
* Proxy-based communication
* Centralized service-mesh configuration
* Integration with Envoy observability and traffic-management features

The purpose of this project is not only to measure overhead but also to demonstrate the architecture and operational components required to introduce Consul Connect into a microservices environment.

---

## Project Limitations

This project is intended as a local proof-of-concept and performance experiment.

It does not represent a production Consul deployment.

Production environments would normally require additional considerations such as:

* Multiple Consul servers
* Persistent storage
* TLS configuration
* ACLs
* Failure recovery
* Automated service registration
* Production-grade application servers
* Resource limits
* Monitoring and alerting
* High availability
* Secure secret management

The IP addresses used by the local Docker environment should not be treated as permanent production addresses.

---

## Related Documentation

Performance measurements and analysis are available in:

```text
PERFORMANCE.md
```

The raw ApacheBench outputs are also retained in the repository for reference.

---

## Summary

This project provides a reproducible demonstration of Consul Connect service-mesh communication between two Dockerized microservices.

It demonstrates:

```text
Direct:
Service A → Service B
```

and:

```text
Service Mesh:
Service A → Envoy A → Envoy B → Service B
```

The project then measures the performance characteristics of both approaches to demonstrate the operational overhead introduced by the service mesh.
