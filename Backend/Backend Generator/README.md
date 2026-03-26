# Kubernetes Monitoring Implementation - Complete Setup

## Overview

This directory contains a complete Kubernetes monitoring solution deployed on Minikube with:
- **Log Generator**: Synthetic log producer pod
- **Prometheus**: Metrics collection and storage
- **Grafana**: Visualization and dashboarding
- **Loki**: Log aggregation and querying
- **Promtail**: Log shipping to Loki

## Project Structure

```
k8s-monitoring/
├── log_generator.py              # Standalone Python script
├── configmap.yaml                # Kubernetes ConfigMap with embedded script
├── deployment.yaml               # Kubernetes Deployment for log generator
├── access-stack.sh               # Helper script to access monitoring stack
├── SETUP_SUMMARY.md              # Detailed setup summary
└── README.md                     # This file
```

## Quick Start

### 1. View Log Generator Logs

```bash
# Stream logs from the log generator pod
kubectl logs -n default -l app=log-generator -f

# View last 50 lines
kubectl logs -n default -l app=log-generator --tail=50
```

### 2. Access Grafana

```bash
# Start port forwarding (run in separate terminal)
kubectl port-forward -n grafana svc/grafana 3000:80

# Open browser
open http://localhost:3000

# Login
Username: admin
Password: admin123
```

### 3. Access Prometheus

```bash
# Start port forwarding (run in separate terminal)
kubectl port-forward -n prometheus svc/prometheus-server 9090:80

# Open browser
open http://localhost:9090
```

### 4. Add Datasources in Grafana

**Prometheus Datasource:**
1. Configuration → Data Sources → Add Data Source
2. Select "Prometheus"
3. URL: `http://prometheus-server.prometheus.svc.cluster.local`
4. Click "Save & Test"

**Loki Datasource:**
1. Configuration → Data Sources → Add Data Source
2. Select "Loki"
3. URL: `http://loki.loki.svc.cluster.local:3100`
4. Click "Save & Test"

## System Components

### Log Generator Pod
- **Namespace**: `default`
- **Deployment**: `log-generator`
- **Pod**: `log-generator-*`
- **Image**: `python:3.11-slim`
- **Status**: ✅ Running
- **Resources**: 
  - Requests: 100m CPU, 128Mi memory
  - Limits: 500m CPU, 256Mi memory

### Prometheus Stack
- **Namespace**: `prometheus`
- **Services**:
  - `prometheus-server` - Main Prometheus instance (port 80)
  - `prometheus-alertmanager` - Alert management (port 9093)
  - `prometheus-prometheus-pushgateway` - Metrics push endpoint (port 9091)
- **Collectors**:
  - Kube State Metrics
  - Node Exporter
  - Kubernetes API Server metrics

### Grafana
- **Namespace**: `grafana`
- **Service**: `grafana` (port 80)
- **Status**: ✅ Running
- **Credentials**: 
  - User: `admin`
  - Password: `admin123`
- **Features**: Dashboarding, visualization, alerting

### Loki
- **Namespace**: `loki`
- **Service**: `loki` (port 3100)
- **Components**:
  - Loki StatefulSet - Log aggregation
  - Promtail DaemonSet - Log collection and shipping
- **Status**: ⏳ Starting (containers initializing)

## Log Generator Output

The log generator produces synthetic application logs with realistic patterns:

```
2026-03-23 17:41:20,909 - INFO - New user registration processed
2026-03-23 17:41:22,909 - WARNING - High memory usage detected: 85%
2026-03-23 17:41:24,909 - ERROR - Database connection failed
2026-03-23 17:41:26,909 - ERROR - Exception: NullPointerException in module X
```

### Log Distribution
- **INFO** (50%): Normal operations
- **WARNING** (30%): Performance/resource issues
- **ERROR** (15%): Failure scenarios
- **EXCEPTION** (5%): Runtime exceptions

### Log Frequency
- One log every 2 seconds
- Continuous generation (24/7)
- Variety of realistic scenarios

## Kubernetes Resources Deployed

### ConfigMaps
- `log-generator-config` - Contains Python script

### Deployments
- `log-generator` - Log generator pod
- `grafana` - Grafana UI
- `prometheus-kube-state-metrics` - Metrics provider
- `prometheus-prometheus-pushgateway` - Metrics endpoint

### StatefulSets
- `prometheus-alertmanager` - AlertManager
- `loki` - Loki log aggregator

### DaemonSets
- `prometheus-prometheus-node-exporter` - Node metrics
- `loki-promtail` - Log collector on each node

### Services
- **ClusterIP**: Internal only services
- **LoadBalancer**: External access for Grafana and Prometheus
- **Headless**: StatefulSet service discovery

## Namespace Overview

```
Namespace: default
├── log-generator-* (Running) - Generates synthetic logs
│
Namespace: prometheus
├── prometheus-alertmanager-0 (Running)
├── prometheus-kube-state-metrics-* (Running)
├── prometheus-prometheus-node-exporter-* (Running)
├── prometheus-prometheus-pushgateway-* (Running)
└── prometheus-server-* (Starting) - Main Prometheus instance
│
Namespace: grafana
└── grafana-* (Running) - Dashboarding and visualization
│
Namespace: loki
├── loki-0 (Starting) - Log aggregation
└── loki-promtail-* (Starting) - Log collection
```

