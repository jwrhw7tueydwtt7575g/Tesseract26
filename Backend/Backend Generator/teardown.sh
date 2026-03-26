#!/bin/bash

echo "🗑️  Tearing down Kubernetes Monitoring Stack..."
echo ""

# Kill all port-forward processes
echo "Stopping port-forwards..."
pkill -f "kubectl port-forward" 2>/dev/null
sleep 2

# Uninstall Helm releases
echo "Uninstalling Helm releases..."
helm uninstall prometheus -n prometheus 2>/dev/null || true
helm uninstall grafana -n grafana 2>/dev/null || true
helm uninstall loki -n loki 2>/dev/null || true

# Delete namespaces (this deletes all resources in those namespaces)
echo "Deleting Kubernetes namespaces..."
kubectl delete namespace prometheus grafana loki 2>/dev/null || true

# Delete log generator from default namespace
echo "Deleting log generator..."
kubectl delete deployment log-generator -n default 2>/dev/null || true
kubectl delete configmap log-generator-config -n default 2>/dev/null || true

# Wait for cleanup
sleep 5

echo ""
echo "✅ Teardown complete!"
echo ""
echo "Remaining resources:"
kubectl get all -A | grep -v kube-system | grep -v kube-public | grep -v kube-node-lease
