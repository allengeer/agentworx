"""
GitHub evaluation datasets for Sengy - tailored for software development and engineering workflows.
These datasets test the agent's ability to analyze GitHub repositories, commits, and pull requests.
"""

# GitHub repositories and commit data for evaluation
GITHUB_REPOSITORIES_DATA = [
    {
        "repo": "acme-corp/payment-service",
        "commits": [
            {
                "sha": "a1b2c3d4e5f6",
                "message": "Fix critical memory leak in payment processing\n\nResolved issue where webhook handlers weren't properly releasing connections to Redis. Added connection pooling and proper cleanup in error cases.",
                "author": {"name": "Sarah Chen", "login": "sarahc", "email": "sarah@acme.com"},
                "date": "2024-01-20T14:30:00Z",
                "url": "https://github.com/acme-corp/payment-service/commit/a1b2c3d4e5f6",
                "stats": {"additions": 45, "deletions": 12, "total": 57},
                "files": [
                    {"filename": "src/webhooks/payment_handler.py", "status": "modified", "additions": 25, "deletions": 8},
                    {"filename": "src/redis/connection_pool.py", "status": "added", "additions": 20, "deletions": 0},
                    {"filename": "tests/test_payment_handler.py", "status": "modified", "additions": 0, "deletions": 4}
                ]
            },
            {
                "sha": "b2c3d4e5f6g7",
                "message": "Implement circuit breaker for external API calls",
                "author": {"name": "Mike Rodriguez", "login": "mikero", "email": "mike@acme.com"},
                "date": "2024-01-19T11:15:00Z",
                "url": "https://github.com/acme-corp/payment-service/commit/b2c3d4e5f6g7",
                "stats": {"additions": 120, "deletions": 15, "total": 135},
                "files": [
                    {"filename": "src/external/circuit_breaker.py", "status": "added", "additions": 85, "deletions": 0},
                    {"filename": "src/payments/processor.py", "status": "modified", "additions": 35, "deletions": 15}
                ]
            }
        ],
        "pull_requests": [
            {
                "number": 342,
                "title": "Performance optimization: Implement async payment processing",
                "body": "This PR implements asynchronous payment processing to improve throughput by 300%.\n\n**Changes:**\n- Added async/await to payment pipeline\n- Implemented background job queue with Redis\n- Added proper error handling and retry logic\n\n**Performance Impact:**\n- Reduced p95 latency from 2.5s to 800ms\n- Increased throughput from 100 to 400 payments/second\n- Reduced resource usage by 25%\n\n**Testing:**\n- Load tested with 10K concurrent requests\n- Validated error scenarios and retry logic\n- Performance benchmarks included\n\nCloses #234, #189",
                "state": "merged",
                "merged": True,
                "author": {"name": "Alex Kim", "login": "alexk", "email": "alex@acme.com"},
                "created_at": "2024-01-18T09:00:00Z",
                "merged_at": "2024-01-20T16:45:00Z",
                "url": "https://github.com/acme-corp/payment-service/pull/342",
                "head_ref": "feature/async-payments",
                "base_ref": "main",
                "changed_files": 12,
                "additions": 450,
                "deletions": 80,
                "labels": ["performance", "enhancement", "backend"],
                "commits": [
                    {
                        "sha": "c3d4e5f6g7h8",
                        "message": "Add async payment processor",
                        "author": {"name": "Alex Kim"}
                    },
                    {
                        "sha": "d4e5f6g7h8i9",
                        "message": "Implement Redis job queue",
                        "author": {"name": "Alex Kim"}
                    }
                ],
                "reviews": [
                    {
                        "user": "senior-architect",
                        "state": "APPROVED",
                        "body": "Excellent work! The async implementation looks solid. Performance improvements are impressive."
                    },
                    {
                        "user": "security-team",
                        "state": "APPROVED", 
                        "body": "Security review passed. Proper error handling prevents data leaks."
                    }
                ]
            }
        ]
    },
    {
        "repo": "acme-corp/user-service",
        "commits": [
            {
                "sha": "e5f6g7h8i9j0",
                "message": "Security: Fix SQL injection vulnerability in user search\n\nCVE-2024-1234: Parameterized queries now used for all user search operations. Added input validation and escape functions.",
                "author": {"name": "Security Team", "login": "security-bot", "email": "security@acme.com"},
                "date": "2024-01-21T08:45:00Z",
                "url": "https://github.com/acme-corp/user-service/commit/e5f6g7h8i9j0",
                "stats": {"additions": 30, "deletions": 45, "total": 75},
                "files": [
                    {"filename": "src/search/user_search.py", "status": "modified", "additions": 25, "deletions": 40},
                    {"filename": "src/utils/input_validator.py", "status": "added", "additions": 5, "deletions": 0},
                    {"filename": "tests/security/test_sql_injection.py", "status": "added", "additions": 0, "deletions": 5}
                ]
            }
        ],
        "pull_requests": [
            {
                "number": 156,
                "title": "Infrastructure: Migrate to microservices architecture",
                "body": "Breaking down the monolithic user service into smaller, focused microservices.\n\n**Services Created:**\n- user-profile-service: Profile management and preferences\n- user-auth-service: Authentication and authorization\n- user-notification-service: Email/SMS notifications\n\n**Migration Strategy:**\n- Strangler fig pattern for gradual migration\n- Shared database initially, separate later\n- API gateway for routing and load balancing\n\n**Benefits:**\n- Independent deployment and scaling\n- Technology diversity (Go for auth, Python for notifications)\n- Better fault isolation\n- Team autonomy\n\n**Risks:**\n- Increased operational complexity\n- Network latency between services\n- Data consistency challenges\n\nPart of Q2 architecture initiative. Closes #89, #102, #145",
                "state": "open",
                "merged": False,
                "author": {"name": "Engineering Manager", "login": "engmgr", "email": "manager@acme.com"},
                "created_at": "2024-01-15T14:00:00Z",
                "url": "https://github.com/acme-corp/user-service/pull/156",
                "head_ref": "feature/microservices-migration",
                "base_ref": "main", 
                "changed_files": 45,
                "additions": 2500,
                "deletions": 800,
                "labels": ["architecture", "breaking-change", "epic"],
                "commits": [
                    {
                        "sha": "f6g7h8i9j0k1",
                        "message": "Extract user-profile-service",
                        "author": {"name": "Senior Developer"}
                    },
                    {
                        "sha": "g7h8i9j0k1l2", 
                        "message": "Add API gateway configuration",
                        "author": {"name": "DevOps Engineer"}
                    }
                ],
                "reviews": [
                    {
                        "user": "tech-lead",
                        "state": "CHANGES_REQUESTED",
                        "body": "Good direction but need to address data consistency. Suggest implementing saga pattern for distributed transactions."
                    },
                    {
                        "user": "platform-architect",
                        "state": "APPROVED",
                        "body": "Architecture looks solid. API gateway approach is correct. Ready for gradual rollout."
                    }
                ]
            }
        ]
    }
]

