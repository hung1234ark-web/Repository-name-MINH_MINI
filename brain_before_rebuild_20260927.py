
def resolve_reference(
    text: str,
    context: Dict[str, Any],
    history: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:

    reference = find_reference(text)
    source_number = extract_source_number(text)

    resolved = {
        "reference": reference,
        "source_number": source_number,
        "target": "",
        "topic": "",
        "query": "",
        "action": "",
    }

    low = lower(text)

    # --------------------------------------------------------
    # explicit source / item number
    # --------------------------------------------------------
    if source_number is not None:
        resolved["reference"] = reference or f"item:{source_number}"

    # --------------------------------------------------------
    # xác định câu hiện tại có thực sự cần context hay không
    # --------------------------------------------------------
    context_reference = any(
        phrase in low
        for phrase in [
            "nó",
            "cái này",
            "cái đó",
            "cái kia",
            "mở nó",
            "đóng nó",
            "xem nó",
            "tìm thêm",
            "thêm nữa",
            "còn cái kia",
            "còn cái đó",
            "còn cái này",
            "rồi sao",
            "vậy sao",
            "thế sao",
        ]
    )

    # --------------------------------------------------------
    # context object
    #
    # CHỈ kế thừa target/topic/query/action khi câu hiện tại
    # thật sự là câu tiếp nối cần context.
    # --------------------------------------------------------
    if context_reference:

        if not resolved["target"]:
            resolved["target"] = str(
                context.get("active_target", "")
                or context.get("last_target", "")
                or ""
            )

        if not resolved["topic"]:
            resolved["topic"] = str(
                context.get("active_topic", "")
                or context.get("topic", "")
                or ""
            )

        if not resolved["query"]:
            resolved["query"] = str(
                context.get("last_query", "")
                or context.get("query", "")
                or ""
            )

        if not resolved["action"]:
            resolved["action"] = str(
                context.get("active_action", "")
                or context.get("last_action", "")
                or ""
            )

    # --------------------------------------------------------
    # resolve exact references from history
    # --------------------------------------------------------
    if history and context_reference:

        recent_user_messages = [
            item.get("content", "")
            for item in reversed(history[-MAX_HISTORY_SCAN:])
            if isinstance(item, dict)
            and str(item.get("role", "")).lower() == "user"
        ]

        for previous in recent_user_messages:
            previous = normalize_text(previous)

            previous_target = extract_target(previous)
            previous_topic = extract_topic(previous)
            previous_action = extract_action(previous)

            if previous_target and not resolved["target"]:
                resolved["target"] = previous_target

            if previous_topic and not resolved["topic"]:
                resolved["topic"] = previous_topic

            if previous_action and not resolved["action"]:
                resolved["action"] = previous_action

            if previous:
                previous_query = extract_query(
                    previous,
                    previous_target,
                )

                if previous_query and not resolved["query"]:
                    resolved["query"] = previous_query

            if (
                resolved["target"]
                or resolved["topic"]
                or resolved["query"]
            ):
                break

    return resolved

