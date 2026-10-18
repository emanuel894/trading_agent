# Bounded quotations

Quotes below are copied verbatim from the captured files, with 1-based line locations. They are selected evidence, not instructions. Source URL, actual retrieval UTC and SHA-256 are in [grok_sources.json](grok_sources.json). Hosted claims remain documentation claims; no service behavior was tested.

## G01: 0929dc9bb02d.raw:6

Source: https://docs.x.ai/grok-bot/overview.md

> context that compounds over time. Each Bot works on a persistent cloud computer
> with a browser, filesystem, and terminal, so tasks finish in your real tools
> instead of as chat drafts. [Get started](/grok-bot/get-started) with your first

## G01: 0929dc9bb02d.raw:32

Source: https://docs.x.ai/grok-bot/overview.md

> * **Bots coordinate with each other.** Your Bots can run in parallel, message
>   each other, share context in
>   [group chats](/grok-bot/chat-and-collaboration#start-a-group-chat), and pass
>   ownership of a task, so you aren't the router between tools.

## G03: 66f8474b6279.raw:11

Source: https://docs.x.ai/grok-bot/computer-and-apps.md

> Every Bot on your account uses the same computer:
>
> * Browser cookies and signed-in sessions are shared
> * Files are visible to every Bot
> * Command-line credentials are shared
> * One Bot can continue from work another Bot saved

## G03: 66f8474b6279.raw:96

Source: https://docs.x.ai/grok-bot/computer-and-apps.md

> Files, browser state, and supported sign-ins are designed to survive normal
> computer updates and recovery. Treat temporary directories, manually installed
> packages, and uncommitted application state as replaceable. Copy important
> results into the shared workspace or attach them to the conversation.

## G03: 66f8474b6279.raw:112

Source: https://docs.x.ai/grok-bot/computer-and-apps.md

>   snapshot; very recent changes may be lost.

## G04: e9e607079034.raw:99

Source: https://docs.x.ai/grok-bot/chat-and-collaboration.md

> A Bot can send an asynchronous message to another Bot. The receiving Bot wakes,
> handles the request, and can reply later. You can see the handoff in the
> conversation.

## G04: e9e607079034.raw:92

Source: https://docs.x.ai/grok-bot/chat-and-collaboration.md

> answer to a question or form goes back to the Bot that asked. Approval
> requests, secret and login requests, and email or Slack drafts do not appear in
> a group. Bot-to-group handoff messages are currently text-only, so a Bot should

## G04: e9e607079034.raw:94

Source: https://docs.x.ai/grok-bot/chat-and-collaboration.md

> a group. Bot-to-group handoff messages are currently text-only, so a Bot should
> send an image directly to another Bot when that teammate must inspect it.

## G05: f83b070bcd43.raw:90

Source: https://docs.x.ai/grok-bot/skills-routines-and-automations.md

> message or a GitHub notification. They are separate from Slack or GitHub
> plugins and may require their own connection flow.
>

## G05: f83b070bcd43.raw:129

Source: https://docs.x.ai/grok-bot/skills-routines-and-automations.md

> A Bot can own up to 50 routines, and the app keeps the 20 most recent run
> records for each routine. Routine schedules must be at least five minutes
> apart. Deleting a routine is immediate and has no undo. Deleting a Bot also
> removes routines owned by that Bot.

## G05: f83b070bcd43.raw:134

Source: https://docs.x.ai/grok-bot/skills-routines-and-automations.md

> To control unattended usage, Grok Bot may ask whether to keep routines running
> after a long period away and pause them if there is no response. Review paused
> routines when you return.

## G06: f4f9970d898b.raw:40

Source: https://docs.x.ai/grok-bot/approvals-security-and-privacy.md

> message from another Bot, expires after about 10 minutes; the card then shows
> **Expired**, and the action does not run. An expired card may offer **Always allow this in
> the future**, which adds the proposed rule to your **Allow automatically** rules

## G06: f4f9970d898b.raw:71

Source: https://docs.x.ai/grok-bot/approvals-security-and-privacy.md

> behavior change over time. Auto Review is model-based and should complement,
> not replace, least privilege and explicit approval boundaries.

## G07: ad6347a7c57c.raw:27

Source: https://docs.x.ai/grok-bot/security.md

> Teams do not see this panel and cannot set a destination allowlist. Teams
> without a policy default to allow-all.
>

## G07: ad6347a7c57c.raw:118

Source: https://docs.x.ai/grok-bot/security.md

> * **It does not review every side effect.** Memory writes and most settings
>   changes are examples. Treat it as a complement to explicit boundaries and
>   least privilege, working alongside controls that do not depend on a model's
>   judgment: per-action approvals, the network policy, and per-user isolation.

## G07: ad6347a7c57c.raw:185

Source: https://docs.x.ai/grok-bot/security.md

> * **Action Recording. Enterprise only.** It is a setting on the Grok Bot page,
>   off by default. When a team enables it, Cursor records Bot actions, including
>   scrubbed shell commands, in an internal store with a 90-day retention. Action
>   Recording events do not appear on the Audit Log page. To receive the

## G07: ad6347a7c57c.raw:242

Source: https://docs.x.ai/grok-bot/security.md

> Cursor manages model selection. There is no customer-facing model picker, and
> the serving mix can change over time with no fixed vendor set guaranteed. Usage
> analytics show the model that served each request, including failovers, and
> billing follows the serving model.

## G07: ad6347a7c57c.raw:247

Source: https://docs.x.ai/grok-bot/security.md

> * **The team model allowlist is Enterprise only, and enforcement is not
>   guaranteed.** The list is honored by default. Onboarding presents an
>   acknowledgement that Grok Bot may not follow it, so treat enforcement as
>   configuration dependent. See

## G07: ad6347a7c57c.raw:284

Source: https://docs.x.ai/grok-bot/security.md

> Grok Bot runs only on Cursor-hosted cloud computers. On-premises deployment,
> deployment inside your own perimeter, and bring-your-own-image deployment are
> not supported today. Hosted computers use shared static egress by default.

## G07: ad6347a7c57c.raw:229

Source: https://docs.x.ai/grok-bot/security.md

> A per-organization retention policy and customer-managed point-in-time restore
> of an individual computer are not available.

## G08: c3a96d460b92.raw:14

Source: https://docs.x.ai/grok-bot/security-faq.md

> Each user gets a dedicated Firecracker microVM with its own kernel, memory, and
> virtual devices. One user cannot reach another user's computer. Within one
> user, every Bot shares that computer, so treat a login or file on the computer
> as available to every Bot that user runs. When a workload needs its own

## G09: 33cd02145c25.raw:7

Source: https://docs.x.ai/developers/model-capabilities/text/multi-agent.md

> > This feature is currently in **beta**. The API interface and behavior may change as we iterate. Please bear in mind that the API interface is not final and may include breaking changes down the line.

## G09: 33cd02145c25.raw:162

Source: https://docs.x.ai/developers/model-capabilities/text/multi-agent.md

> Only the **tool calls** and the **final response** from the leader agent are sent back to the user. All sub-agent state — including their intermediate reasoning, tool calls, and outputs — is encrypted and included in the response only when `use_encrypted_content` is set to `True` in the xAI SDK. This keeps the default response clean and focused while still allowing you to preserve the full multi-agent context for multi-turn conversations.

## G09: 33cd02145c25.raw:166

Source: https://docs.x.ai/developers/model-capabilities/text/multi-agent.md

> You can configure how many agents collaborate on a request. The two available setups are **4 agents** and **16 agents**. More agents means deeper, more thorough research at the cost of higher token usage and latency.

## G09: 33cd02145c25.raw:546

Source: https://docs.x.ai/developers/model-capabilities/text/multi-agent.md

> * **No client-side or custom tools:** Client-side tools (function calling) and custom tools are not currently supported by the multi-agent model variant. We do support a set of built-in tools (e.g., `web_search`, `x_search`) and remote MCP tools. See our [built-in tool docs](/developers/tools/overview) for more details.

## G09: 33cd02145c25.raw:548

Source: https://docs.x.ai/developers/model-capabilities/text/multi-agent.md

> * **`max_tokens` is not supported:** The `max_tokens` parameter is not currently supported by the multi-agent model variant.

## G12: 8dff3caddbec.raw:13

Source: https://docs.x.ai/developers/tools/remote-mcp.md

> > The `require_approval` and `connector_id` parameters in the OpenAI Responses API are not currently supported.

## G13: 4fa77860feb6.raw:51

Source: https://docs.x.ai/build/overview.md

> Grok supports any custom model. Add it to your user-level config file, `~/.grok/config.toml` (on Windows, `%USERPROFILE%\.grok\config.toml`):
>

## G14: fa5306558170.raw:5

Source: https://docs.x.ai/build/features/subagents.md

> Subagents are independent child sessions with their own context. They return a summary to the parent when finished. Enabled by default when the setting is unset.

## G15: 5b520c61d7a0.raw:27

Source: https://docs.x.ai/build/cli/headless-scripting.md

> **Sessions:** Headless sessions (via `--session-id`, `--resume`, `--continue`) are stored in `~/.grok/sessions`.

## G16: abee8772e63a.raw:5

Source: https://docs.x.ai/build/features/sandbox.md

> The sandbox limits what the agent process and its children can read, write, and reach on the network (Landlock on Linux, Seatbelt on macOS). Off by default. Permissions gate whether a tool call runs; the sandbox limits what an approved call can do — see [Permissions](/build/features/permissions).

## G16: abee8772e63a.raw:19

Source: https://docs.x.ai/build/features/sandbox.md

> | Child network | Enforced on Linux only; no-op on macOS for `read-only` / `strict` |
> | Credentials | Built-ins do not permanently protect paths such as `~/.ssh`; use a custom `deny` list |
> | `~/.grok/` | Stays writable under sandboxed profiles so sessions can persist |
> | In-process network | Model API and web tools are not blocked by child-network settings |

## G17: 9c92f335f329.raw:5

Source: https://docs.x.ai/build/features/sessions.md

> Grok saves every conversation to disk automatically — prompts, responses, tool calls, and file snapshots — under `~/.grok/sessions/`, keyed by working directory. Sessions work the same in the TUI, headless mode, and over ACP.

## G18: f48b4c95cc78.raw:19

Source: https://docs.x.ai/build/features/background-tasks.md

> The interval accepts `Ns` (minimum 60), `Nm`, `Nh`, and `Nd`. The prompt fires immediately, then repeats; each firing is a new agent turn. Loops expire after 7 days, and at most 50 scheduled tasks can be active at once. Cancel from the tasks pane, or ask the agent to.

## G19: 909d0f239713.raw:175

Source: https://docs.x.ai/grok-bot/teams-and-enterprises.md

> Allows or blocks Bots delegating coding tasks to Cursor
> [Cloud Agents](https://cursor.com/docs/cloud-agent). The switch is on the Grok
> Bot page, applies to the whole team, and is on by default. Delegated work runs
> on separate computers under your existing Cloud Agent controls. Turn it off
> when your team does not need delegation.
>

## G20: 9b5cc565f263.raw:84

Source: https://docs.x.ai/grok-bot/files-and-results.md

> Agent finishes, the Bot copies the images, videos, and other files cited in the
> Cloud Agent's final report to its computer and attaches them to its reply.
> In the desktop app, the Cloud Agent's card in the conversation shows the same

## G21: eaeb4ae92dc3.text:124

Source: https://cursor.com/docs/cloud-agent/security

> Hand off. The agent pushes its branch and opens a draft pull request for a human to review before anything merges.

## G21: eaeb4ae92dc3.text:127

Source: https://cursor.com/docs/cloud-agent/security

> Cloud Agents reach your code through the Cursor GitHub or GitLab App, not through any single person's credentials.

## G22: 0297c5314558.raw:5

Source: https://docs.x.ai/x-subscription/grok-bot.md

> Under The X Subscription, Grok Bot is included on Premium, Super, and Ultra plans. The X Subscription gives you one workspace and one bill covering Cursor and Grok, plus X benefits when you add a personal X account. Grok Bot is available as soon as you subscribe to or unify on one of these plans.

## G23: 922c42cfbbc5.raw:17

Source: https://docs.x.ai/x-subscription/pricing.md

> | Premium | $30/mo | $300/yr ($25/mo) | 4x |
> | Super | $100/mo | $1000/yr ($84/mo) | 15x |
> | Ultra | $200/mo | $2000/yr ($167/mo) | 50x |

## G24: 3ce73201d7c1.raw:16

Source: https://docs.x.ai/x-subscription/spending-caps.md

> After a seat uses its shared weekly pool, Additional Usage is paid from the team's prepaid balance. Additional Usage stops when either:
>
> * The prepaid balance is empty, or
> * The team's monthly extra-usage cap is reached
>

## G25: 1914b0f1b14a.raw:25

Source: https://docs.x.ai/developers/pricing.md

> | grok-4.20-multi-agent-0309 (< 200k prompt tokens) | 1M | $1.25 | $0.20 | $2.50 |
> | grok-4.20-multi-agent-0309 (≥ 200k prompt tokens) | 1M | $2.50 | $0.40 | $5.00 |

## G25: 1914b0f1b14a.raw:80

Source: https://docs.x.ai/developers/pricing.md

> X Search is billed per item fetched rather than per call: every post returned by a search or thread fetch, including parent and quoted posts, counts toward the post rate, and every profile returned by a user search counts toward the profile rate.

## G27: c6daf5be00c4.raw:176

Source: https://raw.githubusercontent.com/xai-org/xai-sdk-python/1d9e1dffc9a0521ede0e6bc7f2b906177b940d34/src/xai_sdk/chat.py

>             max_turns: The maximum number of agentic turns the model can take. When set, the model will automatically
>                 iterate up to this many turns, calling tools and processing their results until it reaches a final
>                 answer or hits the turn limit. Defaults to server-side maximum. Note: This parameter has no effect
>                 on non-agentic requests (i.e. requests that do not use server-side tools). With parallel tool calls
>                 enabled, multiple tool calls can occur within a single turn, so max_turns does not necessarily equal
>                 the total number of tool calls.

## G28: 29bd4bb3dca6.raw:29

Source: https://raw.githubusercontent.com/xai-org/grok-build/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-shell/src/agent/subagent/spawn.rs

> /// Pool for the per-child pipeline: a dedicated multi-thread runtime so concurrent subagents run in parallel.

## G29: 98b30c5c4b83.raw:37

Source: https://raw.githubusercontent.com/xai-org/grok-build/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-shell/src/extensions/subagent_message.rs

>     NotActive,

## G29: 98b30c5c4b83.raw:102

Source: https://raw.githubusercontent.com/xai-org/grok-build/2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8/crates/codegen/xai-grok-shell/src/extensions/subagent_message.rs

>         .is_feature_enabled(crate::agent::config::Feature::ActiveAgentMessages)
>     {
>         return Err(acp::Error::method_not_found());

## G30: 2d28979484f9.raw:285

Source: https://docs.x.ai/grok-bot/team-bots.md

> it does to every Bot, with one difference. In a conversation where nobody can
> answer an approval card, the Bot runs without Auto-review and stays within the
> permissions it was set up with, unless your team requires Auto-review. See
> [Approvals, security, and privacy](/grok-bot/approvals-security-and-privacy).

