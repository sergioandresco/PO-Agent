import csv
import io

from services.pipeline.models import BacklogResult, Feature, UserStory

_DISCIPLINE_LABELS = {
    "frontend": "Frontend",
    "backend": "Backend",
    "database": "Base de datos",
    "infrastructure": "Infraestructura",
    "qa": "QA",
    "design": "Diseño",
}


def _discipline_label(discipline: str) -> str:
    return _DISCIPLINE_LABELS.get(discipline, discipline)


def to_markdown(backlog: BacklogResult) -> str:
    lines = [
        f"# Backlog: {backlog.meeting_id}",
        "",
        f"_Generado: {backlog.generated_at.isoformat()} — pipeline v{backlog.pipeline_version}_",
        "",
    ]

    features_by_epic: dict[str, list[Feature]] = {epic.id: [] for epic in backlog.epics}
    for feature in backlog.features:
        features_by_epic.setdefault(feature.epic_id, []).append(feature)
    stories_by_feature: dict[str, list[UserStory]] = {
        feature.id: [] for feature in backlog.features
    }
    for story in backlog.stories:
        stories_by_feature.setdefault(story.feature_id, []).append(story)

    for epic in backlog.epics:
        lines.append(f"## {epic.title} `[{epic.status.value}]`")
        lines.append("")
        lines.append(epic.description)
        lines.append("")

        for feature in features_by_epic.get(epic.id, []):
            lines.append(f"### {feature.title} `[{feature.status.value}]`")
            lines.append("")
            lines.append(feature.description)
            lines.append("")

            for story in stories_by_feature.get(feature.id, []):
                lines.append(f"#### {story.title} `[{story.status.value}]`")
                lines.append("")
                lines.append(
                    f"**Como** {story.as_a}, **quiero** {story.i_want}, "
                    f"**para** {story.so_that}."
                )
                lines.append("")
                if story.acceptance_criteria:
                    lines.append("**Criterios de aceptación:**")
                    lines.extend(
                        f"{i}. Dado {ac.given}, cuando {ac.when}, entonces {ac.then}."
                        for i, ac in enumerate(story.acceptance_criteria, start=1)
                    )
                    lines.append("")
                if story.subtasks:
                    lines.append("**Subtareas:**")
                    lines.extend(
                        f"- [ ] [{_discipline_label(st.discipline.value)}] {st.title}"
                        for st in story.subtasks
                    )
                    lines.append("")
                if story.estimate:
                    lines.append(
                        f"**Estimación:** {story.estimate.story_points} pts — "
                        f"{story.estimate.rationale}"
                    )
                    lines.append("")
                lines.append("**Fuente:**")
                lines.extend(
                    f"> {src.speaker or 'Desconocido'}: \"{src.verbatim}\"" for src in story.sources
                )
                lines.append("")

    return "\n".join(lines)


def to_csv(backlog: BacklogResult) -> str:
    epics_by_id = {epic.id: epic for epic in backlog.epics}
    features_by_id = {feature.id: feature for feature in backlog.features}

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "epic",
            "feature",
            "story_title",
            "as_a",
            "i_want",
            "so_that",
            "story_points",
            "status",
            "confidence",
        ]
    )
    for story in backlog.stories:
        feature = features_by_id.get(story.feature_id)
        epic = epics_by_id.get(feature.epic_id) if feature else None
        writer.writerow(
            [
                epic.title if epic else "",
                feature.title if feature else "",
                story.title,
                story.as_a,
                story.i_want,
                story.so_that,
                story.estimate.story_points if story.estimate else "",
                story.status.value,
                story.confidence,
            ]
        )
    return buffer.getvalue()
