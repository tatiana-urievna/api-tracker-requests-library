#!/usr/bin/env python3
"""
Generates an Insomnia v5 collection from the Startrek OpenAPI spec.
Organizes requests into folders by API tag.
"""

import json
import uuid
import time
import re
import yaml
from collections import defaultdict, OrderedDict

BASE_URL = "https://st-api.yandex-team.ru"
NOW_MS = int(time.time() * 1000)


def make_id(prefix="req"):
    return f"{prefix}_{uuid.uuid4().hex}"


def slugify(name):
    return re.sub(r"[^a-z0-9_]", "_", name.lower().strip())


def resolve_ref(spec, ref):
    """Resolve a $ref like #/components/schemas/Foo"""
    if not ref.startswith("#/"):
        return {}
    parts = ref[2:].split("/")
    node = spec
    for p in parts:
        node = node.get(p, {})
    return node


def schema_to_example(spec, schema, depth=0):
    """Generate a minimal JSON example from a schema."""
    if depth > 4:
        return None
    if not schema:
        return None

    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])

    if "allOf" in schema:
        result = {}
        for s in schema["allOf"]:
            ex = schema_to_example(spec, s, depth + 1)
            if isinstance(ex, dict):
                result.update(ex)
        return result or None

    if "oneOf" in schema or "anyOf" in schema:
        variants = schema.get("oneOf", schema.get("anyOf", []))
        if variants:
            return schema_to_example(spec, variants[0], depth + 1)

    schema_type = schema.get("type")
    fmt = schema.get("format", "")

    if schema_type == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = schema.get("required", [])
        result = {}
        keys = required[:5] if required else list(props.keys())[:5]
        for k in keys:
            if k in props:
                result[k] = schema_to_example(spec, props[k], depth + 1)
        return result if result else {}

    if schema_type == "array":
        item_ex = schema_to_example(spec, schema.get("items", {}), depth + 1)
        return [item_ex] if item_ex is not None else []

    if schema_type == "string":
        if "enum" in schema:
            return schema["enum"][0]
        examples = {"date": "2024-01-01", "date-time": "2024-01-01T00:00:00Z",
                    "uri": "https://example.com", "email": "user@example.com",
                    "uuid": "00000000-0000-0000-0000-000000000000"}
        return examples.get(fmt, "string")

    if schema_type == "integer":
        return 1

    if schema_type == "number":
        return 1.0

    if schema_type == "boolean":
        return True

    return None


def get_request_body_example(spec, operation):
    """Extract JSON body example from operation's requestBody."""
    rb = operation.get("requestBody", {})
    if not rb:
        return None
    content = rb.get("content", {})
    json_content = content.get("application/json", content.get("*/*", {}))
    if not json_content:
        return None

    schema = json_content.get("schema", {})
    if "$ref" in schema:
        schema = resolve_ref(spec, schema["$ref"])

    example = json_content.get("example")
    if example:
        return example

    examples = json_content.get("examples", {})
    if examples:
        first = next(iter(examples.values()))
        if "$ref" in first:
            first = resolve_ref(spec, first["$ref"])
        return first.get("value")

    return schema_to_example(spec, schema)


def get_query_params(spec, operation):
    """Extract query parameters from an operation."""
    params = []
    for p in operation.get("parameters", []):
        if "$ref" in p:
            p = resolve_ref(spec, p["$ref"])
        if p.get("in") == "query":
            params.append({
                "name": p["name"],
                "value": str(p.get("example", "")),
                "disabled": not p.get("required", False),
            })
    return params


def path_to_url(path):
    """Convert OpenAPI path params like {id} to Insomnia-style :id."""
    return BASE_URL + path


