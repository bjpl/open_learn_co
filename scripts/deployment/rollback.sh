#!/bin/bash
set -e

##############################################################################
# OpenLearn Colombia - Emergency Rollback Script
#
# This script provides automated rollback capabilities for production
# deployments when issues are detected post-deployment.
#
# Usage:
#   ./rollback.sh [staging|production] [application|database|full]
#
# Examples:
#   ./rollback.sh production application
#   ./rollback.sh staging database
#   ./rollback.sh production full
##############################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=$1
ROLLBACK_TYPE=$2
AWS_REGION="us-east-1"

# Validate arguments
if [ -z "$ENVIRONMENT" ] || [ -z "$ROLLBACK_TYPE" ]; then
    echo -e "${RED}Error: Missing required arguments${NC}"
    echo "Usage: $0 [staging|production] [application|database|full]"
    exit 1
fi

if [ "$ENVIRONMENT" != "staging" ] && [ "$ENVIRONMENT" != "production" ]; then
    echo -e "${RED}Error: Environment must be 'staging' or 'production'${NC}"
    exit 1
fi

if [ "$ROLLBACK_TYPE" != "application" ] && [ "$ROLLBACK_TYPE" != "database" ] && [ "$ROLLBACK_TYPE" != "full" ]; then
    echo -e "${RED}Error: Rollback type must be 'application', 'database', or 'full'${NC}"
    exit 1
fi

# Environment-specific configuration
if [ "$ENVIRONMENT" == "production" ]; then
    ECS_CLUSTER="openlearn-production"
    ECS_SERVICE="openlearn-web"
    DB_INSTANCE="openlearn-production"
    ECR_REPOSITORY="openlearn-production"
else
    ECS_CLUSTER="openlearn-staging"
    ECS_SERVICE="openlearn-web"
    DB_INSTANCE="openlearn-staging"
    ECR_REPOSITORY="openlearn-staging"
fi

##############################################################################
# Functions
##############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

confirm_rollback() {
    echo -e "${YELLOW}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          ⚠️  ROLLBACK CONFIRMATION REQUIRED ⚠️              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "Environment: $ENVIRONMENT"
    echo "Rollback Type: $ROLLBACK_TYPE"
    echo ""
    read -p "Are you sure you want to proceed? (yes/no): " confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled by user"
        exit 0
    fi

    if [ "$ENVIRONMENT" == "production" ]; then
        echo ""
        log_warning "This is a PRODUCTION rollback!"
        read -p "Type 'rollback production' to confirm: " prod_confirmation

        if [ "$prod_confirmation" != "rollback production" ]; then
            log_error "Production confirmation failed. Aborting."
            exit 1
        fi
    fi
}

get_previous_task_definition() {
    log_info "Fetching previous task definition..."

    CURRENT_DEPLOYMENT=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].deployments[0].taskDefinition' \
        --output text)

    PREVIOUS_DEPLOYMENT=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].deployments[1].taskDefinition' \
        --output text)

    if [ -z "$PREVIOUS_DEPLOYMENT" ] || [ "$PREVIOUS_DEPLOYMENT" == "None" ]; then
        log_error "No previous deployment found"
        exit 1
    fi

    log_info "Current: $CURRENT_DEPLOYMENT"
    log_info "Previous: $PREVIOUS_DEPLOYMENT"

    echo $PREVIOUS_DEPLOYMENT
}

get_latest_snapshot() {
    log_info "Finding latest database snapshot..."

    LATEST_SNAPSHOT=$(aws rds describe-db-snapshots \
        --db-instance-identifier $DB_INSTANCE \
        --region $AWS_REGION \
        --query 'sort_by(DBSnapshots[?Status==`available`], &SnapshotCreateTime)[-1].DBSnapshotIdentifier' \
        --output text)

    if [ -z "$LATEST_SNAPSHOT" ] || [ "$LATEST_SNAPSHOT" == "None" ]; then
        log_error "No available snapshots found"
        exit 1
    fi

    SNAPSHOT_TIME=$(aws rds describe-db-snapshots \
        --db-snapshot-identifier $LATEST_SNAPSHOT \
        --region $AWS_REGION \
        --query 'DBSnapshots[0].SnapshotCreateTime' \
        --output text)

    log_info "Latest snapshot: $LATEST_SNAPSHOT (created: $SNAPSHOT_TIME)"

    echo $LATEST_SNAPSHOT
}

rollback_application() {
    log_info "Starting application rollback..."

    # Get previous task definition
    PREVIOUS_TASK_DEF=$(get_previous_task_definition)

    # Update ECS service
    log_info "Updating ECS service to previous task definition..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --task-definition $PREVIOUS_TASK_DEF \
        --region $AWS_REGION \
        --force-new-deployment

    # Wait for service to stabilize
    log_info "Waiting for service to stabilize (this may take several minutes)..."
    aws ecs wait services-stable \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION

    log_info "Application rollback completed successfully"
}

