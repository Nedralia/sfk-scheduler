def normalize_member_name(member):
    first_name = str(
        member.get("first_name")
        or member.get("firstname")
        or member.get("fornamn")
        or ""
    ).strip()
    last_name = str(
        member.get("last_name")
        or member.get("lastname")
        or member.get("efternamn")
        or ""
    ).strip()
    full_name = f"{first_name} {last_name}".strip()

    if not full_name:
        full_name = str(member.get("full_name") or member.get("name") or "").strip()

    if not full_name:
        return None

    return full_name


def normalize_member_number(member):
    raw = (
        member.get("member_number")
        or member.get("membership_number")
        or member.get("member_id")
        or ""
    )
    return str(raw).strip()


def parse_api_response(payload):
    if isinstance(payload, dict):
        if payload.get("errors"):
            error_messages = "; ".join(
                item.get("message", "Unknown API error")
                for item in payload["errors"]
                if isinstance(item, dict)
            )
            raise RuntimeError(f"MyWebLog API error: {error_messages}")

        users = payload.get("users")
        if isinstance(users, list):
            return users

    raise ValueError("Could not find a users list in the MyWebLog response.")


def normalize_members(all_users):
    seen_names = {}
    for member in all_users:
        name = normalize_member_name(member)
        if name and name not in seen_names:
            seen_names[name] = normalize_member_number(member)

    normalized = sorted(
        [(name, number) for name, number in seen_names.items()],
        key=lambda x: x[0],
    )

    if not normalized:
        raise RuntimeError("MyWebLog returned no members.")

    return normalized
