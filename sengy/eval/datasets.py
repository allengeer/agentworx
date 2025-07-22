"""
Evaluation datasets for Sengy - tailored for software engineers and engineering managers.
These datasets test the agent's ability to analyze Jira tickets from an engineering perspective.
"""

# Engineering-focused Jira tickets for evaluation
ENGINEERING_JIRA_TICKETS = [
    {
        "key": "PROJ-123",
        "summary": "Critical API performance degradation in user authentication service",
        "description": "Users experiencing 5-10 second login delays. Database query optimization needed for auth lookup table. Affects 50K+ daily active users.",
        "priority": "Critical",
        "status": "In Progress",
        "assignee": "senior-backend-dev",
        "created": "2024-01-15",
        "labels": ["performance", "backend", "database"],
        "components": ["auth-service", "user-management"],
        "comments": [
            {"author": "tech-lead", "body": "Profiling shows N+1 query pattern in UserAuth.findByToken(). Need to add proper indexing and eager loading."},
            {"author": "dba", "body": "Confirmed missing composite index on auth_tokens(user_id, token_hash, expires_at). Will create migration."},
            {"author": "senior-backend-dev", "body": "Working on query optimization. ETA 2 days for fix + testing."}
        ]
    },
    {
        "key": "PROJ-124", 
        "summary": "Implement circuit breaker pattern for external payment gateway",
        "description": "Payment service failing when external gateway is down. Need resilience patterns to handle failures gracefully and provide better user experience.",
        "priority": "High",
        "status": "To Do",
        "assignee": "backend-architect",
        "created": "2024-01-16",
        "labels": ["architecture", "resilience", "payments"],
        "components": ["payment-service", "external-integrations"],
        "comments": [
            {"author": "product-manager", "body": "Business impact: $50K/hour in lost revenue when payment gateway is down."},
            {"author": "backend-architect", "body": "Proposing Hystrix or resilience4j for circuit breaker implementation. Will include fallback to secondary processor."}
        ]
    },
    {
        "key": "PROJ-125",
        "summary": "Tech debt: Refactor legacy monolith user service to microservices",
        "description": "User service has grown to 500K+ lines of code. Breaking into separate services: user-profile, user-auth, user-preferences, user-notifications.",
        "priority": "Medium",
        "status": "In Planning",
        "assignee": "engineering-manager",
        "created": "2024-01-10",
        "labels": ["tech-debt", "architecture", "microservices"],
        "components": ["user-service", "platform"],
        "comments": [
            {"author": "cto", "body": "Priority initiative for Q2. Need detailed migration plan with zero-downtime strategy."},
            {"author": "senior-architect", "body": "Recommend strangler fig pattern. Start with extracting user-notifications service first - lowest risk."},
            {"author": "engineering-manager", "body": "Resource allocation: 3 senior devs for 6 months. Need to balance with feature delivery."}
        ]
    },
    {
        "key": "PROJ-126",
        "summary": "Security vulnerability: SQL injection in reporting module",
        "description": "Security audit found SQL injection vulnerability in custom report builder. CVSS score 8.5. Requires immediate patching.",
        "priority": "Critical",
        "status": "In Progress",
        "assignee": "security-team-lead",
        "created": "2024-01-17",
        "labels": ["security", "vulnerability", "sql-injection"],
        "components": ["reporting", "analytics"],
        "comments": [
            {"author": "security-auditor", "body": "Vulnerability allows arbitrary SQL execution through report_filter parameter. Affects enterprise customers."},
            {"author": "security-team-lead", "body": "Implementing parameterized queries and input validation. Hotfix ready for testing."},
            {"author": "devops-lead", "body": "Emergency deployment pipeline ready. Can push to production within 2 hours of approval."}
        ]
    },
    {
        "key": "PROJ-127",
        "summary": "Infrastructure scaling: Auto-scaling group configuration for Black Friday",
        "description": "Expected 10x traffic increase during Black Friday. Need to configure auto-scaling, load balancing, and database read replicas.",
        "priority": "High", 
        "status": "In Progress",
        "assignee": "devops-engineer",
        "created": "2024-01-12",
        "labels": ["infrastructure", "scaling", "load-testing"],
        "components": ["aws-infrastructure", "load-balancers"],
        "comments": [
            {"author": "site-reliability-engineer", "body": "Load testing shows current setup handles 2x traffic. Need horizontal scaling for API servers and database optimization."},
            {"author": "devops-engineer", "body": "Configuring ASG to scale from 10 to 100 instances. Adding 3 read replicas and CDN optimization."},
            {"author": "engineering-manager", "body": "War room scheduled for Black Friday weekend. All senior engineers on standby."}
        ]
    }
]