rollback_database() {
    log_info "Starting database rollback..."

    # Get latest snapshot
    SNAPSHOT_ID=$(get_latest_snapshot)

    # Confirm snapshot age
    SNAPSHOT_AGE=$(aws rds describe-db-snapshots \
        --db-snapshot-identifier $SNAPSHOT_ID \
        --region $AWS_REGION \
        --query 'DBSnapshots[0].SnapshotCreateTime' \
        --output text)

    log_warning "Database will be restored to snapshot: $SNAPSHOT_ID"
    log_warning "Snapshot age: $SNAPSHOT_AGE"
    read -p "Continue with database restore? (yes/no): " db_confirmation

    if [ "$db_confirmation" != "yes" ]; then
        log_info "Database rollback cancelled"
        return
    fi

    # Stop application to prevent data corruption
    log_info "Scaling down application..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --desired-count 0 \
        --region $AWS_REGION

    # Wait for tasks to stop
    sleep 30

    # Create temporary restore instance
    RESTORE_INSTANCE="${DB_INSTANCE}-restore-$(date +%Y%m%d%H%M%S)"

    log_info "Creating restore instance: $RESTORE_INSTANCE"
    aws rds restore-db-instance-from-db-snapshot \
        --db-instance-identifier $RESTORE_INSTANCE \
        --db-snapshot-identifier $SNAPSHOT_ID \
        --region $AWS_REGION

    # Wait for restore to complete
    log_info "Waiting for database restore (this may take 10-15 minutes)..."
    aws rds wait db-instance-available \
        --db-instance-identifier $RESTORE_INSTANCE \
        --region $AWS_REGION

    log_info "Database restore completed"
    log_warning "Manual steps required:"
    echo "  1. Update application database endpoint to: $RESTORE_INSTANCE"
    echo "  2. Verify data integrity"
    echo "  3. Delete old database instance: $DB_INSTANCE"
    echo "  4. Rename restored instance to: $DB_INSTANCE"
    echo "  5. Scale up application"
}

rollback_full() {
    log_info "Starting full rollback (application + database)..."

    # First rollback database
    rollback_database

    # Then rollback application
    rollback_application

    log_info "Full rollback completed"
}

verify_rollback() {
    log_info "Verifying rollback..."

    # Check service health
    SERVICE_STATUS=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].status' \
        --output text)

    RUNNING_COUNT=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].runningCount' \
        --output text)

    DESIRED_COUNT=$(aws ecs describe-services \
        --cluster $ECS_CLUSTER \
        --services $ECS_SERVICE \
        --region $AWS_REGION \
        --query 'services[0].desiredCount' \
        --output text)

    log_info "Service status: $SERVICE_STATUS"
    log_info "Running tasks: $RUNNING_COUNT / $DESIRED_COUNT"

    if [ "$RUNNING_COUNT" -eq "$DESIRED_COUNT" ] && [ "$SERVICE_STATUS" == "ACTIVE" ]; then
        log_info "Service is healthy"
        return 0
    else
        log_warning "Service may not be fully healthy"
        return 1
    fi
}

send_notification() {
    local message=$1

    log_info "Sending notification..."

    # Send to Slack (if webhook configured)
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST $SLACK_WEBHOOK_URL \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 OpenLearn Rollback: $message\"}"
    fi

    # Send email (if configured)
    if [ ! -z "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "OpenLearn Rollback Alert" $ALERT_EMAIL
    fi
}

##############################################################################
# Main Execution
##############################################################################

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     OpenLearn Colombia - Emergency Rollback Script        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Confirm rollback
confirm_rollback

# Record start time
START_TIME=$(date +%s)

# Perform rollback
case $ROLLBACK_TYPE in
    application)
        rollback_application
        ;;
    database)
        rollback_database
        ;;
    full)
        rollback_full
        ;;
esac

# Verify rollback
if verify_rollback; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║               ✅ ROLLBACK SUCCESSFUL ✅                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_info "Environment: $ENVIRONMENT"
    log_info "Rollback type: $ROLLBACK_TYPE"
    log_info "Duration: ${DURATION}s"

    send_notification "Rollback completed successfully for $ENVIRONMENT ($ROLLBACK_TYPE) in ${DURATION}s"
else
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║          ⚠️  ROLLBACK COMPLETED WITH WARNINGS ⚠️           ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    log_warning "Please verify the deployment manually"

    send_notification "Rollback completed with warnings for $ENVIRONMENT ($ROLLBACK_TYPE)"
fi

echo ""
log_info "Next steps:"
echo "  1. Verify application functionality"
echo "  2. Check error logs and metrics"
echo "  3. Investigate root cause of original issue"
echo "  4. Update incident report"
echo ""
