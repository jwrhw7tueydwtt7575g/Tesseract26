#!/bin/bash

# Kubernetes Monitoring Stack - Access Helper Script

echo "=== Kubernetes Monitoring Stack Access Guide ==="
echo ""

# Get Grafana info
echo "Grafana:"
echo "--------"
GRAFANA_POD=$(kubectl get pods -n grafana -o name | head -1 | cut -d'/' -f2)
if [ ! -z "$GRAFANA_POD" ]; then
    echo "Pod: $GRAFANA_POD"
    GRAFANA_STATUS=$(kubectl get pod $GRAFANA_POD -n grafana -o jsonpath='{.status.phase}')
    echo "Status: $GRAFANA_STATUS"
    if [ "$GRAFANA_STATUS" == "Running" ]; then
        echo ""
        echo "To access Grafana:"
        echo "  kubectl port-forward -n grafana svc/grafana 3000:80"
        echo "  Open: http://localhost:3000"
        echo "  Username: admin"
        echo "  Password: admin123"
    else
        echo "Note: Grafana pod is not running yet. Status: $GRAFANA_STATUS"
    fi
fi
echo ""

# Get Prometheus info
echo "Prometheus:"
echo "-----------"
PROM_POD=$(kubectl get pods -n prometheus -l app.kubernetes.io/name=prometheus -l app.kubernetes.io/instance=prometheus-server -o name | head -1 | cut -d'/' -f2)
if [ ! -z "$PROM_POD" ]; then
    echo "Pod: $PROM_POD"
    PROM_STATUS=$(kubectl get pod $PROM_POD -n prometheus -o jsonpath='{.status.phase}')
    echo "Status: $PROM_STATUS"
    if [ "$PROM_STATUS" == "Running" ]; then
        echo ""
        echo "To access Prometheus:"
        echo "  kubectl port-forward -n prometheus svc/prometheus-server 9090:80"
        echo "  Open: http://localhost:9090"
    else
        echo "Note: Prometheus pod is not running yet. Status: $PROM_STATUS"
    fi
fi
echo ""

# Get Loki info
echo "Loki:"
echo "----"
LOKI_POD=$(kubectl get pods -n loki -l app=loki -o name | head -1 | cut -d'/' -f2)
if [ ! -z "$LOKI_POD" ]; then
    echo "Pod: $LOKI_POD"
    LOKI_STATUS=$(kubectl get pod $LOKI_POD -n loki -o jsonpath='{.status.phase}')
    echo "Status: $LOKI_STATUS"
    echo "Service URL (for Grafana datasource): http://loki.loki.svc.cluster.local:3100"
else
    echo "No Loki pod found"
fi
echo ""

# Get Log Generator info
echo "Log Generator:"
echo "--------------"
LOG_GEN_POD=$(kubectl get pods -n default -l app=log-generator -o name | head -1 | cut -d'/' -f2)
if [ ! -z "$LOG_GEN_POD" ]; then
    echo "Pod: $LOG_GEN_POD"
    LOG_GEN_STATUS=$(kubectl get pod $LOG_GEN_POD -n default -o jsonpath='{.status.phase}')
    echo "Status: $LOG_GEN_STATUS"
    if [ "$LOG_GEN_STATUS" == "Running" ]; then
        echo ""
        echo "To view logs:"
        echo "  kubectl logs -n default -l app=log-generator -f"
    fi
else
    echo "No log generator pod found"
fi
echo ""

echo "=== All Pods Status ==="
kubectl get pods -A | grep -E "(grafana|prometheus|loki|log-generator)" || kubectl get pods -A
