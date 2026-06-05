def retrieve_policy_chunks(failed_rule_keys, visa_type=None, top_k=3):
    docs = []
    for idx, key in enumerate(failed_rule_keys or []):
        docs.append({
            "id": f"doc_{idx}",
            "text": f"No policy chunk available for {key}.",
            "metadata": {"visa_type": visa_type, "rule_key": key}
        })
    return docs
