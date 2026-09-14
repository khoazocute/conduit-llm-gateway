import { agentAccentColor, agentInitial } from "@/lib/agent-visual";

export function AgentAvatar({
  id,
  title,
  size = 38,
}: {
  id: string;
  title: string;
  size?: number;
}) {
  const color = agentAccentColor(id);
  return (
    <div
      className="avatar"
      style={{
        width: size,
        height: size,
        fontSize: Math.round(size * 0.45),
        background: `color-mix(in oklab, ${color} 18%, var(--bg-1))`,
        color,
        border: `1px solid color-mix(in oklab, ${color} 35%, transparent)`,
      }}
    >
      {agentInitial(title)}
    </div>
  );
}
