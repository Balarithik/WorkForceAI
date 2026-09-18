from __future__ import annotations


def generate_employee_explanation(employee, task, prediction):
    """Create a structured explanation for why an employee was recommended."""
    skill_match = float(prediction.get('skill_match_score', 0.0) or 0.0)
    available_capacity = float(prediction.get('available_capacity_percent', 0.0) or 0.0)
    success_probability = float(prediction.get('success_probability', 0.0) or 0.0)
    sla_probability = float(prediction.get('sla_probability', 0.0) or 0.0)
    predicted_hours = float(prediction.get('predicted_completion_hours', 0.0) or 0.0)
    time_score = float(prediction.get('time_score', 0.0) or 0.0)
    historical_score = float(prediction.get('historical_performance_score', getattr(employee, 'historical_performance_score', 0.0)) or 0.0)
    experience_years = float(prediction.get('experience_years', getattr(employee, 'experience_years', 0.0)) or 0.0)
    required_skills = list(getattr(task, 'required_skills', []) or [])

    if skill_match >= 1.0:
        skill_text = 'Required skills fully matched.'
    elif skill_match >= 0.75:
        skill_text = 'Most required skills matched.'
    elif skill_match >= 0.5:
        skill_text = 'Partial skill match.'
    else:
        skill_text = 'No required skills matched.'

    if available_capacity >= 70:
        capacity_text = f'High available capacity ({available_capacity:.0f}% capacity available).'
    elif available_capacity >= 40:
        capacity_text = f'Moderate available capacity ({available_capacity:.0f}% capacity available).'
    else:
        capacity_text = f'Limited available capacity ({available_capacity:.0f}% capacity available).'

    if predicted_hours <= float(task.sla_hours or 0):
        sla_text = f'Expected completion is within SLA ({predicted_hours:.1f}h vs {float(task.sla_hours):.1f}h).'
    else:
        sla_text = f'Expected completion may exceed SLA ({predicted_hours:.1f}h vs {float(task.sla_hours):.1f}h).'

    if historical_score >= 9.0:
        performance_text = f'Strong historical performance ({historical_score:.1f}/10).'
    elif historical_score >= 8.0:
        performance_text = f'Good historical performance ({historical_score:.1f}/10).'
    else:
        performance_text = f'Historical performance is moderate ({historical_score:.1f}/10).'

    strengths = []
    if skill_match >= 0.5:
        strengths.append(f"Skill match: {skill_match * 100:.0f}%")
    if available_capacity >= 40:
        strengths.append(f"Available capacity: {available_capacity:.0f}%")
    if success_probability >= 0.8:
        strengths.append(f"Success probability: {(success_probability * 100):.1f}%")
    if sla_probability >= 0.8:
        strengths.append(f"SLA probability: {(sla_probability * 100):.1f}%")
    if predicted_hours <= float(task.sla_hours or 0):
        strengths.append(f"Expected completion: {predicted_hours:.1f}h")
    if historical_score >= 9.0:
        strengths.append(f"Historical performance: {historical_score:.1f}/10")
    elif historical_score >= 8.0:
        strengths.append(f"Historical performance: {historical_score:.1f}/10")
    if experience_years > 0:
        strengths.append(f"Experience: {experience_years:.1f} years")

    summary = (
        f"{skill_text} {capacity_text} {sla_text} {performance_text} "
        f"Success probability is {(success_probability * 100):.1f}% and SLA probability is {(sla_probability * 100):.1f}%."
    )

    risks = []
    if available_capacity < 40:
        risks.append('Limited available capacity may affect delivery confidence.')
    if predicted_hours > float(task.sla_hours or 0):
        risks.append('Predicted completion exceeds current SLA threshold.')
    if historical_score < 7.0:
        risks.append('Historical performance is below the stronger team benchmark.')
    if not required_skills:
        risks.append('No explicit required skills were supplied for this task.')
    if success_probability < 0.7:
        risks.append('Success probability is below the preferred quality threshold.')

    reasons = [
        skill_text,
        capacity_text,
        f"{(success_probability * 100):.1f}% success probability.",
        f"{(sla_probability * 100):.1f}% SLA probability.",
        sla_text,
        performance_text,
    ]

    if not risks:
        risks.append('No material risk is currently evident from the available data.')

    return {
        'summary': summary,
        'reasons': reasons,
        'strengths': strengths,
        'risks': risks,
    }
