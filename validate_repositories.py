#!/usr/bin/env python3
"""
Validate Flux v2 Repository resources (HelmRepository and OCIRepository).
This script validates that all resources conform to Flux v2 standards.

Requirements:
    pip install pyyaml

Usage:
    python3 validate_repositories.py [path/to/repositories]

    If no path is provided, defaults to infrastructure/base/repositories
    relative to the script location.
"""

import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required but not installed.")
    print("Install it with: pip install pyyaml")
    sys.exit(1)
from pathlib import Path
from typing import Dict, List, Tuple

# Expected API versions for Flux v2
EXPECTED_API_VERSIONS = {
    'HelmRepository': 'source.toolkit.fluxcd.io/v1',
    'OCIRepository': 'source.toolkit.fluxcd.io/v1',
    'Kustomization': 'kustomize.config.k8s.io/v1beta1'
}

# Required fields for each resource type
REQUIRED_FIELDS = {
    'HelmRepository': {
        'apiVersion': str,
        'kind': str,
        'metadata': dict,
        'spec': dict
    },
    'OCIRepository': {
        'apiVersion': str,
        'kind': str,
        'metadata': dict,
        'spec': dict
    }
}

# Required metadata fields
REQUIRED_METADATA = ['name', 'namespace']

# Required spec fields
REQUIRED_SPEC = {
    'HelmRepository': ['url', 'interval'],
    'OCIRepository': ['url', 'interval']
}


def validate_yaml_file(file_path: Path) -> Tuple[bool, List[str]]:
    """Validate a single YAML file."""
    errors = []

    try:
        with open(file_path, 'r') as f:
            docs = list(yaml.safe_load_all(f))
    except yaml.YAMLError as e:
        return False, [f"Invalid YAML syntax: {e}"]
    except Exception as e:
        return False, [f"Failed to read file: {e}"]

    # Filter out None documents (from empty YAML separator lines)
    docs = [doc for doc in docs if doc is not None]

    if not docs:
        return False, ["No YAML documents found in file"]

    for idx, doc in enumerate(docs):
        doc_num = idx + 1

        # Check apiVersion
        if 'apiVersion' not in doc:
            errors.append(f"Document {doc_num}: Missing 'apiVersion' field")
            continue

        # Check kind
        if 'kind' not in doc:
            errors.append(f"Document {doc_num}: Missing 'kind' field")
            continue

        kind = doc['kind']

        # Skip validation for non-repository resources
        if kind not in ['HelmRepository', 'OCIRepository']:
            continue

        # Validate API version
        expected_version = EXPECTED_API_VERSIONS.get(kind)
        if expected_version and doc['apiVersion'] != expected_version:
            errors.append(
                f"Document {doc_num}: Incorrect apiVersion '{doc['apiVersion']}' "
                f"(expected '{expected_version}')"
            )

        # Validate required top-level fields
        for field, field_type in REQUIRED_FIELDS.get(kind, {}).items():
            if field not in doc:
                errors.append(f"Document {doc_num}: Missing required field '{field}'")
            elif not isinstance(doc[field], field_type):
                errors.append(
                    f"Document {doc_num}: Field '{field}' should be {field_type.__name__}, "
                    f"got {type(doc[field]).__name__}"
                )

        # Validate metadata fields
        if 'metadata' in doc and isinstance(doc['metadata'], dict):
            for field in REQUIRED_METADATA:
                if field not in doc['metadata']:
                    errors.append(f"Document {doc_num}: Missing metadata.{field}")

        # Validate spec fields
        if 'spec' in doc and isinstance(doc['spec'], dict):
            for field in REQUIRED_SPEC.get(kind, []):
                if field not in doc['spec']:
                    errors.append(f"Document {doc_num}: Missing spec.{field}")

        # Specific validation for OCIRepository with Helm charts
        if kind == 'OCIRepository' and 'spec' in doc:
            spec = doc['spec']
            # Check if this is a Helm chart repository (heuristic based on common patterns)
            url = spec.get('url', '')
            if 'helm' in url.lower() or 'charts' in url.lower():
                if 'layerSelector' not in spec:
                    errors.append(
                        f"Document {doc_num}: OCIRepository for Helm charts should include "
                        f"'layerSelector' with mediaType"
                    )

    return len(errors) == 0, errors


def main():
    """Main validation function."""
    # Use CLI argument if provided, otherwise default to relative path from script location
    if len(sys.argv) > 1:
        base_dir = Path(sys.argv[1])
    else:
        base_dir = Path(__file__).parent / 'infrastructure' / 'base' / 'repositories'

    if not base_dir.exists():
        print(f"❌ ERROR: Directory not found: {base_dir}")
        sys.exit(1)

    # Read kustomization.yaml to get list of resources
    kustomization_file = base_dir / 'kustomization.yaml'

    if not kustomization_file.exists():
        print(f"❌ ERROR: kustomization.yaml not found at {kustomization_file}")
        sys.exit(1)

    try:
        with open(kustomization_file, 'r') as f:
            kustomization = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ ERROR: Failed to parse kustomization.yaml: {e}")
        sys.exit(1)

    resources = kustomization.get('resources', [])

    if not resources:
        print("⚠️  WARNING: No resources found in kustomization.yaml")
        return

    print(f"📋 Validating {len(resources)} resources from kustomization.yaml...\n")

    all_valid = True
    validation_results = []

    for resource_path in resources:
        file_path = base_dir / resource_path

        if not file_path.exists():
            all_valid = False
            validation_results.append((resource_path, False, [f"File not found: {file_path}"]))
            continue

        valid, errors = validate_yaml_file(file_path)
        validation_results.append((resource_path, valid, errors))

        if not valid:
            all_valid = False

    # Print results
    for resource_path, valid, errors in validation_results:
        if valid:
            print(f"✅ {resource_path}")
        else:
            print(f"❌ {resource_path}")
            for error in errors:
                print(f"   - {error}")

    print()

    if all_valid:
        print("✅ All resources are valid Flux v2 resources!")
        sys.exit(0)
    else:
        print("❌ Validation failed. Please fix the errors above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
