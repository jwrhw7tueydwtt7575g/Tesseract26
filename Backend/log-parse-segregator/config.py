"""
Log categorization configuration with regex patterns
"""

# MongoDB Configuration
MONGODB_URI = "mongodb+srv://vivekchaudhari3718:vivekchaudhari3718@cluster1.9qlun5j.mongodb.net/"
MONGODB_DB = "k8s_logs"
MONGODB_COLLECTION = "log_streams"

# Log Categories Configuration - Production Grade Regex Patterns
LOG_CATEGORIES = {
    "HEALTH": {
        "keywords": [
            # Memory & Heap Issues
            r"(?i)(heap|memory|oom|OutOfMemoryError|OOMKilled|memory exhaustion)",
            r"(?i)(GC overhead|Heap memory critical|memory leak|Heap usage|memory pressure)",
            r"(?i)(memory limit|WARN.*memory|memory.*critical)",
            
            # Probes & Health Checks  
            r"(?i)(Liveness probe|Readiness probe|Startup probe|health check.*fail|health check failed)",
            r"(?i)(health.*degraded|probe timeout|probe.*fail|restart.*container)",
            
            # Crashes & Restarts
            r"(?i)(CrashLoopBackOff|BackOff.*Restarting|exit code|application exiting)",
            r"(?i)(Uncaught exception|NullPointerException|fatal|FATAL|shutting down)",
            r"(?i)(java\.lang\.|Exception in|error.*stack)",
            
            # Garbage Collection
            r"(?i)(garbage collection|GC pause|objects freed)",
        ]
    },
    
    "ANOMALY": {
        "keywords": [
            # CPU & Performance Issues
            r"(?i)(CPU usage spike|CPU throttling|cpu.*usage|threshold=)",
            r"(?i)(CPU request|Goroutines|goroutines.*active)",
            
            # Latency & Response Time Issues  
            r"(?i)(Slow request|Slow query|latency=|request_id.*latency)",
            r"(?i)(response.*time.*spike|request latency|latency.*degradation)",
            r"(?i)(\d{4,}ms|took \d{3,}ms|timeout|deadline exceeded)",
            r"(?i)(slow response|high latency|p99|response.*exceeded)",
            
            # Memory Pressure
            r"(?i)(memory pressure|heap pressure|throttling requests)",
            r"(?i)(Heap memory usage at \d{2,}%|heap.*usage.*\d{2,}%)",
            
            # Queue & Connection Pool
            r"(?i)(queue depth|pool exhausted|connection pool|pending_requests)",
            r"(?i)(critical if.*>)",
            
            # General Degradation
            r"(?i)(degraded|pressure.*rising|growth rate|miss rate spike|eviction triggered)",
        ]
    },
    
    "SERVICE": {
        "keywords": [
            # HTTP Error Codes (4xx, 5xx)
            r"(\s400\s|\s404\s|\s500\s|\s502\s|\s503\s|\s504\s|\s507\s)",
            r"(?i)(Bad Request|Not Found|Service Unavailable|Bad Gateway|Gateway Timeout|Internal Server Error)",
            
            # Network & Connection Issues
            r"(?i)(Connection refused|connection timeout|connection reset|reset by peer)",
            r"(?i)(DNS resolution failed|DNS|Network unreachable|network packet loss)",
            r"(?i)(Connecting to.*refused|failed to.*connect)",
            
            # Service Communication
            r"(?i)(Upstream service|upstream.*timeout|Upstream connection|No endpoints available)",
            r"(?i)(circuit breaker.*OPEN|Circuit breaker|downstream.*unavailable)",
            r"(?i)(Request dropped|Dependency.*unavailable|dependency|protocol mismatch)",
            r"(?i)(HTTP 5|Dependency.*DEGRADED|response time \d{4,}ms)",
        ]
    },
    
    "SECURITY": {
        "keywords": [
            # HTTP Auth Codes
            r"(\s401\s|\s403\s)",
            r"(?i)(Unauthorized|Forbidden|unauthorized|forbidden)",
            r"(?i)(Missing Authorization|Authentication failed)",
            r"(?i)(invalid password|invalid credentials)",
            
            # RBAC Issues
            r"(?i)(RBAC|permission denied|cannot|insufficient permissions|Access denied)",
            r"(?i)(cannot list|cannot create|cannot get|cannot delete)",
            r"(?i)(Role binding|ServiceAccount|ServiceAccount.*insufficient)",
            
            # Token & Certificate Issues
            r"(?i)(JWT|token.*validation|token.*signature|certificate)",
            r"(?i)(SSL|TLS|SSL.*handshake|TLS.*handshake)",
            r"(?i)(certificate.*expired|CA certificate|signature mismatch)",
            
            # Other Security
            r"(?i)(failed login|Session expired|API key|revoked or expired)",
            r"(?i)(attempted to.*denied|suspicious)",
        ]
    },
}

# Ignored patterns - routine logs that don't indicate issues
IGNORED_PATTERNS = [
    r"( 200 | 201 | 204 )",
    r"(?i)( OK | Created | No Content)",
    r"(?i)(Health check endpoint listening)",
    r"(?i)(Dependency check.*OK)",
    r"(?i)(Starting application|Loading configuration|Initialized|Connected)",
    r"(?i)(Configuration loaded|Configuration file)",
    r"(?i)(Readiness probe.*200|Liveness probe.*200|Startup probe.*200)",
    r"(?i)(Cache HIT|Database query execution|Transaction COMMIT)",
    r"(?i)(RBAC.*success|Role binding created|attempting to bind.*success)",
    r"(?i)(External API call to.*took)",
    r"(?i)(Metrics exported)",
]