# Evaluation scenarios for engineering managers
ENGINEERING_MANAGER_SCENARIOS = [
    {
        "scenario": "Sprint Planning Analysis",
        "tickets": ENGINEERING_JIRA_TICKETS[:3],
        "query": "Analyze these tickets for sprint planning. What are the risks, dependencies, and resource requirements?",
        "expected_insights": [
            "Critical API performance issue should be top priority",
            "Circuit breaker implementation depends on payment team availability", 
            "Microservices refactoring is long-term effort requiring dedicated team",
            "Database optimization skills needed for performance issue",
            "Architecture planning required for both payment and user service work"
        ]
    },
    {
        "scenario": "Technical Debt Assessment",
        "tickets": [ENGINEERING_JIRA_TICKETS[2]],  # Microservices refactoring
        "query": "Evaluate this technical debt item. What's the business impact and recommended approach?",
        "expected_insights": [
            "500K+ lines indicates significant technical debt",
            "Strangler fig pattern is appropriate migration strategy",
            "6-month timeline with 3 senior developers is reasonable",
            "Risk of feature delivery impact needs mitigation",
            "Starting with user-notifications service minimizes risk"
        ]
    },
    {
        "scenario": "Incident Response Priority",
        "tickets": [ENGINEERING_JIRA_TICKETS[0], ENGINEERING_JIRA_TICKETS[3]],  # Performance + Security
        "query": "These are both critical issues. How should we prioritize and allocate resources?",
        "expected_insights": [
            "Security vulnerability (CVSS 8.5) takes immediate priority",
            "SQL injection affects enterprise customers - business critical",
            "Performance issue affects user experience but not security",
            "Parallel workstreams possible with different teams",
            "Security hotfix can be deployed quickly"
        ]
    }
]

# Evaluation scenarios for software engineers  
SOFTWARE_ENGINEER_SCENARIOS = [
    {
        "scenario": "Technical Solution Analysis",
        "tickets": [ENGINEERING_JIRA_TICKETS[1]],  # Circuit breaker
        "query": "What technical approaches should be considered for implementing this circuit breaker pattern?",
        "expected_insights": [
            "Hystrix or resilience4j are good circuit breaker libraries",
            "Need fallback mechanism to secondary payment processor",
            "Consider timeout configuration and failure thresholds",
            "Monitoring and alerting for circuit breaker state changes",
            "Testing strategy for simulating payment gateway failures"
        ]
    },
    {
        "scenario": "Performance Debugging",
        "tickets": [ENGINEERING_JIRA_TICKETS[0]],  # API performance
        "query": "What's causing the performance issue and how should it be fixed?",
        "expected_insights": [
            "N+1 query pattern in UserAuth.findByToken() method",
            "Missing composite index on auth_tokens table",
            "Need database migration for index creation",
            "Eager loading should be implemented for related data",
            "Query optimization will reduce 5-10 second delays"
        ]
    },
    {
        "scenario": "Security Issue Analysis", 
        "tickets": [ENGINEERING_JIRA_TICKETS[3]],  # SQL injection
        "query": "Analyze this security vulnerability. What are the technical details and fix approach?",
        "expected_insights": [
            "SQL injection in report_filter parameter",
            "CVSS score 8.5 indicates high severity",
            "Parameterized queries needed to prevent injection", 
            "Input validation and sanitization required",
            "Affects enterprise customers with custom reporting"
        ]
    }
]

# Expected evaluation metrics
EVALUATION_DIMENSIONS = [
    "technical_accuracy",      # How technically correct are the insights?
    "engineering_relevance",   # Are insights relevant to engineering teams?
    "actionability",          # Are recommendations actionable?
    "priority_assessment",    # Does it correctly assess priorities?
    "risk_identification",    # Does it identify technical and business risks?
    "solution_completeness",  # Are technical solutions comprehensive?
    "manager_perspective",    # Does it consider management concerns?
    "developer_perspective"   # Does it consider developer concerns?
]