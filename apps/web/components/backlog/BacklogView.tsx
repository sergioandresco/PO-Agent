import type { BacklogResult } from "@po-agent/contracts";
import { EpicSection } from "./EpicSection";
import { FeatureCard } from "./FeatureCard";
import { RawJsonViewer } from "./RawJsonViewer";
import { StoryCard } from "./StoryCard";

export function BacklogView({
  result,
  onUpdateArtifact,
}: {
  result: BacklogResult;
  onUpdateArtifact: (
    artifactId: string,
    updates: Record<string, unknown>,
  ) => Promise<void>;
}) {
  const storyIndexById = new Map(result.stories.map((story, i) => [story.id, i]));

  return (
    <div className="flex flex-col gap-3">
      {result.epics.map((epic) => {
        const epicFeatures = result.features.filter(
          (feature) => feature.epicId === epic.id,
        );
        const epicStoryCount = result.stories.filter((story) =>
          epicFeatures.some((feature) => feature.id === story.featureId),
        ).length;

        return (
          <EpicSection
            key={epic.id}
            epic={epic}
            featureCount={epicFeatures.length}
            storyCount={epicStoryCount}
            onSave={(updates) => onUpdateArtifact(epic.id, updates)}
          >
            {epicFeatures.map((feature) => {
              const featureStories = result.stories.filter(
                (story) => story.featureId === feature.id,
              );
              return (
                <FeatureCard
                  key={feature.id}
                  feature={feature}
                  storyCount={featureStories.length}
                  onSave={(updates) => onUpdateArtifact(feature.id, updates)}
                >
                  {featureStories.map((story) => (
                    <StoryCard
                      key={story.id}
                      story={story}
                      index={storyIndexById.get(story.id) ?? 0}
                      onSave={(updates) => onUpdateArtifact(story.id, updates)}
                    />
                  ))}
                </FeatureCard>
              );
            })}
          </EpicSection>
        );
      })}

      <RawJsonViewer result={result} />
    </div>
  );
}
