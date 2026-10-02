import json
import urllib.request
from datetime import date, timedelta
from .config import AI_MODEL, OPENAI_API_KEY


def build_live_insights(tasks: list[dict], stats: dict) -> list[str]:
    today = date.today()
    overdue = [t for t in tasks if t.get('is_overdue')]
    high_pending = [t for t in tasks if t['status'] == 'Pending' and t['priority'] == 'High']
    upcoming = [t for t in tasks if t.get('task_status', t['status']) != 'Completed' and today <= date.fromisoformat(t['deadline']) <= today + timedelta(days=2)]
    recent_start = today - timedelta(days=6)
    previous_start = today - timedelta(days=13)
    recent_completed = sum(bool(t.get('completed_at')) and date.fromisoformat(t['completed_at'][:10]) >= recent_start for t in tasks)
    previous_completed = sum(bool(t.get('completed_at')) and previous_start <= date.fromisoformat(t['completed_at'][:10]) < recent_start for t in tasks)
    trend_delta = recent_completed - previous_completed
    trend = 'up' if trend_delta > 0 else 'down' if trend_delta < 0 else 'steady'
    insights = [
        f"{len(overdue)} task{'s are' if len(overdue) != 1 else ' is'} overdue.",
        f"{len(high_pending)} high-priority task{'s are' if len(high_pending) != 1 else ' is'} currently pending.",
        f"{len(upcoming)} task{'s are' if len(upcoming) != 1 else ' is'} due within the next 2 days.",
        f"Completion rate is {stats['completion_rate']}% across {stats['total_tasks']} tasks.",
        f"7-day completion trend is {trend}: {recent_completed} completed this week vs {previous_completed} the prior week.",
    ]
    employees = {}
    for task in tasks:
        name = task.get('employee_name')
        if name:
            employees.setdefault(name, []).append(task)
    if employees:
        name, assigned = max(employees.items(), key=lambda pair: len(pair[1]))
        employee_overdue = sum(t.get('is_overdue', False) for t in assigned)
        insights.append(f"{name} has {len(assigned)} assigned task{'s' if len(assigned) != 1 else ''}, including {employee_overdue} overdue.")
    return insights


def analyze(tasks: list[dict], stats: dict) -> dict:
    overdue = [t for t in tasks if t.get('is_overdue')]
    pending = [t for t in tasks if t.get('task_status', t['status']) == 'Pending' and not t.get('is_overdue')]
    live_insights = build_live_insights(tasks, stats)
    if OPENAI_API_KEY:
        prompt = {'tasks': tasks, 'stats': stats, 'live_insights': live_insights}
        body = json.dumps({'model': AI_MODEL, 'messages': [
            {'role': 'system', 'content': 'You are a concise operations coach. Return JSON with summary (string), recommendations (array of strings), and focus_tasks (array of task titles). Use only supplied data. Do not alter the supplied calculated metrics.'},
            {'role': 'user', 'content': json.dumps(prompt)}], 'response_format': {'type': 'json_object'}}).encode()
        req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=body, headers={'Authorization': f'Bearer {OPENAI_API_KEY}', 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                content = json.loads(response.read())['choices'][0]['message']['content']
            return {**json.loads(content), 'live_insights': live_insights, 'source': 'ai'}
        except Exception:
            pass
    recommendations = []
    if overdue:
        recommendations.append(f"Review {len(overdue)} overdue task{'s' if len(overdue) != 1 else ''}, starting with {overdue[0]['title']}.")
    if pending:
        recommendations.append(f"Confirm owners and next steps for {len(pending)} pending task{'s' if len(pending) != 1 else ''} at the next team check-in.")
    if not recommendations:
        recommendations.append('Keep the current pace and review upcoming deadlines in the next stand-up.')
    return {
        'summary': f"The team has {stats['total_tasks']} tasks, with {stats['completed']} completed and {len(overdue)} overdue. On-time completion is {stats['on_time_percentage']}%.",
        'recommendations': recommendations,
        'focus_tasks': [t['title'] for t in list({t['id']: t for t in overdue + pending}.values())[:3]],
        'live_insights': live_insights,
        'source': 'rules',
    }
