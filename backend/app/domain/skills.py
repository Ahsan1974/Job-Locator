"""Java ecosystem skill catalog and text extractors."""

from __future__ import annotations

import json
import re

JAVA_SKILLS: tuple[str, ...] = (
    "Java",
    "Spring Boot",
    "Spring Framework",
    "Spring Cloud",
    "Spring Security",
    "Spring Data",
    "Hibernate",
    "JPA",
    "Microservices",
    "REST API",
    "GraphQL",
    "Kafka",
    "RabbitMQ",
    "Redis",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Oracle",
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Terraform",
    "Jenkins",
    "Git",
    "Maven",
    "Gradle",
    "JUnit",
    "Mockito",
    "Testcontainers",
    "Elasticsearch",
    "Cassandra",
    "gRPC",
    "OpenAPI",
    "Swagger",
    "CI/CD",
    "Linux",
    "Kotlin",
    "Reactive",
    "WebFlux",
    "Quarkus",
    "Micronaut",
    "Apache Camel",
    "Solace",
    "ActiveMQ",
    "Prometheus",
    "Grafana",
    "Helm",
    "Istio",
    "Java 17",
    "Java 21",
    "Multithreading",
    "Concurrency",
    "Design Patterns",
    "DDD",
    "TDD",
    "Agile",
    "Scrum",
)

SKILL_ALIASES: dict[str, str] = {
    "springboot": "Spring Boot",
    "spring-boot": "Spring Boot",
    "k8s": "Kubernetes",
    "postgres": "PostgreSQL",
    "amazon web services": "AWS",
    "ms sql": "MySQL",
    "junit5": "JUnit",
    "rest": "REST API",
    "restful": "REST API",
    "ci cd": "CI/CD",
    "cicd": "CI/CD",
}

SKILL_LEARNING: dict[str, dict] = {
    "Kafka": {
        "hours": 40,
        "priority": "high",
        "courses": [
            {"title": "Apache Kafka Series", "url": "https://www.udemy.com/topic/apache-kafka/", "provider": "Udemy"},
            {"title": "Kafka Docs", "url": "https://kafka.apache.org/documentation/", "provider": "Apache"},
        ],
        "docs": [{"title": "Kafka Documentation", "url": "https://kafka.apache.org/documentation/"}],
        "projects": ["Build a Spring Boot order events pipeline with Kafka"],
        "improvement": 8,
    },
    "Redis": {
        "hours": 20,
        "priority": "high",
        "courses": [
            {"title": "Redis University", "url": "https://university.redis.com/", "provider": "Redis"},
        ],
        "docs": [{"title": "Redis Docs", "url": "https://redis.io/docs/"}],
        "projects": ["Add Redis caching to a Spring Boot API"],
        "improvement": 5,
    },
    "Docker": {
        "hours": 25,
        "priority": "high",
        "courses": [
            {"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/", "provider": "Docker"},
        ],
        "docs": [{"title": "Docker Docs", "url": "https://docs.docker.com/"}],
        "projects": ["Containerize a Spring Boot + Postgres app"],
        "improvement": 6,
    },
    "Kubernetes": {
        "hours": 50,
        "priority": "high",
        "courses": [
            {"title": "Kubernetes Basics", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "provider": "CNCF"},
        ],
        "docs": [{"title": "K8s Docs", "url": "https://kubernetes.io/docs/home/"}],
        "projects": ["Deploy Spring Boot microservices to a local Kind cluster"],
        "improvement": 9,
    },
    "AWS": {
        "hours": 60,
        "priority": "high",
        "courses": [
            {"title": "AWS Free Tier Labs", "url": "https://aws.amazon.com/getting-started/", "provider": "AWS"},
        ],
        "docs": [{"title": "AWS Docs", "url": "https://docs.aws.amazon.com/"}],
        "projects": ["Deploy Spring Boot on ECS/Fargate with RDS"],
        "improvement": 10,
    },
    "RabbitMQ": {
        "hours": 20,
        "priority": "medium",
        "courses": [
            {"title": "RabbitMQ Tutorials", "url": "https://www.rabbitmq.com/getstarted.html", "provider": "RabbitMQ"},
        ],
        "docs": [{"title": "RabbitMQ Docs", "url": "https://www.rabbitmq.com/documentation.html"}],
        "projects": ["Async notifications with Spring AMQP"],
        "improvement": 4,
    },
    "Spring Cloud": {
        "hours": 35,
        "priority": "medium",
        "courses": [
            {"title": "Spring Cloud Docs", "url": "https://spring.io/projects/spring-cloud", "provider": "Spring"},
        ],
        "docs": [{"title": "Spring Cloud", "url": "https://docs.spring.io/spring-cloud/reference/"}],
        "projects": ["Service discovery + config server demo"],
        "improvement": 7,
    },
}

SALARY_BASE: dict[str, dict[str, tuple[int, int, str]]] = {
    # country -> level -> (min, max, currency)
    "USA": {
        "entry": (70000, 95000, "USD"),
        "junior": (85000, 110000, "USD"),
        "mid": (110000, 145000, "USD"),
        "senior": (140000, 185000, "USD"),
        "lead": (165000, 210000, "USD"),
        "principal": (180000, 240000, "USD"),
        "architect": (175000, 230000, "USD"),
    },
    "Germany": {
        "entry": (45000, 58000, "EUR"),
        "junior": (52000, 65000, "EUR"),
        "mid": (65000, 85000, "EUR"),
        "senior": (80000, 105000, "EUR"),
        "lead": (95000, 120000, "EUR"),
        "principal": (110000, 140000, "EUR"),
        "architect": (105000, 135000, "EUR"),
    },
    "United Kingdom": {
        "entry": (35000, 48000, "GBP"),
        "junior": (42000, 55000, "GBP"),
        "mid": (55000, 75000, "GBP"),
        "senior": (70000, 95000, "GBP"),
        "lead": (85000, 110000, "GBP"),
        "principal": (95000, 130000, "GBP"),
        "architect": (90000, 125000, "GBP"),
    },
    "Canada": {
        "entry": (65000, 85000, "CAD"),
        "junior": (75000, 95000, "CAD"),
        "mid": (95000, 125000, "CAD"),
        "senior": (120000, 155000, "CAD"),
        "lead": (140000, 175000, "CAD"),
        "principal": (155000, 195000, "CAD"),
        "architect": (150000, 190000, "CAD"),
    },
    "Remote": {
        "entry": (50000, 70000, "USD"),
        "junior": (60000, 85000, "USD"),
        "mid": (85000, 120000, "USD"),
        "senior": (110000, 150000, "USD"),
        "lead": (130000, 170000, "USD"),
        "principal": (145000, 190000, "USD"),
        "architect": (140000, 185000, "USD"),
    },
}

DEFAULT_SALARY = SALARY_BASE["Remote"]


def extract_skills(text: str) -> list[str]:
    if not text:
        return []
    lower = text.lower()
    found: list[str] = []
    for alias, canonical in SKILL_ALIASES.items():
        if alias in lower and canonical not in found:
            found.append(canonical)
    for skill in JAVA_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()).replace(r"\ ", r"[\s\-]?") + r"\b"
        if re.search(pattern, lower) and skill not in found:
            found.append(skill)
    return found


def parse_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(x) for x in data]
    except json.JSONDecodeError:
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def dump_json(value) -> str:
    return json.dumps(value, ensure_ascii=False)
