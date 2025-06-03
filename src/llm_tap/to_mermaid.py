def to_identifier(s):
    return (
        s.replace("<", "_")
        .replace(">", "_")
        .replace('"', "_")
        .replace("(", "_")
        .replace(")", "_")
        .replace(" ", "_")
    )


def escape(s):
    return (
        s.replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("(", "#40;")
        .replace(")", "#41;")
        .replace(" ", "_")
    )


def format_guard(guard):
    conds = [
        f"{cond.value.type.name} {cond.operator} {cond.value.value}"
        for cond in guard.conditions
    ]
    return f"Guard: {' ' + guard.conditions_operator + ' ' .join(conds)}"


def workflow_to_mermaid(workflow):
    lines = ["flowchart LR"]

    # Collect all unique places
    places = set()
    for t in workflow.transitions:
        for arc in t.inputs + t.outputs:
            places.add(arc.place)

    lines.append("    subgraph Sources")
    for place in places:
        if place.type == "source":
            lines.append(
                f"        {to_identifier(place.name)}[{escape(place.name)}<br/>{place.token_type.name}: {place.token_type.type}]"
            )
    lines.append("    end")

    lines.append("    subgraph Sink")
    for place in places:
        if place.type == "sink":
            lines.append(
                f"        {to_identifier(place.name)}[{escape(place.name)}<br/>{place.token_type.name}: {place.token_type.type}]"
            )
    lines.append("    end")

    # Transitions and arcs
    lines.append("    subgraph Transitions")
    for transition in workflow.transitions:
        guard_str = ""
        if transition.guard:
            guard_str = "<br/>" + " AND ".join(
                [
                    f"{c.value.type.name} {c.operator} {c.value.value}"
                    for g in transition.guard
                    for c in g.conditions
                ]
            )
        trans_node = transition.name.replace(" ", "_")
        lines.append(f"        {trans_node}[{transition.name}{guard_str}]")
    lines.append("    end")

    # Arcs
    for t in workflow.transitions:
        trans_node = t.name.replace(" ", "_")
        for arc in t.inputs:
            place_node = to_identifier(arc.place.name)
            lines.append(
                f"    {place_node} -->|{arc.token_name}| {trans_node}"
            )
        for arc in t.outputs:
            place_node = to_identifier(arc.place.name)
            value = arc.produce_token.value
            lines.append(
                f"    {trans_node} -->|{arc.produce_token.type.name} = {value}| {place_node}"
            )

    return "\n".join(lines)
