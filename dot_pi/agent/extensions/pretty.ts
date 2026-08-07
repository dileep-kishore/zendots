import type { AssistantMessage } from "@earendil-works/pi-ai";
import {
  CustomEditor,
  type ExtensionAPI,
  type ExtensionContext,
  type KeybindingsManager,
} from "@earendil-works/pi-coding-agent";
import type { EditorTheme, TUI } from "@earendil-works/pi-tui";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

const SPINNER = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"];
const BAR_WIDTH = 12;

type Totals = { input: number; output: number; cost: number };
type DiffStat = { added: number; removed: number };

function fitBorder(left: string, width: number, color: (text: string) => string): string {
  if (width <= 0) return "";
  if (width === 1) return color("─");
  left = truncateToWidth(left, Math.max(0, width - 2), "");
  return `${color("─")}${left}${color("─".repeat(Math.max(1, width - visibleWidth(left) - 2)))}${color("─")}`;
}

function fitLine(left: string, right: string, width: number): string {
  if (width <= 0) return "";
  if (!right) return truncateToWidth(left, width, "");

  right = truncateToWidth(right, Math.min(visibleWidth(right), Math.floor(width * 0.45)), "");
  left = truncateToWidth(left, Math.max(0, width - visibleWidth(right) - 1), "");
  const gap = " ".repeat(Math.max(1, width - visibleWidth(left) - visibleWidth(right)));
  return truncateToWidth(`${left}${gap}${right}`, width, "");
}

function compactNumber(value: number): string {
  if (value < 1_000) return `${value}`;
  if (value < 1_000_000) return `${(value / 1_000).toFixed(1)}k`;
  return `${(value / 1_000_000).toFixed(1)}M`;
}

function formatDuration(ms: number): string {
  const totalSeconds = Math.floor(ms / 1_000);
  return `${Math.floor(totalSeconds / 60)}m ${totalSeconds % 60}s`;
}

function totals(ctx: ExtensionContext): Totals {
  const result: Totals = { input: 0, output: 0, cost: 0 };

  // ponytail: a branch scan keeps this extension stateless; cache if huge sessions make rendering measurable.
  for (const entry of ctx.sessionManager.getBranch()) {
    if (entry.type !== "message" || entry.message.role !== "assistant") continue;
    const message = entry.message as AssistantMessage;
    result.input += message.usage.input ?? 0;
    result.output += message.usage.output ?? 0;
    result.cost += message.usage.cost.total ?? 0;
  }
  return result;
}

function workflowMode(ctx: ExtensionContext): string | undefined {
  for (const entry of ctx.sessionManager.getEntries().toReversed()) {
    if (entry.type !== "custom" || entry.customType !== "workflow-preset") continue;
    const name = (entry.data as { name?: unknown } | undefined)?.name;
    return typeof name === "string" && name !== "off" ? name : undefined;
  }
}

