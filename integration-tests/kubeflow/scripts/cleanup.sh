#!/bin/bash
# Source: https://gitlab.cee.redhat.com/data-hub/olminstall/-/blob/main/cleanup.sh
# Synced from commit: <FILL_IN_COMMIT_HASH>
# Last synced: <FILL_IN_DATE>
#
# TODO: Replace this placeholder with the actual cleanup.sh content from the
# source repository above. This file cannot be auto-synced because Konflux
# pipelines do not have VPN access to gitlab.cee.redhat.com.
#
# Usage: ./cleanup.sh -t operator -g
#
# Until replaced, this script performs a basic ODH/RHOAI operator cleanup
# that covers the common resources. The full script from olminstall handles
# additional edge cases (CRD cleanup, finalizer removal, etc.).

set -e

usage() {
    echo "Usage: $0 -t <type> [-g]"
    echo "  -t type    Cleanup type: 'operator'"
    echo "  -g         Generic/global cleanup"
    exit 1
}

CLEANUP_TYPE=""
GLOBAL=false

while getopts "t:g" opt; do
    case $opt in
        t) CLEANUP_TYPE="$OPTARG" ;;
        g) GLOBAL=true ;;
        *) usage ;;
    esac
done

if [[ -z "${CLEANUP_TYPE}" ]]; then
    usage
fi

echo "=== ODH/RHOAI Cleanup (type=${CLEANUP_TYPE}, global=${GLOBAL}) ==="

echo "--- Deleting DataScienceCluster ---"
oc delete dsc --all --timeout=120s 2>/dev/null || true

echo "--- Deleting DSCInitialization ---"
oc delete dsci --all --timeout=120s 2>/dev/null || true

echo "--- Deleting operator Subscription ---"
oc delete subscription --all -n redhat-ods-operator --timeout=60s 2>/dev/null || true

echo "--- Deleting CSVs ---"
oc delete csv --all -n redhat-ods-operator --timeout=60s 2>/dev/null || true

echo "--- Deleting CatalogSource ---"
oc delete catalogsource odh-operator-catalog -n openshift-marketplace --timeout=60s 2>/dev/null || true

echo "--- Deleting OperatorGroup ---"
oc delete operatorgroup --all -n redhat-ods-operator --timeout=60s 2>/dev/null || true

if [[ "${GLOBAL}" == "true" ]]; then
    echo "--- Deleting operator namespaces ---"
    for ns in redhat-ods-operator redhat-ods-applications redhat-ods-monitoring rhods-notebooks; do
        if oc get namespace "${ns}" &>/dev/null; then
            echo "  Deleting namespace ${ns}"
            oc delete namespace "${ns}" --timeout=180s 2>/dev/null || true
        fi
    done

    echo "--- Waiting for namespaces to be fully deleted ---"
    for ns in redhat-ods-operator redhat-ods-applications redhat-ods-monitoring rhods-notebooks; do
        if oc get namespace "${ns}" &>/dev/null; then
            echo "  Waiting for namespace ${ns} to be deleted..."
            oc wait --for=delete "namespace/${ns}" --timeout=180s 2>/dev/null || true
        fi
    done
fi

echo "=== Cleanup complete ==="
