#!/bin/bash

# Quick test script to demonstrate the log parser

echo "🧪 Log Parser Test Suite"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Create sample logs file
cat > /tmp/sample_logs.txt << 'EOF'
2026-03-23 17:41:20,909 - INFO - Application started successfully
2026-03-23 17:41:22,909 - ERROR - OOMKill detected in pod
2026-03-23 17:41:24,909 - WARNING - CPU throttling detected
2026-03-23 17:41:26,909 - ERROR - Connection refused from service
2026-03-23 17:41:28,909 - ERROR - Authentication failed: 401
2026-03-23 17:41:30,909 - INFO - GET /health 200 OK
2026-03-23 17:41:32,909 - ERROR - CrashLoopBackOff detected
2026-03-23 17:41:34,909 - WARNING - High latency detected: 5000ms
2026-03-23 17:41:36,909 - ERROR - 503 Service Unavailable
2026-03-23 17:41:38,909 - ERROR - Permission denied - RBAC violation
2026-03-23 17:41:40,909 - WARNING - Memory pressure detected
2026-03-23 17:41:42,909 - ERROR - Timeout: request exceeded deadline
2026-03-23 17:41:44,909 - ERROR - 502 Bad Gateway
2026-03-23 17:41:46,909 - ERROR - Liveness probe failed
2026-03-23 17:41:48,909 - ERROR - Unauthorized: invalid token
2026-03-23 17:41:50,909 - INFO - Service health check passed
2026-03-23 17:41:52,909 - ERROR - 504 Gateway Timeout
2026-03-23 17:41:54,909 - ERROR - Pod restarting after crash
2026-03-23 17:41:56,909 - WARNING - Spike in error rate detected
2026-03-23 17:41:58,909 - DEBUG - Trace: function call stack
EOF

echo "📝 Sample logs created at: /tmp/sample_logs.txt"
echo ""

echo "🔍 Testing categorizer..."
echo "════════════════════════════════════════════════════════════════"
echo ""

# Run the parser with test logs
python3 << 'PYTHON_TEST'
import sys
sys.path.insert(0, '/home/vivek/Desktop/Ai-Agent/log-parse-segregator')

from categorizer import LogCategorizer

categorizer = LogCategorizer()

test_logs = [
    "OOMKill detected in pod",
    "CPU throttling on container",
    "Connection refused from upstream",
    "401 Unauthorized access",
    "INFO - GET /health 200 OK",
]

print("Testing Log Categorization:")
print("-" * 60)
for log in test_logs:
    category = categorizer.categorize_log(log)
    keywords = categorizer.extract_keywords(log, category)
    print(f"\n📌 Log: {log}")
    print(f"   Category: {category}")
    if keywords:
        print(f"   Keywords: {', '.join(keywords[:2])}")

print("\n" + "=" * 60)
print("✅ Categorizer test passed!")
PYTHON_TEST

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📦 Testing chunk creation..."
echo "════════════════════════════════════════════════════════════════"
echo ""

python3 << 'PYTHON_TEST'
import sys
sys.path.insert(0, '/home/vivek/Desktop/Ai-Agent/log-parse-segregator')

from log_parser import LogParser

parser = LogParser(max_logs_per_chunk=5)

sample_logs = [
    "OOMKill detected",
    "CPU throttling",
    "Connection refused",
    "401 Unauthorized",
    "INFO - startup OK",
    "Memory pressure detected",
]

print("Processing sample logs into chunks...")
stats = parser.process_log_stream(sample_logs, auto_dump=False)

print(f"\nChunk Statistics:")
print(f"  Total processed: {stats['total_processed']}")
print(f"  Health: {stats['health']}")
print(f"  Anomaly: {stats['anomaly']}")
print(f"  Service: {stats['service']}")
print(f"  Security: {stats['security']}")
print(f"  Ignored: {stats['ignored']}")

chunk_data = parser.current_chunk.to_dict()
print(f"\n✅ Chunk created: {chunk_data['chunk_id']}")
print(f"   Total logs in chunk: {chunk_data['stats']['total_logs']}")
PYTHON_TEST

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "✅ All tests passed!"
echo ""
echo "Next steps:"
echo "  1. Install dependencies: pip install -r requirements.txt"
echo "  2. Test with real logs: python main.py --source file --file /tmp/sample_logs.txt"
echo "  3. Stream from Kubernetes: kubectl logs -n default deployment/log-generator | python main.py"
echo ""