def make_request(spec, method, path, operation, sort_key):
    url = path_to_url(path)
    name = operation.get("summary") or operation.get("operationId") or f"{method.upper()} {path}"
    description = operation.get("description", "")

    body_example = get_request_body_example(spec, operation) if method in ("post", "put", "patch") else None
    query_params = get_query_params(spec, operation)

    request = {
        "url": url,
        "name": name,
        "meta": {
            "id": make_id("req"),
            "created": NOW_MS,
            "modified": NOW_MS,
            "isPrivate": False,
            "description": description,
            "sortKey": sort_key,
        },
        "method": method.upper(),
        "headers": [
            {"name": "Authorization", "value": "OAuth {{token}}"},
        ],
        "authentication": {
            "type": "oauth2",
            "disabled": False,
        },
        "settings": {
            "renderRequestBody": True,
            "encodeUrl": True,
            "followRedirects": "global",
            "cookies": {"send": True, "store": True},
            "rebuildPath": True,
        },
    }

    if body_example is not None:
        request["headers"].append({"name": "Content-Type", "value": "application/json"})
        try:
            request["body"] = {
                "mimeType": "application/json",
                "text": json.dumps(body_example, ensure_ascii=False, indent=2),
            }
        except Exception:
            request["body"] = {"mimeType": "application/json", "text": "{}"}

    if query_params:
        request["parameters"] = query_params

    return request


def tag_to_folder_name(tag):
    mapping = {
        "Agile boards": "Agile Boards",
        "ru.yandex.startrek.forms.web.v2": "Forms (internal)",
        "ru.yandex.startrek.web.api.doc": "API Doc (internal)",
    }
    return mapping.get(tag, tag)


def main():
    print("Loading OpenAPI spec...")
    with open("openapi.json", "r") as f:
        spec = json.load(f)

    paths = spec.get("paths", {})
    print(f"Total endpoints: {len(paths)}")

    # Group requests by tag
    tag_requests = defaultdict(list)
    sort_counter = 0

    for path, methods in sorted(paths.items()):
        for method, operation in methods.items():
            if method not in ("get", "post", "put", "patch", "delete", "head"):
                continue
            if not isinstance(operation, dict):
                continue
            tags = operation.get("tags", ["Other"])
            tag = tags[0]
            sort_counter -= 50
            req = make_request(spec, method, path, operation, sort_counter)
            tag_requests[tag].append(req)

    # Build collection: folders with nested requests
    collection = []
    folder_sort = 0

    # Sort tags: put common ones first
    priority_tags = ["Issues", "Comments", "Queue", "Sprints", "Agile boards",
                     "Attachments", "Work logs", "Components", "Projects",
                     "User", "Myself", "Statuses", "Priorities", "Resolutions"]

    all_tags = list(tag_requests.keys())
    ordered_tags = []
    for t in priority_tags:
        if t in all_tags:
            ordered_tags.append(t)
    for t in sorted(all_tags):
        if t not in ordered_tags:
            ordered_tags.append(t)

    total_requests = 0
    for tag in ordered_tags:
        requests = tag_requests[tag]
        folder_sort -= 100
        folder = {
            "name": tag_to_folder_name(tag),
            "meta": {
                "id": make_id("fld"),
                "created": NOW_MS,
                "modified": NOW_MS,
                "sortKey": folder_sort,
            },
            "children": requests,
        }
        collection.append(folder)
        total_requests += len(requests)

    print(f"Total requests generated: {total_requests}")
    print(f"Total folders: {len(collection)}")

    output = {
        "type": "collection.insomnia.rest/5.0",
        "schema_version": "5.1",
        "name": "Startrek API (st-api.yandex-team.ru)",
        "meta": {
            "id": make_id("wrk"),
            "created": NOW_MS,
            "modified": NOW_MS,
            "description": "Auto-generated from OpenAPI spec. Use {{token}} environment variable for OAuth token.",
        },
        "collection": collection,
    }

    out_path = "Startrek_API_Insomnia.yaml"
    with open(out_path, "w", encoding="utf-8") as f:
        yaml.dump(output, f, allow_unicode=True, sort_keys=False,
                  default_flow_style=False, width=120)

    print(f"\nDone! Saved to: {out_path}")
    print("\nTo use:")
    print("  1. Open Insomnia")
    print("  2. File -> Import -> From File -> Startrek_API_Insomnia.yaml")
    print("  3. Set environment variable 'token' to your OAuth token")


if __name__ == "__main__":
    main()