export default function pretty(pi: ExtensionAPI) {
  let working = false;
  let spinner = 0;
  let timer: ReturnType<typeof setInterval> | undefined;
  let tui: TUI | undefined;
  let diff: DiffStat | undefined;
  let activeMs = 0;
  let activeSince: number | undefined;

  const stopSpinner = () => {
    if (timer) clearInterval(timer);
    timer = undefined;
  };

  const refreshDiff = async (ctx: ExtensionContext) => {
    const result = await pi.exec("git", ["diff", "--numstat", "HEAD"], { cwd: ctx.cwd }).catch(() => undefined);
    if (!result || result.code !== 0) {
      diff = undefined;
      return;
    }

    diff = result.stdout.split("\n").reduce<DiffStat>(
      (sum, line) => {
        const [added, removed] = line.split("\t");
        if (added !== "-" && removed !== "-") {
          sum.added += Number(added) || 0;
          sum.removed += Number(removed) || 0;
        }
        return sum;
      },
      { added: 0, removed: 0 },
    );
    tui?.requestRender();
  };

  pi.on("agent_start", () => {
    working = true;
    activeSince ??= Date.now();
    stopSpinner();
    timer = setInterval(() => {
      spinner = (spinner + 1) % SPINNER.length;
      tui?.requestRender();
    }, 80);
  });

  pi.on("agent_end", () => {
    working = false;
    if (activeSince !== undefined) activeMs += Date.now() - activeSince;
    activeSince = undefined;
    stopSpinner();
    tui?.requestRender();
  });

  pi.on("turn_end", (_event, ctx) => void refreshDiff(ctx));
  pi.on("session_shutdown", () => {
    stopSpinner();
    tui = undefined;
  });

  pi.on("session_start", (_event, ctx) => {
    if (ctx.mode !== "tui") return;

    ctx.ui.setTitle(`pi · ${ctx.cwd.split("/").pop() || ctx.cwd}`);
    ctx.ui.setWorkingVisible(false);
    void refreshDiff(ctx);

    ctx.ui.setFooter((instance, theme, footerData) => {
      const unsubscribe = footerData.onBranchChange(() => instance.requestRender());
      tui = instance;

      return {
        dispose: unsubscribe,
        invalidate() {},
        render(width: number): string[] {
          const stats = totals(ctx);
          const context = ctx.getContextUsage();
          const percent = Math.max(0, Math.min(100, Math.round(context?.percent ?? 0)));
          const filled = Math.round((percent / 100) * BAR_WIDTH);
          const level = percent >= 90 ? "error" : percent >= 70 ? "warning" : "success";
          const bar = theme.fg(level, "▓".repeat(filled)) + theme.fg("borderMuted", "░".repeat(BAR_WIDTH - filled));
          const model = ctx.model ? `${ctx.model.id}` : "no model";
          const project = ctx.cwd.split("/").pop() || ctx.cwd;
          const branch = footerData.getGitBranch();
          const statuses = [...footerData.getExtensionStatuses().values()].join(" · ");
          const elapsed = activeMs + (activeSince === undefined ? 0 : Date.now() - activeSince);

          let leftTop = `${theme.fg("accent", `󰧑 ${model}`)} ${theme.fg("thinkingText", pi.getThinkingLevel())}`;
          leftTop += ` ${theme.fg("borderMuted", "│")} ${theme.fg("toolTitle", ` ${project}`)}`;
          if (branch) leftTop += ` ${theme.fg("borderMuted", "│")} ${theme.fg("warning", ` ${branch}`)}`;
          if (diff && (diff.added || diff.removed)) {
            leftTop += ` ${theme.fg("success", `+${diff.added}`)} ${theme.fg("error", `-${diff.removed}`)}`;
          }

          const rightTop = statuses ? `${theme.fg("accent", "✦")} ${statuses}` : "";
          const window = context?.contextWindow ?? ctx.model?.contextWindow;
          const used = context?.tokens ?? 0;
          const leftBottom = `${bar} ${theme.fg("dim", `${percent}%`)} ${theme.fg("borderMuted", "│")} ${theme.fg("muted", `${compactNumber(used)}/${window ? compactNumber(window) : "?"}`)}`;
          const cost = stats.cost ? ` ${theme.fg("warning", `$${stats.cost.toFixed(2)}`)} ${theme.fg("borderMuted", "│")}` : "";
          const rightBottom = `${theme.fg("muted", `↑${compactNumber(stats.input)} ↓${compactNumber(stats.output)}`)}${cost} ${theme.fg("muted", `󱎫 ${formatDuration(elapsed)}`)}`;

          return [fitLine(leftTop, rightTop, width), fitLine(leftBottom, rightBottom, width), ""];
        },
      };
    });

    class PrettyEditor extends CustomEditor {
      constructor(instance: TUI, theme: EditorTheme, keybindings: KeybindingsManager) {
        super(instance, theme, keybindings, { paddingX: 0 });
        tui = instance;
      }

      render(width: number): string[] {
        const lines = super.render(width);
        if (lines.length < 2) return lines;

        const theme = ctx.ui.theme;
        const mode = workflowMode(ctx);
        const session = pi.getSessionName();
        const identity = ` π${session ? ` · ${session}` : ""}${mode ? ` · ${mode}` : ""} `;
        const activity = working ? theme.fg("accent", ` ${SPINNER[spinner]} working `) : theme.fg("muted", identity);
        lines[0] = fitBorder(activity, width, (text) => this.borderColor(text));
        return lines;
      }
    }

    ctx.ui.setEditorComponent((instance, theme, keybindings) => new PrettyEditor(instance, theme, keybindings));
  });
}
