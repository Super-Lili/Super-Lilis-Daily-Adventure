```python
import collections

def context_weaver(messages: list[dict]) -> dict:
    """
    Aggregates and organizes simulated project-related messages from various sources
    into a structured, project-centric digest.

    Args:
        messages: A list of dictionaries, where each dictionary represents a message
                  and contains at least 'source', 'project', and 'content' keys.
                  Example: {'source': 'Slack', 'project': 'Apollo', 'content': 'Decision: Go with phase one deployment.'}

    Returns:
        A dictionary where keys are project names and values are lists of
        aggregated messages for that project, sorted by source for consistency.
    """
    project_digest = collections.defaultdict(list)

    for message in messages:
        if all(k in message for k in ['source', 'project', 'content']):
            project_name = message['project']
            project_digest[project_name].append({
                'source': message['source'],
                'content': message['content']
            })
        else:
            print(f"Warning: Skipping malformed message: {message}")

    # Optional: Sort messages within each project by source for consistent output
    for project in project_digest:
        project_digest[project].sort(key=lambda x: x['source'])

    return dict(project_digest)

if __name__ == "__main__":
    # Simulate today's scattered communications
    todays_messages = [
        {'source': 'Slack', 'project': 'Project Phoenix', 'content': 'Urgent: Server outage in region B. Investigating.'},
        {'source': 'Email', 'project': 'Project Gemini', 'content': 'Meeting notes attached: Q3 Budget review finalized.'},
        {'source': 'Jira', 'project': 'Project Phoenix', 'content': 'Task #1234: Escalated to senior ops for resolution.'},
        {'source': 'Notion', 'project': 'Project Gemini', 'content': 'Design iteration 3 uploaded for feedback.'},
        {'source': 'Slack', 'project': 'Project Gemini', 'content': 'Heads up: Design feedback session moved to tomorrow.'},
        {'source': 'Email', 'project': 'Project Phoenix', 'content': 'Incident report drafted, awaiting approval.'},
        {'source': 'Jira', 'project': 'Project Apollo', 'content': 'Bug #567: High priority, assigned to Dev Team A.'},
        {'source': 'Teams', 'project': 'Project Apollo', 'content': 'Discussing API integration challenges now.'},
    ]

    print("--- RAW INCOMING MESSAGES ---")
    for msg in todays_messages:
        print(f"[{msg['source']}] ({msg['project']}): {msg['content']}")
    print("\n" + "="*40 + "\n")

    # Weave the context
    digested_context = context_weaver(todays_messages)

    print("--- CONTEXT WEAVER DIGEST ---")
    if digested_context:
        for project, messages in digested_context.items():
            print(f"\n[{project.upper()} PROJECT UPDATES]")
            for msg in messages:
                print(f"  - [{msg['source']}] {msg['content']}")
    else:
        print("No messages to digest today.")

    # Example of a malformed message
    malformed_messages = [
        {'source': 'Slack', 'project': 'Project X', 'content': 'Valid message'},
        {'source': 'Email', 'content': 'Missing project'}, # Malformed
        {'project': 'Project Y', 'content': 'Missing source'}, # Malformed
        {'source': 'Teams', 'project': 'Project Z'} # Missing content
    ]
    print("\n" + "="*40 + "\n")
    print("--- TESTING WITH MALFORMED MESSAGES ---")
    context_weaver(malformed_messages)
```