# GitHub evaluation scenarios for different engineering roles
GITHUB_ENGINEERING_SCENARIOS = [
    {
        "scenario": "Code Review Analysis",
        "repo_data": GITHUB_REPOSITORIES_DATA[0],
        "query": "Analyze the recent commits and pull request in this payment service repository. What are the key technical improvements and risks?",
        "expected_insights": [
            "Memory leak fix in webhook handlers improves system reliability",
            "Circuit breaker pattern adds resilience to external API failures", 
            "Async payment processing provides significant performance gains",
            "Redis connection pooling prevents resource exhaustion",
            "300% throughput improvement with 400 payments/second capacity",
            "Performance optimization reduces p95 latency from 2.5s to 800ms",
            "Proper error handling and retry logic implemented"
        ]
    },
    {
        "scenario": "Security Vulnerability Assessment", 
        "repo_data": GITHUB_REPOSITORIES_DATA[1],
        "query": "Review the security-related commits and assess the overall security posture of this user service.",
        "expected_insights": [
            "SQL injection vulnerability (CVE-2024-1234) was properly patched",
            "Parameterized queries now prevent injection attacks",
            "Input validation and escaping functions added",
            "Security testing implemented for SQL injection scenarios",
            "User search functionality was the attack vector",
            "Security team automated the fix deployment"
        ]
    },
    {
        "scenario": "Architecture Migration Planning",
        "repo_data": GITHUB_REPOSITORIES_DATA[1], 
        "query": "Evaluate the microservices migration pull request. What are the benefits, risks, and implementation considerations?",
        "expected_insights": [
            "Strangler fig pattern is appropriate for gradual migration",
            "Three focused microservices: profile, auth, and notifications",
            "Independent deployment and scaling capabilities",
            "Technology diversity allows optimal tool selection",
            "Data consistency challenges need saga pattern",
            "Increased operational complexity requires monitoring",
            "API gateway provides centralized routing and load balancing",
            "Network latency between services is a consideration"
        ]
    }
]

# GitHub scenarios for development teams
GITHUB_DEVELOPMENT_SCENARIOS = [
    {
        "scenario": "Performance Optimization Review",
        "repo_data": GITHUB_REPOSITORIES_DATA[0],
        "query": "What performance improvements were made in the payment service? How effective are they?",
        "expected_insights": [
            "Async processing implementation increased throughput by 300%",
            "Redis job queue handles background payment processing",
            "P95 latency reduced from 2.5 seconds to 800 milliseconds",
            "Resource usage decreased by 25% despite higher throughput",
            "Load testing validated 10K concurrent request handling",
            "Circuit breaker prevents cascading failures"
        ]
    },
    {
        "scenario": "Technical Debt Assessment",
        "repo_data": GITHUB_REPOSITORIES_DATA[1],
        "query": "Analyze the microservices migration effort. What technical debt is being addressed?",
        "expected_insights": [
            "Monolithic architecture being broken into focused services",
            "45 files changed indicates significant refactoring effort",
            "2500 additions vs 800 deletions shows net code growth",
            "Service separation improves maintainability",
            "Team autonomy benefits from independent services",
            "Breaking change label indicates API compatibility impact"
        ]
    },
    {
        "scenario": "Incident Response Analysis",
        "repo_data": GITHUB_REPOSITORIES_DATA[0],
        "query": "What critical issues were addressed in recent commits? How quickly were they resolved?",
        "expected_insights": [
            "Memory leak in payment webhook handlers was critical issue",
            "Redis connection pooling implemented to prevent resource exhaustion",
            "Proper cleanup in error cases prevents memory accumulation",
            "Circuit breaker adds fault tolerance for external dependencies",
            "Quick resolution with focused, targeted fixes",
            "Testing included to prevent regression"
        ]
    }
]

# Evaluation dimensions specific to GitHub analysis
GITHUB_EVALUATION_DIMENSIONS = [
    "code_quality_assessment",     # Can it assess code quality from commits/PRs?
    "security_awareness",          # Does it identify security issues and fixes?
    "performance_understanding",   # Can it understand performance improvements?
    "architecture_insights",       # Does it provide architectural analysis?
    "development_workflow",        # Does it understand dev team workflows?
    "risk_identification",         # Can it identify technical and business risks?
    "change_impact_analysis",      # Does it assess impact of changes?
    "best_practices_recognition"   # Does it recognize engineering best practices?
]