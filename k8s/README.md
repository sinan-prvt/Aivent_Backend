# Kubernetes Deployment – Aivent Backend

This Kubernetes setup was deployed on an AWS EC2 instance using k3s.

## Components
- auth-service (Django REST API + JWT)
- postgres (StatefulSet for persistence)
- redis (cache & celery result backend)
- rabbitmq (message broker)
- celery worker (background async tasks)

## Architecture Notes
- Each service is isolated with its own Deployment/StatefulSet.
- Internal communication is handled via Kubernetes Services (ClusterIP).
- auth-service is exposed externally using a NodePort for testing.
- Environment variables are injected via manifests to mirror production setup.

## Verification
The system was verified by:
- Successful pod startup
- Service discovery via Kubernetes DNS
- External API access through NodePort
