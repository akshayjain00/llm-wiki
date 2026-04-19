from llm_wiki.manifests import build_ref_manifest


def test_build_ref_manifest_records_roots_and_live_refs() -> None:
    manifest = build_ref_manifest(
        project_slug="demo-project",
        live_paths=["/tmp/demo"],
        origin_roots=["/tmp"],
        last_scanned_timestamp="2026-04-09T10:00:00Z",
    )
    assert manifest["project_slug"] == "demo-project"
    assert manifest["authoritative_live_paths"] == ["/tmp/demo"]
    assert manifest["origin_roots"] == ["/tmp"]
    assert manifest["last_scanned_timestamp"] == "2026-04-09T10:00:00Z"