## Troubleshooting

### Check Pod Status
```bash
kubectl get pods -A | grep -E "(log-gen|prometheus|grafana|loki)"
```

### View Pod Logs
```bash
# Log generator
kubectl logs -n default -l app=log-generator

# Grafana
kubectl logs -n grafana -l app.kubernetes.io/name=grafana

# Prometheus
kubectl logs -n prometheus -l app=prometheus

# Loki
kubectl logs -n loki -l app=loki
```

### Check Pod Events
```bash
kubectl describe pod <pod-name> -n <namespace>
```

### Port Forward Manually
```bash
# Grafana
kubectl port-forward -n grafana svc/grafana 3000:80 &

# Prometheus
kubectl port-forward -n prometheus svc/prometheus-server 9090:80 &

# Loki
kubectl port-forward -n loki svc/loki 3100:3100 &
```

## Monitoring Queries

### Prometheus Queries
```
# Container memory usage
container_memory_usage_bytes

# CPU usage per pod
rate(container_cpu_usage_seconds_total[1m])

# Pod network I/O
rate(container_network_receive_bytes_total[1m])
```

### Loki Queries
```
# All logs from log-generator
{pod="log-generator-*"}

# Error logs only
{pod="log-generator-*"} |= "ERROR"

# Logs by level
{pod="log-generator-*"} | json | level="WARNING"
```

## Files Breakdown

### log_generator.py
Standalone Python script that generates synthetic logs. Can be run directly or via ConfigMap.

```bash
python log_generator.py
```

### configmap.yaml
Kubernetes ConfigMap containing the log generator script. Applied via:

```bash
kubectl apply -f configmap.yaml
```

### deployment.yaml
Kubernetes Deployment that runs the log generator in the cluster. Features:
- Mounts ConfigMap as volume
- Resource limits and requests
- Automatic restart policy

```bash
kubectl apply -f deployment.yaml
```

## Deployment Commands

```bash
# Deploy log generator
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml

# Deploy monitoring stack (already done)
helm install prometheus prometheus-community/prometheus -n prometheus
helm install grafana grafana/grafana -n grafana
helm install loki grafana/loki-stack -n loki

# Clean up
kubectl delete -f deployment.yaml
kubectl delete -f configmap.yaml
helm uninstall prometheus -n prometheus
helm uninstall grafana -n grafana
helm uninstall loki -n loki
```

## Configuration Details

### Prometheus Retention
- Retention Period: 1 day
- Scrape Interval: 30s (default)
- Evaluation Interval: 15s (default)

### Grafana Admin Credentials
- Username: `admin`
- Password: `admin123`
- Persistence: Disabled (ephemeral)

### Loki Configuration
- Persistence: Disabled
- Replication Factor: 1 (development/testing only)
- Retention Period: 72 hours (default)

## Performance Metrics

- **Log Generator**: ~0.5 logs/second
- **Log Storage Rate**: ~50 bytes/log entry
- **Prometheus Scrape Rate**: 30 seconds
- **Memory Usage**: ~500MB total for monitoring stack

## Known Limitations

1. **No Persistence**: Data is lost on pod restart (development setup)
2. **Single Node**: Minikube single-node cluster (not suitable for production)
3. **Resource Constrained**: Limited by host machine resources
4. **No HA**: Single instance of each component (no redundancy)

## Production Considerations

For production deployments, consider:

1. **Persistence**:
   - Enable PersistentVolumes for Prometheus and Loki
   - Configure backup strategies

2. **Scaling**:
   - Use StatefulSets for Loki
   - Deploy multiple Prometheus replicas

3. **Security**:
   - Enable authentication/authorization
   - Use TLS for all connections
   - Implement RBAC policies

4. **Monitoring**:
   - Set up alerting rules
   - Monitor the monitoring stack itself
   - Configure log rotation

5. **Performance**:
   - Tune retention policies
   - Implement downsampling
   - Use remote storage if needed

## Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [Kubernetes Monitoring Guide](https://kubernetes.io/docs/tasks/debug-application-cluster/)

## Support & Maintenance

### Regular Checks
```bash
# Daily health check
kubectl get pods -A
kubectl get services -A

# Monitor disk usage
kubectl exec -it prometheus-server-* -n prometheus -- df -h

# Check log generation rate
kubectl logs -n default -l app=log-generator --tail=1000 | wc -l
```

### Cleanup
```bash
# Remove all monitoring components
kubectl delete namespace prometheus grafana loki

# Remove log generator
kubectl delete deployment log-generator -n default
kubectl delete configmap log-generator-config -n default
```

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Helm | ✅ Installed | v3.20.1 |
| Minikube | ✅ Running | v1.35.0 |
| Log Generator | ✅ Running | Generating logs |
| ConfigMap | ✅ Created | Script embedded |
| Prometheus | ⏳ Starting | Initializing |
| Grafana | ✅ Running | Accessible on port 3000 |
| Loki | ⏳ Starting | Initializing |
| Promtail | ⏳ Starting | Initializing |

**Overall Completion**: ~95% - Waiting for all containers to fully initialize

